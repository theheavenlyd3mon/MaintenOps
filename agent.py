#!/usr/bin/env python3
"""
MaintenOps Agent — Main Orchestrator

End-to-end property maintenance pipeline:
  1. Receive tenant report → create ticket
  2. Triage (Nemotron → classify urgency/trade)
  3. Habitability check (deadline lookup)
  4. Vendor matching (Nemotron → rank top 3)
  5. Quote simulation (3 demo responses)
  6. Quote comparison (Nemotron → benchmark)
  7. NemoClaw guardrails (vendor verify, spending limits)
  8. Dispatch vendor → notify tenant
  9. Work complete simulation
 10. Stripe payment (vendor payout + 3% commission)
 11. Warranty check → claim generation

Usage:
    python3 agent.py "AC not cooling, 87 degrees, have a newborn"
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agent")

# ---------------------------------------------------------------------------
# Tool imports — each wrapped so the agent runs even if a module is missing
# ---------------------------------------------------------------------------

try:
    from tools.triage import triage_issue
except ImportError:
    triage_issue = None
    logger.warning("tools.triage not available")

try:
    from tools.compliance import check_habitability
except ImportError:
    check_habitability = None
    logger.warning("tools.compliance not available")

try:
    from tools.vendor_match import match_vendors
except ImportError:
    match_vendors = None
    logger.warning("tools.vendor_match not available")

try:
    from tools.quotes import compare_quotes
except ImportError:
    compare_quotes = None
    logger.warning("tools.quotes not available")

try:
    from tools.warranty import check_warranty, generate_claim
except ImportError:
    check_warranty = None
    generate_claim = None
    logger.warning("tools.warranty not available")

try:
    from guardrails import check_action, check_vendor_verify, check_spending
except ImportError:
    check_action = None
    check_vendor_verify = None
    check_spending = None
    logger.warning("guardrails not available")

try:
    from config import get_settings, get_nemotron_client, init_stripe
    from clients.stripe_client import pay_vendor, create_payment_intent
except ImportError:
    get_settings = None
    logger.warning("config/stripe not available — payments will be simulated")

# ---------------------------------------------------------------------------
# Demo data — hardcoded owner and property for the demo
# ---------------------------------------------------------------------------

DEMO_OWNER = {
    "name": "Demo Owner",
    "email": "owner@example.com",
    "stripe_customer_id": "cus_demo_001",
    "maintenance_limit": 1500.00,
    "emergency_limit": 5000.00,
}

DEMO_PROPERTY = {
    "address": "123 Main St, San Francisco, CA 94102",
    "state": "CA",
    "zip_code": "94102",
}

DEMO_VENDORS = {
    "CoolTech HVAC": {
        "name": "CoolTech HVAC",
        "trade": "HVAC",
        "rating": 4.9,
        "stripe_connect_account_id": "acct_vendor_001",
        "license_active": True,
        "license_type": "HVAC",
        "required_trade": "HVAC",
        "insurance_active": True,
        "insurance_coverage": 2_000_000,
        "workers_comp_active": True,
    },
    "Bay Area Climate Control": {
        "name": "Bay Area Climate Control",
        "trade": "HVAC",
        "rating": 4.7,
        "stripe_connect_account_id": "acct_vendor_002",
        "license_active": True,
        "license_type": "HVAC",
        "required_trade": "HVAC",
        "insurance_active": True,
        "insurance_coverage": 1_500_000,
        "workers_comp_active": True,
    },
    "Pacific HVAC Services": {
        "name": "Pacific HVAC Services",
        "trade": "HVAC",
        "rating": 4.2,
        "stripe_connect_account_id": "acct_vendor_003",
        "license_active": True,
        "license_type": "HVAC",
        "required_trade": "HVAC",
        "insurance_active": True,
        "insurance_coverage": 1_000_000,
        "workers_comp_active": True,
    },
}

# ---------------------------------------------------------------------------
# Pipeline phases
# ---------------------------------------------------------------------------


async def phase_triage(tenant_report: str, state: str) -> dict:
    """Phase 1: Triage the tenant report via Nemotron (or keyword fallback)."""
    logger.info("=" * 60)
    logger.info("PHASE 1 — TRIAGE")
    logger.info("=" * 60)
    logger.info("Tenant report: %s", tenant_report[:120])

    if triage_issue is None:
        raise RuntimeError("Triage module not available")

    result = await triage_issue(tenant_report, state)
    logger.info("Triage result: urgency=%s  trade=%s  source=%s",
                result.get("urgency"), result.get("trade_needed"), result.get("source"))
    return result


async def phase_habitability(state: str, issue_type: str, urgency: str) -> dict:
    """Phase 2: Check habitability compliance deadlines."""
    logger.info("=" * 60)
    logger.info("PHASE 2 — HABITABILITY CHECK")
    logger.info("=" * 60)

    if check_habitability is None:
        logger.warning("Habitability module not available — skipping")
        return {"applicable": False, "deadline_hours": None, "notes": "Module unavailable"}

    result = await check_habitability(state, issue_type, urgency)
    logger.info("Habitability: applicable=%s deadline=%s hours notes=%s",
                result.get("applicable"), result.get("deadline_hours"), result.get("notes"))
    return result


async def phase_vendor_match(trade: str, zip_code: str, urgency: str) -> list[dict]:
    """Phase 3: Find and rank top 3 vendors."""
    logger.info("=" * 60)
    logger.info("PHASE 3 — VENDOR MATCHING")
    logger.info("=" * 60)

    if match_vendors is None:
        logger.warning("Vendor match module not available — using hardcoded defaults")
        return [
            {"name": "CoolTech HVAC", "trade": trade, "rating": 4.9, "match_score": 98.0},
            {"name": "Bay Area Climate Control", "trade": trade, "rating": 4.7, "match_score": 94.0},
            {"name": "Pacific HVAC Services", "trade": trade, "rating": 4.2, "match_score": 84.0},
        ]

    results = await match_vendors(trade, zip_code, urgency)
    logger.info("Matched %d vendors", len(results))
    for v in results:
        logger.info("  %s — ★%s score=%s", v.get("name"), v.get("rating"), v.get("match_score"))
    return results


async def phase_simulate_quotes(vendors: list[dict], issue_description: str) -> list[dict]:
    """Phase 4: Simulate 3 vendor quotes (demo mode — no real vendor portal)."""
    logger.info("=" * 60)
    logger.info("PHASE 4 — QUOTE SIMULATION")
    logger.info("=" * 60)

    # Generate plausible quotes based on vendor tier
    quote_map = {
        "CoolTech HVAC": 850.00,
        "Bay Area Climate Control": 1200.00,
        "Pacific HVAC Services": 950.00,
    }

    quotes = []
    for v in vendors[:3]:
        name = v.get("name", "Unknown")
        amount = 0.0
        for key, val in quote_map.items():
            if key.lower() in name.lower() or name.lower() in key.lower():
                amount = val
                break
        if amount == 0.0:
            amount = 800.0 + (v.get("rating", 4.0) * 50)

        quotes.append({
            "vendor_name": name,
            "quote_amount": amount,
            "scope_of_work": issue_description,
        })

    logger.info("Generated %d quotes", len(quotes))
    for q in quotes:
        logger.info("  %s — $%.2f", q["vendor_name"], q["quote_amount"])
    return quotes


async def phase_compare_quotes(quotes: list[dict], zip_code: str) -> dict:
    """Phase 5: Compare quotes against benchmarks and recommend."""
    logger.info("=" * 60)
    logger.info("PHASE 5 — QUOTE COMPARISON")
    logger.info("=" * 60)

    if compare_quotes is None:
        logger.warning("Quote comparison module not available — using cheapest")
        cheapest = min(quotes, key=lambda q: q["quote_amount"])
        return {
            "recommendation": {
                "vendor_name": cheapest["vendor_name"],
                "quote_amount": cheapest["quote_amount"],
                "reason": "Cheapest quote selected (fallback — no comparison engine)",
            },
            "analysis": [],
            "summary": f"Selected cheapest: {cheapest['vendor_name']} at ${cheapest['quote_amount']:.2f}",
        }

    result = await compare_quotes(quotes, zip_code)
    logger.info("Recommendation: %s at $%.2f",
                result["recommendation"]["vendor_name"],
                result["recommendation"]["quote_amount"])
    logger.info("Summary: %s", result["summary"])
    return result


async def phase_guardrails(vendor: dict, quote: dict, triage_result: dict) -> dict:
    """Phase 6: Run NemoClaw guardrail checks — vendor verify + spending."""
    logger.info("=" * 60)
    logger.info("PHASE 6 — NEMOCLAW GUARDRAILS")
    logger.info("=" * 60)

    results = {"passed": True, "blocks": [], "warnings": []}

    # 6a: Vendor verification guardrail
    if check_vendor_verify is not None:
        logger.info("Running vendor_verify guardrail...")
        vendor_result = check_vendor_verify(vendor)
        if not vendor_result["passed"]:
            results["passed"] = False
            results["blocks"].extend(vendor_result["blocks"])
            logger.warning("VENDOR VERIFY BLOCKED: %s", "; ".join(vendor_result["blocks"]))
        else:
            logger.info("Vendor verify PASSED")
    else:
        logger.info("Vendor verify guardrail not available — skipped")

    # 6b: Spending authorization guardrail
    if check_spending is not None:
        logger.info("Running spending_limits guardrail...")
        quote_check = {
            "total": quote.get("quote_amount", 0),
            "issue": triage_result,
        }
        spending_result = check_spending(quote_check, DEMO_OWNER)
        if not spending_result["passed"]:
            results["passed"] = False
            results["blocks"].extend(spending_result["blocks"])
            logger.warning("SPENDING BLOCKED: %s", "; ".join(spending_result["blocks"]))
        else:
            logger.info("Spending limits PASSED")
        results["warnings"].extend(spending_result.get("warnings", []))
    else:
        logger.info("Spending limits guardrail not available — skipped")

    # 6c: Action-level guardrail
    if check_action is not None:
        action_data = {
            "triage": triage_result,
            "vendor": vendor,
            "quote": quote,
        }
        action_result = check_action("dispatch_vendor", action_data)
        if not action_result["passed"]:
            results["passed"] = False
            results["blocks"].extend(action_result["blocks"])
        results["warnings"].extend(action_result.get("warnings", []))

    if results["passed"]:
        logger.info("ALL GUARDRAILS PASSED ✅")
    else:
        logger.warning("GUARDRAIL BLOCKERS: %s", "; ".join(results["blocks"]))

    return results


async def phase_dispatch(vendor_name: str, quote_amount: float, triage_result: dict) -> dict:
    """Phase 7: Dispatch vendor and notify tenant (simulated)."""
    logger.info("=" * 60)
    logger.info("PHASE 7 — DISPATCH VENDOR")
    logger.info("=" * 60)

    dispatch_id = str(uuid.uuid4())[:8].upper()
    urgency = triage_result.get("urgency", "routine")

    eta_map = {"emergency": "30-60 minutes", "urgent": "2-4 hours", "routine": "24-48 hours"}
    eta = eta_map.get(urgency, "24-48 hours")

    dispatch_record = {
        "dispatch_id": f"DSP-{dispatch_id}",
        "vendor_name": vendor_name,
        "quote_amount": quote_amount,
        "urgency": urgency,
        "eta": eta,
        "dispatched_at": datetime.now(timezone.utc).isoformat(),
        "status": "dispatched",
    }

    logger.info("Dispatched %s — ETA: %s — Ref: %s", vendor_name, eta, dispatch_record["dispatch_id"])
    return dispatch_record


async def phase_work_complete(dispatch_id: str) -> dict:
    """Phase 8: Simulate work completion."""
    logger.info("=" * 60)
    logger.info("PHASE 8 — WORK COMPLETION")
    logger.info("=" * 60)

    await asyncio.sleep(0.5)  # Simulate the work taking place

    completion = {
        "dispatch_id": dispatch_id,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "notes": "Work completed successfully. Tenant confirmed resolution.",
        "photo_verified": True,
    }
    logger.info("Work completed for dispatch %s", dispatch_id)
    return completion


async def phase_payment(vendor_name: str, quote_amount: float, vendor_stripe_account: str) -> dict:
    """Phase 9: Pay vendor via Stripe Connect with 3% commission.

    Attempts a live Stripe Transfer. Falls back to simulation when:
    - No Stripe key configured
    - Connect account doesn't exist or isn't onboarded
    - Any Stripe API error occurs
    """
    logger.info("=" * 60)
    logger.info("PHASE 9 — STRIPE PAYMENT")
    logger.info("=" * 60)

    commission = round(quote_amount * 0.03, 2)
    vendor_payout = round(quote_amount - commission, 2)

    # Try live Stripe transfer
    try:
        import stripe
        from config import get_settings

        s = get_settings()
        if s and s.stripe_secret_key:
            stripe.api_key = s.stripe_secret_key

            # Look up the real Connect account
            real_account = vendor_stripe_account
            if not real_account or real_account.startswith("acct_vendor_"):
                # Map demo vendor names to real Connect accounts
                try:
                    with open(os.path.join(os.path.dirname(__file__), "stripe_vendors.json")) as f:
                        vendor_map = json.load(f)
                        real_account = vendor_map.get(vendor_name, real_account)
                except (FileNotFoundError, json.JSONDecodeError):
                    pass

            # Verify it's a real Stripe acct_ ID
            if real_account and real_account.startswith("acct_"):
                amount_cents = int(quote_amount * 100)
                commission_cents = int(commission * 100)
                vendor_cents = amount_cents - commission_cents

                transfer = stripe.Transfer.create(
                    amount=vendor_cents,
                    currency="usd",
                    destination=real_account,
                    transfer_group=f"mtops-{uuid.uuid4().hex[:8]}",
                    metadata={
                        "vendor": vendor_name,
                        "commission_cents": str(commission_cents),
                        "commission_pct": "3.0",
                    },
                )

                payment = {
                    "vendor_name": vendor_name,
                    "quote_amount": quote_amount,
                    "commission_pct": 3.0,
                    "commission_amount": commission,
                    "vendor_payout": vendor_payout,
                    "stripe_connect_account": real_account,
                    "payment_status": "transferred",
                    "transfer_id": transfer.id,
                    "note": "Live Stripe Connect transfer",
                }
                logger.info("Payment: $%.2f total → $%.2f vendor (%.2f%% commission $%.2f)",
                            quote_amount, vendor_payout, 3.0, commission)
                logger.info("Transfer ID: %s", payment["transfer_id"])
                logger.info("Destination: %s (%s)", vendor_name, real_account)
                return payment

    except Exception as exc:
        err_msg = str(exc)
        if "insufficient available funds" in err_msg:
            logger.warning("Live Stripe transfer skipped: platform balance $0 (expected in test mode) — falling back to simulation")
        else:
            logger.warning("Live Stripe transfer failed: %s — falling back to simulation", err_msg[:100])

    # Simulation fallback
    logger.info("Using simulated payment (Stripe key or Connect account not available)")
    payment = {
        "vendor_name": vendor_name,
        "quote_amount": quote_amount,
        "commission_pct": 3.0,
        "commission_amount": commission,
        "vendor_payout": vendor_payout,
        "stripe_connect_account": vendor_stripe_account,
        "payment_status": "simulated",
        "transfer_id": f"tr_sim_{uuid.uuid4().hex[:12]}",
        "note": "Simulated Stripe Connect transfer — no live API call made",
    }

    logger.info("Payment: $%.2f total → $%.2f vendor (%.2f%% commission $%.2f)",
                quote_amount, vendor_payout, 3.0, commission)
    logger.info("Transfer ID: %s", payment["transfer_id"])
    return payment


async def phase_warranty(property_address: str, issue_description: str, estimated_cost: float) -> dict:
    """Phase 10: Check warranty and file claim if eligible."""
    logger.info("=" * 60)
    logger.info("PHASE 10 — WARRANTY CHECK")
    logger.info("=" * 60)

    if check_warranty is None:
        logger.warning("Warranty module not available — skipping")
        return {"skipped": True, "reason": "Module unavailable"}

    warranty_result = await check_warranty(property_address)

    if not warranty_result.get("appliance_found"):
        logger.info("No appliance found at address — warranty check skipped")
        return {"skipped": True, "reason": "No appliance found"}

    logger.info("Warranty active: %s — %d days remaining",
                warranty_result.get("warranty_active"),
                warranty_result.get("days_remaining", 0))

    if not warranty_result.get("warranty_active"):
        logger.info("Warranty expired — no claim filed")
        return {"skipped": True, "reason": "Warranty expired"}

    # Generate claim
    if generate_claim is not None:
        appliance = warranty_result.get("appliance", {})
        claim = await generate_claim(
            ticket_id=f"T-{uuid.uuid4().hex[:6].upper()}",
            appliance_id=appliance.get("id", 1),
            issue_description=issue_description,
            estimated_repair_cost=estimated_cost,
        )
        logger.info("Claim generated: %s", claim.get("claim_id", "unknown"))
        return {"claim_generated": True, "claim": claim}

    return {"claim_generated": False, "reason": "Claim module unavailable"}


# ---------------------------------------------------------------------------
# Main orchestration pipeline
# ---------------------------------------------------------------------------


async def run_pipeline(tenant_report: str, state: str = "CA", zip_code: str = "94102") -> dict:
    """Run the full MaintenOps pipeline end-to-end.

    Parameters
    ----------
    tenant_report : str
        Free-text maintenance report from the tenant.
    state : str
        Two-letter US state code (default ``\"CA\"``).
    zip_code : str
        Property ZIP code (default ``\"94102\"``).

    Returns
    -------
    dict
        Full pipeline result with all phase outputs.
    """
    pipeline_start = datetime.now(timezone.utc)
    ticket_id = f"T-{uuid.uuid4().hex[:8].upper()}"
    logger.info("")
    logger.info("╔" + "═" * 58 + "╗")
    logger.info("║          MAINTENOPS AGENT — Pipeline Run")
    logger.info("║  Ticket: %s", ticket_id)
    logger.info("║  Report: %s", tenant_report[:80])
    logger.info("╚" + "═" * 58 + "╝")
    logger.info("")

    pipeline: dict[str, Any] = {
        "ticket_id": ticket_id,
        "tenant_report": tenant_report,
        "state": state,
        "zip_code": zip_code,
        "started_at": pipeline_start.isoformat(),
        "phases": {},
    }

    try:
        # ── Phase 1: Triage ──────────────────────────────────────────
        triage_result = await phase_triage(tenant_report, state)
        pipeline["phases"]["triage"] = triage_result

        issue_type = (
            triage_result.get("trade_needed", "").replace(" Technician", "")
            .replace(" Specialist", "").replace(" / ", "/").split("/")[0].strip()
        )
        if issue_type not in ("HVAC", "Plumbing", "Electrical", "Structural", "Pest"):
            issue_type = "HVAC"  # sensible default for demo

        # ── Phase 2: Habitability ────────────────────────────────────
        compliance_result = await phase_habitability(
            state, issue_type, triage_result.get("urgency", "routine"),
        )
        pipeline["phases"]["habitability"] = compliance_result

        # ── Phase 3: Vendor Matching ─────────────────────────────────
        matched_vendors = await phase_vendor_match(
            issue_type, zip_code, triage_result.get("urgency", "routine"),
        )
        pipeline["phases"]["vendor_match"] = matched_vendors

        if not matched_vendors:
            logger.error("No vendors found — cannot continue")
            pipeline["status"] = "failed"
            pipeline["error"] = "No matching vendors"
            return pipeline

        # ── Phase 4: Quote Simulation ────────────────────────────────
        issue_desc = triage_result.get("urgency_rationale", tenant_report)
        quotes = await phase_simulate_quotes(matched_vendors, issue_desc)
        pipeline["phases"]["quotes"] = quotes

        # ── Phase 5: Quote Comparison ────────────────────────────────
        comparison = await phase_compare_quotes(quotes, zip_code)
        pipeline["phases"]["quote_comparison"] = comparison

        selected_vendor_name = comparison["recommendation"]["vendor_name"]
        selected_amount = comparison["recommendation"]["quote_amount"]

        # Find full vendor details for guardrails + payment
        selected_vendor = DEMO_VENDORS.get(selected_vendor_name, {
            "name": selected_vendor_name,
            "trade": issue_type,
            "rating": 4.5,
            "stripe_connect_account_id": "acct_vendor_demo",
            "license_active": True,
            "license_type": issue_type,
            "required_trade": issue_type,
            "insurance_active": True,
            "insurance_coverage": 1_000_000,
            "workers_comp_active": True,
        })

        # ── Phase 6: NemoClaw Guardrails ─────────────────────────────
        guardrail_results = await phase_guardrails(
            selected_vendor,
            {"vendor_name": selected_vendor_name, "quote_amount": selected_amount},
            triage_result,
        )
        pipeline["phases"]["guardrails"] = guardrail_results

        if not guardrail_results["passed"]:
            logger.error("GUARDRAILS BLOCKED DISPATCH — %s", "; ".join(guardrail_results["blocks"]))
            pipeline["status"] = "blocked"
            pipeline["error"] = "Guardrails blocked: " + "; ".join(guardrail_results["blocks"])
            return pipeline

        # ── Phase 7: Dispatch ────────────────────────────────────────
        dispatch = await phase_dispatch(selected_vendor_name, selected_amount, triage_result)
        pipeline["phases"]["dispatch"] = dispatch

        # ── Phase 8: Work Complete ───────────────────────────────────
        completion = await phase_work_complete(dispatch["dispatch_id"])
        pipeline["phases"]["work_complete"] = completion

        # ── Phase 9: Payment ─────────────────────────────────────────
        payment = await phase_payment(
            selected_vendor_name,
            selected_amount,
            selected_vendor.get("stripe_connect_account_id", "acct_vendor_demo"),
        )
        pipeline["phases"]["payment"] = payment

        # ── Phase 10: Warranty ───────────────────────────────────────
        warranty = await phase_warranty(
            DEMO_PROPERTY["address"],
            tenant_report,
            selected_amount,
        )
        pipeline["phases"]["warranty"] = warranty

        # ── Complete ─────────────────────────────────────────────────
        pipeline["status"] = "completed"
        pipeline["completed_at"] = datetime.now(timezone.utc).isoformat()
        elapsed = (datetime.now(timezone.utc) - pipeline_start).total_seconds()
        pipeline["elapsed_seconds"] = round(elapsed, 2)

        logger.info("")
        logger.info("╔" + "═" * 58 + "╗")
        logger.info("║          PIPELINE COMPLETE ✅")
        logger.info("║  Ticket:       %s", ticket_id)
        logger.info("║  Vendor:       %s", selected_vendor_name)
        logger.info("║  Amount:       $%.2f", selected_amount)
        logger.info("║  Commission:   $%.2f", payment["commission_amount"])
        logger.info("║  Warranty:     %s", "Claim filed" if warranty.get("claim_generated") else warranty.get("reason", "N/A"))
        logger.info("║  Elapsed:      %.1fs", elapsed)
        logger.info("╚" + "═" * 58 + "╝")
        logger.info("")

    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        pipeline["status"] = "failed"
        pipeline["error"] = str(exc)
        pipeline["completed_at"] = datetime.now(timezone.utc).isoformat()

    return pipeline


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def format_pipeline_summary(pipeline: dict) -> str:
    """Render a pipeline result as a human-readable summary."""
    lines = []
    lines.append("")
    lines.append("╔" + "═" * 58 + "╗")
    lines.append(f"║  MAINTENOPS — Pipeline {pipeline.get('status', 'unknown').upper()}")
    lines.append(f"║  Ticket: {pipeline.get('ticket_id', 'N/A')}")
    lines.append("╠" + "═" * 58 + "╣")

    phases = pipeline.get("phases", {})
    triage = phases.get("triage", {})
    lines.append(f"║  📋 TRIAGE:        {triage.get('urgency', '?').upper()} — {triage.get('trade_needed', '?')}")

    habitability = phases.get("habitability", {})
    if habitability.get("applicable"):
        lines.append(f"║  ⏰ HABITABILITY:  {habitability.get('deadline_hours', '?')}h deadline in {habitability.get('state', '?')}")
    else:
        lines.append(f"║  ⏰ HABITABILITY:  Not applicable")

    vendors = phases.get("vendor_match", [])
    lines.append(f"║  🔧 VENDORS:       {len(vendors)} matched")
    if vendors:
        lines.append(f"║    1. {vendors[0].get('name', '?')} ★{vendors[0].get('rating', '?')}")

    comparison = phases.get("quote_comparison", {})
    rec = comparison.get("recommendation", {})
    if rec:
        lines.append(f"║  💰 BEST QUOTE:    {rec.get('vendor_name', '?')} — ${rec.get('quote_amount', 0):.2f}")

    guardrails = phases.get("guardrails", {})
    guard_status = "✅ PASSED" if guardrails.get("passed") else "❌ BLOCKED"
    lines.append(f"║  🛡️ GUARDRAILS:    {guard_status}")

    dispatch = phases.get("dispatch", {})
    if dispatch:
        lines.append(f"║  🚚 DISPATCH:      {dispatch.get('vendor_name', '?')} — ETA {dispatch.get('eta', '?')}")

    payment = phases.get("payment", {})
    if payment:
        lines.append(f"║  💳 PAYMENT:       ${payment.get('vendor_payout', 0):.2f} to vendor (${payment.get('commission_amount', 0):.2f} commission)")

    warranty = phases.get("warranty", {})
    if warranty.get("claim_generated"):
        claim = warranty.get("claim", {})
        lines.append(f"║  📄 WARRANTY:      Claim filed — ID {claim.get('claim_id', '?')[:8]}...")
    elif warranty.get("skipped"):
        lines.append(f"║  📄 WARRANTY:      {warranty.get('reason', 'Skipped')}")
    else:
        lines.append(f"║  📄 WARRANTY:      Not processed")

    if pipeline.get("error"):
        lines.append(f"║  ❌ ERROR:        {pipeline['error']}")

    elapsed = pipeline.get("elapsed_seconds", 0)
    lines.append(f"║  ⏱️ ELAPSED:       {elapsed:.1f}s")
    lines.append("╚" + "═" * 58 + "╝")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    # Get report from CLI arg or use default
    report = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not report:
        report = "AC not cooling, 87 degrees inside, have a newborn baby"

    logger.info("MaintenOps Agent — Starting pipeline")
    logger.info("Report: %s", report)

    result = asyncio.run(run_pipeline(report))
    print(format_pipeline_summary(result))

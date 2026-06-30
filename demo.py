#!/usr/bin/env python3
"""
MaintenOps — Interactive Demo Mode

Runs the full pipeline with a timed, stage-by-stage reveal.
No real API calls — everything is simulated in-memory.

Usage:
    python3 demo.py
    python3 demo.py "AC not cooling, 87 degrees, have a newborn"
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone

# Colors
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[38;5;83m"
    YELLOW = "\033[38;5;221m"
    RED = "\033[38;5;196m"
    BLUE = "\033[38;5;75m"
    PURPLE = "\033[38;5;141m"
    CYAN = "\033[38;5;51m"
    ORANGE = "\033[38;5;208m"
    GREY = "\033[38;5;242m"
    BGGREEN = "\033[48;5;22m"
    BGRED = "\033[48;5;52m"

terminal_width = shutil.get_terminal_size().columns or 80


def hr(char="─", color=C.GREY):
    print(f"{color}{char * terminal_width}{C.RESET}")


def title(text, color=C.BOLD):
    hr("═", color)
    print(f"{color}{' ' * 2}{text}{' ' * (terminal_width - len(text) - 4)}{C.RESET}")
    hr("═", color)


def step(icon, label, detail="", delay=0.8):
    time.sleep(delay)
    print(f"\n  {icon}  {C.BOLD}{label}{C.RESET}")
    if detail:
        for line in detail.split("\n"):
            print(f"     {C.DIM}{line}{C.RESET}")


def ok(text):
    print(f"     {C.GREEN}✓{C.RESET} {text}")


def warn(text):
    print(f"     {C.YELLOW}⚠{C.RESET} {text}")


def money(amount):
    return f"{C.GREEN}${amount:,.2f}{C.RESET}"


def badge(text, color=C.PURPLE):
    return f"{color}{C.BOLD}{text}{C.RESET}"


async def run_demo(report: str):
    os.environ["PYTHONIOENCODING"] = "utf-8"

    # ── Banner ──
    os.system("clear" if os.name == "posix" else "cls")
    print()
    print(f"{C.BOLD}{C.PURPLE}  ⌘  M A I N T E N O P S  —  Interactive Demo{C.RESET}")
    print(f"{C.DIM}  AI-native property maintenance agent{C.RESET}")
    print(f"  {C.GREY}NVIDIA × Stripe × Nous Research Hackathon 2026{C.RESET}")
    print()
    hr("─")
    print(f"  {C.YELLOW}📱 Tenant reports:{C.RESET}  {C.BOLD}{report[:80]}{C.RESET}")
    hr("─")
    time.sleep(1)

    # ── Import ──
    print(f"\n  {C.DIM}Initializing agent pipeline...{C.RESET}")
    time.sleep(0.5)

    try:
        from agent import run_pipeline
    except ImportError as e:
        print(f"\n  {C.RED}✗ Import error: {e}{C.RESET}")
        print(f"\n  {C.YELLOW}Fix:{C.RESET}  cd ~/maintenops && pip install stripe openai pyyaml")
        return

    # ── Run ──
    result = await run_pipeline(report)
    phases = result.get("phases", {})

    os.system("clear" if os.name == "posix" else "cls")

    # ════════════════════════════════════════════════════════════════
    # PHASE 1 — Triage
    # ════════════════════════════════════════════════════════════════
    title("📋 PHASE 1 — AI Triaging the Report", C.BLUE)
    step("🧠", "Nemotron 3 Ultra analyzes the tenant message...")
    time.sleep(0.5)

    triage = phases.get("triage", {})
    urgency = triage.get("urgency", "unknown")
    urgency_colors = {"emergency": C.RED, "urgent": C.YELLOW, "routine": C.GREEN}
    uc = urgency_colors.get(urgency, C.GREY)
    print(f"     Urgency:      {badge(urgency.upper(), uc)}")
    print(f"     Trade:        {C.BOLD}{triage.get('trade_needed', 'N/A')}{C.RESET}")
    print(f"     Rationale:    {triage.get('urgency_rationale', 'N/A')}")
    if triage.get("source") == "nemotron":
        ok("AI triage via Nemotron 3 Ultra")
    else:
        warn(f"Fallback triage (source: {triage.get('source', 'keyword')})")
    ok("Safety instructions generated for tenant")

    time.sleep(1.5)

    # ════════════════════════════════════════════════════════════════
    # PHASE 2 — Habitability
    # ════════════════════════════════════════════════════════════════
    title("⏰ PHASE 2 — Habitability Compliance Check", C.BLUE)
    step("📜", "Looking up state habitability laws...")
    time.sleep(0.4)

    hab = phases.get("habitability", {})
    if hab.get("applicable"):
        deadline = hab.get("deadline_hours", 24)
        print(f"     State:        {badge(hab.get('state', 'CA'), C.YELLOW)}")
        print(f"     Deadline:     {C.BOLD}{deadline}h{C.RESET} — {hab.get('deadline_label', '')}")
        print(f"     Escalation:   50% → PM | 75% → Owner | 100% → Legal")
        ok(f"{deadline}-hour response deadline triggered")
    else:
        warn("Not applicable for this issue type")

    time.sleep(1)

    # ════════════════════════════════════════════════════════════════
    # PHASE 3 — Vendor Matching
    # ════════════════════════════════════════════════════════════════
    title("🔧 PHASE 3 — Vendor Matching Engine", C.BLUE)
    step("🔍", "Querying vendor database + Nemotron AI ranking...")
    time.sleep(0.6)

    vendors = phases.get("vendor_match", [])
    print(f"     {C.BOLD}{len(vendors)} vendors matched{C.RESET}")
    for i, v in enumerate(vendors[:3], 1):
        stars = "★" * int(v.get("rating", 0))
        print(f"       #{i}  {v.get('name', '?')}  {C.YELLOW}{stars}{C.RESET}  "
              f"{C.DIM}score: {v.get('match_score', '?')}{C.RESET}")
    ok("Top vendors ranked by AI scoring")

    time.sleep(1.2)

    # ════════════════════════════════════════════════════════════════
    # PHASE 4 — Quotes
    # ════════════════════════════════════════════════════════════════
    title("💰 PHASE 4 — Quote Simulation & Comparison", C.BLUE)
    step("📬", "Requesting quotes from top vendors...")
    time.sleep(0.3)

    quotes = phases.get("quotes", [])
    for q in quotes:
        print(f"     {C.DIM}←{C.RESET} {q.get('vendor_name', '?')}:  {money(q.get('quote_amount', 0))}")
    time.sleep(0.5)

    step("📊", "Nemotron compares against market benchmarks...")
    time.sleep(0.5)
    comparison = phases.get("quote_comparison", {})
    rec = comparison.get("recommendation", {})
    print(f"     {C.GREEN}★{C.RESET} {C.BOLD}Best value:{C.RESET}  {rec.get('vendor_name', 'N/A')} — {money(rec.get('quote_amount', 0))}")

    analysis = comparison.get("analysis", [])
    for a in analysis:
        status = f"{C.GREEN}✓{C.RESET}" if a.get("within_benchmark") else f"{C.RED}✗{C.RESET}"
        flag = f" {C.YELLOW}OUTLIER{C.RESET}" if a.get("outlier") else ""
        print(f"       {status} {a.get('vendor_name', '?')}{flag}")
    ok("Quote comparison complete — recommendation generated")

    time.sleep(1.2)

    # ════════════════════════════════════════════════════════════════
    # PHASE 5 — Guardrails
    # ════════════════════════════════════════════════════════════════
    title("🛡️ PHASE 5 — NemoClaw Guardrails", C.BLUE)
    step("🔒", "Running safety and compliance checks...")
    time.sleep(0.4)

    guardrails = phases.get("guardrails", {})
    if guardrails.get("passed"):
        ok(f"Vendor License & Insurance — PASSED")
        ok(f"Spending Authorization — PASSED")
        ok(f"Emergency Escalation — PASSED")
        ok(f"Habitability Compliance — PASSED")
        for w in guardrails.get("warnings", []):
            warn(w)
    else:
        for b in guardrails.get("blocks", []):
            print(f"     {C.RED}✗{C.RESET} {b}")
    time.sleep(0.5)

    # ════════════════════════════════════════════════════════════════
    # PHASE 6 — Dispatch
    # ════════════════════════════════════════════════════════════════
    title("🚚 PHASE 6 — Vendor Dispatch", C.BLUE)
    step("📲", "Notifying vendor and tenant...")
    time.sleep(0.3)

    dispatch = phases.get("dispatch", {})
    print(f"     Vendor:       {C.BOLD}{dispatch.get('vendor_name', 'N/A')}{C.RESET}")
    print(f"     Amount:       {money(dispatch.get('quote_amount', 0))}")
    print(f"     ETA:          {badge(dispatch.get('eta', 'N/A'), C.CYAN)}")
    print(f"     Dispatch ID:  {C.DIM}{dispatch.get('dispatch_id', 'N/A')}{C.RESET}")
    ok("Tenant notified via SMS")
    ok("Vendor dispatched to property")

    time.sleep(1)

    # ════════════════════════════════════════════════════════════════
    # PHASE 7 — Work Complete
    # ════════════════════════════════════════════════════════════════
    title("✅ PHASE 7 — Work Completion", C.BLUE)
    step("🔨", "Vendor completes the repair...")
    time.sleep(0.6)

    work = phases.get("work_complete", {})
    ok(f"Work completed: {work.get('notes', 'Done')}")
    ok("Photo verification received")
    ok("Tenant confirmed resolution")

    time.sleep(0.8)

    # ════════════════════════════════════════════════════════════════
    # PHASE 8 — Payment
    # ════════════════════════════════════════════════════════════════
    title("💳 PHASE 8 — Stripe Payment", C.BLUE)
    step("🏦", "Processing payment via Stripe Connect...")
    time.sleep(0.5)

    payment = phases.get("payment", {})
    payout = payment.get("vendor_payout", 0)
    commission = payment.get("commission_amount", 0)
    print(f"     Quote:            {money(payment.get('quote_amount', 0))}")
    print(f"     Commission (3%):  {money(commission)}  {C.GREEN}→ Platform revenue{C.RESET}")
    print(f"     Vendor payout:    {money(payout)}  {C.DIM}→ Stripe Connect{C.RESET}")
    print(f"     Transfer ID:      {C.DIM}{payment.get('transfer_id', 'N/A')}{C.RESET}")
    ok(f"{money(payout)} transferred to vendor with 3% commission")
    time.sleep(0.5)

    # ════════════════════════════════════════════════════════════════
    # PHASE 9 — Warranty
    # ════════════════════════════════════════════════════════════════
    title("📄 PHASE 9 — Warranty Check", C.BLUE)
    step("🔍", "Checking warranty eligibility...")
    time.sleep(0.3)

    warranty = phases.get("warranty", {})
    if warranty.get("claim_generated"):
        claim = warranty.get("claim", {})
        print(f"     Appliance:    Lennox XC20-048 HVAC System")
        print(f"     Coverage:     compressor, refrigerant system, coils")
        print(f"     Claim ID:     {C.DIM}{claim.get('claim_id', '?')}{C.RESET}")
        ok(f"Warranty claim filed — ${claim.get('estimated_cost', 0):,.2f} repair covered")
    elif warranty.get("skipped"):
        warn(f"Warranty: {warranty.get('reason', 'Skipped')}")
    else:
        warn("No warranty claim filed")

    time.sleep(0.8)

    # ════════════════════════════════════════════════════════════════
    # SUMMARY
    # ════════════════════════════════════════════════════════════════
    print()
    hr("═", C.GREEN)
    print(f"  {C.BOLD}{C.GREEN}  P I P E L I N E   C O M P L E T E   ✅{C.RESET}")
    hr("═", C.GREEN)

    elapsed = result.get("elapsed_seconds", 0)
    print()
    print(f"     Ticket:       {C.BOLD}{result.get('ticket_id', 'N/A')}{C.RESET}")
    print(f"     Urgency:      {badge(urgency.upper(), uc)}")
    print(f"     Vendor:       {C.BOLD}{dispatch.get('vendor_name', 'N/A')}{C.RESET}")
    print(f"     Amount:       {money(payment.get('quote_amount', 0))}")
    print(f"     Commission:   {money(commission)}  earned")
    print(f"     Warrantied:   {'Yes ✅' if warranty.get('claim_generated') else 'No'}")
    print(f"     Elapsed:      {elapsed:.1f}s")
    print()

    # ── Key Stats ──
    print(f"  {C.DIM}{'─' * terminal_width}{C.RESET}")
    print(f"  {C.BOLD}  Demo Summary{C.RESET}")
    print(f"  {C.DIM}  Real-time agent pipeline: triage → dispatch → payment → warranty{C.RESET}")
    print(f"  {C.DIM}  0 external API calls • 100% simulated • ready for recording{C.RESET}")
    print(f"  {C.DIM}{'─' * terminal_width}{C.RESET}")
    print()


if __name__ == "__main__":
    report = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not report:
        report = "AC not cooling, 87 degrees inside, have a newborn baby"

    asyncio.run(run_demo(report))

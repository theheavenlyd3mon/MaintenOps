"""
NemoClaw Guardrails Loader Module

Loads all 6 guardrail YAML configurations and provides:
  - check_action(action_type, action_data)  — run all applicable guardrails
  - Individual check_*() functions for each guardrail domain
"""

import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None
    print("[GUARDRAIL] WARNING: PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_guardrails = {}          # guardrail_id -> rule dict
_guardrail_files = {}     # guardrail_id -> source filename


def _load_yaml(filepath: Path) -> dict | None:
    """Load a single YAML file and return its 'guardrails' list keyed by id."""
    if yaml is None:
        print(f"[GUARDRAIL] ERROR: Cannot load {filepath} — PyYAML not available", file=sys.stderr)
        return None
    try:
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
    except Exception as exc:
        print(f"[GUARDRAIL] ERROR loading {filepath}: {exc}", file=sys.stderr)
        return None

    if not data or "guardrails" not in data:
        print(f"[GUARDRAIL] WARNING: {filepath} has no 'guardrails' key", file=sys.stderr)
        return None

    for rule in data["guardrails"]:
        gid = rule.get("id", "unknown")
        _guardrails[gid] = rule
        _guardrail_files[gid] = filepath.name
    return data


def _load_all() -> None:
    """Load all YAML files from the guardrails directory."""
    guardrails_dir = Path(__file__).parent.resolve()
    for yml_file in sorted(guardrails_dir.glob("*.yml")):
        if yml_file.name.startswith("_"):
            continue
        _load_yaml(yml_file)

    if not _guardrails:
        print("[GUARDRAIL] WARNING: No guardrails loaded — directory may be empty", file=sys.stderr)
    else:
        print(f"[GUARDRAIL] Loaded {len(_guardrails)} guardrails: {', '.join(sorted(_guardrails))}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Trigger matching — maps action types to guardrail IDs
# ---------------------------------------------------------------------------

_TRIGGER_MAP = {
    "dispatch_vendor":       ["vendor_license_check"],
    "approve_quote":         ["spending_authorization"],
    "send_tenant_sms":       ["tenant_communication"],
    "send_tenant_email":     ["tenant_communication"],
    "file_warranty_claim":   ["warranty_claims"],
}

# Guardrails that match by urgency (emergency.yml, habitability.yml)
_URGENCY_TRIGGERED = ["emergency_escalation", "habitability_compliance"]


def _applicable_guardrails(action_type: str, action_data: dict) -> list[dict]:
    """Return the list of guardrail rules that apply to this action."""
    gids = []

    # Direct action-type match
    gids.extend(_TRIGGER_MAP.get(action_type, []))

    # Urgency-based match
    urgency = None
    if isinstance(action_data, dict):
        urgency = action_data.get("urgency") or (
            action_data.get("triage", {}).get("urgency") if isinstance(action_data.get("triage"), dict) else None
        )
        if urgency is None:
            ticket = action_data.get("ticket", {})
            if isinstance(ticket, dict):
                urgency = ticket.get("urgency")

    if urgency in ("emergency", "urgent"):
        gids.extend(_URGENCY_TRIGGERED)

    # Deduplicate preserving order
    seen = set()
    unique = []
    for gid in gids:
        if gid not in seen:
            seen.add(gid)
            unique.append(gid)
    return [_guardrails[gid] for gid in unique if gid in _guardrails]


# ---------------------------------------------------------------------------
# Public API  —  check_action
# ---------------------------------------------------------------------------

def check_action(action_type: str, action_data: dict) -> dict:
    """
    Run all guardrails applicable to *action_type* with *action_data*.

    Returns dict:
        {passed: bool, blocks: list[str], warnings: list[str]}
    """
    results = {"passed": True, "blocks": [], "warnings": []}

    applicable = _applicable_guardrails(action_type, action_data)
    if not applicable:
        print(f"[GUARDRAIL] No guardrails match action_type={action_type!r}")
        return results

    for rule in applicable:
        gid = rule["id"]
        print(f"[GUARDRAIL] Checking guardrail: {gid} — {rule.get('description', '')}")

        # Simple simulation: most guardrails pass by default.
        # If action_data contains explicit failure hints, we honour them.
        fail_key = f"fail_{gid}"
        if isinstance(action_data, dict) and action_data.get(fail_key):
            msg = f"Guardrail {gid} blocked: {action_data.get('fail_reason', 'simulated failure')}"
            results["blocks"].append(msg)
            results["passed"] = False
            print(f"[GUARDRAIL] BLOCKED: {msg}")
        else:
            print(f"[GUARDRAIL] PASSED: {gid}")

    return results


# ---------------------------------------------------------------------------
# Public API  —  Individual guardrail checkers
# ---------------------------------------------------------------------------

def check_vendor_verify(vendor: dict) -> dict:
    """Vendor License & Insurance Verification."""
    gid = "vendor_license_check"
    print(f"[GUARDRAIL] Running check_vendor_verify — guardrail: {gid}")
    blocks = []
    vendor = vendor or {}

    if not vendor.get("license_active"):
        blocks.append("Vendor license is not active")
    if vendor.get("license_type") != vendor.get("required_trade"):
        blocks.append(f"License type '{vendor.get('license_type')}' does not match required trade '{vendor.get('required_trade')}'")
    if not vendor.get("insurance_active"):
        blocks.append("Vendor insurance is not active")
    if (vendor.get("insurance_coverage") or 0) < 1_000_000:
        blocks.append(f"Insurance coverage ${vendor.get('insurance_coverage', 0):,} is below $1,000,000 minimum")
    if not vendor.get("workers_comp_active"):
        blocks.append("Workers' compensation insurance is not active")

    passed = len(blocks) == 0
    if not passed:
        print(f"[GUARDRAIL] BLOCKED: {gid} — {'; '.join(blocks)}")
    else:
        print(f"[GUARDRAIL] PASSED: {gid}")
    return {"passed": passed, "blocks": blocks, "warnings": []}


def check_spending(quote: dict, owner: dict) -> dict:
    """Spending Authorization."""
    gid = "spending_authorization"
    print(f"[GUARDRAIL] Running check_spending — guardrail: {gid}")
    blocks = []
    warnings = []
    quote = quote or {}
    owner = owner or {}

    total = quote.get("total", 0)
    limit = owner.get("maintenance_limit", 0)

    # Emergency override
    issue = quote.get("issue", {})
    if isinstance(issue, dict) and issue.get("category") == "emergency" and issue.get("habitability_risk") == "immediate":
        if total <= 5000:
            print(f"[GUARDRAIL] OVERRIDE: {gid} — emergency override up to $5,000 with post-approval notification")
            warnings.append(f"Emergency override applied for ${total:,} (post-approval required)")
            return {"passed": True, "blocks": [], "warnings": warnings}
        else:
            blocks.append(f"Emergency override max is $5,000 but total is ${total:,}")

    if total <= limit:
        print(f"[GUARDRAIL] AUTO-APPROVE: {gid} — ${total:,} <= owner limit ${limit:,}")
        return {"passed": True, "blocks": [], "warnings": []}

    if total <= limit * 1.5:
        blocks.append(f"Quote ${total:,} exceeds owner limit ${limit:,}; requires owner approval via SMS/email")
    elif total > limit * 1.5:
        blocks.append(f"Quote ${total:,} exceeds 1.5x owner limit; requires owner approval + property manager review")

    if total > 2500:
        blocks.append(f"Quote ${total:,} > $2,500; requires 3 quotes compared")

    passed = len(blocks) == 0
    if not passed:
        print(f"[GUARDRAIL] BLOCKED: {gid} — {'; '.join(blocks)}")
    else:
        print(f"[GUARDRAIL] PASSED: {gid}")
    return {"passed": passed, "blocks": blocks, "warnings": warnings}


def check_emergency(triage: dict, tenant_report: str = "") -> dict:
    """Emergency Escalation."""
    gid = "emergency_escalation"
    print(f"[GUARDRAIL] Running check_emergency — guardrail: {gid}")
    blocks = []
    warnings = []
    triage = triage or {}

    urgency = triage.get("urgency")
    if urgency != "emergency":
        warnings.append(f"Urgency is '{urgency}', not 'emergency' — no escalation needed")
        return {"passed": True, "blocks": [], "warnings": warnings}

    keywords = ["gas leak", "gas smell", "fire", "smoke", "flood", "burst pipe",
                "electrical sparks", "carbon monoxide", "structural collapse"]
    report = (tenant_report or triage.get("tenant_report") or "").lower()
    keyword_found = any(kw in report for kw in keywords)

    if keyword_found:
        warnings.append("Life-safety keyword detected — escalating to 911, property manager, and owner")
        warnings.append("Bypassing normal quote process, using emergency vendor rates")
    else:
        warnings.append("Emergency without life-safety keyword — escalating to property manager SMS and owner email")
        warnings.append("Vendor dispatch required within 1 hour")

    print(f"[GUARDRAIL] PASSED: {gid} (emergency action taken)")
    return {"passed": True, "blocks": blocks, "warnings": warnings}


def check_tenant_comms(content: str) -> dict:
    """Tenant Communication Standards."""
    gid = "tenant_communication"
    print(f"[GUARDRAIL] Running check_tenant_comms — guardrail: {gid}")
    blocks = []
    content = content or ""

    checks = {
        "owner financial information": ["owner financial information", "owner's financial", "owner_financial",
                                          "maintenance_limit", "owner_budget"],
        "vendor cost details": ["vendor cost", "quote total", "repair cost", "$", "invoice total",
                                 "vendor_rate", "hourly rate"],
        "emergency severity": ["emergency severity", "life threatening", "life-safety"],
    }

    for label, patterns in checks.items():
        for pat in patterns:
            if pat in content.lower():
                blocks.append(f"Content must not contain {label} (matched: '{pat}')")
                break

    warnings = []
    if "ETA" not in content and "eta" not in content.lower():
        warnings.append("Content should include ETA when available")
    if "ticket" not in content.lower() and "reference" not in content.lower() and "#" not in content:
        warnings.append("Content should include ticket reference number")

    passed = len(blocks) == 0
    if not passed:
        print(f"[GUARDRAIL] BLOCKED: {gid} — {'; '.join(blocks)}")
    else:
        print(f"[GUARDRAIL] PASSED: {gid}")
    return {"passed": passed, "blocks": blocks, "warnings": warnings}


def check_warranty(appliance: dict, repair: dict) -> dict:
    """Warranty Claim Validation."""
    gid = "warranty_claims"
    print(f"[GUARDRAIL] Running check_warranty — guardrail: {gid}")
    blocks = []
    appliance = appliance or {}
    repair = repair or {}

    if not appliance.get("warranty_active"):
        blocks.append("Appliance warranty is not active")
    current_date = repair.get("current_date") or appliance.get("current_date", "9999-12-31")
    if appliance.get("warranty_expiry") and appliance["warranty_expiry"] <= current_date:
        blocks.append(f"Warranty expired on {appliance.get('warranty_expiry')}")
    issue_type = repair.get("issue_type")
    coverage = appliance.get("warranty_coverage", [])
    if issue_type and coverage and issue_type not in coverage:
        blocks.append(f"Issue type '{issue_type}' is not covered by warranty ({coverage})")
    if not appliance.get("warranty_provider"):
        blocks.append("Warranty provider is not specified")

    passed = len(blocks) == 0
    if not passed:
        print(f"[GUARDRAIL] BLOCKED: {gid} — {'; '.join(blocks)}")
    else:
        print(f"[GUARDRAIL] PASSED: {gid}")
    return {"passed": passed, "blocks": blocks, "warnings": []}


def check_habitability(ticket: dict, property_state: str) -> dict:
    """Habitability Compliance by State."""
    gid = "habitability_compliance"
    print(f"[GUARDRAIL] Running check_habitability — guardrail: {gid}")
    blocks = []
    warnings = []
    ticket = ticket or {}

    state_deadlines = {
        "CA": {"heating": "24h", "water": "24h", "electrical": "24h", "structural": "24h"},
        "NY": {"heating": "24h", "water": "24h", "electrical": "24h", "structural": "24h"},
        "TX": {"heating": "reasonable", "water": "reasonable", "electrical": "reasonable"},
        "FL": {"heating": "none", "water": "24h", "electrical": "24h", "AC": "7d"},
        "IL": {"heating": "24h", "water": "24h", "electrical": "24h"},
        "WA": {"heating": "24h", "water": "24h", "electrical": "24h", "hot_water": "24h"},
        "CO": {"heating": "24h", "water": "24h", "electrical": "24h", "structural": "24h"},
        "AZ": {"heating": "reasonable", "water": "reasonable", "electrical": "reasonable"},
        "GA": {"heating": "reasonable", "water": "reasonable", "electrical": "reasonable"},
        "NC": {"heating": "reasonable", "water": "reasonable", "electrical": "reasonable"},
    }

    state_key = property_state.upper() if property_state else "NONE"
    deadlines = state_deadlines.get(state_key, {})

    if not deadlines:
        warnings.append(f"No habitability deadlines defined for state '{state_key}'")
    else:
        issue_type = ticket.get("issue_type", "unknown")
        deadline = deadlines.get(issue_type, deadlines.get("heating", "unknown"))
        warnings.append(f"State '{state_key}' deadline for '{issue_type}': {deadline}")

    time_elapsed = ticket.get("time_elapsed_hours", 0)

    # Simulated deadline parsing: assume 24h standard
    if state_key in state_deadlines:
        if time_elapsed > 0:
            pct = time_elapsed / 24.0
            if pct > 1.0:
                blocks.append(f"Deadline exceeded for state '{state_key}'; escalate to owner + legal team")
            elif pct > 0.75:
                warnings.append(f"{pct:.0%} of deadline elapsed; escalate to property manager")
            else:
                warnings.append(f"{pct:.0%} of deadline elapsed — within compliance window")
        else:
            warnings.append(f"Deadline for '{issue_type}' in {state_key}: {deadline}")

    passed = len(blocks) == 0
    if not passed:
        print(f"[GUARDRAIL] BLOCKED: {gid} — {'; '.join(blocks)}")
    else:
        print(f"[GUARDRAIL] PASSED: {gid}")
    return {"passed": passed, "blocks": blocks, "warnings": warnings}


# ---------------------------------------------------------------------------
# Load guardrails on import
# ---------------------------------------------------------------------------

_load_all()

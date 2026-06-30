"""Maintenance Triage Engine — Nemotron-powered with keyword fallback.

Exports:
    triage_issue(tenant_report: str, state: str = "CA") -> dict
"""

from __future__ import annotations

import json
import re
from typing import Any

from clients.nemotron import run_triage

# ---------------------------------------------------------------------------
# Fallback triage — keyword-based when Nemotron is unavailable
# ---------------------------------------------------------------------------

_RULES: list[tuple[re.Pattern, dict[str, Any]]] = [
    # ── Emergency (immediate life/safety/property damage) ──────────────
    (
        re.compile(r"gas\s*leak|smell\s+gas|natural\s+gas", re.IGNORECASE),
        {
            "likely_issues": [{"issue": "Gas leak suspected", "confidence": "high"}],
            "trade_needed": "Gas Utility / Plumber",
            "urgency": "emergency",
            "urgency_rationale": "Gas leak poses immediate risk of explosion or asphyxiation — requires emergency shutdown and repair.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 24,
            "safety_instructions": "IMMEDIATELY evacuate the unit. Do NOT operate any electrical switches or flames. Call 911 and your gas utility provider from outside the building. Keep windows open if safe. Do not re-enter until cleared by emergency services.",
        },
    ),
    (
        re.compile(
            r"fire|flame|burning|smoke\s+(alarm|detector|in\s+the)|electrical\s+spark",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [{"issue": "Fire or active fire risk", "confidence": "high"}],
            "trade_needed": "Fire Department / Electrician",
            "urgency": "emergency",
            "urgency_rationale": "Active fire or electrical sparking is immediately life-threatening and can destroy property within minutes.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 24,
            "safety_instructions": "IMMEDIATELY evacuate the building. Call 911. Do not attempt to extinguish electrical fires with water. After the fire is out, do not re-enter until the fire department declares it safe.",
        },
    ),
    (
        re.compile(
            r"flood|burst\s*pipe|water\s+(gushing|pouring|rushing)|sewage\s+backup|raw\s+sewage",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Major water leak or flood", "confidence": "high"}
            ],
            "trade_needed": "Emergency Plumber",
            "urgency": "emergency",
            "urgency_rationale": "Active flooding causes rapid structural damage, mold growth, and electrical hazards within hours.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 24,
            "safety_instructions": "Immediately shut off the main water valve if you can reach it safely. Move valuables and electronics to higher ground. Turn off power to affected rooms if safe to do so. Do not walk through standing water if electrical outlets are submerged. Call emergency maintenance NOW.",
        },
    ),
    (
        re.compile(
            r"carbon\s*monoxide|co\s+(alarm|detector|leak)|no\s+carbon",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Possible carbon monoxide exposure", "confidence": "high"}
            ],
            "trade_needed": "HVAC Technician / Gas Fitter",
            "urgency": "emergency",
            "urgency_rationale": "Carbon monoxide is a colorless, odorless gas that can be fatal within minutes.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 24,
            "safety_instructions": "IMMEDIATELY evacuate everyone from the unit. Call 911 and the gas utility. Do not re-enter until emergency services confirm safe CO levels. If experiencing headache, dizziness, or nausea, seek medical attention immediately.",
        },
    ),
    (
        re.compile(
            r"no\s+(running\s+)?water|water\s+shut\s*off|without\s+water|lack\s+of\s+water",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [{"issue": "Complete water outage", "confidence": "medium"}],
            "trade_needed": "Plumber",
            "urgency": "emergency",
            "urgency_rationale": "Complete loss of water makes the unit uninhabitable and violates habitability requirements.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 24,
            "safety_instructions": "Check if this is a building-wide outage or unit-specific. If building-wide, contact building management. If unit-specific, check your main water shutoff valve. Do not attempt to repair pipes yourself.",
        },
    ),
    (
        re.compile(
            r"no\s+(electricity|power|lights|living\s+room\s+light)|power\s+out\b|electrical\s+outage|blackout|circuit\s+breaker\s+(keeps\s+)?tripping|breaker\s+keeps\s+popping",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Complete electrical failure", "confidence": "medium"}
            ],
            "trade_needed": "Electrician",
            "urgency": "emergency",
            "urgency_rationale": "No electrical power renders the unit uninhabitable, especially for tenants with medical devices.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 24,
            "safety_instructions": "Check if the outage affects only your unit or the whole building. If building-wide, contact utility provider. Check your circuit breaker panel — if a breaker is tripped, try resetting it once. If it trips again, do NOT keep resetting — call an electrician immediately. Unplug sensitive electronics to avoid surge damage when power returns.",
        },
    ),
    (
        re.compile(
            r"sewer|septic|toilet\s+(not\s+flushing|overflowing|backed\s*up|blocked|clogged)|sewage|raw sewage|human waste|poop|shit",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Sewage backup / toilet blockage", "confidence": "high"}
            ],
            "trade_needed": "Plumber",
            "urgency": "emergency",
            "urgency_rationale": "Sewage backup poses serious health hazards and makes the unit unsanitary and uninhabitable.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 24,
            "safety_instructions": "Do NOT flush any toilets or run water — this will worsen the backup. Keep everyone away from affected areas. If sewage is visible, avoid contact — it contains harmful bacteria. Call emergency plumbing service immediately.",
        },
    ),
    # ── Urgent (habitability affected, 24-48h) ──────────────────────
    (
        re.compile(
            r"(ac|a\.?c\.?|air\s+condition|aircon|cooling)\s+(not\s+)?(cooling|working|blowing|fixed|broken|not\s+cold|hot)",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "AC system failure / not cooling", "confidence": "high"}
            ],
            "trade_needed": "HVAC Technician",
            "urgency": "urgent",
            "urgency_rationale": "Lack of cooling in hot weather creates unsafe indoor temperatures, especially for vulnerable tenants (elderly, infants, medically fragile).",
            "habitability_applicable": True,
            "habitability_deadline_hours": 48,
            "safety_instructions": "Close blinds/curtains to block sunlight. Use fans if available. Stay hydrated. If indoor temperature exceeds 95°F (35°C) and you have an infant, elderly person, or someone with a medical condition, seek alternative cooling (public library, cooling center). Do not attempt DIY AC repairs — refrigerant handling requires EPA certification.",
        },
    ),
    (
        re.compile(
            r"(heat|heater|furnace|boiler|radiator|baseboard)\s+(not\s+)?(working|heating|turning\s+on|broken|blowing\s+cold|not\s+hot)",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Heating system failure", "confidence": "high"}
            ],
            "trade_needed": "HVAC Technician",
            "urgency": "urgent",
            "urgency_rationale": "No heat in cold weather creates unsafe indoor temperatures that can cause hypothermia and frozen pipes.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 48,
            "safety_instructions": "If temperature drops below 55°F (13°C) indoors, seek alternative shelter. Do NOT use oven or stovetop for heating — risk of fire and carbon monoxide poisoning. Use space heaters safely: keep 3ft from combustibles, plug directly into wall (not extension cord), and never leave unattended. Open cabinet doors under sinks to prevent pipes from freezing.",
        },
    ),
    (
        re.compile(
            r"(water\s+)?(leak|drip|dripping|water\s+stain|water\s+damage|wet\s+(ceiling|wall|floor|carpet)|puddle|water\s+on\s+the\s+floor|water\s+coming\s+(from|through)|ceiling\s+leak|roof\s+leak|pipe\s+leak)",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Water leak (non-emergency)", "confidence": "medium"}
            ],
            "trade_needed": "Plumber",
            "urgency": "urgent",
            "urgency_rationale": "Water leaks cause structural damage and mold growth if not addressed promptly.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 48,
            "safety_instructions": "Place a bucket or towel under the leak. Move furniture and electronics away. If the leak is near electrical fixtures, turn off power to that room. Document the leak with photos. Do not attempt pipe repairs yourself.",
        },
    ),
    (
        re.compile(
            r"(fridge|refrigerator|freezer)\s+(not\s+)?(working|cooling|cold|broken|warm|stopped)",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [{"issue": "Refrigerator failure", "confidence": "medium"}],
            "trade_needed": "Appliance Repair Technician",
            "urgency": "urgent",
            "urgency_rationale": "Refrigerator failure leads to food spoilage and potential health risks within 4-6 hours.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 48,
            "safety_instructions": "Keep refrigerator and freezer doors closed as much as possible. A fridge keeps food cold for about 4 hours; a freezer keeps food frozen for 24-48 hours if full. Move perishables to a cooler with ice if repair will take more than 6 hours. Do not attempt to repair the compressor yourself.",
        },
    ),
    (
        re.compile(
            r"(toilet|toilet\s+tank|flush)\s+(not\s+)?(flushing|working|running|filling)|running\s+toilet|toilet\s+runs|toilet\s+won'?t\s+stop",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Toilet malfunction (non-emergency)", "confidence": "medium"}
            ],
            "trade_needed": "Plumber",
            "urgency": "urgent",
            "urgency_rationale": "A non-functioning toilet is a habitability concern when it's the only toilet in the unit.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 48,
            "safety_instructions": "If the toilet is clogged, try a plunger first. If it's running continuously, turn off the water shutoff valve behind the toilet (turn clockwise). If there is only one bathroom and the toilet is unusable, inform the landlord immediately.",
        },
    ),
    (
        re.compile(
            r"(no\s+hot\s+water|water\s+(not\s+)?(heating|hot|luke|tepid|cold\s+shower)|water\s+heater\s+(not\s+)?(working|broken)|cold\s+shower)",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Water heater failure", "confidence": "medium"}
            ],
            "trade_needed": "Plumber / Water Heater Specialist",
            "urgency": "urgent",
            "urgency_rationale": "Lack of hot water makes the unit partially uninhabitable and triggers habitability timelines.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 48,
            "safety_instructions": "Check if the pilot light is on (gas water heaters). If you see water pooling around the water heater, turn off the gas/breaker and water supply to the heater immediately. Do not attempt to relight a pilot light if you smell gas.",
        },
    ),
    (
        re.compile(
            r"(mold|mildew|musty\s+smell|black\s+(spots|mold)|fungus)",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {
                    "issue": "Mold growth suspected (visible or smell)",
                    "confidence": "low",
                }
            ],
            "trade_needed": "Mold Remediation Specialist",
            "urgency": "urgent",
            "urgency_rationale": "Mold can cause respiratory issues and worsens quickly if moisture source isn't addressed.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 48,
            "safety_instructions": "Do NOT disturb visible mold — disturbing it releases spores into the air. Reduce humidity with dehumidifier or fans. Identify and report any water source feeding the mold. If you have asthma or allergies, consider staying elsewhere until remediation is complete.",
        },
    ),
    (
        re.compile(
            r"(electrical\s+outlet|outlet\s+(not\s+)?working|dead\s+outlet|spark|shock|zapped|electrical\s+issue|light\s+(switch|fixture)\s+(not\s+)?working|flickering\s+(lights?|lighting))",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Electrical outlet/fixture issue", "confidence": "medium"}
            ],
            "trade_needed": "Electrician",
            "urgency": "urgent",
            "urgency_rationale": "Electrical problems can indicate underlying wiring issues that pose fire or shock hazards.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 48,
            "safety_instructions": "Do NOT use the affected outlet or switch. If you see sparks or smell burning, turn off that circuit breaker immediately. Do not plug anything into a sparking outlet. Do not attempt electrical repairs yourself.",
        },
    ),
    (
        re.compile(
            r"(pest|roach|cockroach|bed\s*bug|rat|mice|mouse|rodent|termite|ant\s+(infest|swarm)|infest)",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Pest infestation suspected", "confidence": "low"}
            ],
            "trade_needed": "Exterminator / Pest Control",
            "urgency": "urgent",
            "urgency_rationale": "Pest infestations worsen exponentially and can affect neighboring units.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 48,
            "safety_instructions": "Seal food in airtight containers. Remove trash regularly. Do not use over-the-counter foggers or bug bombs — they are ineffective and can be dangerous. Document the infestation with photos/videos for your records.",
        },
    ),
    (
        re.compile(
            r"(lock|deadbolt|key|door\s+(won'?t|not)\s+(lock|close|open|shut)|stuck\s+door|broken\s+lock|cannot\s+(lock|secure))",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Broken lock or door not securing", "confidence": "medium"}
            ],
            "trade_needed": "Locksmith / General Contractor",
            "urgency": "urgent",
            "urgency_rationale": "A door that won't lock poses a security risk and violates the warranty of habitability.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 48,
            "safety_instructions": "If the front door won't lock, do not leave the unit unattended. Ask a neighbor to watch the unit or notify building security. Use a secondary lock or door wedge for temporary security. Do not attempt to force the lock open — you may get locked out.",
        },
    ),
    (
        re.compile(
            r"(window\s+(won'?t|not|can'?t|cannot|stuck|broken|shattered|cracked|seal|open|close|lock)|broken\s+glass|shattered\s+glass)",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Window broken or inoperable", "confidence": "medium"}
            ],
            "trade_needed": "General Contractor / Glazier",
            "urgency": "urgent",
            "urgency_rationale": "A broken window compromises security, insulation, and can cause injury.",
            "habitability_applicable": True,
            "habitability_deadline_hours": 48,
            "safety_instructions": "DO NOT touch broken glass — wear gloves if you must handle it. Cover the window with cardboard or plywood if safe to do so. If the window is on a ground floor, ensure the temporary cover is secure against intrusion. Keep children and pets away from broken glass.",
        },
    ),
    # ── Routine (3-7 day window) ─────────────────────────────────────
    (
        re.compile(
            r"(garbage\s+disposal|disposal\s+(not\s+)?(working|humming|running)|sink\s+(not\s+)?(draining|clogged|slow)\s+(?!.*(sewer|sewage|flood|burst|gushing|pouring|rushing)))",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Garbage disposal or sink drain clog", "confidence": "medium"}
            ],
            "trade_needed": "Plumber",
            "urgency": "routine",
            "urgency_rationale": "Slow drain or non-working disposal does not pose an immediate health or safety risk if there is alternative sink access.",
            "habitability_applicable": False,
            "habitability_deadline_hours": None,
            "safety_instructions": "Do NOT pour chemical drain cleaners down the sink — they damage pipes and are hazardous. Try a plunger first. If using a disposal, always turn it off and use tongs (not fingers) to remove debris. Never put grease, fibrous foods, or pasta down the disposal.",
        },
    ),
    (
        re.compile(
            r"(paint|crack\s+(in\s+)?(wall|ceiling|drywall)|hole\s+in\s+(wall|ceiling)|dented|scratched\s+(wall|floor)|cosmetic)",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Cosmetic / drywall damage", "confidence": "medium"}
            ],
            "trade_needed": "General Contractor",
            "urgency": "routine",
            "urgency_rationale": "Cosmetic damage does not affect habitability or safety.",
            "habitability_applicable": False,
            "habitability_deadline_hours": None,
            "safety_instructions": "No immediate action needed. Document the damage with photos for maintenance records. Small holes can be temporarily patched with spackle if desired.",
        },
    ),
    (
        re.compile(
            r"(appliance|dishwasher|washer|washing\s+machine|dryer|oven|stove|range|cooktop|microwave)\s+(not\s+)?(working|running|heating|spinning|draining|cleaning|broken)",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Appliance malfunction (non-essential)", "confidence": "medium"}
            ],
            "trade_needed": "Appliance Repair Technician",
            "urgency": "routine",
            "urgency_rationale": "Non-essential appliance failure is inconvenient but does not affect basic habitability (water, heat, electricity).",
            "habitability_applicable": False,
            "habitability_deadline_hours": None,
            "safety_instructions": "Unplug the appliance before attempting any inspection. Do not attempt internal repairs unless qualified. Check if the appliance is still under warranty.",
        },
    ),
    (
        re.compile(
            r"(clogged\s+(sink|drain|shower|tub|bathroom\s+sink|kitchen\s+sink)|slow\s+(drain|draining)|drain\s+slow|hair\s+in\s+drain)",
            re.IGNORECASE,
        ),
        {
            "likely_issues": [
                {"issue": "Clogged drain (non-emergency)", "confidence": "high"}
            ],
            "trade_needed": "Plumber",
            "urgency": "routine",
            "urgency_rationale": "A slow drain is an inconvenience but not a health or safety emergency.",
            "habitability_applicable": False,
            "habitability_deadline_hours": None,
            "safety_instructions": "Try a plunger or a drain snake (not chemical drain cleaners). Remove visible hair/debris from the drain cover. If the drain is completely blocked and you have no other functional sink in the unit, this should be escalated.",
        },
    ),
]


def _keyword_triage(tenant_report: str, state: str) -> dict[str, Any]:
    """Fallback triage using keyword/regex matching.

    Returns a reasonably structured triage result when Nemotron is unavailable.
    """
    report_lower = tenant_report.lower()

    # Check rules in order (emergency → urgent → routine).
    for pattern, result in _RULES:
        if pattern.search(report_lower):
            out = dict(result)  # shallow copy
            out["state"] = state
            out["source"] = "fallback_keyword"
            return out

    # ── Default: routine general ────────────────────────────────────
    return {
        "likely_issues": [
            {"issue": "Unspecified maintenance request", "confidence": "low"}
        ],
        "trade_needed": "General Contractor",
        "urgency": "routine",
        "urgency_rationale": "No specific emergency or urgent keywords detected. Defaulting to routine scheduling.",
        "habitability_applicable": False,
        "habitability_deadline_hours": None,
        "safety_instructions": "Describe the issue in more detail so we can route it to the correct trade. No immediate action required.",
        "state": state,
        "source": "fallback_keyword",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def triage_issue(tenant_report: str, state: str = "CA") -> dict[str, Any]:
    """Run Nemotron-powered maintenance triage, falling back to keyword matching.

    Parameters
    ----------
    tenant_report : str
        Free-text description of the maintenance issue from the tenant.
    state : str
        Two-letter US state code used for habitability law context (default ``"CA"``).

    Returns
    -------
    dict
        Structured triage result with keys:
          - ``likely_issues`` — list of {issue, confidence} dicts
          - ``trade_needed`` — e.g. ``"HVAC Technician"``
          - ``urgency`` — ``"emergency"``, ``"urgent"``, or ``"routine"``
          - ``urgency_rationale`` — explanation of the urgency classification
          - ``habitability_applicable`` — bool
          - ``habitability_deadline_hours`` — int | None
          - ``safety_instructions`` — str
    """
    try:
        result = await run_triage(tenant_report, state)
        # Ensure the result has all required keys.
        required = {
            "likely_issues",
            "trade_needed",
            "urgency",
            "urgency_rationale",
            "habitability_applicable",
            "habitability_deadline_hours",
            "safety_instructions",
        }
        missing = required - set(result.keys())
        if missing:
            result["fallback_fields"] = list(missing)
            fallback = _keyword_triage(tenant_report, state)
            for k in missing:
                result[k] = fallback[k]
        result["source"] = "nemotron"
        result["state"] = state
        return result
    except Exception:
        return _keyword_triage(tenant_report, state)


# ---------------------------------------------------------------------------
# CLI test harness
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    async def _main() -> None:
        test_cases = [
            ("emergency", "I smell gas in the kitchen, there might be a gas leak!"),
            ("urgent", "AC not cooling, 87 degrees inside, have a newborn baby"),
            ("routine", "The garbage disposal is humming but not spinning. Sink drains fine."),
        ]

        for label, report in test_cases:
            print(f"\n{'='*70}")
            print(f"TEST: {label.upper()}")
            print(f"{'='*70}")
            print(f"Report: {report}")
            result = await triage_issue(report)
            print(json.dumps(result, indent=2, default=str))

    import asyncio

    asyncio.run(_main())

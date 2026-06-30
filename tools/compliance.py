"""
Habitability Compliance Checker

A lookup-table-based compliance checker that determines habitability deadlines
for property maintenance issues based on state regulations and issue type.

Exports:
    async def check_habitability(state, issue_type, urgency) -> dict
    def get_escalation_schedule(deadline_hours) -> dict
"""

# Hardcoded habitability deadline matrix (from hackathon spec Appendix A)
# Format: { state_code: { issue_type: deadline_hours } }
_HABITABILITY_MATRIX: dict[str, dict[str, int]] = {
    "CA": {"HVAC": 24, "Plumbing": 24, "Electrical": 24, "Structural": 72, "Pest": 120},
    "NY": {"HVAC": 24, "Plumbing": 24, "Electrical": 48, "Structural": 72, "Pest": 168},
    "TX": {"HVAC": 48, "Plumbing": 48, "Electrical": 48, "Structural": 168, "Pest": 168},
    "FL": {"HVAC": 24, "Plumbing": 24, "Electrical": 48, "Structural": 72, "Pest": 120},
    "IL": {"HVAC": 48, "Plumbing": 48, "Electrical": 48, "Structural": 168, "Pest": 168},
    "PA": {"HVAC": 48, "Plumbing": 72, "Electrical": 48, "Structural": 168, "Pest": 240},
    "OH": {"HVAC": 72, "Plumbing": 72, "Electrical": 48, "Structural": 168, "Pest": 240},
    "WA": {"HVAC": 24, "Plumbing": 24, "Electrical": 24, "Structural": 72, "Pest": 120},
    "AZ": {"HVAC": 48, "Plumbing": 48, "Electrical": 48, "Structural": 168, "Pest": 240},
    "CO": {"HVAC": 48, "Plumbing": 48, "Electrical": 48, "Structural": 168, "Pest": 168},
}

# Default values for states not explicitly listed
_DEFAULT_DEADLINES: dict[str, int] = {
    "HVAC": 72, "Plumbing": 72, "Electrical": 72, "Structural": 240, "Pest": 240,
}

# Valid issue types for lookup
_VALID_ISSUE_TYPES = {"HVAC", "Plumbing", "Electrical", "Structural", "Pest"}


def _get_deadline(state: str, issue_type: str) -> int:
    """Look up the deadline hours for a given state and issue type."""
    # Normalize state to uppercase
    state_upper = state.upper()
    issue_type_normalized = issue_type.capitalize()

    # Use the issue_type key as-is if it matches exactly, otherwise try normalized
    for key in _VALID_ISSUE_TYPES:
        if key.lower() == issue_type.lower():
            issue_type_normalized = key
            break

    # Look up state matrix, falling back to default
    state_deadlines = _HABITABILITY_MATRIX.get(state_upper, _DEFAULT_DEADLINES)
    return state_deadlines.get(issue_type_normalized, _DEFAULT_DEADLINES.get(issue_type_normalized, 72))


def _format_deadline_label(hours: int) -> str:
    """Format deadline hours into a human-readable label."""
    if hours == 1:
        return "1 hour"
    return f"{hours} hours"


def _build_notes(state: str, issue_type: str, deadline: int) -> str:
    """Build contextual notes for the compliance check result."""
    state_upper = state.upper()
    is_specific_state = state_upper in _HABITABILITY_MATRIX

    if not is_specific_state:
        return f"Default habitability deadline applied — {state} not in specific state matrix"

    if deadline <= 24:
        return "Emergency response required — 24-hour or less deadline"
    elif deadline <= 72:
        return "Expedited response required — within 72-hour window"
    else:
        return "Standard response timeline applies"


def get_escalation_schedule(deadline_hours: int) -> dict:
    """
    Return the escalation schedule for a given deadline in hours.

    Milestones:
        - 50%  → notify project manager
        - 75%  → notify property owner
        - 100% → legal escalation

    Args:
        deadline_hours: Total allowed hours for resolution.

    Returns:
        dict with milestone percentages, times, and actions.
    """
    if deadline_hours <= 0:
        return {
            "milestones": [],
            "deadline_hours": deadline_hours,
        }

    milestones = [
        {
            "percentage": 50,
            "label": "50%",
            "hours": deadline_hours * 0.5,
            "action": "Notify project manager",
        },
        {
            "percentage": 75,
            "label": "75%",
            "hours": deadline_hours * 0.75,
            "action": "Notify property owner",
        },
        {
            "percentage": 100,
            "label": "100%",
            "hours": float(deadline_hours),
            "action": "Legal escalation",
        },
    ]

    return {
        "milestones": milestones,
        "deadline_hours": deadline_hours,
    }


async def check_habitability(state: str, issue_type: str, urgency: str) -> dict:
    """
    Check habitability compliance for a given state, issue type, and urgency level.

    Args:
        state: Two-letter US state code (e.g., "CA", "NY"). Case-insensitive.
        issue_type: Type of issue (HVAC, Plumbing, Electrical, Structural, Pest).
                    Case-insensitive.
        urgency: Urgency level (e.g., "urgent", "standard", "non-urgent").

    Returns:
        dict with compliance information:
            - state: Normalized state code (uppercase)
            - issue_type: Normalized issue type
            - applicable: Whether a habitability deadline applies
            - deadline_hours: Deadline in hours
            - deadline_label: Human-readable label (e.g. "24 hours")
            - escalation_75pct_hours: Hours at which 75% escalation triggers
            - escalation_100pct_hours: Hours at which 100% escalation triggers
            - notes: Contextual notes about the result
    """
    # Normalize inputs
    state_upper = state.upper()
    issue_type_normalized = issue_type.capitalize()
    for key in _VALID_ISSUE_TYPES:
        if key.lower() == issue_type.lower():
            issue_type_normalized = key
            break

    urgency_lower = urgency.lower()

    # Look up deadline
    deadline_hours = _get_deadline(state_upper, issue_type_normalized)

    # Determine applicability — all valid issue types are applicable
    applicable = issue_type_normalized in _VALID_ISSUE_TYPES

    # Calculate escalation thresholds
    escalation_75pct = deadline_hours * 0.75
    escalation_100pct = deadline_hours

    # Build notes
    notes = _build_notes(state_upper, issue_type_normalized, deadline_hours)

    if urgency_lower == "urgent" and deadline_hours <= 24:
        notes += " | URGENT: Escalate immediately — within emergency window"

    return {
        "state": state_upper,
        "issue_type": issue_type_normalized,
        "applicable": applicable,
        "deadline_hours": deadline_hours,
        "deadline_label": _format_deadline_label(deadline_hours),
        "escalation_75pct_hours": escalation_75pct,
        "escalation_100pct_hours": escalation_100pct,
        "notes": notes,
    }


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(check_habitability("CA", "HVAC", "urgent"))
    print("Habitability Check Result:")
    import json
    print(json.dumps(result, indent=2))
    print()
    print("Escalation Schedule:")
    schedule = get_escalation_schedule(result["deadline_hours"])
    print(json.dumps(schedule, indent=2))

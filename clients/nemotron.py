"""Nemotron 3 Ultra API client via NVIDIA NIM Cloud."""

from config import get_nemotron_client, get_settings

# System prompts for each Nemotron model (from spec §4.3)

TRIAGE_SYSTEM_PROMPT = """You are a property maintenance triage expert. Given a tenant's description of an issue, determine:
1. Likely issue(s) — specific diagnosis with confidence level
2. Trade needed — electrician, plumber, HVAC, general contractor, etc.
3. Urgency level — emergency (life/safety/property damage imminent), urgent (habitability affected, needs 24-48h), routine (can be scheduled within 3-7 days)
4. State habitability law applicability — does this trigger habitability requirements in {state}?
5. Safety instructions for tenant — what should they do/not do immediately

Respond in structured JSON only."""

VENDOR_MATCH_SYSTEM_PROMPT = """You are a vendor matching system for property maintenance. Given a maintenance issue, location, and urgency, identify the best vendor(s) from the available pool.

Prioritize by:
1. Trade match (exact trade for the issue type)
2. License verification status (must be current)
3. Proximity to property (within 20 miles preferred for routine, 50 miles for emergency)
4. Rating (minimum 4.0★)
5. Availability (can arrive within urgency window)
6. Pricing tier (within 15% of market benchmark for the trade in that ZIP code)
7. Insurance coverage (minimum $1M general liability)

Return top 3 vendors ranked with match scores and rationale."""

QUOTE_COMPARISON_SYSTEM_PROMPT = """You are a construction cost estimator. Compare quotes from vendors against market benchmarks for the specific repair type in the given ZIP code.

Benchmarks by trade (national averages, adjusted by regional cost index):
- HVAC capacitor replacement: $150-$400
- HVAC refrigerant recharge (R-410A): $200-$600
- HVAC compressor replacement: $1,200-$2,500
- Plumbing leak repair (accessible): $150-$500
- Plumbing pipe replacement (in-wall): $500-$2,000
- Electrical outlet/switch: $100-$300
- Electrical panel repair: $500-$1,500
- Water heater replacement: $800-$2,000
- Roof leak repair: $300-$1,500
- Drywall repair: $200-$800

For each quote, assess:
1. Within benchmark range?
2. Includes all necessary scope?
3. Warranty on workmanship included?
4. Materials quality specified?
5. Any red flags (too cheap = cutting corners, too expensive = gouging)?

Return recommendation with justification."""


async def run_triage(tenant_report: str, state: str = "CA") -> dict:
    """Run Nemotron 3 Ultra maintenance triage on a tenant report."""
    client = get_nemotron_client()
    prompt = TRIAGE_SYSTEM_PROMPT.format(state=state)

    response = client.chat.completions.create(
        model=get_settings().nemotron_model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": tenant_report},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1000,
    )
    import json
    result = json.loads(response.choices[0].message.content)
    return result


async def match_vendors(trade: str, zip_code: str, urgency: str, vendors: list[dict]) -> list[dict]:
    """Rank available vendors using Nemotron."""
    client = get_nemotron_client()

    vendor_list = "\n".join(
        f"- {v['name']} ({v['trade']}, ★{v['rating']}, {v.get('distance_miles', '?')}mi, ${v.get('estimated_cost_range', '?')})"
        for v in vendors
    )

    response = client.chat.completions.create(
        model=get_settings().nemotron_model,
        messages=[
            {"role": "system", "content": VENDOR_MATCH_SYSTEM_PROMPT},
            {"role": "user", "content": f"Trade needed: {trade}\nZIP: {zip_code}\nUrgency: {urgency}\n\nAvailable vendors:\n{vendor_list}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1500,
    )
    import json
    result = json.loads(response.choices[0].message.content)
    return result.get("matches", [])


async def compare_quotes(quotes: list[dict], zip_code: str) -> dict:
    """Compare vendor quotes against market benchmarks using Nemotron."""
    client = get_nemotron_client()

    quotes_text = "\n".join(
        f"- Vendor: {q.get('vendor_name', '?')}, Amount: ${q['quote_amount']}, Scope: {q.get('scope_of_work', '?')}"
        for q in quotes
    )

    response = client.chat.completions.create(
        model=get_settings().nemotron_model,
        messages=[
            {"role": "system", "content": QUOTE_COMPARISON_SYSTEM_PROMPT},
            {"role": "user", "content": f"ZIP Code: {zip_code}\n\nQuotes to compare:\n{quotes_text}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1500,
    )
    import json
    result = json.loads(response.choices[0].message.content)
    return result

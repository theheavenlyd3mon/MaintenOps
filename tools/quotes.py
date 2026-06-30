"""Quote Comparison Engine — AI-powered with deterministic fallback.

Attempts Nemotron 3 Ultra analysis first; falls back to a hardcoded benchmark
engine when the AI service is unavailable.
"""

import asyncio
import logging
import re

logger = logging.getLogger(__name__)

# Lazy import — clients/nemotron pulls in config which needs stripe/openai,
# which may not be installed in all environments.  If the import fails we
# silently use the deterministic fallback.
_nemotron_available = False
_nemotron_compare = None

try:
    from clients.nemotron import compare_quotes as _nemotron_compare

    _nemotron_available = True
except ImportError:
    logger.debug("clients.nemotron not available — will use fallback engine")

# ---------------------------------------------------------------------------
# Benchmark data
# ---------------------------------------------------------------------------

BENCHMARKS = {
    "HVAC": {"min": 150, "max": 600, "description": "HVAC diagnostic/repair"},
    "Plumbing": {"min": 150, "max": 500, "description": "Plumbing repair"},
    "Electrical": {"min": 100, "max": 500, "description": "Electrical repair"},
    "Structural": {"min": 300, "max": 1500, "description": "Structural/cosmetic repair"},
}

REGIONAL_MULTIPLIERS = {"94102": 1.3, "94103": 1.3, "94104": 1.3, "default": 1.0}

# Trade detection — regex patterns matched case-insensitively against scope_of_work
_TRADE_KEYWORDS = {
    "HVAC": [
        r"\bac\b",
        r"\bhvac\b",
        r"\bheating\b",
        r"\bcooling\b",
        r"\bfurnace\b",
        r"\bthermostat\b",
        r"\brefrigerant\b",
        r"\brecharge\b",
        r"\bcompressor\b",
        r"air condition",
        r"\bventilation\b",
        r"\ba/c\b",
        r"heat pump",
        r"\bduct\b",
    ],
    "Plumbing": [
        r"\bplumb",
        r"\bpipe\b",
        r"\bdrain\b",
        r"\bfaucet\b",
        r"\btoilet\b",
        r"water heater",
        r"\bsewer\b",
        r"\bleak\b",
        r"water line",
        r"\bvalve\b",
        r"\bsink\b",
        r"\bshower\b",
        r"\btub\b",
    ],
    "Electrical": [
        r"\belectrical\b",
        r"\bwiring\b",
        r"\boutlet\b",
        r"\bswitch\b",
        r"\bbreaker\b",
        r"\bpanel\b",
        r"\bcircuit\b",
        r"\blight\b",
        r"\bfixture\b",
        r"\belectric\b",
        r"\bconduit\b",
        r"\bsubpanel\b",
    ],
    "Structural": [
        r"\bstructural\b",
        r"\bdrywall\b",
        r"\broof\b",
        r"\bfoundation\b",
        r"\bwall\b",
        r"\bceiling\b",
        r"\bfloor\b",
        r"\bframing\b",
        r"\binsulation\b",
        r"\bpaint\b",
        r"\bcosmetic\b",
        r"\bdemo\b",
        r"\bfascia\b",
    ],
}


# ---------------------------------------------------------------------------
# Trade detection helper
# ---------------------------------------------------------------------------

def _detect_trade(scope_of_work: str) -> str:
    """Detect the trade category from scope of work text using keyword matching.

    Returns one of: HVAC, Plumbing, Electrical, Structural.
    Defaults to Structural when no keywords match.
    """
    text = scope_of_work.lower()
    scores: dict[str, int] = {}
    for trade, patterns in _TRADE_KEYWORDS.items():
        score = sum(1 for p in patterns if re.search(p, text))
        if score > 0:
            scores[trade] = score
    if scores:
        return max(scores, key=scores.get)
    return "Structural"


# ---------------------------------------------------------------------------
# Regional multiplier
# ---------------------------------------------------------------------------

def _get_regional_multiplier(zip_code: str) -> float:
    """Return the cost multiplier for *zip_code* (defaults to 1.0)."""
    if zip_code in REGIONAL_MULTIPLIERS:
        return REGIONAL_MULTIPLIERS[zip_code]
    if zip_code and zip_code.startswith("941"):
        return REGIONAL_MULTIPLIERS.get("94102", 1.3)
    return REGIONAL_MULTIPLIERS["default"]


# ---------------------------------------------------------------------------
# Fallback benchmark engine
# ---------------------------------------------------------------------------

def _fallback_benchmark_engine(quotes: list[dict], zip_code: str) -> dict:
    """Deterministic comparison against hardcoded market benchmarks.

    Every quote is classified into a trade by scanning its scope_of_work.
    Benchmarks are adjusted with the regional multiplier for *zip_code*.
    Quotes more than 30 % above/below the adjusted average are flagged as
    outliers.  The recommended vendor is the one closest to benchmark average
    that falls within the adjusted range; if none are within range, the
    closest-quote overall is selected.
    """
    if not quotes:
        return {
            "recommendation": None,
            "analysis": [],
            "summary": "No quotes provided for comparison.",
        }

    multiplier = _get_regional_multiplier(zip_code)
    analysis: list[dict] = []
    best_within_range: list[dict] = []

    for quote in quotes:
        vendor_name = quote.get("vendor_name", "Unknown")
        amount = quote.get("quote_amount", 0.0)
        scope = quote.get("scope_of_work", "")

        trade = _detect_trade(scope)
        benchmark = BENCHMARKS.get(trade, BENCHMARKS["Structural"])
        adj_min = round(benchmark["min"] * multiplier, 2)
        adj_max = round(benchmark["max"] * multiplier, 2)
        adj_avg = round((benchmark["min"] + benchmark["max"]) / 2 * multiplier, 2)

        within_benchmark = adj_min <= amount <= adj_max
        upper_outlier = round(adj_avg * 1.3, 2)
        lower_outlier = round(adj_avg * 0.7, 2)
        is_outlier = amount > upper_outlier or amount < lower_outlier

        pct_diff = ((amount - adj_avg) / adj_avg) * 100
        notes = (
            f"Detected trade: {trade} — "
            f"Adjusted benchmark range for ZIP {zip_code}: "
            f"${adj_min:.0f}-${adj_max:.0f} (avg ${adj_avg:.0f}) — "
        )
        if within_benchmark:
            notes += "Within benchmark range"
        else:
            notes += "Outside benchmark range"
        if is_outlier:
            sign = "+" if amount > adj_avg else ""
            notes += f" — Flagged as outlier ({sign}{pct_diff:.0f}% vs benchmark avg)"

        analysis.append(
            {
                "vendor_name": vendor_name,
                "within_benchmark": within_benchmark,
                "outlier": is_outlier,
                "notes": notes,
            }
        )

        if within_benchmark and not is_outlier:
            best_within_range.append(quote)

    # --- Recommendation ---
    def _distance_to_avg(q: dict) -> float:
        t = _detect_trade(q.get("scope_of_work", ""))
        b = BENCHMARKS.get(t, BENCHMARKS["Structural"])
        avg = round((b["min"] + b["max"]) / 2 * multiplier, 2)
        return abs(q.get("quote_amount", 0) - avg)

    if best_within_range:
        best_vendor = min(best_within_range, key=_distance_to_avg)
        reason = (
            f"Vendor is within the adjusted benchmark range for ZIP {zip_code} "
            f"and offers a competitive quote."
        )
    else:
        best_vendor = min(quotes, key=_distance_to_avg)
        reason = (
            f"No quotes fall within the adjusted benchmark range for ZIP {zip_code}. "
            f"Recommend the closest quote to the market average."
        )

    recommendation = {
        "vendor_name": best_vendor["vendor_name"],
        "quote_amount": best_vendor["quote_amount"],
        "reason": reason,
    }

    within_count = sum(1 for a in analysis if a["within_benchmark"])
    outlier_count = sum(1 for a in analysis if a["outlier"])
    summary = (
        f"Compared {len(quotes)} quote(s) for ZIP {zip_code}. "
        f"{within_count} within benchmark range, {outlier_count} flagged as outlier(s). "
        f"Recommended: {recommendation['vendor_name']} at "
        f"${recommendation['quote_amount']:.2f}."
    )

    return {
        "recommendation": recommendation,
        "analysis": analysis,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def compare_quotes(quotes: list[dict], zip_code: str = "94102") -> dict:
    """Compare vendor quotes against market benchmarks.

    Tries AI-powered analysis via Nemotron 3 Ultra first.  If that call
    fails (network error, missing API key, etc.) the deterministic fallback
    benchmark engine is used instead.

    Parameters
    ----------
    quotes : list[dict]
        Each dict must contain ``vendor_name``, ``quote_amount``, and
        ``scope_of_work``.
    zip_code : str
        ZIP code for regional cost adjustment (default ``"94102"``).

    Returns
    -------
    dict
        ``{"recommendation": {...}, "analysis": [...], "summary": "..."}``
    """
    try:
        if _nemotron_available:
            result = await _nemotron_compare(quotes, zip_code)
            logger.info("Nemotron quote comparison succeeded")
            return result
        raise RuntimeError("Nemotron client not available")
    except Exception as exc:
        logger.warning("Nemotron comparison failed, using fallback: %s", exc)
        return _fallback_benchmark_engine(quotes, zip_code)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    test_quotes = [
        {
            "vendor_name": "CoolTech",
            "quote_amount": 850.0,
            "scope_of_work": "AC diagnostic + recharge",
        },
        {
            "vendor_name": "BayArea",
            "quote_amount": 1200.0,
            "scope_of_work": "Full AC inspection",
        },
        {
            "vendor_name": "Pacific HVAC",
            "quote_amount": 950.0,
            "scope_of_work": "AC diagnostic and repair",
        },
    ]

    result = asyncio.run(compare_quotes(test_quotes, "94102"))
    print(f"Recommendation: {result['recommendation']['vendor_name']}")
    print(f"At: ${result['recommendation']['quote_amount']:.2f}")
    print(f"Reason: {result['recommendation']['reason']}")
    print()
    for a in result["analysis"]:
        print(f"  {a['vendor_name']}: within={a['within_benchmark']}, "
              f"outlier={a['outlier']}")
    print()
    print(f"Summary: {result['summary']}")

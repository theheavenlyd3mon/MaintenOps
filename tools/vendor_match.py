#!/usr/bin/env python3
"""Vendor Matching Engine — finds and ranks best vendors for a maintenance job.

Queries the database for trade-matching vendors with AI ranking via
Nemotron 3 Ultra, falling back to hardcoded demo data and rating-based
sorting when upstream services are unavailable.
"""

import json
import logging

from clients.nemotron import match_vendors as nemotron_rank_vendors
from db import check_db_connection, get_pool

logger = logging.getLogger(__name__)

# ── Hardcoded Demo Vendor Profiles (fallback when DB is unavailable) ──────────
# These match the 5 demo vendors from seed.py (3 HVAC + 2 Plumbing).

DEMO_VENDORS = [
    {
        "name": "CoolTech HVAC",
        "trade": "HVAC",
        "rating": 4.9,
        "zip_code": "94102",
        "pricing_tier": "market_avg",
    },
    {
        "name": "Bay Area Climate Control",
        "trade": "HVAC",
        "rating": 4.7,
        "zip_code": "94104",
        "pricing_tier": "market_avg",
    },
    {
        "name": "Pacific HVAC Services",
        "trade": "HVAC",
        "rating": 4.2,
        "zip_code": "94102",
        "pricing_tier": "below_market",
    },
    {
        "name": "QuickFix Plumbing",
        "trade": "Plumbing",
        "rating": 4.8,
        "zip_code": "94102",
        "pricing_tier": "market_avg",
    },
    {
        "name": "Golden Gate Plumbing",
        "trade": "Plumbing",
        "rating": 4.3,
        "zip_code": "94104",
        "pricing_tier": "above_market",
    },
]

# Map pricing tier → human-readable estimated cost range for SF Bay Area.
_COST_MAP: dict[str, str] = {
    "below_market": "$150-$350",
    "market_avg": "$200-$500",
    "above_market": "$350-$650",
}


# ── Helpers ────────────────────────────────────────────────────────────────────


def _estimate_distance(vendor_zip: str, target_zip: str) -> float:
    """Estimate distance (miles) between two SF Bay Area ZIP codes.

    This is a stripped-down heuristic for demo purposes only:
      - Same ZIP → ~0.5-2.5 miles
      - Different but nearby (941xx range) → ~2-6 miles
      - Otherwise → a nominal 10 miles
    """
    v = int(vendor_zip)
    t = int(target_zip)

    if v == t:
        # Same ZIP: 0.5–2.5 mi  (deterministic via arithmetic)
        return round(0.5 + ((v * 7 + t * 3) % 20) / 10, 1)

    if 94100 <= v <= 94199 and 94100 <= t <= 94199:
        # Both in SF — base distance on ZIP difference
        diff = abs(v - t)
        return round(2.0 + (diff * 0.08), 1)

    return 10.0


def _enrich_vendor(v: dict, zip_code: str) -> dict:
    """Add derived fields (distance_miles, estimated_cost_range) to a vendor dict."""
    return {
        **v,
        "distance_miles": _estimate_distance(str(v.get("zip_code", zip_code)), zip_code),
        "estimated_cost_range": _COST_MAP.get(v.get("pricing_tier", "market_avg"), "$200-$500"),
    }


# ── Database access ────────────────────────────────────────────────────────────


async def _query_db_vendors(trade: str, zip_code: str) -> list[dict] | None:
    """Query the vendors table for trade-matching, available vendors.

    Returns ``None`` if the database is unreachable, so callers can fall
    back to hardcoded demo data.  Returns an empty list when the DB is
    reachable but no vendors match.
    """
    try:
        if not await check_db_connection():
            logger.info("DB unavailable — will use fallback vendors")
            return None

        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT name, trade, rating, pricing_tier
                FROM vendors
                WHERE trade = $1
                  AND available = true
                ORDER BY rating DESC
                """,
                trade,
            )

        if not rows:
            logger.info("No DB vendors found for trade=%s", trade)
            return []

        return [
            {
                "name": row["name"],
                "trade": row["trade"],
                "rating": float(row["rating"]),
                "pricing_tier": row["pricing_tier"],
            }
            for row in rows
        ]

    except Exception as exc:
        logger.warning("DB query failed: %s", exc)
        return None


# ── Public API ─────────────────────────────────────────────────────────────────


async def match_vendors(trade: str, zip_code: str, urgency: str = "routine") -> list[dict]:
    """Find and rank the top 3 vendors for a maintenance job.

    Pipeline:
      1. Query the database for vendors matching *trade*.
      2. Fall back to hardcoded demo vendors if DB is unavailable.
      3. Pass candidates through ``clients.nemotron.match_vendors()`` for
         AI-powered ranking.
      4. If the Nemotron call fails, sort candidates by rating descending
         (simple, deterministic fallback).

    Parameters
    ----------
    trade:
        Required trade, e.g. ``"HVAC"``, ``"Plumbing"``.
    zip_code:
        Property ZIP code for distance estimation.
    urgency:
        One of ``"emergency"``, ``"urgent"``, or ``"routine"`` (default).

    Returns
    -------
    list[dict]
        Top 3 vendors. Each dict contains:

        - **name** — Vendor name
        - **trade** — Trade category
        - **rating** — Star rating (0-5)
        - **distance_miles** — Estimated distance to property
        - **estimated_cost_range** — String price range
        - **match_score** — 0-100 score
        - **rationale** — Brief explanation of ranking
    """
    # ── Step 1 & 2: get vendor candidates ────────────────────────────────
    candidates = await _query_db_vendors(trade, zip_code)

    if candidates is None:
        # DB unreachable → use hardcoded fallback
        candidates = [v for v in DEMO_VENDORS if v["trade"] == trade]
        logger.info(
            "Using %d hardcoded demo vendors for trade=%s",
            len(candidates),
            trade,
        )

    if not candidates:
        return []

    # Enrich with distance and cost estimates before ranking
    enriched = [_enrich_vendor(v, zip_code) for v in candidates]

    # ── Step 3: AI ranking via Nemotron ──────────────────────────────────
    try:
        ranked = await nemotron_rank_vendors(trade, zip_code, urgency, enriched)
    except Exception as exc:
        logger.warning("Nemotron ranking failed: %s — falling back to rating sort", exc)
        ranked = None

    # ── Step 4 (fallback) / normalise output ─────────────────────────────
    if ranked is not None and isinstance(ranked, list):
        # Nemotron returned a list — take top 3, normalise fields
        results = []
        for v in ranked[:3]:
            results.append({
                "name": v.get("name", ""),
                "trade": v.get("trade", trade),
                "rating": v.get("rating", 0.0),
                "distance_miles": v.get("distance_miles", 0.0),
                "estimated_cost_range": v.get("estimated_cost_range", "$200-$500"),
                "match_score": v.get("match_score", 0),
                "rationale": v.get("rationale", ""),
            })
        return results

    # Fallback: sort by rating descending, take top 3
    sorted_vendors = sorted(enriched, key=lambda v: v["rating"], reverse=True)[:3]
    return [
        {
            "name": v["name"],
            "trade": v["trade"],
            "rating": v["rating"],
            "distance_miles": v["distance_miles"],
            "estimated_cost_range": v["estimated_cost_range"],
            "match_score": round(v["rating"] * 20, 0),  # 4.9 → 98.0
            "rationale": (
                f"Top-rated {v['trade']} vendor (★{v['rating']}) "
                f"serving your area."
            ),
        }
        for v in sorted_vendors
    ]


# ── CLI / test block ──────────────────────────────────────────────────────────


async def _main():
    """Demo: run match_vendors(trade='HVAC', zip_code='94102') and display results."""
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("  Vendor Matching Engine — Demo")
    print("=" * 60)
    print(f"  Trade:     HVAC")
    print(f"  ZIP Code:  94102")
    print(f"  Urgency:   routine")
    print("-" * 60)

    results = await match_vendors(trade="HVAC", zip_code="94102")

    print(f"\n  Top {len(results)} vendor(s):\n")
    for i, v in enumerate(results, 1):
        print(f"  #{i}  {v['name']}")
        print(f"      Trade:            {v['trade']}")
        print(f"      Rating:           ★{v['rating']}")
        print(f"      Distance:         {v['distance_miles']} mi")
        print(f"      Est. Cost Range:  {v['estimated_cost_range']}")
        print(f"      Match Score:      {v['match_score']}")
        print(f"      Rationale:        {v['rationale']}")
        print()

    print("-" * 60)
    print("Done.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())

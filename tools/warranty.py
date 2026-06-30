#!/usr/bin/env python3
"""
MaintenOps Warranty Checker Tool

Hardcoded appliance inventory for the demo property at 123 Main St.
Exports async functions for warranty checking and claim generation.
"""

import uuid
from datetime import date, datetime
from typing import Any, Optional

# ─────────────────────────────────────────────────────────────
# Hardcoded demo appliance inventory
# ─────────────────────────────────────────────────────────────
_PROPERTY_ADDRESS = "123 Main St, San Francisco, CA 94102"

_APPLIANCES: list[dict[str, Any]] = [
    {
        "id": 1,
        "type": "HVAC System",
        "brand": "Lennox",
        "model": "XC20-048",
        "installed_date": "2023-03-15",
        "warranty_provider": "Lennox Manufacturer Warranty",
        "warranty_type": "manufacturer",
        "warranty_expiry": "2028-03-15",
        "warranty_coverage": ["compressor", "refrigerant system", "coils"],
        "expected_lifespan_years": 15,
        "status": "active",
    }
]


# ─────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────
def _today_str() -> str:
    """Return today's date as YYYY-MM-DD string."""
    return date.today().isoformat()


def _parse_date(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────


async def check_warranty(
    property_address: str = "123 Main St, San Francisco, CA 94102",
) -> dict[str, Any]:
    """
    Check warranty status for all appliances at a property.

    Parameters
    ----------
    property_address : str
        Address string to look up (default: demo address).

    Returns
    -------
    dict with keys:
        property_address, appliance_found, appliance, warranty_active,
        days_remaining, coverage_applies, coverage_details,
        claim_eligible, claim_package
    """
    # Match the address to our hardcoded demo data
    if property_address != _PROPERTY_ADDRESS:
        return {
            "property_address": property_address,
            "appliance_found": False,
            "appliance": None,
            "warranty_active": None,
            "days_remaining": None,
            "coverage_applies": False,
            "coverage_details": [],
            "claim_eligible": False,
            "claim_package": None,
        }

    today = date.today()
    appliance = _APPLIANCES[0]
    warranty_expiry = _parse_date(appliance["warranty_expiry"])

    warranty_active = today <= warranty_expiry
    days_remaining = (warranty_expiry - today).days

    coverage_applies = warranty_active
    coverage_details = list(appliance["warranty_coverage"]) if warranty_active else []

    claim_eligible = warranty_active

    result: dict[str, Any] = {
        "property_address": property_address,
        "appliance_found": True,
        "appliance": appliance,
        "warranty_active": warranty_active,
        "days_remaining": days_remaining,
        "coverage_applies": coverage_applies,
        "coverage_details": coverage_details,
        "claim_eligible": claim_eligible,
        "claim_package": None,
    }

    return result


async def generate_claim(
    ticket_id: str,
    appliance_id: int,
    issue_description: str,
    estimated_repair_cost: float,
) -> dict[str, Any]:
    """
    Generate a warranty claim package for an appliance issue.

    Parameters
    ----------
    ticket_id : str
        Maintenance ticket identifier (e.g. "T-001").
    appliance_id : int
        ID of the appliance in the hardcoded inventory.
    issue_description : str
        Description of the issue being claimed.
    estimated_repair_cost : float
        Estimated cost of the repair.

    Returns
    -------
    dict with the claim package or an error message.
    """
    # Find the appliance
    appliance = None
    for a in _APPLIANCES:
        if a["id"] == appliance_id:
            appliance = a
            break

    if appliance is None:
        return {
            "error": True,
            "message": f"Appliance with id {appliance_id} not found.",
        }

    # Check warranty is still valid
    today = date.today()
    warranty_expiry = _parse_date(appliance["warranty_expiry"])

    if today > warranty_expiry:
        return {
            "error": True,
            "message": (
                f"Warranty for {appliance['brand']} {appliance['model']} "
                f"expired on {appliance['warranty_expiry']}. Cannot generate claim."
            ),
        }

    # Generate a simulated claim ID (UUID-like)
    claim_id = str(uuid.uuid4())

    claim_package: dict[str, Any] = {
        "ticket_id": ticket_id,
        "appliance": appliance,
        "issue": issue_description,
        "estimated_cost": estimated_repair_cost,
        "claim_status": "generated",
        "provider": appliance["warranty_provider"],
        "coverage_items": list(appliance["warranty_coverage"]),
        "submission_date": _today_str(),
        "claim_id": claim_id,
    }

    return claim_package


# ─────────────────────────────────────────────────────────────
# CLI / __main__ test block
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def _main() -> None:
        print("═" * 60)
        print("  MaintenOps — Warranty Checker (Demo)")
        print("═" * 60)

        # 1. Check warranty for demo address
        print("\n📋 Checking warranty for 123 Main St...\n")
        result = await check_warranty()
        print(f"  Property Address:  {result['property_address']}")
        print(f"  Appliance Found:   {result['appliance_found']}")
        if result["appliance"]:
            a = result["appliance"]
            print(f"  Appliance:         {a['brand']} {a['model']} ({a['type']})")
        print(f"  Warranty Active:   {result['warranty_active']}")
        print(f"  Days Remaining:    {result['days_remaining']}")
        print(f"  Coverage Applies:  {result['coverage_applies']}")
        print(f"  Coverage Details:  {result['coverage_details']}")
        print(f"  Claim Eligible:    {result['claim_eligible']}")

        # 2. Generate a claim
        print("\n📄 Generating claim for ticket T-001...\n")
        claim = await generate_claim(
            ticket_id="T-001",
            appliance_id=1,
            issue_description="AC compressor not engaging, no cooling output",
            estimated_repair_cost=1850.00,
        )
        if claim.get("error"):
            print(f"  ❌ {claim['message']}")
        else:
            print(f"  Claim ID:         {claim['claim_id']}")
            print(f"  Ticket ID:        {claim['ticket_id']}")
            print(f"  Appliance:        {claim['appliance']['brand']} {claim['appliance']['model']}")
            print(f"  Issue:            {claim['issue']}")
            print(f"  Estimated Cost:   ${claim['estimated_cost']:,.2f}")
            print(f"  Claim Status:     {claim['claim_status']}")
            print(f"  Provider:         {claim['provider']}")
            print(f"  Coverage Items:   {claim['coverage_items']}")
            print(f"  Submission Date:  {claim['submission_date']}")

        print("\n" + "═" * 60)
        print("  Demo complete.")
        print("═" * 60)

    asyncio.run(_main())

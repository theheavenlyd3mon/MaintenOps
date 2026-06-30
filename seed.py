#!/usr/bin/env python3
"""
MaintenOps Demo Data Seed Script

Populates the PostgreSQL database with demo data for the MaintenOps hackathon demo.
Works in two modes:
  1. SQL mode: Writes SQL INSERT statements to a file
  2. Simulation mode: Prints what it WOULD insert (for validation)

Usage:
  python3 seed.py                    # writes seed.sql by default
  python3 seed.py --simulate         # prints what would be inserted
  python3 seed.py --output my.sql    # write to custom path
"""

import argparse
import json
import sys
from datetime import date, datetime
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════
# Demo Data Definitions
# ═══════════════════════════════════════════════════════════════

OWNER = {
    "id": "00000000-0000-0000-0000-000000000001",
    "name": "Demo Owner",
    "email": "owner@example.com",
    "stripe_customer_id": "cus_demo_001",
    "maintenance_limit": 1500.00,
    "emergency_limit": 5000.00,
}

PROPERTY = {
    "id": "00000000-0000-0000-0000-000000000010",
    "address": "123 Main St, San Francisco, CA 94102",
    "owner_id": OWNER["id"],
}

VENDORS = [
    {
        "id": "00000000-0000-0000-0000-000000000101",
        "name": "CoolTech HVAC",
        "trade_type": "HVAC",
        "license_number": "CA-HVAC-4821",
        "license_expiry": "2027-06-01",
        "insurance_amount": 2000000.00,
        "insurance_provider": "ActiveSure",
        "workers_comp": True,
        "rating": 4.9,
        "service_zip_codes": [94102, 94103, 94110, 94111, 94117],
        "pricing_tier": "market_avg",
        "stripe_connect_account_id": "acct_vendor_001",
        "available": True,
    },
    {
        "id": "00000000-0000-0000-0000-000000000102",
        "name": "Bay Area Climate Control",
        "trade_type": "HVAC",
        "license_number": "CA-HVAC-7193",
        "license_expiry": "2026-12-01",
        "insurance_amount": 1500000.00,
        "insurance_provider": "InsurePro",
        "workers_comp": True,
        "rating": 4.7,
        "service_zip_codes": [94102, 94104, 94105, 94107, 94108],
        "pricing_tier": "market_avg",
        "stripe_connect_account_id": "acct_vendor_002",
        "available": True,
    },
    {
        "id": "00000000-0000-0000-0000-000000000103",
        "name": "Pacific HVAC Services",
        "trade_type": "HVAC",
        "license_number": "CA-HVAC-3348",
        "license_expiry": "2026-09-15",
        "insurance_amount": 1000000.00,
        "insurance_provider": "CoveragePlus",
        "workers_comp": True,
        "rating": 4.2,
        "service_zip_codes": [94102, 94103, 94109, 94115, 94121],
        "pricing_tier": "below_market",
        "stripe_connect_account_id": "acct_vendor_003",
        "available": True,
    },
    {
        "id": "00000000-0000-0000-0000-000000000104",
        "name": "QuickFix Plumbing",
        "trade_type": "Plumbing",
        "license_number": "CA-PL-8821",
        "license_expiry": "2027-03-01",
        "insurance_amount": 1500000.00,
        "insurance_provider": "ActiveSure",
        "workers_comp": True,
        "rating": 4.8,
        "service_zip_codes": [94102, 94103, 94110, 94111, 94117, 94122, 94123],
        "pricing_tier": "market_avg",
        "stripe_connect_account_id": "acct_vendor_004",
        "available": True,
    },
    {
        "id": "00000000-0000-0000-0000-000000000105",
        "name": "Golden Gate Plumbing",
        "trade_type": "Plumbing",
        "license_number": "CA-PL-5543",
        "license_expiry": "2026-08-01",
        "insurance_amount": 1000000.00,
        "insurance_provider": "InsurePro",
        "workers_comp": True,
        "rating": 4.3,
        "service_zip_codes": [94102, 94104, 94105, 94107, 94108, 94109],
        "pricing_tier": "above_market",
        "stripe_connect_account_id": "acct_vendor_005",
        "available": True,
    },
]

APPLIANCE_INVENTORY = {
    "id": "00000000-0000-0000-0000-000000000201",
    "property_id": PROPERTY["id"],
    "appliance_type": "HVAC",
    "brand": "Lennox",
    "model": "XC20-048",
    "installed_date": "2023-03-15",
    "warranty_provider": "Lennox Manufacturer Warranty",
    "warranty_type": "manufacturer",
    "warranty_expiry": "2028-03-15",
    "warranty_coverage": ["compressor", "refrigerant system", "coils"],
    "expected_lifespan_years": 15,
}

QUOTES = [
    {
        "id": "00000000-0000-0000-0000-000000000301",
        "vendor_id": VENDORS[0]["id"],  # CoolTech HVAC
        "property_id": PROPERTY["id"],
        "amount": 850.00,
        "scope": "AC diagnostic + refrigerant recharge + system test",
        "status": "pending",
    },
    {
        "id": "00000000-0000-0000-0000-000000000302",
        "vendor_id": VENDORS[1]["id"],  # Bay Area Climate Control
        "property_id": PROPERTY["id"],
        "amount": 1200.00,
        "scope": "Full AC inspection + refrigerant service",
        "status": "pending",
    },
    {
        "id": "00000000-0000-0000-0000-000000000303",
        "vendor_id": VENDORS[2]["id"],  # Pacific HVAC Services
        "property_id": PROPERTY["id"],
        "amount": 950.00,
        "scope": "AC diagnostic and repair",
        "status": "pending",
    },
]


# ═══════════════════════════════════════════════════════════════
# SQL Generation
# ═══════════════════════════════════════════════════════════════

CREATE_TABLE_SQL = """
-- ============================================================
-- MaintenOps Demo Schema
-- ============================================================

CREATE TABLE IF NOT EXISTS owners (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    stripe_customer_id VARCHAR(255),
    maintenance_limit NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    emergency_limit NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS properties (
    id UUID PRIMARY KEY,
    address TEXT NOT NULL,
    owner_id UUID NOT NULL REFERENCES owners(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    trade_type VARCHAR(100) NOT NULL,
    license_number VARCHAR(100) NOT NULL UNIQUE,
    license_expiry DATE NOT NULL,
    insurance_amount NUMERIC(12, 2) NOT NULL,
    insurance_provider VARCHAR(255) NOT NULL,
    workers_comp BOOLEAN NOT NULL DEFAULT FALSE,
    rating NUMERIC(3, 1) NOT NULL DEFAULT 0.0,
    pricing_tier VARCHAR(50) NOT NULL DEFAULT 'market_avg',
    stripe_connect_account_id VARCHAR(255),
    available BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vendor_service_zip_codes (
    id SERIAL PRIMARY KEY,
    vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    zip_code VARCHAR(10) NOT NULL,
    UNIQUE(vendor_id, zip_code)
);

CREATE TABLE IF NOT EXISTS appliance_inventory (
    id UUID PRIMARY KEY,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    appliance_type VARCHAR(100) NOT NULL,
    brand VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    installed_date DATE NOT NULL,
    warranty_provider VARCHAR(255),
    warranty_type VARCHAR(50),
    warranty_expiry DATE,
    warranty_coverage JSONB,
    expected_lifespan_years INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quotes (
    id UUID PRIMARY KEY,
    vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL,
    scope TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""


def _escape(val: Any) -> str:
    """Escape a Python value for use in a SQL string."""
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, (date, datetime)):
        return f"'{val.isoformat()}'"
    if isinstance(val, (list, dict)):
        return f"'{json.dumps(val)}'"
    # string
    escaped = str(val).replace("'", "''")
    return f"'{escaped}'"


def _sql_insert(table: str, row: dict) -> str:
    """Generate a single INSERT statement for a row."""
    columns = ", ".join(row.keys())
    values = ", ".join(_escape(v) for v in row.values())
    return f"INSERT INTO {table} ({columns}) VALUES ({values});"


def _sql_insert_multi(table: str, rows: list[dict]) -> str:
    """Generate INSERT statements for multiple rows."""
    return "\n".join(_sql_insert(table, row) for row in rows)


def generate_sql(path: str) -> None:
    """Write all CREATE TABLE and INSERT statements to a file."""
    lines = [
        "-- ============================================================",
        "-- MaintenOps Demo Data Seed Script",
        f"-- Generated: {datetime.now().isoformat()}",
        "-- ============================================================",
        "",
        "-- Start a transaction so everything is atomic",
        "BEGIN;",
        "",
        "-- ============================================================",
        "-- Schema (CREATE TABLE statements)",
        "-- ============================================================",
        CREATE_TABLE_SQL,
        "",
        "-- ============================================================",
        "-- Seed Data",
        "-- ============================================================",
        "",
        "-- Owners",
        _sql_insert("owners", OWNER),
        "",
        "-- Properties",
        _sql_insert("properties", PROPERTY),
        "",
        "-- Vendors",
    ]

    for vendor in VENDORS:
        # Make a copy without service_zip_codes for the vendors table
        vendor_row = {k: v for k, v in vendor.items() if k != "service_zip_codes"}
        lines.append(_sql_insert("vendors", vendor_row))

    lines.append("")
    lines.append("-- Vendor Service Zip Codes")
    for vendor in VENDORS:
        for zc in vendor["service_zip_codes"]:
            lines.append(
                _sql_insert(
                    "vendor_service_zip_codes",
                    {
                        "vendor_id": vendor["id"],
                        "zip_code": str(zc),
                    },
                )
            )

    lines.append("")
    lines.append("-- Appliance Inventory")
    lines.append(_sql_insert("appliance_inventory", APPLIANCE_INVENTORY))

    lines.append("")
    lines.append("-- Quotes")
    for q in QUOTES:
        lines.append(_sql_insert("quotes", q))

    lines.append("")
    lines.append("COMMIT;")
    lines.append("")

    content = "\n".join(lines)

    with open(path, "w") as f:
        f.write(content)

    print(f"✅ SQL seed script written to: {path}")


# ═══════════════════════════════════════════════════════════════
# Simulation Mode
# ═══════════════════════════════════════════════════════════════

def _simulate_table(label: str, rows: list[dict]) -> None:
    """Print a simulation summary for a table's data."""
    print(f"\n{'─' * 72}")
    print(f"  📋 {label}")
    print(f"{'─' * 72}")
    for row in rows:
        name = row.get("name", row.get("address", row.get("brand", row["id"])))
        print(f"    • {name}")
        for k, v in row.items():
            if k == "id":
                continue
            print(f"      {k}: {v}")
        print()


def simulate() -> None:
    """Print what would be inserted (simulation mode)."""
    print()
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║      MaintenOps Demo Data — Simulation Mode                  ║")
    print("║      Showing what would be inserted into the database        ║")
    print("╚═══════════════════════════════════════════════════════════════╝")

    # -- Owners --
    _simulate_table("OWNERS (1 record)", [OWNER])

    # -- Properties --
    _simulate_table("PROPERTIES (1 record)", [PROPERTY])

    # -- Vendors --
    hvac_vendors = [v for v in VENDORS if v["trade_type"] == "HVAC"]
    plumbing_vendors = [v for v in VENDORS if v["trade_type"] == "Plumbing"]

    print(f"\n{'─' * 72}")
    print(f"  🔧 VENDORS — HVAC ({len(hvac_vendors)} records)")
    print(f"{'─' * 72}")
    for v in hvac_vendors:
        print(f"    • {v['name']}")
        for k, val in v.items():
            if k == "id":
                continue
            print(f"      {k}: {val}")
        print()

    print(f"\n{'─' * 72}")
    print(f"  🔧 VENDORS — Plumbing ({len(plumbing_vendors)} records)")
    print(f"{'─' * 72}")
    for v in plumbing_vendors:
        print(f"    • {v['name']}")
        for k, val in v.items():
            if k == "id":
                continue
            print(f"      {k}: {val}")
        print()

    # -- Appliance Inventory --
    _simulate_table("APPLIANCE INVENTORY (1 record)", [APPLIANCE_INVENTORY])

    # -- Quotes --
    print(f"\n{'─' * 72}")
    print(f"  💰 PRE-SEEDED QUOTES ({len(QUOTES)} records)")
    print(f"{'─' * 72}")
    vendor_names = {v["id"]: v["name"] for v in VENDORS}
    for q in QUOTES:
        vname = vendor_names.get(q["vendor_id"], "Unknown")
        print(f"    • ${q['amount']:,.2f} — {vname}")
        for k, val in q.items():
            if k == "id" or k == "vendor_id":
                continue
            print(f"      {k}: {val}")
        print()

    print(f"{'═' * 72}")
    print(f"  ✅ Simulation complete. No data was written to the database.")
    print(f"  🗂  Run without --simulate to generate the SQL file.")
    print(f"{'═' * 72}\n")


# ═══════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="MaintenOps Demo Data Seed Script",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Print what would be inserted without writing SQL",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="seed.sql",
        help="Path to write the SQL seed file (default: seed.sql)",
    )
    args = parser.parse_args()

    if args.simulate:
        simulate()
    else:
        generate_sql(args.output)


if __name__ == "__main__":
    main()

"""Database connection pool and schema management."""

import asyncpg
from config import get_settings


_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        s = get_settings()
        _pool = await asyncpg.create_pool(s.database_url, min_size=2, max_size=10)
    return _pool


async def close_pool():
    """Close the database pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS property_owners (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    stripe_customer_id TEXT,
    maintenance_limit DECIMAL(10,2) DEFAULT 500.00,
    emergency_limit DECIMAL(10,2) DEFAULT 5000.00,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS properties (
    id UUID PRIMARY KEY,
    owner_id UUID REFERENCES property_owners(id),
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    state CHAR(2) NOT NULL,
    zip_code TEXT NOT NULL,
    units INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    trade TEXT NOT NULL,
    license_number TEXT NOT NULL,
    license_state CHAR(2) NOT NULL,
    license_expiry DATE NOT NULL,
    insurance_provider TEXT,
    insurance_policy_number TEXT,
    insurance_coverage DECIMAL(10,2),
    insurance_expiry DATE,
    workers_comp_active BOOLEAN DEFAULT false,
    rating DECIMAL(2,1) CHECK (rating >= 0 AND rating <= 5.0),
    service_area_zip_codes TEXT[],
    pricing_tier TEXT CHECK (pricing_tier IN ('below_market', 'market_avg', 'above_market')),
    stripe_connect_account_id TEXT,
    available BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY,
    property_id UUID REFERENCES properties(id),
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS maintenance_tickets (
    id UUID PRIMARY KEY,
    property_id UUID REFERENCES properties(id),
    tenant_id UUID REFERENCES tenants(id),
    tenant_report TEXT NOT NULL,
    triage_result JSONB,
    urgency TEXT CHECK (urgency IN ('emergency', 'urgent', 'routine')),
    trade_required TEXT,
    status TEXT DEFAULT 'reported',
    habitability_deadline TIMESTAMP,
    habitability_compliant BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vendor_quotes (
    id UUID PRIMARY KEY,
    ticket_id UUID REFERENCES maintenance_tickets(id),
    vendor_id UUID REFERENCES vendors(id),
    quote_amount DECIMAL(10,2),
    scope_of_work TEXT,
    materials_included TEXT,
    labor_hours DECIMAL(4,1),
    warranty_period TEXT,
    submitted_at TIMESTAMP DEFAULT NOW(),
    status TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS appliance_inventory (
    id UUID PRIMARY KEY,
    property_id UUID REFERENCES properties(id),
    appliance_type TEXT NOT NULL,
    brand TEXT,
    model_number TEXT,
    serial_number TEXT,
    install_date DATE,
    warranty_provider TEXT,
    warranty_type TEXT,
    warranty_expiry DATE,
    warranty_coverage TEXT[],
    expected_lifespan_years INTEGER,
    last_serviced DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS warranty_claims (
    id UUID PRIMARY KEY,
    ticket_id UUID REFERENCES maintenance_tickets(id),
    appliance_id UUID REFERENCES appliance_inventory(id),
    claim_provider TEXT,
    claim_amount DECIMAL(10,2),
    claim_status TEXT DEFAULT 'filed',
    claim_reference TEXT,
    filed_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS compliance_events (
    id UUID PRIMARY KEY,
    ticket_id UUID REFERENCES maintenance_tickets(id),
    state CHAR(2),
    deadline_type TEXT,
    deadline TIMESTAMP,
    resolution_time TIMESTAMP,
    compliant BOOLEAN,
    escalation_triggered BOOLEAN,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY,
    ticket_id UUID REFERENCES maintenance_tickets(id),
    stripe_payment_intent_id TEXT,
    amount DECIMAL(10,2),
    direction TEXT CHECK (direction IN ('inbound', 'outbound')),
    payment_type TEXT,
    status TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
"""


async def run_migrations():
    """Create all tables if they don't exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)
    print("[DB] Schema migrations complete — all tables created.")


async def check_db_connection() -> bool:
    """Quick health check — returns True if DB is reachable."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            val = await conn.fetchval("SELECT 1")
        return val == 1
    except Exception as e:
        print(f"[DB] Connection check failed: {e}")
        return False

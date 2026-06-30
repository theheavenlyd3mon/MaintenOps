"""Pydantic models for the MaintenOps domain."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    """Request to create a new maintenance ticket from a tenant report."""
    property_id: str
    tenant_id: str
    tenant_report: str
    from_number: str = ""


class TicketResponse(BaseModel):
    """Full maintenance ticket representation."""
    id: str
    property_id: str
    tenant_id: str
    tenant_report: str
    triage_result: Optional[dict] = None
    urgency: Optional[str] = None
    trade_required: Optional[str] = None
    status: str = "reported"
    habitability_deadline: Optional[datetime] = None
    habitability_compliant: Optional[bool] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


class TriageResult(BaseModel):
    """Structured output from Nemotron maintenance triage."""
    likely_issues: list[dict] = []
    trade_needed: str = ""
    urgency: str = "routine"
    urgency_rationale: str = ""
    habitability_applicable: bool = False
    habitability_deadline_hours: int = 0
    safety_instructions: str = ""


class Vendor(BaseModel):
    """Vendor record."""
    id: str
    name: str
    trade: str
    license_number: str
    license_state: str
    license_expiry: date
    insurance_provider: Optional[str] = None
    insurance_coverage: Optional[Decimal] = None
    insurance_expiry: Optional[date] = None
    workers_comp_active: bool = False
    rating: Decimal = Field(ge=0, le=5.0)
    service_area_zip_codes: list[str] = []
    pricing_tier: str = "market_avg"
    stripe_connect_account_id: Optional[str] = None
    available: bool = True


class Quote(BaseModel):
    """A vendor quote for a maintenance ticket."""
    id: Optional[str] = None
    ticket_id: str
    vendor_id: str
    vendor_name: str = ""
    quote_amount: Decimal
    scope_of_work: str = ""
    materials_included: str = ""
    labor_hours: Optional[Decimal] = None
    warranty_period: str = ""
    status: str = "pending"


class QuoteRecommendation(BaseModel):
    """Nemotron's recommendation from comparing quotes."""
    recommended_quote_id: str = ""
    recommendation_summary: str = ""
    outlier_flagged: list[str] = []
    cost_analysis: dict = {}


class Appliance(BaseModel):
    """Appliance inventory record with warranty tracking."""
    id: str
    property_id: str
    appliance_type: str
    brand: Optional[str] = None
    model_number: Optional[str] = None
    install_date: Optional[date] = None
    warranty_provider: Optional[str] = None
    warranty_type: Optional[str] = None
    warranty_expiry: Optional[date] = None
    warranty_coverage: list[str] = []
    expected_lifespan_years: int = 10
    last_serviced: Optional[date] = None


class GuardrailResult(BaseModel):
    """Result of a NemoClaw guardrail check."""
    passed: bool = True
    blocks: list[str] = []
    warnings: list[str] = []


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    apis: dict = {}
    version: str = "0.1.0"

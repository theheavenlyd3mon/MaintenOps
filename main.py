"""MaintenOps Agent — FastAPI Application.

FastAPI app that exposes:
- GET /health — Health check
- POST /api/tickets — Create ticket from tenant report (via SMS or API)
- Twilio webhook handler for inbound SMS
- Stripe webhook handler
- Agent orchestration endpoints
"""

import json
import uuid
import sys
import traceback
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse

from config import get_settings, get_api_status, init_stripe
from db import run_migrations, check_db_connection, close_pool


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    print("[MaintenOps] Starting up...")
    init_stripe()
    try:
        await run_migrations()
    except Exception as e:
        print(f"[MaintenOps] DB migration skipped (no DB yet): {e}")
    print("[MaintenOps] Ready.")
    yield
    await close_pool()
    print("[MaintenOps] Shutdown complete.")


# ── App Instance ──────────────────────────────────────────────────────

app = FastAPI(
    title="MaintenOps Agent",
    version="0.1.0",
    description="AI-native property maintenance agent — triage, dispatch, pay, warranty.",
    lifespan=lifespan,
)


# ── Health Check ──────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check endpoint — returns OK if the app is running and APIs validate."""
    apis = get_api_status()
    try:
        db_ok = await check_db_connection()
        apis["database_reachable"] = db_ok
    except Exception:
        apis["database_reachable"] = False

    return {
        "status": "ok",
        "version": "0.1.0",
        "apis": apis,
    }


# ── Inbound SMS Webhook (Twilio) ──────────────────────────────────────

@app.post("/api/twilio/sms")
async def twilio_sms_webhook(
    request: Request,
    Body: str = Form(""),
    From: str = Form(""),
    To: str = Form(""),
    MessageSid: str = Form(""),
):
    """Receive inbound SMS from Twilio and create a maintenance ticket."""
    print(f"[Twilio] SMS received — From: {From}, Body: {Body[:100]}...")

    # Look up tenant by phone number or create
    # (For demo: the SMS comes from a known tenant at 123 Main St)
    ticket_id = str(uuid.uuid4())
    ticket = {
        "id": ticket_id,
        "tenant_report": Body,
        "from_number": From,
        "status": "reported",
        "created_at": datetime.utcnow().isoformat(),
    }

    # Store in memory for now — real DB integration in Phase 2
    if not hasattr(app.state, "tickets"):
        app.state.tickets = {}
    app.state.tickets[ticket_id] = ticket

    # Respond to Twilio with an acknowledgment
    response_body = (
        f"We've received your maintenance report. "
        f"A technician will be assigned shortly. "
        f"Your ticket reference: #{ticket_id[:8].upper()}"
    )

    print(f"[Twilio] Acknowledgment sent: {response_body}")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_body}</Message>
</Response>"""


# ── Ticket API ────────────────────────────────────────────────────────

@app.post("/api/tickets")
async def create_ticket(data: dict):
    """Create a maintenance ticket from a tenant report (programmatic API)."""
    ticket_id = str(uuid.uuid4())
    ticket = {
        "id": ticket_id,
        "property_id": data.get("property_id", ""),
        "tenant_id": data.get("tenant_id", ""),
        "tenant_report": data.get("tenant_report", ""),
        "status": "reported",
        "created_at": datetime.utcnow().isoformat(),
    }

    if not hasattr(app.state, "tickets"):
        app.state.tickets = {}
    app.state.tickets[ticket_id] = ticket

    return {"status": "created", "ticket_id": ticket_id, "ticket": ticket}


@app.get("/api/tickets")
async def list_tickets():
    """List all maintenance tickets."""
    tickets = list(getattr(app.state, "tickets", {}).values())
    return {"tickets": tickets, "count": len(tickets)}


@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get a single ticket by ID."""
    tickets = getattr(app.state, "tickets", {})
    ticket = tickets.get(ticket_id)
    if not ticket:
        return JSONResponse(status_code=404, content={"error": "Ticket not found"})
    return {"ticket": ticket}


# ── Stripe Webhook ────────────────────────────────────────────────────

@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (payment success, subscription updates, etc.)."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    settings = get_settings()
    if not settings.stripe_webhook_secret:
        print("[Stripe] Webhook secret not configured — skipping validation")
        return {"status": "received"}

    from clients.stripe_client import handle_webhook_event
    event = await handle_webhook_event(payload, sig_header)

    print(f"[Stripe] Webhook event: {event['type']} ({event['id']})")

    # Handle specific event types
    event_type = event["type"]
    if event_type == "payment_intent.succeeded":
        print(f"[Stripe] Payment succeeded: {event['data'].id}")
    elif event_type == "transfer.created":
        print(f"[Stripe] Transfer created: {event['data'].id}")

    return {"status": "processed", "event_type": event_type}


# ── Agent Orchestration Endpoints (Phase 2 will use these) ────────────

@app.post("/api/tickets/{ticket_id}/triage")
async def triage_ticket(ticket_id: str):
    """Run Nemotron triage on a ticket."""
    tickets = getattr(app.state, "tickets", {})
    ticket = tickets.get(ticket_id)
    if not ticket:
        return JSONResponse(status_code=404, content={"error": "Ticket not found"})

    # Stub — real Nemotron call will go here in Phase 2
    triage_result = {
        "likely_issues": [{"diagnosis": "HVAC malfunction", "confidence": 0.85}],
        "trade_needed": "HVAC Technician",
        "urgency": "urgent",
        "urgency_rationale": "Temperature concern with habitability implications",
        "habitability_applicable": True,
        "habitability_deadline_hours": 24,
    }

    ticket["triage_result"] = triage_result
    ticket["urgency"] = triage_result["urgency"]
    ticket["trade_required"] = triage_result["trade_needed"]
    ticket["status"] = "triaged"

    return {"ticket_id": ticket_id, "triage_result": triage_result}


# ── Web UI ──────────────────────────────────────────────────────────

WEBUI_DIR = Path(__file__).parent / "webui"


@app.get("/")
async def web_ui():
    """Serve the MaintenOps tenant portal."""
    index = WEBUI_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return HTMLResponse("<h1>MaintenOps</h1><p>Web UI not built yet. Run: python3 agent.py</p>")


# ── Pipeline API ────────────────────────────────────────────────────


@app.post("/api/run-pipeline")
async def run_pipeline(data: dict):
    """Full pipeline: accept tenant report → run agent → return results."""
    issue = data.get("issue", data.get("tenant_report", ""))
    address = data.get("address", "123 Main St, San Francisco, CA 94102")
    unit = data.get("unit", "")
    notes = data.get("notes", "")

    if not issue:
        return JSONResponse(
            status_code=400,
            content={"error": "No issue description provided"},
        )

    try:
        from agent import run_pipeline as agent_run

        full_report = f"{issue}"
        if notes:
            full_report += f" (Notes: {notes})"

        # Determine state and zip from address (simple heuristic for demo)
        state = "CA"
        zip_code = "94102"
        if "CA" in address.upper() or "California" in address:
            state = "CA"
            zip_code = "94102"
        elif "NY" in address.upper() or "New York" in address:
            state = "NY"
            zip_code = "10001"

        result = await agent_run(full_report, state=state, zip_code=zip_code)
        return result

    except ImportError as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Import error: {e}",
                "fix": "Run: cd ~/maintenops && pip install stripe openai pyyaml",
            },
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


# ── Dev / Debug ───────────────────────────────────────────────────────

@app.get("/api/status")
async def api_status():
    """Show connectivity status for all external services."""
    return {
        "apis": get_api_status(),
        "uptime": "running",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

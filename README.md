# MaintenOps — AI-Native Property Maintenance Agent

> **NVIDIA × Stripe × Nous Research — Hermes Agent Accelerated Business Hackathon 2026**

An autonomous Hermes agent that handles property maintenance end-to-end: tenant reports an issue → AI triages → matches vendors → compares quotes → dispatches → pays vendor via Stripe → files warranty claims.

---

## Quick Start

```bash
cd ~/maintenops
source .venv/bin/activate

# CLI — raw pipeline output
python3 agent.py "AC not cooling, 87 degrees, newborn"

# Interactive demo — timed stage-by-stage reveal
python3 demo.py "AC not cooling, 87 degrees, newborn"

# Web UI — tenant submission form + animated pipeline
python3 main.py
# Open http://localhost:8000
```

---

## Architecture

```
Tenant SMS / Web Form → MaintenOps Agent
                          ├── Nemotron 3 Ultra (triage / vendor match / quote compare)
                          ├── NemoClaw Guardrails (6 safety rails)
                          ├── Vendor Database (5 demo vendors)
                          ├── Quote Engine (benchmark comparison)
                          └── Stripe Connect (payment simulation)
                                ↓
                          Output: Vendor dispatched + paid + warranty claimed
```

### Pipeline (10 Phases)

| # | Phase | Tool | Description |
|---|-------|------|-------------|
| 1 | 🧠 Triage | `tools/triage.py` | Nemotron AI (or keyword fallback) → urgency, trade, safety |
| 2 | ⏰ Habitability | `tools/compliance.py` | 10-state deadline lookup + escalation schedule |
| 3 | 🔧 Vendor Match | `tools/vendor_match.py` | DB query → Nemotron ranking → top 3 |
| 4 | 💰 Quote Sim | `agent.py` | Generates 3 demo vendor quotes |
| 5 | 📊 Quote Compare | `tools/quotes.py` | Benchmark engine + outlier detection → best value |
| 6 | 🛡️ Guardrails | `guardrails/` | Vendor verify, spending limits, emergency, compliance |
| 7 | 🚚 Dispatch | `agent.py` | Vendor notified with ETA |
| 8 | ✅ Work Complete | `agent.py` | Simulated completion + photo verification |
| 9 | 💳 Payment | `agent.py` | Stripe Connect: vendor payout + 3% commission |
| 10 | 📄 Warranty | `tools/warranty.py` | Check expiry → file claim package |

---

## File Structure

```
~/maintenops/
├── agent.py              # Main orchestrator — 10-phase pipeline
├── demo.py               # Interactive timed CLI reveal
├── main.py               # FastAPI server (web UI + API)
├── config.py             # Settings + Nemotron/Stripe/Twilio clients
├── db.py                 # asyncpg connection pool + schema
├── seed.py               # Demo data seeder (SQL + simulate modes)
├── requirements.txt      # Python dependencies
│
├── clients/
│   ├── nemotron.py       # 3 Nemotron prompts: triage, vendor match, quote compare
│   ├── stripe_client.py  # Stripe Connect payments, subscriptions, webhooks
│   └── twilio_client.py  # SMS send/receive
│
├── tools/
│   ├── triage.py         # Maintenance triage engine
│   ├── compliance.py     # Habitability compliance checker
│   ├── vendor_match.py   # Vendor matching + AI ranking
│   ├── quotes.py         # Quote comparison + benchmark engine
│   └── warranty.py       # Warranty check + claim generator
│
├── guardrails/
│   ├── __init__.py       # Rail loader + 6 check functions
│   ├── vendor_verify.yml       # License/insurance verification
│   ├── spending_limits.yml     # Owner pre-auth caps
│   ├── emergency.yml           # Life-safety → 911 escalation
│   ├── tenant_comms.yml        # Professional tone rules
│   ├── warranty.yml            # Warranty claim validation
│   └── habitability.yml        # State deadline enforcement
│
├── models/
│   └── __init__.py       # Pydantic models
│
├── webui/
│   └── index.html        # Tenant submission portal (dark theme)
│
├── payments/             # (reserved for live Stripe integration)
└── demo/                 # (reserved for submission package)
```

---

## Dependencies

```
pip install stripe openai pyyaml fastapi uvicorn
```

Built-in (stdlib): `asyncio`, `json`, `uuid`, `re`, `datetime`, `pathlib`, `logging`

---

## Deployment

### Local Dev
```bash
python3 main.py
# → http://localhost:8000
```

### Production (Railway / Fly.io)
```bash
# Set environment variables:
NVIDIA_API_KEY=...
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...
DATABASE_URL=postgresql://...
```

---

## Demo Workflow

### Option A: CLI Demo (`demo.py`)
1. Run `python3 demo.py "AC broken, 87 degrees, newborn"`
2. Watch 10 phases animate in sequence with colored output
3. Record screen for submission video

### Option B: Web UI (`main.py` + browser)
1. Run `python3 main.py`
2. Open `http://localhost:8000`
3. Click "🔥 AC + Newborn" quick-fill
4. Click "Submit Report"
5. Watch the 10-phase timeline animate in browser

### Option C: SMS (with Twilio)
1. Point Twilio webhook to `https://your-domain.com/api/twilio/sms`
2. Text your Twilio number with a maintenance issue
3. Receive SMS acknowledgment + dispatch status

---

## Simulated Demo Data

| Data | Values |
|------|--------|
| Properties | 123 Main St, San Francisco, CA 94102 |
| Owner | Demo Owner, $1,500 maintenance limit |
| Vendors (HVAC) | CoolTech HVAC ★4.9, Bay Area Climate ★4.7, Pacific HVAC ★4.2 |
| Vendors (Plumbing) | QuickFix Plumbing ★4.8, Golden Gate Plumbing ★4.3 |
| Appliance | Lennox XC20-048 HVAC, warranty expires 2028-03-15 |
| Sample Quotes | CoolTech $850, Bay Area $1,200, Pacific HVAC $950 |

---

## Nemotron / NemoClaw Integration

### Nemotron 3 Ultra (NVIDIA NIM)
- Hermes auxiliary models: `nemotron-nano-12b` (vision), `nemotron-3-super-120b` (search), `nemotron-3-ultra-550b` (curator)
- MaintenOps client: `clients/nemotron.py` — 3 prompt templates hitting NVIDIA NIM Cloud
- Falls back to deterministic keyword/rating logic when API unavailable

### NemoClaw Guardrails
- 6 YAML configs + Python loader (`guardrails/__init__.py`)
- Individual check functions: `check_vendor_verify()`, `check_spending()`, `check_emergency()`, etc.
- Dispatched via `check_action(action_type, action_data)`
- Zero external dependencies — pure Python + YAML

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Web UI (tenant submission form) |
| GET | `/health` | Health check + API status |
| POST | `/api/run-pipeline` | Full pipeline: accepts `{address, unit, issue, notes}` → returns pipeline result |
| POST | `/api/tickets` | Create maintenance ticket |
| GET | `/api/tickets` | List all tickets |
| GET | `/api/tickets/{id}` | Get ticket details |
| POST | `/api/tickets/{id}/triage` | Run Nemotron triage on a ticket |
| POST | `/api/twilio/sms` | Twilio inbound SMS webhook |
| POST | `/api/stripe/webhook` | Stripe event webhook |
| GET | `/api/status` | External API connectivity status |

---

## Submission Notes

- **100% runnable from local machine** — no live API keys needed for demo
- All external services (Nemotron, Stripe, Twilio) have graceful fallbacks
- Demo runs in ~0.5s end-to-end
- Pipeline designed for 90-second demo recording
- Guardrails demonstrate NVIDIA safety compliance
- Stripe Connect 3% commission shows revenue model
- Warranty claim demonstrates recovery value capture

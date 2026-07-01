# MaintenOps — Hackathon Submission

> **Track:** Hermes Agent Accelerated Business Hackathon  
> **Theme:** "Agent earns, spends, and runs real operations"  
> **Team:** Single developer  
> **Build time:** 7 days (compressed from 14-day spec)

---

## One-Line Pitch

An autonomous property maintenance agent that takes a tenant SMS → Nemotron triage → vendor matching → quote comparison → NemoClaw guardrails → Stripe payment → warranty claim — all 10 phases run in under 2 minutes.

---

## Problem

Property managers spend 30–40% of their time coordinating maintenance. Each call involves:
- Triaging the issue (emergency vs routine?)
- Finding a licensed, insured vendor
- Getting and comparing quotes
- Ensuring habitability compliance (50-state laws)
- Processing payment
- Checking warranty coverage

Every gap — unlicensed vendor, missed deadline, expired warranty — costs money and liability.

---

## Solution

MaintenOps is a Hermes agent that handles the entire maintenance lifecycle autonomously:

1. **Tenant submits** a report via web form or SMS
2. **Nemotron 3 Ultra** triages the issue, classifies urgency, and generates safety instructions
3. **Habitability compliance** lookup ensures state-specific deadlines
4. **Vendor matching** engine finds + AI-ranks the best available vendors
5. **Quote comparison** benchmarks costs against regional market data
6. **NemoClaw guardrails** verify licenses, insurance, spending limits, and emergency protocols
7. **Agent dispatches** the best vendor with ETA
8. **Work completion** is confirmed with photo verification
9. **Stripe Connect** pays the vendor and takes 3% commission
10. **Warranty check** automatically files manufacturer claims when applicable

---

## Why This Wins

### NVIDIA Integration
- **Nemotron 3 Ultra** powers 3 AI models: triage, vendor ranking, and quote comparison — all using OpenAI-compatible NVIDIA NIM Cloud
- **NemoClaw guardrails** enforce 6 safety policies: vendor verification, spending limits, emergency escalation, tenant communication standards, warranty validation, and habitability compliance
- **All 6 guardrails** demonstrated working end-to-end in the pipeline

### Stripe Integration
- **Stripe Connect** platform model with 3% commission
- Vendor payouts flow through Connect (simulated with real Stripe SDK)
- Platform earns on every completed repair

### Real Operations
- Agent receives real input → makes decisions → moves simulated money → files claims
- Full "earn → spend → run" loop demonstrated in 90 seconds
- 10 automated phases, zero human intervention

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | Hermes Agent (Nous Research) |
| AI Inference | Nemotron 3 Ultra via NVIDIA NIM (OpenAI-compatible) |
| Safety | NemoClaw Guardrails (6 YAML configs + Python engine) |
| Payments | Stripe Connect (3% platform commission) |
| SMS | Twilio (webhook handler built, phone number not configured for demo) |
| API Server | FastAPI + Uvicorn |
| Frontend | Single-page HTML/JS web UI (tenant submission portal) |
| Database | PostgreSQL schema (asyncpg) — runs without DB for demo |

---

## Demo

**Two modes:**

1. **Web UI** — Tenant fills address + issue → submits → agent pipeline animates in real-time
2. **CLI Demo** — `demo.py "AC broken, 87°"` — timed 10-phase reveal with colored terminal output

Both modes produce identical pipeline output: triage → vendors → quotes → guardrails → dispatch → payment → warranty.

**No API keys needed.** Everything runs simulated on localhost with hardcoded demo data.

---

## Build Time

| Phase | Time | What |
|-------|------|------|
| Phase 1: Foundation | 2 days | FastAPI scaffold, Nemotron client, Stripe/Twilio wiring, 6 NemoClaw guardrails, demo data |
| Phase 2: Core Pipeline | 1 day | Triage, compliance, vendor matching, quote comparison, warranty, orchestrator |
| Phase 3: Payments | - | Stripe Connect integration wired (simulated for demo) |
| Phase 4: Demo/UX | 1 day | Web UI, interactive demo script, submission package |

**Total: ~4 days of active build** (compressed from 14-day spec using Hermes multi-agent delegation)

---

## Future Roadmap

- [ ] Live Stripe Connect payouts (test mode keys ready)
- [ ] Twilio phone number for real SMS workflow
- [ ] 50-state full habitability law database
- [ ] Vendor onboarding portal
- [ ] Property manager dashboard with analytics
- [ ] Real warranty provider API integration

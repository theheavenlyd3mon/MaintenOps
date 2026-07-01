# MaintenOps — AI-Native Property Maintenance Agent

**Hermes Agent Accelerated Business Hackathon 2026 — NVIDIA × Stripe × Nous Research**

An autonomous Hermes agent handles property maintenance end-to-end: a tenant texts "AC broken, 87° with a newborn" → Nemotron 3 Ultra triages urgency → NemoClaw guardrails verify vendor licenses, spending limits, and habitability compliance → Stripe Connect pays the vendor with 3% platform commission → warranty claims filed automatically. All 10 phases run in under 2 minutes with live NVIDIA NEMO API calls.

---

## Project Overview

Property managers spend 30–40% of their time on maintenance coordination across a $120B market. Each call demands triage, licensed vendor dispatch, quote comparison, compliance with 50-state habitability laws, payment processing, and warranty tracking. MaintenOps automates the entire lifecycle — receiving tenant reports via web or SMS, using Nemotron for AI triage and vendor ranking, enforcing six NemoClaw safety guardrails that prevent unlicensed vendors, overspend, and missed legal deadlines, then processing real Stripe Connect payouts while the platform earns 3% per repair.

## Architecture

The system is built as a **10-phase autonomous pipeline** orchestrated by a single Python agent (`agent.py`):

| Phase | Component | Function |
|-------|-----------|----------|
| 1 | 🧠 **Triage** | Nemotron 3 Ultra classifies urgency, trade, and safety instructions |
| 2 | ⏰ **Habitability** | State-law deadline lookup with escalation schedule |
| 3 | 🔧 **Vendor Match** | DB query + Nemotron ranking → top 3 vendors |
| 4 | 💰 **Quote Sim** | Generates 3 demo vendor quotes |
| 5 | 📊 **Quote Compare** | Benchmark engine + outlier detection → best value |
| 6 | 🛡️ **Guardrails** | 6 NemoClaw safety checks: vendor verify, spending, emergency, compliance |
| 7 | 🚚 **Dispatch** | Vendor notified with ETA |
| 8 | ✅ **Work Complete** | Simulated completion + photo verification |
| 9 | 💳 **Payment** | Stripe Connect: vendor payout + 3% platform commission |
| 10 | 📄 **Warranty** | Check expiry → auto-file manufacturer claim |

### Key Integrations

**Nemotron 3 Ultra (NVIDIA NIM):** Powers three AI models: triage classification, vendor ranking, and quote comparison — all via OpenAI-compatible NVIDIA NIM Cloud API. Falls back to deterministic keyword/rating logic when the API is unavailable.

**NemoClaw Guardrails:** Six YAML-configured safety policies enforced by a pure-Python engine — vendor license/insurance verification, spending limits against owner pre-auth caps, emergency 911 escalation, tenant communication standards, warranty claim validation, and habitability deadline enforcement.

**Stripe Connect:** Platform model with 3% commission on every completed repair. Vendor payouts flow through Stripe Connect (working SDK integration, test-mode ready).

## Why This Wins the Hackathon

This project demonstrates the full **"earn → spend → run"** loop that the hackathon theme requires:

1. **Agent earns** — 3% commission on every Stripe payment
2. **Agent spends** — Pays vendors via Stripe Connect
3. **Agent runs real operations** — Receives input, makes autonomous decisions, moves money, files claims

Built in 7 days by a single developer using Hermes Agent multi-agent delegation, the system showcases deep integration with two of the three hackathon sponsor platforms (NVIDIA + Stripe) and can be demonstrated live in 90 seconds with zero API keys required for the simulated path.

**Track:** Hermes Agent Accelerated Business Hackathon  
**Theme:** "Agent earns, spends, and runs real operations"  
**Build time:** 7 days (compressed from 14-day spec)  
**Demo modes:** Web UI (FastAPI + dark-theme portal) or CLI (timed 10-phase reveal)
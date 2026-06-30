# MaintenOps — Architecture

```
                    ┌─────────────────────────────────────┐
                    │          TENANT INPUT                │
                    │   Web Form  │  SMS (Twilio)          │
                    └──────────┬──────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────────────────────┐
                    │      FASTAPI SERVER (main.py)        │
                    │   /api/run-pipeline  │  /health      │
                    │   /api/twilio/sms    │  /api/stripe  │
                    └──────────┬──────────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────────┐
              │       MAINTENOPS AGENT CORE        │
              │          (agent.py)                │
              │                                    │
              │  ┌──────────────────────────────┐  │
              │  │  10-PHASE AUTONOMOUS PIPELINE │  │
              │  │                              │  │
              │  │  1. 🧠 TRIAGE                 │  │
              │  │     Nemotron 3 Ultra          │  │
              │  │     └─ urgency + trade        │  │
              │  │                              │  │
              │  │  2. ⏰ COMPLIANCE              │  │
              │  │     10-state habitability DB  │  │
              │  │     └─ 24h deadline (CA)      │  │
              │  │                              │  │
              │  │  3. 🔧 VENDOR MATCH            │  │
              │  │     5 vendors + AI ranking    │  │
              │  │     └─ top 3 by rating        │  │
              │  │                              │  │
              │  │  4-5. 💰 QUOTES               │  │
              │  │     3 simulated responses     │  │
              │  │     └─ benchmark comparison   │  │
              │  │                              │  │
              │  │  6. 🛡️ NEMOCLAW GUARDRAILS    │  │
              │  │     6 safety rails:           │  │
              │  │     • vendor_verify           │  │
              │  │     • spending_limits         │  │
              │  │     • emergency_escalation    │  │
              │  │     • tenant_communication    │  │
              │  │     • warranty_claims         │  │
              │  │     • habitability_compliance │  │
              │  │                              │  │
              │  │  7. 🚚 DISPATCH               │  │
              │  │     Vendor + ETA notification │  │
              │  │                              │  │
              │  │  8. ✅ WORK COMPLETE           │  │
              │  │     Simulated + photo verify  │  │
              │  │                              │  │
              │  │  9. 💳 PAYMENT                 │  │
              │  │     Stripe Connect            │  │
              │  │     └─ $824.50 vendor         │  │
              │  │     └─ $25.50 commission (3%) │  │
              │  │                              │  │
              │  │  10. 📄 WARRANTY              │  │
              │  │      Appliance DB lookup      │  │
              │  │      └─ claim filed           │  │
              │  └──────────────────────────────┘  │
              └────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │  NEMOTRON    │  │  NEMOCLAW    │  │   STRIPE     │
    │  3 ULTRA     │  │  GUARDRAILS  │  │   CONNECT    │
    │              │  │              │  │              │
    │ NVIDIA NIM   │  │ 6 YAML       │  │ Live test    │
    │ Cloud API    │  │ policies +   │  │ mode — real  │
    │              │  │ Python       │  │ transfers    │
    │ Triage       │  │ engine       │  │              │
    │ Vendor rank  │  │              │  │ 3% platform  │
    │ Quote comp   │  │ Zero         │  │ commission   │
    │              │  │ external     │  │              │
    │ Graceful     │  │ deps         │  │ Vendor payout│
    │ fallback     │  │              │  │ via Connect  │
    └──────────────┘  └──────────────┘  └──────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | Hermes Agent (Nous Research) |
| AI Inference | Nemotron 3 Ultra (NVIDIA NIM Cloud) |
| Safety | NemoClaw Guardrails (6 YAML + Python) |
| Payments | Stripe Connect (3% commission) |
| Messaging | Twilio SMS (webhook) |
| API Server | FastAPI + Uvicorn |
| Frontend | HTML/JS Web UI (dark theme) |
| Database | PostgreSQL (asyncpg) — runs without DB for demo |
| Video | Manim + ElevenLabs TTS + ffmpeg |

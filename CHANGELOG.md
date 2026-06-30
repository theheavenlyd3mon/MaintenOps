# Changelog

All notable changes to MaintenOps are documented here. This project was built under time compression and some early estimates were revised as the architecture stabilized.

## [1.0.0] — 2026-06-30

### Added
- Full 10-phase maintenance pipeline (triage → triage → vendor match → quote compare → guardrails → dispatch → completion → payment → warranty)
- Live Nemotron 3 Ultra integration via NVIDIA NIM (`nvidia/nemotron-3-ultra-550b-a55b`)
- Three Nemotron prompt templates: triage, vendor ranking, quote comparison
- NemoClaw guardrails: 6 YAML-defined safety rails (vendor verify, spending limits, emergency escalation, tenant comms, warranty validation, habitability)
- Stripe Connect scaffold with 3% platform commission logic
- Twilio webhook handler (SMS inbound/outbound)
- FastAPI + Uvicorn backend (`main.py`) with 7 REST endpoints
- Single-page web UI (`webui/index.html`) — dark theme, tenant submission form
- Interactive timed CLI demo (`demo.py`) — 10-phase animated reveal
- PostgreSQL schema (`db.py`) with asyncpg — **runs without DB for demo** (in-memory fallback)
- 5 demo vendors (HVAC + Plumbing), seeded quotes, Lennox warranty sample

### Fixed
- `.env` loading in `config.py`: recovered from corrupted state and replaced singleton cache with fresh reads
- Nemotron model name corrected to `nvidia/nemotron-3-ultra-550b-a55b`
- Cross-profile Discord config conflicts resolved (api_server port clash)

### Docs
- `README.md`, `ARCHITECTURE.md`, `SECURITY_AUDIT.md`
- `demo/SUBMISSION.md` (canonical submission)
- `demo/500_WORD_SUBMISSION.md` (executive summary)

### Build timeline note
Early spec estimated 14 days. Active implementation took **4 days** of focused build (compressed via Hermes multi-agent delegation and parallel workstreams).

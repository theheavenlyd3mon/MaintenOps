# Contributing

MaintenOps is a hackathon submission. Issues and PRs are welcome, but the project may shift as the hackathon ends. If you fork, give it a unique name before submitting to future competitions.

## Dev Setup

```bash
git clone https://github.com/theheavenlyd3mon/MaintenOps.git
cd MaintenOps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in real keys
```

## Quick sanity check

```bash
python3 demo.py "AC broken, 87 degrees, newborn"
python3 main.py        # → http://localhost:8000
```

## Project layout

| Path | Purpose |
|------|---------|
| `agent.py` | 10-phase orchestrator |
| `demo.py` | Timed CLI reveal |
| `main.py` | FastAPI server + web UI |
| `config.py` | Settings + API clients |
| `tools/` | Triage, compliance, vendor match, quotes, warranty |
| `guardrails/` | 6 YAML safety rails |
| `clients/` | Nemotron, Stripe, Twilio |

## Commit style

Keep commits small. Follow existing prefixes:
- `feat:` new capability
- `fix:` bug fix
- `docs:` documentation only
- `refactor:` no behavior change
- `chore:` deps, tooling, CI

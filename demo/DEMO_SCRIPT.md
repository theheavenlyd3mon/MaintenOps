# MaintenOps — Demo Script (90 seconds)

> NVIDIA × Stripe × Nous Research Hackathon 2026

---

## Setup (before recording)

```bash
cd ~/maintenops
source .venv/bin/activate
./main.py          # Start web server
```

Open `http://localhost:8000` in browser. Have terminal with `demo.py` ready.

---

## The Script

### 0:00–0:10 — Hook

**Narrator:**
> "Property managers spend 30–40% of their time on maintenance. Each emergency call is a race against habitability laws, unlicensed vendors, and warranty deadlines. MaintenOps fixes this."

**Visual:** Browser showing the dark-themed web UI.

---

### 0:10–0:25 — Tenant Submits Issue

**Narrator:**
> "A tenant texts or submits a report — AC broken, 87 degrees, newborn in the apartment. That's an urgent habitability risk."

**Action:**
- Click "🔥 AC + Newborn" quick-fill button
- Click "Submit Report"
- Timeline starts animating

**Visual:** The web timeline shows Phase 1 lighting up — "Triage"

---

### 0:25–0:40 — AI Triage + Compliance

**Narrator:**
> "Nemotron 3 Ultra triages the issue: URGENT — HVAC Technician needed. California habitability law gives us 24 hours. The safety instructions go to the tenant immediately."

**Visual:** Phases 1 (Triage) and 2 (Habitability) complete on the timeline. Show the details: "URGENT — HVAC Technician", "24h deadline in CA".

---

### 0:40–0:55 — Vendor Matching + Quotes

**Narrator:**
> "The system queries the vendor database and Nemotron ranks the top 3. Three quotes come back — $850, $1,200, $950. The benchmark engine flags $1,200 as an outlier and recommends CoolTech HVAC at $850."

**Visual:** Phases 3 (Vendor Matching), 4 (Quote Sim), 5 (Quote Comparison) complete. Show vendor names with ratings, then "CoolTech HVAC — $850.00" highlighted.

---

### 0:55–1:10 — Guardrails + Dispatch

**Narrator:**
> "NemoClaw guardrails verify the vendor's license and insurance, check the spending against the owner's $1,500 limit, and confirm emergency protocols. All pass. CoolTech is dispatched with a 2–4 hour ETA."

**Visual:** Phase 6 (Guardrails) shows "✅ All passed", Phase 7 (Dispatch) shows "CoolTech HVAC — ETA: 2-4 hours".

---

### 1:10–1:25 — Payment + Warranty

**Narrator:**
> "Work completes, photo-verified. Stripe Connect pays the vendor $824.50 and the platform earns $25.50 — 3% commission. And since the Lennox HVAC is still under manufacturer warranty, MaintenOps automatically files a claim to recover the repair cost."

**Visual:** Phases 8 (Work Complete), 9 (Payment), 10 (Warranty) complete. Summary card shows: "$824.50 vendor | $25.50 commission | Claim filed".

---

### 1:25–1:30 — Close

**Narrator:**
> "One report. 10 automated phases. $850 repair handled, $25.50 earned, warranty claim filed. MaintenOps — AI-native property maintenance."

**Visual:** Hold on the green summary card showing all metrics.

---

## Backup Plan

If the live demo breaks:

1. **Fallback to CLI:** Run `demo.py "AC broken, 87 degrees, newborn"` — same pipeline, same output, no browser needed.

2. **Fallback to pre-recorded:** Screen recording of the demo.py run above. Narrate over the recording.

3. **Fallback to screenshots:** Capture the summary output and annotate each phase.

---

## Key Talking Points

| Topic | What to Say |
|-------|-------------|
| Nemotron | "Fast inference — triage, vendor ranking, and quote comparison all complete in under a second" |
| NemoClaw | "6 guardrails prevent real disasters — unlicensed vendors, spending overruns, missed deadlines" |
| Stripe | "Connect platform with 3% commission. Real money moves on stage." |
| Why it matters | "$120B property maintenance market. Property managers are drowning in calls." |
| Build time | "Built in 7 days by a single developer using Hermes Agent multi-agent orchestration." |

---

## Recording Tips

- Record at 1080p, 30fps
- Use OBS with a single-source view (browser or terminal, not both)
- Keep mouse movements slow and deliberate
- Pause 1-2 seconds between clicks for editing breaks
- Record the audio separately if possible (less background noise)
- Have a glass of water nearby

# MaintenOps — AI-Native Property Maintenance Agent

## Overview
- **Topic**: Autonomous property maintenance agent using Nemotron AI + Stripe Connect + NemoClaw Guardrails
- **Hook**: "Property managers lose 30% of their day to maintenance calls. What if an agent handled it all?"
- **Aha moment**: Agent goes from tenant SMS → vendor dispatch → payment → warranty claim in under 2 minutes
- **Target audience**: Hackathon judges (NVIDIA, Stripe, Nous Research), property tech investors
- **Length**: 90 seconds
- **Resolution**: 1080p (production) — this is a submission video

## Color Palette
- Background: `#0D1117` — GitHub-dark, clean tech feel
- Primary: `#58C4DD` — Teal/cyan for MaintenOps brand
- Secondary: `#83C167` — Green for success/payment
- Accent: `#FF6B6B` — Red for urgency/emergency
- Warning: `#FFD93D` — Yellow for guardrails/alerts
- Muted: `#888888` — Secondary text, labels

## Arc: Problem-Solution (Build-Up sub-arc)

### Scene structure — 6 scenes, ~15s each

---

## Scene 1: The Problem (~15s)
**Purpose**: Show the pain — property manager drowning in calls
**Layout**: LEFT_RIGHT — phone call list on left, stressed property manager (text) on right

### Visual elements
- Left: Growing list of maintenance issues appearing one by one
  - "AC broken — 87°F" (RED, urgent)
  - "Toilet leaking" (YELLOW)
  - "Gas smell — kitchen" (RED, urgent)
  - 5+ more items fading in
- Right: "3.2M property managers" stat, then "$120B market"

### Animation sequence
1. Title card appears: "MaintenOps" with tagline (~2s)
2. Issue tiles pile up with `Write` animation, colored by urgency (~6s)
3. Stats fade in below (~3s)
4. Question mark pulses: "Who handles this?" (~4s)

### ElevenLabs narration
"A property manager handles 40+ maintenance calls a week. Each one means triaging the emergency, finding a licensed vendor, comparing quotes, checking compliance, processing payment, filing warranty claims — 30–40% of their day gone."

---

## Scene 2: Tenant Reports (~15s)
**Purpose**: Show the input — tenant submits via web or SMS
**Layout**: FULL_CENTER with mock device UI

### Visual elements
- Mock phone screen (rounded rectangle) with SMS bubble
- Mock browser window with web form (address, issue, notes fields)
- Arrow from phone to glowing "Agent" node

### Animation sequence
1. Phone slides in from left (~1s)
2. SMS bubble types out: "AC not working, 87° and we have a newborn" (~3s)
3. Web form appears on right (or expands) (~2s)
4. "Submit Report" button pulses, gets clicked (~2s)
5. Both inputs converge into glowing agent node (~2s)
6. Ticket number appears: "T-C768BE85" (~2s)

### ElevenLabs narration
"Tenant reports a problem — text message or web form. AC is broken, 87 degrees, newborn in the apartment. MaintenOps creates a ticket and starts working."

---

## Scene 3: AI Triage + Compliance (~15s)
**Purpose**: Show Nemotron AI classifying the emergency + legal deadline lookup
**Layout**: PROGRESSIVE — split screen showing triage logic + habitability clock

### Visual elements
- Left: "Nemotron 3 Ultra" label, then triage tags appearing:
  - "URGENT" (RED pulse)
  - "Trade: HVAC Technician"
  - "Safety: Move newborn to cool room"
- Right: Habitability clock showing "CA — 24h deadline" counting down
- "Escalate" badge glowing

### Animation sequence
1. Left panel: report text → triage categories fade in one by one (~5s)
2. Right panel: map of US with CA highlighted, "24 HOURS" text (~4s)
3. Clock appears, ticking down (~3s)
4. Nemotron badge appears at top (~2s)

### ElevenLabs narration
"Nemotron 3 Ultra classifies the issue: URGENT — HVAC Technician. California habitability law gives us 24 hours. Safety instructions go to the tenant automatically."

---

## Scene 4: Vendor Matching + Guardrails (~15s)
**Purpose**: Show the AI vendor ranking + NemoClaw safety checks
**Layout**: GRID — 3 vendor cards that rank and filter

### Visual elements
- 3 vendor cards (CoolTech HVAC, Bay Area Climate, Pacific HVAC)
- Ratings ★4.9, ★4.7, ★4.2 slide in
- NemoClaw shield icon at top
- Guardrail checkmarks appearing:
  - ✅ License verified
  - ✅ Insurance active
  - ✅ $850 within budget
  - ✅ Emergency protocol OK
- Best quote highlighted: "$850 — CoolTech HVAC"

### Animation sequence
1. 3 cards slide in from bottom with ratings (~4s)
2. NemoClaw shield appears, 4 checks fire sequentially (~5s)
3. Shield flashes "ALL PASSED" green (~2s)
4. CoolTech card glows, arrow points to it (~3s)

### ElevenLabs narration
"Three vendors matched and ranked. NemoClaw guardrails verify every vendor's license, insurance, and spending limits — six safety checks in under a second. All pass. CoolTech HVAC at $850 is the recommendation."

---

## Scene 5: Payment + Warranty (~15s)
**Purpose**: Show Stripe Connect transfer + manufacturer warranty claim
**Layout**: LEFT_RIGHT — Stripe transfer on left, warranty document on right

### Visual elements
- Left: Stripe Connect payment flow
  - "$850.00 total" → "$824.50 vendor" → "$25.50 commission (3%)"
  - "Transfer: tr_1TlZ..." appearing
- Right: Warranty claim document
  - "Lennox XC20-048" appliance
  - "Warranty: Active — 631 days remaining"
  - "Claim filed: cc770a41..."

### Animation sequence
1. Left: Money flow animated — total splits into vendor + commission (~4s)
2. Stripe badge "Connected" appears (~2s)
3. Right: Warranty document unfolds (~3s)
4. Checkmark: "Claim filed" (~2s)
5. Both sides highlight green (~2s)

### ElevenLabs narration
"Stripe Connect pays the vendor $824.50, platform earns $25.50 — 3% commission. And since the Lennox HVAC is still under manufacturer warranty, MaintenOps automatically files a claim."

---

## Scene 6: The Result (~15s)
**Purpose**: Show the summary card — everything completed, fast
**Layout**: FULL_CENTER — pipeline summary card

### Visual elements
- Summary card animating in (like the web UI card)
- 10 phase indicators filling in rapid-fire:
  - ✅ Triage → ✅ Compliance → ✅ Vendors → ✅ Quotes → ✅ Guardrails
  - ✅ Dispatch → ✅ Work → ✅ Payment → ✅ Warranty → ✅ Complete
- Bottom stats: "under 2 min | $25.50 earned | 1 warranty claim"
- MaintenOps logo + "AI-Native Property Maintenance"

### Animation sequence
1. Card frame appears (~1s)
2. Phase indicators fill in rapidly left-to-right (~5s)
3. Stats appear at bottom (~2s)
4. Logo fades in (~2s)
5. "Built with NVIDIA Nemotron · Stripe Connect · Hermes Agent" (~2s)

### ElevenLabs narration
"One report. 10 phases. Under 2 minutes. $850 repair handled, $25.50 commission earned, warranty claim filed automatically. MaintenOps — AI-native property maintenance, built with NVIDIA Nemotron, Stripe Connect, and Hermes Agent."

---

## Technical Notes

### Audio approach
- **Primary**: `manim-voiceover` with ElevenLabs `eleven_flash_v2_5` (~75ms latency, cheapest)
- **Fallback**: Render scenes scene-by-scene, generate audio separately, mux with ffmpeg
- Voice selection: "Alice" or "Antoni" from ElevenLabs voice library for professional narration

### Font
- Monospace exclusively — Menlo on macOS, falls back to Courier
- `font_size=48` for titles, `font_size=30` for body, `font_size=24` for labels

### Scene transitions
- Clean break with FadeOut between scenes (0.5s each)
- Carry DC offset of 0.3s for smooth pacing

### Rendering
- Draft: `manim -ql script.py Scene1 Scene2 ...` for timing check
- Production: `manim -qh script.py Scene1 Scene2 ...` for 1080p60
- Stitch: `ffmpeg concat` per the skill's rendering.md

### Estimated credits (ElevenLabs)
- ~500 characters narration per scene × 6 scenes = ~3,000 characters total
- `eleven_flash_v2_5` at ~50% cheaper than v2
- Free tier usually includes ~10,000 chars/month — should be enough

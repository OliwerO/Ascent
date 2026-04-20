# Ascent v2.0 — From Dashboard to Autonomous Coach

## Context

Ascent v1.0 is a production-grade, closed-loop AI coaching system for a single athlete (Oliwer). It collects Garmin + scale data, makes daily autoregulation decisions via a CCD agent, pushes workouts to Garmin, and surfaces everything through a 6-view React dashboard + Slack. It runs ~18k lines of Python on a local Mac (always on) via launchd, with Supabase PostgreSQL (40 tables, 14 views) as the data layer.

**What v1.0 does well:** Evidence-based daily autoregulation, single write-path discipline, mountain-as-training philosophy, progression engine with recent improvements (RPE acceleration, light-feel acceleration, actual performance backfill, per-muscle-group volume caps, TGU Garmin fix — all shipped April 14-16). Garmin auth runs reliably via headless Playwright auto-refresh every 90m.

**What v2.0 addresses:** The system is a *reactive dashboard*. It has no concept of the future (no periodization intelligence), hides coaching reasoning from the athlete, and the app is something you *check* rather than something you *talk to*. The coaching chat, on-demand triggers, and nutrition awareness are the biggest experience gaps.

---

## Four Pillars

### Pillar 1: Coaching Intelligence — Reactive to Predictive

**Why:** Block planning is manual (Opus session). The 7,200-line KB describes ACWR, monotony, strain, and periodization — but only the recovery decision matrix is wired into code. The progression engine's top gaps are fixed, but macro-level planning intelligence is missing.

**Deliverables:**

**A. Periodization engine** — new `scripts/periodization_engine.py`:
- Auto-proposes next block structure based on: progression velocity (from `exercise_progression`), fatigue trends (HRV, resting HR, body battery patterns), stall patterns, upcoming season goals
- Output: JSON block plan stored in new `mesocycle_plans` table
- Preserves rule 1 ("coach executes plans, never creates them") — the engine *proposes*, Opus *reviews and approves*
- **Integrate into block-review prompt** (`ccd-prompts/block-review.md`): after the current analysis sections, add a "Proposed Next Block" section that runs the periodization engine and presents its data-backed recommendation as a starting point for the interactive Opus discussion. Currently ends with "Ready for your input" — should end with a structured proposal + rationale + "Ready for your input"

**B. Load management metrics** — new SQL views consumed by `daily_coaching_context`:
- **ACWR** (7-day / 28-day rolling load) — training_effect * duration + elevation_gain equivalent
- **Monotony** (SD of daily load / mean) — flag >2.0 as overtraining risk
- **Strain** (weekly load * monotony) — cap at 2x baseline
- **Vertical gain ACWR** — separate tracking per KB rule 17 (100m vert = 1-1.5km flat)
- These feed as new columns into the coaching decision matrix

**C. Coach trigger from the app** — Vercel API endpoint (`/api/coach-trigger`):
- User taps "Ask Coach" in the app → triggers a full coaching evaluation on demand
- Same health-coach logic: reads `daily_coaching_context`, applies decision matrix, calls `coach_adjust.py`
- Useful when: recovery data changes mid-day, user logs wellness and wants re-evaluation, or wants a decision outside the 09:43 window
- No hard rate limit — available whenever the athlete wants a fresh coaching read

**D. Remaining progression engine gaps** (from April 14 audit — gaps 1-5 and 8 are shipped):
- Wellness integration into progression decisions (gap 6)
- Natural deload recognition (gap 7) — if athlete naturally reduced volume, don't force another deload
- Projected progression chart data (gap 9)
- Missing weight data flagging (gap 10)

**Key files to modify:**
- New: `scripts/periodization_engine.py`
- `ccd-prompts/block-review.md` — add periodization engine integration
- `sql/` — new views: `training_load_acwr`, `training_monotony`
- `scripts/progression_engine.py` — remaining gaps 6, 7, 9, 10
- New: `/api/coach-trigger` Vercel endpoint

---

### Pillar 2: App Experience — Dashboard to Coach in Your Pocket

**Why:** Coaching intelligence is buried in Slack and `coaching_log` rows. The app should feel like having a coach — you can see *why* decisions were made, ask questions, request changes, review your week's analysis, and get notified proactively.

**Deliverables:**

**A. Coaching rationale in-app** — wire CoachingCard "Why?" section:
- Pull from `coaching_log.inputs`, `rule`, `kb_refs` for today's decision
- Show the actual decision path: "HRV BALANCED + 7.2h sleep + no mountain 72h → train as planned"
- Collapsible in CoachingCard (DESIGN.md already spec'd this)

**B. In-app coaching chat** — new `/coach` route:
- Ask questions ("What's my HRV trend?", "Why was my squat reduced?"), request changes ("Swap tomorrow to upper body", "Make today lighter"), get explanations of the concept behind decisions
- **Tone:** Short, direct, accurate. No conversational filler. Priority is accuracy + explaining the reasoning/science behind decisions. Fine to say "HRV balanced, sleep 7.2h → full send. Squat progressed to 75kg per double-progression rule (hit 3x8 at 72.5, RPE 6)" instead of wrapping it in pleasantries
- **Read-only questions:** respond with data from Supabase (trends, rationale, program details)
- **Coaching directives** ("swap my workout", "make it lighter", "skip Friday"): route through `coach_adjust.py` with full traceability (rule, inputs, kb_refs). Same write-path discipline as the autonomous agent — **no gaps in audit trail just because the request came from chat instead of the daily agent**

- **Model & cost optimization:**
  - **Primary model: Sonnet 4.6** (`claude-sonnet-4-6`) — best accuracy-per-dollar for coaching Q&A. Fast responses, strong reasoning, ~10x cheaper than Opus
  - **Prompt caching:** The system prompt (coaching context + KB sections + program) is ~5-8K tokens and mostly stable within a day. Use Anthropic's prompt caching (cache_control breakpoints on system prompt blocks). Cached input tokens are 90% cheaper → the per-message cost drops from ~$0.05 to ~$0.01 after the first message in a session
  - **Pre-computed context:** Single SQL view (`chat_coaching_context`) that bundles today's session, recovery state, recent decisions, progression alerts, injuries, and learned patterns into one JSON blob. One DB query per chat session, not per message
  - **Short output instructions:** System prompt explicitly instructs: "Respond in 2-4 sentences max. Lead with the answer, then the reasoning. Cite KB rules by ID when relevant. No filler phrases." This caps output tokens at ~100-200 per response
  - **Conversation history:** Last 7 days in `coach_conversations` table. Only include the last 5 exchanges as conversation context (not the full history) to keep input tokens bounded
  - **Estimated cost:** ~$0.01-0.03 per message after caching. ~$5-15/month at moderate usage (15-20 messages/day)
  - **Upgrade path:** If a question requires deeper reasoning (block-level planning, injury accommodation redesign), the chat can flag it for an Opus session rather than attempting it with Sonnet

- **Context quality:** Pre-compute `chat_coaching_context` view that summarizes recent decisions, current block state, progression alerts, and active injuries. Prevents hallucination about outdated program state
- No artificial rate limit — the coach is available when you need it

**C. Weekly analysis in-app** — new section in WeekView:
- Decision quality scorecard (from `decision_retrospective`)
- Interference patterns (mountain-gym correlation)
- Progression velocity per exercise (chart)
- Body recomp trend
- Replaces "check Slack #ascent-training" workflow

**D. PWA push notifications** via service worker + Web Push API:
- Morning coaching decision (09:43)
- RPE reminder (20:00 on training days)
- Garmin auth failure alert
- Stall alerts (exercise stuck 4+ sessions)

**E. Mountain activity in coaching review:**
- Mountain deep dive card already shipped (splits, VAM, HR zones, historical comparison)
- v2.0: integrate mountain performance data into weekly analysis view, surface interference patterns visually, coaching review includes mountain trend assessment

**Key files:**
- `web/src/components/CoachingCard.tsx` — "Why?" section
- New: `web/src/views/CoachView.tsx` — chat interface
- `web/src/views/WeekView.tsx` — weekly analysis section
- New: Supabase Edge Function for chat backend
- New: service worker for PWA push

---

### Pillar 3: Nutrition Awareness

**Why:** No nutrition tracking exists despite DB tables being ready. Protein intake is the highest-impact nutritional lever (1.6-2.2 g/kg/day per KB). User wants to use an existing app with barcode scanning + meal memory for data entry, and Ascent consumes that data.

**Approach: Cronometer for data entry (barcode scan + meal memory), Ascent reads the data.**

**Deliverables:**

**A. Cronometer API integration:**
- Build with Cronometer's REST API first (official, documented)
- Research phase (Phase 1): verify API access — can we get macros (protein, carbs, fat) per meal or daily? Auth flow? Rate limits? Free tier?
- If Cronometer API doesn't work or is too limited, evaluate alternatives (MFP community libraries, manual CSV export, etc.)
- Oliwer uses Cronometer app for daily logging (barcode scanning, meal memory, favorites) — Ascent pulls the data, doesn't replace the input UX

**B. Nutrition sync script** (`scripts/nutrition_sync.py`):
- Daily sync from Cronometer → `food_log` table in Supabase
- Runs as launchd cron (21:00, after dinner) or on-demand
- Pulls: protein, carbs, fat, calories — daily totals first, per-meal if API supports it
- Uses existing `foods`, `food_log`, `meal_templates` tables (already in schema)

**C. Coaching integration (protein-first, expand later):**
- Daily protein target display in TodayView: progress bar toward 1.6-2.2 g/kg
- If protein consistently below target (3+ days), coaching card mentions it
- Mountain day carb guidance from KB rule 14 (informational)
- **Priority: protein tracking first.** Expand to full macro awareness over time as data quality proves out

**Key files:**
- `sql/001_schema.sql` lines 162-208 — existing tables
- New: `scripts/nutrition_sync.py`
- `web/src/views/TodayView.tsx` — protein display
- `openclaw/skills/health-coach/SKILL.md` — add nutrition awareness

---

### Pillar 4: Feedback Loops & Code Quality

**Why:** Several feedback loops are partially closed but not surfaced in the app. CI/CD sends failure emails that get ignored. Test coverage is limited.

**Deliverables:**

**A. Planned vs. actual comparison UI:**
- Side-by-side in Week and Plan views: planned weight/reps vs. actual from `exercise_progression`
- Delta highlighting: "Planned: 3x8 @ 72.5kg → Actual: 3x8 @ 72.5kg, RPE 7" or "Planned: 3x8 → Actual: 2x6, RPE 9 (overreached)"
- Uses existing `backfill_actuals()` data

**B. Decision outcome tracking visualization:**
- "Rest recommended → HRV improved 12% next day (good call)"
- Uses existing `coaching_decision_outcomes` view
- Surface in weekly analysis section and coaching chat context

**C. Mountain-gym interference visualization:**
- Recovery view: "After mountain days >800m, next gym session averages -12% volume"
- Uses existing `interference_analysis.py` output — currently Slack-only, surface in app

**D. Progression velocity chart:**
- Per-exercise trend: weight over time with projected progression line
- Shows where athlete is ahead/behind expected trajectory

**E. CI/CD — close the feedback loop:**
- Current problem: CI sends failure emails, builds deploy anyway, nothing changes
- **Fix: CI failures trigger autonomous rework.** When CI fails:
  1. Failure context (error message, file, line) posted to Slack #ascent-dev
  2. Claude Code agent is triggered with the failure context + relevant files
  3. Agent proposes a fix (PR or commit)
  4. Oliwer gets a Slack notification: "CI failed on X. Auto-fix proposed: [link]. Approve?"
  5. On approval, fix is merged and redeployed
- Distinguish: lint warnings (non-blocking), type errors (blocking + auto-fix), test failures (blocking + auto-fix), build failures (blocking + auto-fix)
- This replaces the current "email → ignore → builds pass anyway" anti-pattern

**F. Test coverage expansion** — target 80% on coaching-critical code:
- `coach_adjust.py`: all 11 action types
- `progression_engine.py`: edge cases for acceleration/volume cap (already 46 tests)
- `workout_push.py`: Garmin JSON generation
- Integration test: full coaching loop

**Note on planned_workouts write-path:** The April 12 audit identified 4 non-coach_adjust writers (garmin_sync writing status, workout_push writing garmin_workout_id, etc.). These were evaluated and left as-is because they represent operational status updates (sync status, Garmin linkage) rather than coaching decisions — they don't change the workout content, just metadata. The coaching decision write-path (what exercises, weights, reps, adjustments) remains exclusively through `coach_adjust.py`. A DB trigger enforcing status transition rules (e.g., `planned` → `pushed` → `completed`, never `completed` → `planned`) would add a safety net without consolidating all writes, but this is lower priority than the other deliverables.

**Key files:**
- `.github/workflows/ci.yml` — add auto-fix trigger
- `web/src/views/WeekView.tsx` — planned vs actual
- `web/src/views/RecoveryView.tsx` — interference visualization
- `web/src/views/TrendsView.tsx` — progression velocity chart

---

## Phased Rollout

### Phase 1: Foundation (Weeks 1-4)
- Coaching rationale in-app (CoachingCard "Why?" section)
- Planned vs. actual comparison UI
- Coach trigger from app (Vercel API endpoint)
- Progression engine remaining gaps (6, 7, 9, 10)
- CI/CD auto-fix pipeline setup
- Nutrition app research (Cronometer API feasibility, MFP scraping feasibility)

### Phase 2: Intelligence (Weeks 5-8)
- ACWR + monotony + strain SQL views in `daily_coaching_context`
- Periodization engine (`periodization_engine.py`)
- Integrate periodization engine into block-review prompt
- Weekly analysis surfaced in-app
- Nutrition sync script (from chosen app → Supabase)

### Phase 3: Experience (Weeks 9-12)
- In-app coaching chat (Claude API backend, read + write capability via coach_adjust.py)
- PWA push notifications
- Mountain-gym interference visualization in Recovery view
- Progression velocity charts in Trends view
- Decision outcome tracking visualization
- Protein target display in TodayView

### Phase 4: Polish (Weeks 13-16)
- Mountain performance data in coaching review
- Python package restructure
- 80% test coverage on coaching-critical code
- Coaching chat refinements based on real usage
- Expand nutrition features based on data quality from sync

---

## What We Explicitly DO NOT Build

| Not Building | Why |
|---|---|
| Cloud migration off Mac | Mac is always on. Garmin auth requires Playwright. No proven need. |
| Workout execution mode | Workout is on the watch. App shows details if needed. |
| Manual protein/food entry in app | Too much friction, incomplete data. Use a dedicated app (Cronometer/MFP) with barcode scanning + meal memory. Ascent reads the data. |
| Multi-athlete support | Single-user system. No multi-tenancy overhead. |
| Native mobile app | PWA is correct for one user. |
| Google Calendar integration | Scoped out. Coaching reads from Ascent planned_workouts. |
| Custom ML models | KB evidence-based rules > model trained on 1 athlete. |
| Grafana dashboards | Web app replaced this need. |
| Strava integration | Garmin is single source of truth. |
| Meal planning / recipes | Ascent tracks macros, doesn't plan meals. |
| Per-set RPE logging UI | Already available. |

---

## Verification Plan

- **Phase 1:** Deploy coaching rationale, verify on phone. Test coach trigger (3 scenarios: train/lighten/rest). Verify CI auto-fix on a deliberate type error.
- **Phase 2:** Compare ACWR calculations against manual spreadsheet for known dates. Review periodization engine proposal during Block 1 review (April 28). Test nutrition sync end-to-end.
- **Phase 3:** Test chat with 10 real coaching questions (5 read-only, 5 coaching directives). Verify coach_adjust.py audit trail from chat-initiated changes has no gaps vs. agent-initiated changes. Verify push notifications on iOS Safari.
- **Phase 4:** Run full test suite, verify no coaching decision regression. Check nutrition data quality after 2 weeks of usage.

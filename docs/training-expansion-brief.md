# Ascent — Training Expansion Brief (Consolidated)

> **Purpose:** Complete specification for expanding Ascent into a fully autonomous closed-loop training platform. Contains detailed implementation specs, all decisions, dependencies, and checklists. This is the single document Claude Code needs to execute Phases 7–10.
>
> **Save to:** `~/vault/second-brain/projects/ascent/training-expansion-brief.md`
> **Created:** Opus session, March 29, 2026
> **Prereqs:** Read alongside the original Ascent project brief and `coaching-context.md`

-----

## 1. System Overview

### What We're Building

Expand Ascent from a coaching analysis system into a **fully autonomous closed-loop training platform** that generates, delivers, tracks, and adapts training across strength and cardio (splitboarding / hike&fly) domains — with zero manual computer interaction.

### Core Loop

```
Opus creates plan → Claude Code generates weekly workouts →
Push to Garmin watch + Google Calendar →
Athlete executes → Garmin records performance →
Data syncs to Supabase → Claude Code analyzes compliance →
Apply progressive overload / micro-adjustments →
Generate next week → repeat
```

### Three-Tier Agent Model (Unchanged)

|Tier       |Agent               |Role in Training Expansion                                                                                                       |
|-----------|--------------------|---------------------------------------------------------------------------------------------------------------------------------|
|Strategic  |Opus                |Creates macro plans: periodization, progressive overload rules, season structure. Produces `coaching-context.md`.                |
|Tactical   |Claude Code (weekly)|Generates concrete workouts from the plan, applies progressive overload, pushes to Garmin + Calendar, runs compliance analysis.  |
|Operational|Haiku (daily)       |Morning readiness check. If adjustment needed, suggests via Telegram. On confirmation, pushes updated workout + updates calendar.|

### Autonomy Principle

The entire cycle runs without manual computer interaction. Oliwer's only touchpoints:

- **Telegram confirmations** when daily adjustments are suggested
- **Telegram approval** when replanning is triggered
- **Garmin watch** to execute workouts (weights pre-filled, no lookup needed)
- **Google Calendar** to see upcoming sessions

-----

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PLANNING LAYER                          │
│  Opus ─── creates macro plans, periodization,               │
│           progressive overload rules, season structure      │
│                                                             │
│  Output: coaching-context.md                                │
│  Input:  knowledge base, blood tests, Supabase history      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXECUTION LAYER                           │
│  Claude Code (weekly cron via OpenClaw)                     │
│                                                             │
│  1. Pull last week's Garmin data → Supabase                │
│  2. Run weekly_analysis.py (compliance, adaptation)         │
│  3. Generate next week's workouts (FIT / JSON)              │
│  4. Upload workouts to Garmin Connect                       │
│  5. Create/update Google Calendar events                    │
│  6. Evaluate replanning triggers                            │
│  7. Report summary to Telegram                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   MONITORING LAYER                          │
│  Haiku (daily cron via OpenClaw)                            │
│                                                             │
│  1. Pull morning readiness (HRV, body battery, sleep)       │
│  2. Compare against today's planned session                 │
│  3. If adjustment needed → Telegram suggestion              │
│  4. On confirmation → push updated workout + update cal     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   DEVICE LAYER                              │
│  Garmin Watch                                               │
│                                                             │
│  ← Receives structured workouts (weights pre-filled)        │
│  → Exports: HR, GPS, duration, elevation, per-set data,     │
│     training effect, HRV, body battery, sleep               │
└─────────────────────────────────────────────────────────────┘
```

-----

## 3. Phase Map & Dependencies

### Complete Phase List

|Phase|Name                        |Status       |Depends On     |
|-----|----------------------------|-------------|---------------|
|1    |Supabase Schema & Seed Data |🟡 In Progress|—              |
|2–4  |(Per original project brief)|⬜ Planned    |Phase 1        |
|5    |Weekly Analysis Script      |⬜ Planned    |Phase 1        |
|6    |First Opus Planning Session |⬜ Planned    |Phase 1, KB    |
|KB   |Scientific Knowledge Base   |⬜ Planned    |—              |
|GS   |Garmin Auth Spike           |⬜ Planned    |—              |
|7a   |Garmin Data Pull            |⬜ Planned    |GS, Phase 1    |
|7b   |Garmin Workout Push         |⬜ Planned    |GS             |
|8    |Workout Generation Engine   |⬜ Planned    |Phase 6, 7a, 7b|
|9    |Google Calendar Integration |⬜ Planned    |Phase 8        |
|10   |Autonomous Orchestration    |⬜ Planned    |7a, 8, 9       |

### Dependency Graph

```
            ┌─── KB (Deep Research) ──────────────┐
            │                                      ▼
Phase 1 ──► │                              Phase 6 (Opus Plan)
            │                                      │
            ├─── GS (Garmin Spike) ──┐             │
            │                        ▼             │
            │                    Phase 7a ─────────┤
            │                    Phase 7b ─────────┤
            │                                      ▼
            │                              Phase 8 (Workout Gen)
Phase 5 ───►──────────────────────────────►    │
            │                              Phase 9 (Calendar)
            │                                      │
            │                                      ▼
            └──────────────────────────────► Phase 10 (Orchestration)
```

**Parallelizable now:** KB, GS, Phase 1 completion
**Blocked until Phase 1:** 5, 6, 7a
**Blocked until Garmin Spike:** 7a, 7b
**Blocked until Phase 6:** 8

-----

## 4. Garmin Integration Layer (Phases GS, 7a, 7b)

### Garmin Auth Spike (Phase GS)

**Context:** No official Garmin developer API access (enterprise only). Using unofficial Python libraries.

**Test three options in priority order:**

1. **`garth`** — OAuth-based, best token persistence. Primary candidate.
2. **`garminconnect`** — session-based, more established but sessions expire.
3. **FIT file hybrid** — generate FIT files + upload via whichever auth works.

**Spike deliverable:** Completed evaluation matrix (see spike document at `~/projects/ascent/spikes/garmin-auth-spike.md`) resolving these open items:

- Which library works reliably for auth + read + write
- Whether tokens persist across 24h+ gaps
- Whether target weights can be pre-filled per set on pushed workouts
- Whether custom exercise names are supported or limited to Garmin's library
- What per-set data Garmin returns after a completed strength workout

### Phase 7a: Garmin Data Pull

**Script:** `scripts/garmin_sync.py`

**Responsibilities:**

- Authenticate with Garmin Connect (using spike winner)
- Pull activity summaries: type, duration, distance, calories, avg/max HR, training effect
- Pull detailed activity data: HR trace, GPS track, laps/splits, elevation profile
- Pull daily readiness: HRV status, body battery, sleep score, stress, resting HR
- Write all data to Supabase
- Handle auth token refresh; on failure → Telegram alert

**Supabase schema additions:**

```sql
-- Garmin credentials (encrypted at rest)
CREATE TABLE garmin_auth (
  user_id UUID REFERENCES users(id) PRIMARY KEY,
  email TEXT NOT NULL,
  encrypted_password TEXT NOT NULL,
  session_token JSONB,
  last_sync_at TIMESTAMPTZ
);

-- Raw activity data from Garmin
CREATE TABLE garmin_activities (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  garmin_activity_id BIGINT UNIQUE NOT NULL,
  activity_type TEXT NOT NULL,        -- 'strength', 'hiking', 'backcountry_skiing', 'snowboarding', etc.
  started_at TIMESTAMPTZ NOT NULL,
  duration_seconds INTEGER,
  distance_meters NUMERIC,
  elevation_gain_meters NUMERIC,
  avg_hr INTEGER,
  max_hr INTEGER,
  calories INTEGER,
  training_effect NUMERIC,
  anaerobic_effect NUMERIC,
  vo2max_estimate NUMERIC,
  hr_zones JSONB,                     -- time-in-zone breakdown
  laps JSONB,                         -- lap/split details
  gps_summary JSONB,                  -- simplified track
  raw_data JSONB,                     -- full Garmin response
  synced_at TIMESTAMPTZ DEFAULT now()
);

-- Daily readiness/wellness metrics
CREATE TABLE garmin_daily_metrics (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  date DATE NOT NULL,
  hrv_status TEXT,                    -- 'balanced', 'low', 'unbalanced'
  hrv_value INTEGER,                  -- 7-day avg HRV
  body_battery_morning INTEGER,       -- 0-100
  body_battery_evening INTEGER,
  sleep_score INTEGER,
  sleep_duration_seconds INTEGER,
  stress_avg INTEGER,
  resting_hr INTEGER,
  UNIQUE(user_id, date)
);
```

**OpenClaw cron:** `garmin_daily_sync` — daily at 06:00

### Phase 7b: Garmin Workout Push

**Script:** `scripts/garmin_workout_push.py`

**Responsibilities:**

- Accept workout definition (JSON) → convert to Garmin format
- Upload structured workout to Garmin Connect
- Schedule workout for a specific date
- Pre-fill target weights and reps per set (critical UX requirement)
- Return confirmation: workout ID, sync status
- FIT file fallback if API push fails

**Workout definition format (internal JSON):**

Strength:

```json
{
  "type": "strength",
  "name": "Week 12 — Upper Body A",
  "scheduled_date": "2026-04-06",
  "estimated_duration_minutes": 75,
  "exercises": [
    {
      "name": "Bench Press",
      "garmin_exercise_id": "BENCH_PRESS",
      "sets": 4,
      "reps": 6,
      "target_weight_kg": 87.5,
      "target_rpe": 8,
      "rest_seconds": 180
    }
  ]
}
```

Cardio (touring):

```json
{
  "type": "cardio_touring",
  "name": "Week 12 — Endurance Hike",
  "scheduled_date": "2026-04-08",
  "target_duration_minutes": 180,
  "target_elevation_gain_m": 1200,
  "hr_zones": [
    { "zone": 2, "percentage": 70 },
    { "zone": 3, "percentage": 25 },
    { "zone": 4, "percentage": 5 }
  ]
}
```

**Exercise mapping:** If Garmin does not support custom exercises (determined by spike), maintain a mapping table:

```
Ascent exercise name → Garmin exercise key
"Bench Press"        → "BENCH_PRESS"
"Bulgarian Split Sq" → "SINGLE_LEG_SQUAT" (closest match)
```

Unmapped exercises: include full details in the workout step name/notes so the athlete sees them on-watch.

-----

## 5. Workout Generation Engine (Phase 8)

**Script:** `scripts/workout_generator.py`

### Inputs

1. **`coaching-context.md`** — the Opus-authored plan containing:
- Current training block (e.g., "Hypertrophy Block 2, Week 3 of 4")
- Exercise selection per session template
- Progression rules per exercise category
- Weekly structure (e.g., Mon: Upper A, Wed: Lower A, Fri: Upper B, Sat: Touring)
- Deload rules (e.g., "every 4th week, reduce volume 40%")
- Cardio periodization phases (base → build → peak → taper)
1. **Last week's Garmin activities** (`garmin_activities` table)
- Actual weights/reps per set for strength (matched via workout ID)
- Actual HR zones, duration, elevation for cardio
- Completion rate (did all planned sessions happen?)
- Unplanned activities (resort snowboarding → detected by `activity_type = 'snowboarding'`)
1. **Readiness context** (`garmin_daily_metrics` table)
- Week average HRV trend, body battery trend, sleep quality

### Progressive Overload Logic — Strength

```
FOR each exercise in next_week_plan:
  last = get_last_performance(exercise)
  rule = get_progression_rule(exercise.category)

  IF last.all_sets_completed AND last.avg_rpe <= target_rpe:
    → APPLY progression (per rule: +2.5kg, or +1 rep, or +1 set)
  ELIF last.avg_rpe > target_rpe + 1:
    → HOLD or REDUCE load slightly
  ELIF last.missed_sets > 0:
    → HOLD current load, flag for review

  IF current_week == deload_week:
    → APPLY deload modifiers (volume × 0.6, intensity × 0.9)
```

### Progressive Overload Logic — Cardio

```
FOR each cardio_session in next_week_plan:
  last = get_last_cardio(session.type)

  IF block_phase == 'base':
    → Progress via duration (+10-15 min/week) or elevation (+100-200m)
    → Maintain HR mostly in zone 2
  ELIF block_phase == 'build':
    → Introduce zone 3 intervals, increase density
  ELIF block_phase == 'peak':
    → Sport-specific sessions (sustained climbing, technical terrain)
  ELIF block_phase == 'taper':
    → Reduce volume 40-60%, maintain intensity
```

### Unplanned Activity Handling

Resort snowboarding and other unplanned high-intensity sessions:

- Detected by: `activity_type IN ('snowboarding', 'resort_skiing')` without a matching `planned_workouts` entry
- Calculate estimated training load from HR data + duration
- Factor into weekly volume: may reduce next planned session intensity or trigger a recovery suggestion
- Include in weekly report as "unplanned load"

### Output

- Workout JSON definitions (one per session) → `garmin_workout_push.py`
- New `planned_workouts` rows in Supabase
- New `exercise_progression` rows
- Triggers calendar event creation (Phase 9)
- Summary for Telegram weekly report

### Supabase Schema

```sql
CREATE TABLE planned_workouts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  training_block TEXT NOT NULL,
  week_number INTEGER NOT NULL,
  session_name TEXT NOT NULL,
  session_type TEXT NOT NULL,           -- 'strength', 'cardio_touring', 'mobility'
  scheduled_date DATE NOT NULL,
  scheduled_time TIME,
  estimated_duration_minutes INTEGER,
  workout_definition JSONB NOT NULL,
  garmin_workout_id TEXT,
  calendar_event_id TEXT,
  status TEXT DEFAULT 'planned',        -- 'planned', 'adjusted', 'completed', 'skipped'
  actual_garmin_activity_id BIGINT REFERENCES garmin_activities(garmin_activity_id),
  compliance_score NUMERIC,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE exercise_progression (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  exercise_name TEXT NOT NULL,
  date DATE NOT NULL,
  planned_sets INTEGER,
  planned_reps INTEGER,
  planned_weight_kg NUMERIC,
  planned_rpe NUMERIC,
  actual_sets INTEGER,
  actual_reps_per_set JSONB,            -- [8, 8, 7, 6]
  actual_weight_kg NUMERIC,
  actual_rpe NUMERIC,
  progression_applied TEXT,             -- 'weight_increase', 'rep_increase', 'hold', 'deload'
  notes TEXT,
  UNIQUE(user_id, exercise_name, date)
);
```

-----

## 6. Google Calendar Integration (Phase 9)

### Calendar Event Structure

Strength:

```
Title:    🏋️ Upper Body A — Week 12
Time:     Mon 19:00 – 20:15
Description:
  Bench Press: 4×6 @ 87.5kg (RPE 8)
  Barbell Row: 4×8 @ 70kg (RPE 7)
  OHP: 3×8 @ 50kg (RPE 7)
  Pull-ups: 3×10 @ BW+10kg (RPE 8)

  Total volume: ~18,500 kg
  Estimated duration: 75 min
```

Cardio:

```
Title:    ⛷️ Touring — Endurance Build
Time:     Sat 07:00 – 11:00
Description:
  Target: 1200m elevation gain
  Duration: ~3h moving time
  HR zones: 70% Z2, 25% Z3, 5% Z4
```

### Implementation

- Use Google Calendar API via MCP connector (available in OpenClaw) or direct API
- Dedicated **"Ascent Training"** calendar (color-coded, separate from personal)
- Events created Sunday evening for the upcoming week
- Store `calendar_event_id` in `planned_workouts` table for updates/deletes
- If Haiku adjusts a session → update the existing calendar event
- After completion → optionally update event description with actual performance

### Schedule Defaults (Learned from Habits — Decision U4/U5)

|Session Type     |Default Time                 |
|-----------------|------------------------------|
|Gym (strength)   |Weekday evenings, 19:00 start|
|Touring (weekday)|17:00–18:00 start            |
|Touring (weekend)|07:00–08:00 start            |

Start with these defaults. Future enhancement: learn from actual activity start times in `garmin_activities` and adjust.

-----

## 7. Autonomous Orchestration (Phase 10)

### OpenClaw Cron Schedule

|Time        |Job                    |Agent      |Description                                                       |
|------------|-----------------------|-----------|------------------------------------------------------------------|
|Daily 06:00 |`garmin_daily_sync`    |Script     |Pull yesterday's activities + today's morning metrics             |
|Daily 06:30 |`daily_readiness_check`|Haiku      |Check readiness vs. planned session, Telegram if adjustment needed|
|Sunday 20:00|`weekly_analysis`      |Claude Code|Compliance analysis, replanning trigger evaluation                |
|Sunday 20:30|`workout_generation`   |Claude Code|Generate next week, push to Garmin + Calendar                     |
|Sunday 20:45|`weekly_summary`       |Claude Code|Send report to Telegram                                           |
|On trigger  |`opus_data_prep`       |Script     |Generate structured summary for Opus planning session             |

### Telegram Interaction Patterns

**Weekly report (no confirmation needed):**

```
📊 Week 12 Summary

Strength: 3/3 sessions completed
  Bench: 85kg × 4×6 → progressing to 87.5kg ✅
  Squat: 110kg × 4×5 → holding (RPE 9.5) ⚠️

Cardio: 1/1 touring completed
  Elevation: 1350m (target: 1200m) ✅
  Zone 2 time: 68% (target: 70%) ✅

Unplanned: Resort snowboarding Sat (2.5h, est. high intensity)
  → Next week Lower A volume reduced 10%

Readiness: HRV stable, avg body battery 72

Next week generated and synced to Garmin + Calendar.
```

**Daily adjustment (confirmation required — Decision U1):**

```
⚠️ Adjustment Suggested

Body battery: 38 (low)
HRV: below baseline for 2 days
Sleep: 5.2h (poor)

Today's planned: Lower Body A (heavy squats + deadlifts)
Suggestion: Swap to mobility/recovery session

Reply CONFIRM to apply, or KEEP to train as planned.
```

On CONFIRM → push updated workout to Garmin + update Calendar event.
On KEEP → no changes, log that override happened for weekly analysis.

**Replanning trigger (escalation to Opus — Decision U3):**

```
🔄 Replanning Trigger Detected

Trigger: 3 consecutive weeks of missed progression on compound lifts
Context: RPE consistently >9 despite adequate recovery metrics

Recommendation: Schedule Opus session to reassess training block.

Reply SCHEDULE to auto-prep data, or DISMISS.
```

On SCHEDULE → run `opus_data_prep` → save prep doc to Obsidian → notify that it's ready.

### Failure Handling

|Failure            |Response                                                                                     |
|-------------------|----------------------------------------------------------------------------------------------|
|Garmin auth expired|Telegram: "Garmin auth expired. Reply /garmin_reauth to re-authenticate."                    |
|Garmin API down    |Generate FIT files, Telegram: "Garmin API unavailable. FIT files saved, manual sync needed." |
|Workout push fails |Retry once, then Telegram alert with manual fallback                                         |
|Calendar API fails |Workout still pushed to Garmin, Telegram: "Calendar sync failed, workouts are on your watch."|

-----

## 8. Decisions Log

All decisions locked across planning conversations.

### Architecture

|# |Decision                                                                        |
|--|--------------------------------------------------------------------------------|
|D1|Three-tier model: Opus (plan) → Claude Code (weekly) → Haiku (daily)            |
|D2|Coach executes plans, never creates them — plan creation is Opus's role         |
|D3|`coaching-context.md` is the central state file                                 |
|D4|Micro-adjustments (≤10-15% volume) at Claude Code tier without Opus replanning  |
|D5|Garmin integration via unofficial Python library (no developer API access)      |
|D6|`garth` primary, `garminconnect` fallback, FIT hybrid last resort               |
|D7|Bidirectional Garmin: pull activities/readiness, push structured workouts       |
|D8|Workout-activity matching: primary by Garmin workout ID, fallback by date + type|

### Training Domains

|# |Decision                                                                                  |
|--|---------------------------------------------------------------------------------------------|
|T1|V1 scope: Strength + Cardio (splitboarding / hike&fly)                                    |
|T2|Mobility deferred to V2                                                                   |
|T3|Target weights pre-filled on Garmin watch — no manual lookup                              |
|T4|Must use Garmin built-in exercises OR validate custom exercise creation (spike determines)|
|T5|Resort snowboarding = unplanned high-intensity cardio, factored into weekly load          |
|T6|Coaching foundation based on scientific evidence / knowledge base                         |

### Schedule & UX

|# |Decision                                                                               |
|--|-----------------------------------------------------------------------------------------|
|U1|Daily adjustments: Haiku suggests via Telegram, user confirms                          |
|U2|Weekly reports: informational, no confirmation needed                                  |
|U3|Replanning triggers: Telegram with SCHEDULE / DISMISS                                  |
|U4|Training times learned from habits, not rigid                                          |
|U5|Defaults: gym 19:00-20:30 weekday evenings, touring 17-18h weekdays or weekend mornings|
|U6|All training sessions appear in Google Calendar automatically                          |
|U7|Calendar events updated if Haiku adjusts a session                                     |
|U8|System fully autonomous — no manual computer interaction                               |

-----

## 9. Open Items

|# |Item                                                        |Blocking  |Resolution                 |
|--|------------------------------------------------------------|----------|---------------------------|
|O1|Which Garmin Python library works for auth + read + write?  |Phase 7   |Garmin spike               |
|O2|Does Garmin API support pre-filling target weights per set? |Phase 7b/8|Garmin spike               |
|O3|Custom exercise names or limited to Garmin library?         |Phase 7b/8|Garmin spike               |
|O4|Garmin auth token persistence — how long do tokens last?    |Phase 7a  |Spike: test after 24h+     |
|O5|Re-auth failure Telegram flow                               |Phase 10  |Design during Phase 10     |
|O6|Detecting resort snowboarding vs other activities           |Phase 7a/8|Match `activity_type`      |
|O7|Post-workout RPE: Garmin sufficient or need Telegram prompt?|Phase 8   |Spike: check returned data |
|O8|Google Calendar: MCP connector or direct API?               |Phase 9   |Evaluate in Phase 9        |
|O9|Training time model: defaults only or learned?              |Phase 8   |Start defaults, learn later|

-----

## 10. Artifact Registry

### Planning Documents

|Artifact                |Location                                                                      |
|------------------------|------------------------------------------------------------------------------|
|Original Project Brief  |`~/vault/second-brain/projects/ascent/`                                       |
|Training Expansion Brief|`~/vault/second-brain/projects/ascent/training-expansion-brief.md` (THIS FILE)|
|Deep Research Prompt    |Run in Claude Deep Research                                                   |
|Garmin Auth Spike       |`~/projects/ascent/spikes/garmin-auth-spike.md`                               |
|Blood Test Results      |`~/vault/second-brain/projects/ascent/blood-tests/`                           |

### Knowledge Base (Phase KB)

|Artifact                 |Location                                              |Status       |
|-------------------------|------------------------------------------------------|-------------|
|Scientific Knowledge Base|`~/vault/second-brain/projects/ascent/knowledge-base/`|⬜ Not started|

### Supabase Tables

|Table                 |Phase|Status       |
|----------------------|-----|-------------|
|`users`               |1    |🟡 In progress|
|`training_log`        |1    |🟡 In progress|
|`nutrition_log`       |1    |🟡 In progress|
|Biomarker seed data   |1    |⬜            |
|`garmin_auth`         |7a   |⬜            |
|`garmin_activities`   |7a   |⬜            |
|`garmin_daily_metrics`|7a   |⬜            |
|`planned_workouts`    |8    |⬜            |
|`exercise_progression`|8    |⬜            |
|`calendar_events`     |9    |⬜            |

### Scripts

|Script                  |Phase|Status|
|------------------------|-----|------|
|`weekly_analysis.py`    |5    |⬜     |
|`garmin_sync.py`        |7a   |⬜     |
|`garmin_workout_push.py`|7b   |⬜     |
|`workout_generator.py`  |8    |⬜     |
|Calendar sync module    |9    |⬜     |

### OpenClaw Cron Jobs

|Job                    |Time        |Phase|Status|
|-----------------------|------------|-----|------|
|`garmin_daily_sync`    |Daily 06:00 |7a   |⬜     |
|`daily_readiness_check`|Daily 06:30 |10   |⬜     |
|`weekly_analysis`      |Sunday 20:00|5/10 |⬜     |
|`workout_generation`   |Sunday 20:30|8/10 |⬜     |
|`weekly_summary`       |Sunday 20:45|10   |⬜     |
|`opus_data_prep`       |On trigger  |6/10 |⬜     |

-----

## 11. Phase Checklists

### Before Starting Any Phase

- [ ] Read this document — check dependencies are met
- [ ] Check decisions log — align with all locked decisions
- [ ] Check open items — resolve any that block this phase
- [ ] Read original project brief for full context

### Garmin Spike Checklist

- [ ] Tested library options (stop at first success)
- [ ] Evaluation matrix completed
- [ ] Auth persistence validated (24h+ gap)
- [ ] Read tests: activities, HRV, body battery, sleep
- [ ] Write test: workout uploaded, appears on watch
- [ ] Target weights visible on watch
- [ ] Custom exercises supported or mapping defined
- [ ] Completed activity returns per-set data
- [ ] Open items O1–O4, O7 resolved and documented

### Phase 6 (Opus Planning) Output Checklist

- [ ] Knowledge base available as input
- [ ] Blood test data available
- [ ] `coaching-context.md` produced with ALL of:
  - [ ] Training block structure (mesocycles)
  - [ ] Exercise selection per session template
  - [ ] Progressive overload rules per exercise category
  - [ ] Weekly structure (sessions × days)
  - [ ] Deload rules
  - [ ] Cardio periodization (base/build/peak/taper)
  - [ ] Replanning trigger definitions
  - [ ] Season plan (annual periodization)

### Phase 8 (Workout Generation) Checklist

- [ ] Reads `coaching-context.md` correctly
- [ ] Pulls last week's Garmin data
- [ ] Progressive overload logic works per exercise
- [ ] Deload weeks handled
- [ ] Strength workout JSONs in correct format
- [ ] Cardio definitions generated (HR zones, elevation targets)
- [ ] Unplanned activities (resort snowboarding) factored into load
- [ ] Outputs to `planned_workouts` table
- [ ] Triggers Garmin push + calendar sync

### Phase 10 (Orchestration) Checklist

- [ ] All cron jobs configured in OpenClaw
- [ ] Daily flow end-to-end: sync → readiness → Telegram → confirm → push + calendar
- [ ] Weekly flow end-to-end: analysis → generation → Garmin → calendar → Telegram
- [ ] Replanning trigger → Telegram → SCHEDULE → opus prep doc
- [ ] Garmin auth failure → Telegram alert → recovery
- [ ] No manual computer interaction for any normal flow

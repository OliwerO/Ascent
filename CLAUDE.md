## type: brief

status: ready
created: 2026-03-27
project: ascent
tech: [supabase, postgresql, grafana, vercel, react, vite, tailwind, python, garminconnect, openclaw, mcp]
tags: [brief, health, fitness, coaching, garmin]

# Ascent — Personal AI Health Intelligence for Jarvis

## What

Ascent is a health intelligence module for Jarvis that turns Garmin wearable data into actionable coaching. It combines automatic data collection, statistical analysis, interactive visualization, and AI-powered coaching that adapts to Oliwer's seasonal training pattern (mountain sports ↔ gym), goals, and life context.

Ascent is NOT a standalone platform. It extends the existing Jarvis infrastructure: OpenClaw gateway, Telegram channel, Obsidian vault, Claude Code via ACP. No new infrastructure patterns — just new capabilities on proven foundations.

## Architecture

```
Garmin Watch (Fenix/Epix)
    │
    ▼
Garmin Connect (cloud)
    │
    ├──► Garmin MCP Server (on Mac, live queries)
    │    └──► OpenClaw/Jarvis → Telegram
    │         (conversational: "how was my sleep?")
    │
    └──► Python Cron (on Mac, nightly sync)
         └──► Supabase (PostgreSQL)
              │
              ├──► Grafana Cloud (time-series dashboards)
              │    HRV trends, sleep charts, body comp,
              │    training volume, built-in alerts
              │
              ├──► React App on Vercel (interactive UI)
              │    Food logging, training log input,
              │    blood test upload, goal management
              │
              ├──► Claude Code ACP (weekly analysis, $0)
              │    Statistical analysis, coaching reports,
              │    plan adjustments, goal tracking
              │
              ├──► Opus via Claude App (plan creation, interactive)
              │    Training programs, nutrition plans,
              │    seasonal planning, strategic reviews
              │
              └──► Obsidian Vault (weekly summary notes)
                   Coaching context, goal tracking,
                   blood test records, DEXA results
```

### Data Flow Summary

|Data                                                                   |Source      |Input Method                                  |Storage              |Frequency       |
|-----------------------------------------------------------------------|------------|----------------------------------------------|---------------------|----------------|
|HRV, sleep, HR, stress, Body Battery, steps, VO2max, training readiness|Garmin      |Automatic sync                                |Supabase             |Nightly         |
|Activities (runs, rides, strength, ski tours)                          |Garmin      |Automatic sync                                |Supabase             |Nightly         |
|Body weight                                                            |Xiaomi Mi Scale (Zepp Life)|Automatic sync (SmartScaleConnect)        |Supabase             |Daily 05:30     |
|Food/nutrition                                                         |User        |Text/voice/photo via React app or Telegram    |Supabase             |Manual, optional|
|Blood tests                                                            |User        |PDF upload via Telegram → Claude Vision parses|Supabase + Obsidian  |~1x/year        |
|DEXA scans                                                             |User        |Screenshot via Telegram → Claude parses       |Supabase + Obsidian  |Occasional      |
|Injuries, soreness, context                                            |User        |Telegram chat with Jarvis                     |Coaching context file|Ad-hoc          |
|Goals                                                                  |User + Coach|Set via Telegram or React app                 |Supabase + Obsidian  |As needed       |

### Component Responsibilities

|Component              |Reads                       |Writes                                |Purpose                                                 |
|-----------------------|----------------------------|--------------------------------------|--------------------------------------------------------|
|Garmin MCP server      |Garmin Connect API          |Nothing                               |Live data access for Jarvis conversations               |
|Python sync script     |Garmin Connect API          |Supabase                              |Nightly data accumulation                               |
|Grafana Cloud          |Supabase                    |Nothing                               |Time-series visualization (read-only dashboards)        |
|React app (Vercel)     |Supabase                    |Supabase                              |Interactive input (food, training, goals) + custom views|
|Claude Code (weekly)   |Supabase + coaching context |Supabase + Obsidian + coaching context|Statistical analysis, coaching reports                  |
|Jarvis/Haiku (daily)   |Garmin MCP + Supabase       |Telegram + coaching log               |Morning briefing, anomaly alerts                        |
|Opus (interactive)     |Coaching context + data prep|Coaching context + Obsidian           |Plan creation, strategic reviews, seasonal transitions  |
|Jarvis/Opus (quarterly)|Everything                  |Coaching context + Obsidian           |Strategic reviews, season planning                      |

-----

## Phase Breakdown

### Phases 1-3: Infrastructure (Autonomous via ACP, careful mode)

These phases are well-scoped with testable outputs. Jarvis executes them sequentially without user intervention.

### Phase 1: Supabase Schema + Seed Data

**Task:** Create the Supabase project and deploy the full database schema.

**Create these tables in Supabase:**

```sql
-- =============================================
-- GARMIN DAILY METRICS
-- =============================================

CREATE TABLE daily_metrics (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  total_steps INTEGER,
  total_distance_meters REAL,
  active_calories INTEGER,
  total_calories INTEGER,
  floors_ascended INTEGER,
  floors_descended INTEGER,
  intensity_minutes INTEGER,
  moderate_intensity_minutes INTEGER,
  vigorous_intensity_minutes INTEGER,
  resting_hr INTEGER,
  min_hr INTEGER,
  max_hr INTEGER,
  avg_hr INTEGER,
  avg_stress_level INTEGER,
  max_stress_level INTEGER,
  rest_stress_duration INTEGER,
  activity_stress_duration INTEGER,
  body_battery_highest INTEGER,
  body_battery_lowest INTEGER,
  body_battery_charged INTEGER,
  body_battery_drained INTEGER,
  training_readiness_score REAL,
  training_load REAL,
  vo2max REAL,
  spo2_avg REAL,
  respiration_avg REAL,
  raw_json JSONB,
  synced_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- SLEEP
-- =============================================

CREATE TABLE sleep (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  sleep_start TIMESTAMPTZ,
  sleep_end TIMESTAMPTZ,
  total_sleep_seconds INTEGER,
  deep_sleep_seconds INTEGER,
  light_sleep_seconds INTEGER,
  rem_sleep_seconds INTEGER,
  awake_seconds INTEGER,
  overall_score INTEGER,
  quality_score INTEGER,
  duration_score INTEGER,
  rem_percentage_score INTEGER,
  restlessness_score INTEGER,
  stress_score INTEGER,
  revitalization_score INTEGER,
  raw_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- HRV
-- =============================================

CREATE TABLE hrv (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  weekly_avg REAL,
  last_night_avg REAL,
  last_night_5min_high REAL,
  baseline_low_upper REAL,
  baseline_balanced_low REAL,
  baseline_balanced_upper REAL,
  status TEXT,
  readings JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- BODY COMPOSITION
-- =============================================

CREATE TABLE body_composition (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  weight_grams INTEGER,
  weight_kg REAL GENERATED ALWAYS AS (weight_grams / 1000.0) STORED,
  bmi REAL,
  body_fat_pct REAL,
  body_water_pct REAL,
  bone_mass_grams INTEGER,
  muscle_mass_grams INTEGER,
  visceral_fat_rating REAL,
  metabolic_age INTEGER,
  lean_body_mass_grams INTEGER,
  source TEXT DEFAULT 'garmin',
  raw_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- ACTIVITIES
-- =============================================

CREATE TABLE activities (
  id BIGSERIAL PRIMARY KEY,
  garmin_activity_id TEXT UNIQUE,
  date DATE NOT NULL,
  activity_type TEXT NOT NULL,
  activity_name TEXT,
  start_time TIMESTAMPTZ,
  duration_seconds INTEGER,
  distance_meters REAL,
  calories INTEGER,
  avg_hr INTEGER,
  max_hr INTEGER,
  avg_speed REAL,
  max_speed REAL,
  elevation_gain REAL,
  elevation_loss REAL,
  training_effect_aerobic REAL,
  training_effect_anaerobic REAL,
  vo2max REAL,
  total_sets INTEGER,
  total_reps INTEGER,
  hr_zones JSONB,
  raw_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- HEART RATE + STRESS TIME SERIES
-- =============================================

CREATE TABLE heart_rate_series (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  readings JSONB,
  resting_hr INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE stress_series (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  readings JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- FOOD LOGGING
-- =============================================

CREATE TABLE foods (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  brand TEXT,
  calories_per_100g REAL,
  protein_per_100g REAL,
  carbs_per_100g REAL,
  fat_per_100g REAL,
  fiber_per_100g REAL,
  sugar_per_100g REAL,
  sodium_per_100g REAL,
  source TEXT,
  source_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE food_log (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  meal_type TEXT NOT NULL,
  food_id BIGINT REFERENCES foods(id),
  description TEXT,
  quantity_grams REAL,
  calories REAL,
  protein_g REAL,
  carbs_g REAL,
  fat_g REAL,
  fiber_g REAL,
  input_method TEXT,
  photo_url TEXT,
  confidence REAL,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE meal_templates (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  items JSONB,
  total_calories REAL,
  total_protein REAL,
  total_carbs REAL,
  total_fat REAL,
  use_count INTEGER DEFAULT 0,
  last_used TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- TRAINING LOG (WEIGHT TRAINING)
-- =============================================

CREATE TABLE exercises (
  id BIGSERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  category TEXT,
  muscle_groups JSONB,
  equipment TEXT,
  is_compound BOOLEAN DEFAULT FALSE,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE training_sessions (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  garmin_activity_id TEXT,
  name TEXT,
  program TEXT,
  duration_minutes INTEGER,
  pre_hrv REAL,
  pre_body_battery INTEGER,
  pre_resting_hr INTEGER,
  sleep_score_prev_night INTEGER,
  total_volume_kg REAL,
  total_sets INTEGER,
  notes TEXT,
  rating INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE training_sets (
  id BIGSERIAL PRIMARY KEY,
  session_id BIGINT NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
  exercise_id BIGINT NOT NULL REFERENCES exercises(id),
  set_number INTEGER NOT NULL,
  set_type TEXT DEFAULT 'working',
  weight_kg REAL,
  reps INTEGER,
  rpe REAL,
  tempo TEXT,
  rest_seconds INTEGER,
  volume_kg REAL GENERATED ALWAYS AS (weight_kg * reps) STORED,
  estimated_1rm REAL GENERATED ALWAYS AS (
    CASE WHEN reps = 1 THEN weight_kg
         WHEN reps > 0 AND weight_kg > 0 THEN weight_kg * (1 + reps / 30.0)
         ELSE NULL END
  ) STORED,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE exercise_prs (
  id BIGSERIAL PRIMARY KEY,
  exercise_id BIGINT NOT NULL REFERENCES exercises(id),
  pr_type TEXT NOT NULL,
  value REAL NOT NULL,
  date DATE NOT NULL,
  set_id BIGINT REFERENCES training_sets(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- BLOOD TESTS
-- =============================================

CREATE TABLE blood_test_panels (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  lab_name TEXT,
  fasting BOOLEAN,
  notes TEXT,
  pdf_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE blood_test_results (
  id BIGSERIAL PRIMARY KEY,
  panel_id BIGINT NOT NULL REFERENCES blood_test_panels(id) ON DELETE CASCADE,
  biomarker TEXT NOT NULL,
  value REAL NOT NULL,
  unit TEXT NOT NULL,
  reference_low REAL,
  reference_high REAL,
  optimal_low REAL,
  optimal_high REAL,
  flag TEXT,
  category TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE biomarker_definitions (
  id BIGSERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  category TEXT NOT NULL,
  standard_unit TEXT NOT NULL,
  optimal_low REAL,
  optimal_high REAL,
  reference_low REAL,
  reference_high REAL,
  description TEXT,
  higher_is TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- GOALS & COACHING
-- =============================================

CREATE TABLE goals (
  id BIGSERIAL PRIMARY KEY,
  category TEXT NOT NULL,
  metric TEXT NOT NULL,
  target_value REAL NOT NULL,
  current_value REAL,
  start_date DATE,
  target_date DATE,
  status TEXT DEFAULT 'active',
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE coaching_log (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  type TEXT NOT NULL,
  channel TEXT,
  message TEXT NOT NULL,
  data_context JSONB,
  acknowledged BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- INDEXES
-- =============================================

CREATE INDEX idx_daily_metrics_date ON daily_metrics(date);
CREATE INDEX idx_sleep_date ON sleep(date);
CREATE INDEX idx_hrv_date ON hrv(date);
CREATE INDEX idx_body_comp_date ON body_composition(date);
CREATE INDEX idx_activities_date ON activities(date);
CREATE INDEX idx_activities_type ON activities(activity_type);
CREATE INDEX idx_food_log_date ON food_log(date);
CREATE INDEX idx_food_log_meal ON food_log(date, meal_type);
CREATE INDEX idx_training_sessions_date ON training_sessions(date);
CREATE INDEX idx_training_sets_session ON training_sets(session_id);
CREATE INDEX idx_training_sets_exercise ON training_sets(exercise_id);
CREATE INDEX idx_blood_results_panel ON blood_test_results(panel_id);
CREATE INDEX idx_blood_results_biomarker ON blood_test_results(biomarker);
CREATE INDEX idx_goals_status ON goals(status);
CREATE INDEX idx_coaching_log_date ON coaching_log(date);
CREATE INDEX idx_coaching_log_type ON coaching_log(type);

-- =============================================
-- USEFUL VIEWS
-- =============================================

CREATE VIEW daily_summary AS
SELECT
  dm.date,
  dm.total_steps,
  dm.resting_hr,
  dm.avg_stress_level,
  dm.body_battery_highest,
  dm.body_battery_lowest,
  dm.training_readiness_score,
  dm.vo2max,
  s.overall_score AS sleep_score,
  s.total_sleep_seconds,
  s.deep_sleep_seconds,
  s.rem_sleep_seconds,
  h.last_night_avg AS hrv_avg,
  h.weekly_avg AS hrv_weekly_avg,
  h.status AS hrv_status,
  bc.weight_kg,
  bc.body_fat_pct,
  bc.muscle_mass_grams
FROM daily_metrics dm
LEFT JOIN sleep s ON dm.date = s.date
LEFT JOIN hrv h ON dm.date = h.date
LEFT JOIN body_composition bc ON dm.date = bc.date AND bc.source = 'garmin';
```

**Seed data:** Insert biomarker definitions (includes testosterone, lipids, vitamins, inflammation markers, CBC, metabolic, thyroid panels with optimal + reference ranges). Insert standard exercises (bench press, squat, deadlift, overhead press, rows, pull-ups, and ~30 common accessories with muscle group mappings).

**Done when:**

- [ ] Supabase project created
- [ ] All tables deployed with correct types and constraints
- [ ] Indexes and views created
- [ ] Biomarker definitions seeded
- [ ] Exercises seeded
- [ ] Connection string stored in `.env` on Mac at `~/projects/ascent/.env`
- [ ] Supabase URL and anon key stored in same `.env`

### Phase 2: Garmin Sync Script

**Task:** Create a Python script that syncs all Garmin data to Supabase nightly.

**File:** `~/projects/ascent/scripts/garmin_sync.py`

**Dependencies:** `garminconnect>=0.2.40`, `garth>=0.4`, `supabase` (Python client), `python-dotenv`

**Requirements file:** `~/projects/ascent/scripts/requirements.txt`

**Authentication flow:**

```python
# Use garth for persistent auth (~1 year token lifetime)
# Token storage: ~/.garth/
# On first run: login with email/password from env vars
# Subsequent runs: garth.resume() to reuse tokens
# If resume fails: re-login automatically
```

**What to sync (all endpoints):**

```python
# For the given date (default: yesterday):
client.get_stats(date)           → daily_metrics table
client.get_sleep_data(date)      → sleep table
client.get_hrv_data(date)        → hrv table
client.get_heart_rates(date)     → heart_rate_series table
client.get_stress_data(date)     → stress_series table
client.get_body_composition(date, date)  → body_composition table
client.get_activities(0, 20)     → activities table (deduplicate by garmin_activity_id)
client.get_training_readiness(date)  → daily_metrics.training_readiness_score
client.get_spo2_data(date)       → daily_metrics.spo2_avg
client.get_respiration_data(date) → daily_metrics.respiration_avg
```

**Key behaviors:**

- Upsert on date (don't duplicate if re-run)
- Rate limit: 1 second between API calls
- Store raw JSON in `raw_json` column for every table (future-proofing)
- Log sync results to stdout (for cron log capture)
- Exit code 0 on success, 1 on failure
- Support `--date YYYY-MM-DD` flag for backfilling specific dates
- Support `--range YYYY-MM-DD YYYY-MM-DD` for bulk backfill
- Default (no flags): sync yesterday's data

**Cron setup (launchd on Mac):**

Create a launchd plist at `~/Library/LaunchAgents/com.ascent.garmin-sync.plist` that runs daily at 06:00.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ascent.garmin-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/jarvisforoli/projects/ascent/scripts/garmin_sync.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/jarvisforoli/projects/ascent/logs/sync.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/jarvisforoli/projects/ascent/logs/sync-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
    <key>WorkingDirectory</key>
    <string>/Users/jarvisforoli/projects/ascent</string>
</dict>
</plist>
```

**Done when:**

- [ ] `garmin_sync.py` runs successfully and populates Supabase tables
- [ ] `--date` flag works for single-day backfill
- [ ] `--range` flag works for multi-day backfill
- [ ] Upsert logic prevents duplicates
- [ ] Raw JSON preserved in every table
- [ ] Launchd plist created and loaded
- [ ] Sync runs at 06:00 and logs to `~/projects/ascent/logs/`
- [ ] `.env` file contains: `GARMIN_EMAIL`, `GARMIN_PASSWORD`, `SUPABASE_URL`, `SUPABASE_KEY`

### Phase 3: Garmin MCP Server + OpenClaw Config

**Task:** Install and configure a Garmin MCP server so Jarvis can query health data conversationally via Telegram.

**MCP Server:** Use `garmin-connect-mcp` by Nicolasvegam (61 tools, most comprehensive) as primary. The garth-mcp-server as fallback option.

**Installation:**

```bash
pip install garmin-connect-mcp
# or via uvx for isolated install
```

**OpenClaw config addition** (add to `openclaw.json` under `mcp_servers` or equivalent config path):

```json
{
  "garmin": {
    "command": "uvx",
    "args": ["--python", "3.12", "--from", "garmin-connect-mcp", "garmin-connect-mcp"],
    "env": {
      "GARMIN_EMAIL": "${GARMIN_EMAIL}",
      "GARMIN_PASSWORD": "${GARMIN_PASSWORD}"
    }
  }
}
```

**Health-coach skill** — Create `~/.openclaw/workspace/skills/health-coach/SKILL.md`:

```markdown
---
name: health-coach
description: Personal health intelligence and coaching for Oliwer
metadata:
  emoji: 💪
  requires: [garmin-mcp]
---

# Health Coach Skill

You are Oliwer's personal health coach with access to Garmin data via MCP tools.

## When to activate
- Any question about health, fitness, sleep, recovery, training, HRV, body composition
- Morning briefing requests
- Questions about training readiness
- Requests to analyze trends or patterns

## Available data via Garmin MCP
- Sleep data (stages, scores, duration)
- HRV (readings, baseline, status)
- Heart rate (resting, time series)
- Stress (levels, duration)
- Body Battery (charge, drain)
- Activities (type, duration, HR zones, training effect)
- Body composition (weight, body fat)
- Training readiness, VO2max
- Steps, floors, intensity minutes

## Communication style
- Concise and actionable (Telegram messages, not reports)
- Lead with the insight, not the number
- Use numbers to support recommendations, not as the message itself
- When flagging concerns, explain why AND suggest what to do
- Be direct, no hedging or disclaimers
- Adapt over time to how Oliwer prefers feedback

## Context awareness
- Read coaching-context.md (~/vault/second-brain/projects/ascent/coaching-context.md) for:
  current goals, injury status, training program, learned preferences, season context
- Mountain sport activities (ski touring, splitboarding, hiking) ARE training — treat elevation
  gain and zone time as cardio load, don't flag them as "missed gym sessions"
- Seasonal awareness: winter/spring = mountain primary, summer/fall = gym primary

## Plan management
- **Coach executes plans, does not create them.** Plan creation and redesign is Opus's job
  during interactive sessions in the Claude app.
- Coach can make day-to-day adjustments within the existing plan:
  - Swap exercises for injury avoidance (e.g., replace overhead press with landmine press for shoulder pain)
  - Suggest rest day or lighter session based on recovery data
  - Adjust session timing or order within the week
  - Reduce volume/intensity when recovery metrics warrant it
- Coach flags when the plan needs redesigning but does NOT redesign it autonomously.
  Instead: "Your squat e1RM has plateaued for 6 weeks. I'd recommend an Opus session to
  redesign your strength block."
- When user provides ad-hoc input ("I'm sore", "shoulder hurts", "I'll be traveling next week"),
  coach adjusts immediately and logs the adjustment in coaching-context.md under Coaching
  Decisions Log with the reason and what was changed.

## What NOT to do
- Don't give generic fitness advice — use actual data
- Don't alarm unnecessarily (one bad night isn't a crisis)
- Don't ignore context (sore shoulder = adjust pressing recommendations)
- Don't prescribe medical advice — flag concerns, suggest consulting a doctor
- Don't pad responses with "let me know if you need anything"
- Don't create new training programs or nutrition plans — that's Opus's role
- Don't make structural changes to the plan (changing the split, swapping training blocks,
  modifying progression schemes) — flag these for Opus
```

**Done when:**

- [ ] Garmin MCP server installed and tested (can query sleep, HRV, activities)
- [ ] OpenClaw config updated with MCP server entry
- [ ] Health-coach skill created with correct frontmatter
- [ ] Jarvis responds to "how was my sleep last night?" with actual Garmin data
- [ ] Jarvis responds to "what's my HRV trend?" with contextual analysis
- [ ] Gateway restarted and skill visible in `/context detail`

## Training Expansion (Phases 7–10)

Ascent is being expanded from a coaching analysis system into a fully autonomous closed-loop training platform. The complete specification lives in `docs/training-expansion-brief.md`. Read that file before working on any Phase 7+ task.

### Key Context for All Phases

- **Garmin integration** uses unofficial Python libraries (`garth` preferred, `garminconnect` fallback). No official developer API access.
- **Workout generation** reads `coaching-context.md` (Opus-authored) and applies progressive overload rules against Garmin performance data.
- **Google Calendar** events are created automatically for every training session.
- **Telegram** is the only user interaction channel — no manual computer interaction required.
- Resort snowboarding and other unplanned activities are detected from Garmin data and factored into weekly training load.

### New Supabase Tables (Phases 7–10)

**Schema conflict resolved (2026-03-30):** Three tables from the original expansion brief
were dropped as redundant — see `docs/schema-conflict-resolution.md` for full rationale.

Dropped (already covered by Phase 1-2):
- ~~`garmin_auth`~~ — auth handled by garth tokens on filesystem (`~/.garth/`)
- ~~`garmin_activities`~~ — covered by `activities` + `activity_details`
- ~~`garmin_daily_metrics`~~ — covered by `daily_metrics` + `sleep` + `hrv`

Tables to be created:
- `planned_workouts` — generated workout definitions with Garmin/Calendar IDs (Phase 8)
- `exercise_progression` — per-exercise progression tracking (Phase 8)

Migration: `sql/006_training_expansion.sql`

**Note:** Phase 7a (Garmin data pull) is effectively complete — `garmin_sync.py` already
pulls all 11 data types to existing tables. The Garmin Auth Spike is only needed to
validate the push side (uploading workouts to the watch).

### New Scripts (Phases 7–10)

- `scripts/garmin_sync.py` — pull Garmin data to Supabase (Phase 7a)
- `scripts/garmin_workout_push.py` — push workouts to Garmin Connect (Phase 7b)
- `scripts/workout_generator.py` — generate weekly workouts with progressive overload (Phase 8)

### OpenClaw Cron Jobs (Phase 10)

| Time | Job | Agent |
|------|-----|-------|
| Daily 06:00 | `garmin_daily_sync` | Script |
| Daily 06:30 | `daily_readiness_check` | Haiku |
| Sunday 20:00 | `weekly_analysis` | Claude Code |
| Sunday 20:30 | `workout_generation` | Claude Code |
| Sunday 20:45 | `weekly_summary` | Claude Code |
| On trigger | `opus_data_prep` | Script |

### Data Integrity & Validation Rules

All wearable data passes through validation before reaching the dashboard or coaching layer.

**Reject-level rules (applied in garmin_sync.py before writing to Supabase):**

| Metric | Reject if |
|--------|-----------|
| rMSSD (ms) | < 5 or > 250 |
| Resting HR (bpm) | < 25 or > 120 |
| Exercise HR (bpm) | < 30 or > 230 |
| Sleep duration (hours) | < 2 or > 16 |
| Daily weight change (kg) | > ± 3.0 in 24h |
| VO2max change | > 5 ml/kg/min in one session |
| Elevation gain rate | > 300 m/hour (non-climbing) |

**Flag-level rules (applied at dashboard/coaching query layer):**
- rMSSD < 8 or > 200; resting HR < 30 or > 100; sleep < 3h or > 14h
- Daily weight change > ± 2.0 kg; weekly weight change > ± 3.0 kg
- VO2max change > 3 ml/kg/min week-over-week
- All HR data during tagged strength activities (wrist HR MAPE 15–28% during RT)

**Gap-aware rolling calculations:**
- Never use `ROWS BETWEEN N PRECEDING` — it counts rows, not dates.
- Always use `generate_series()` date spine with LEFT JOIN, NULL-aware aggregation.
- Minimum valid-day thresholds: 4/7 for weekly, 20/30 for monthly, 60/90 for quarterly.

**Epoch-aware baselines:**
- Device changes, firmware updates, or algorithm shifts trigger baseline reset.
- Track in `data_epochs` table. Baselines recalculate from epoch start date.
- HRV: 7-day short-term vs 60-day normal. Weight: 7-day vs 30-day. Performance: 30-day vs 90-day.

**Data retention:** Daily granularity forever. Sub-daily: full 90 days → hourly aggregates 90d–2y → daily aggregates permanently.

### Critical Decisions

These are locked and must not be changed without an Opus session:

- Coach EXECUTES plans, never creates them. Plan creation is Opus's role.
- `coaching-context.md` is the central state file for all plan data.
- Micro-adjustments (≤10-15% volume reduction) can happen at Claude Code tier without Opus replanning.
- Target weights MUST be pre-filled on Garmin watch — athlete should never have to look up what weight to use.
- Daily adjustments require Telegram confirmation before applying.
- Training times default to: gym 19:00 weekday evenings, touring 17:00 weekdays / 07:00 weekends.
- Subjective wellness questionnaire is the highest-priority unbuilt feature — stronger evidence base than any wearable metric for detecting maladaptation (Saw et al. 2016, Nummela et al. 2024).
- ACWR ratio is not implemented — use absolute weekly load monitoring with >10–15% spike detection.
- Body Battery and Garmin Training Readiness are used as **safety guard rails at extreme values only** (BB<30, TR<40 trigger hard rest overrides), but are NOT used for graduated decision-making. These overrides are **gated on data freshness** — they only fire when `data_age_hours < 12` to prevent stale-data false positives (see sql/026). Sleep staging is contextual display only.
- All coaching messages use autonomy-supportive framing per SDT research — never directive language ("should," "must," "need to").
- Alert system uses compound conditions and time-delay filtering — no single-metric single-day alerts.

### Open Items (Blocked on Garmin Spike)

Before starting Phase 7 implementation, the Garmin auth spike must be completed. Results determine:
- Which Python library to use
- Whether custom exercises are supported
- Whether target weights can be pre-filled per set
- What per-set data Garmin returns after completion

Spike document: `spikes/garmin-auth-spike.md`

### Phase Dependencies
```
KB (knowledge base) ──────────► Phase 6 (Opus plan)
GS (Garmin spike) ──► Phase 7a ──► Phase 8 (workout gen)
                └─► Phase 7b ──┘        │
                              Phase 9 (calendar)
Phase 5 (weekly analysis) ──────────►      │
                              Phase 10 (orchestration)
```

-----

## Development Practices

Detailed coding standards, testing strategy, and deployment practices are in `docs/development-practices.md`. Follow those practices for all code changes. Key rules:

- **Always run `cd web && npm run build`** before committing frontend changes
- **SQL migrations** in numbered files (`sql/NNN_description.sql`) — never modify applied migrations
- **Secrets** in `.env` only — never in code or commits
- **Python scripts** log to stdout, exit 0/1, rate-limit external APIs
- **TypeScript strict mode** — no `any` types, fix errors don't suppress them

## Working Rules (for Claude Code sessions)

- **Prioritize quality over speed.** Always test before calling something done. Only stop when everything passes strict testing or when user input is needed.
- **Split work when it produces better results.** Don't rush complex changes in a single pass.
- **`planned_workouts` is the single source of truth** for the React app's training plan display. Any session adjustments must be written to this Supabase table.
- **Jarvis (coaching agent) must update `planned_workouts`** when adjusting sessions — not just coaching-context.md. Update his skill definition accordingly.
- **Test frontend changes** by running `cd web && npm run build` before committing. TypeScript errors block deployment.

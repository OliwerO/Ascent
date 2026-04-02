# Ascent — System Architecture & Workflows

## Mental Model

Ascent is a closed-loop personal training system. Data flows in a cycle:

```
  Plan (Opus)                    Execute (Athlete)              Track (Garmin)
  ─────────────                  ───────────────                ──────────────
  coaching-program.md    →→→     Garmin Watch Workout    →→→    Garmin Connect
       │                              │                              │
       ▼                              ▼                              ▼
  workout_generator.py           Gym Session                   garmin_sync.py
       │                                                           │
       ▼                                                           ▼
  planned_workouts table  ◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄    training_sessions
       │                                                    training_sets
       ▼                                                           │
  React App (display)                                              ▼
  Jarvis (adjust)           ◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄◄    progression_engine.py
```

### Key Principle
`planned_workouts` is the **single source of truth** for what the app displays. The coaching agent (Jarvis) reads from it and writes adjustments to it. The React app reads from it. The Garmin push reads from it.

---

## Data Ownership

| Table | Written By | Read By |
|-------|-----------|---------|
| `planned_workouts` | workout_generator.py, Jarvis (adjustments) | React app, workout_push.py |
| `training_sessions` | garmin_sync.py (from Garmin) | React app, progression_engine |
| `training_sets` | garmin_sync.py (from Garmin) | React app, progression_engine |
| `exercise_progression` | progression_engine.py | workout_generator.py, React app |
| `activities` | garmin_sync.py | React app (mountain load) |
| `body_composition` | scale_sync.py (xiaomi), egym_sync.py, garmin_sync.py | React app, daily_summary view |
| `daily_metrics`, `sleep`, `hrv` | garmin_sync.py | React app (recovery signals) |
| `subjective_wellness` | React app (user input) | morning_briefing.py, coaching agent |
| `coaching_log` | morning_briefing.py, Jarvis, API triggers | React app |

---

## Daily Coaching Cycle

```
06:00   garmin_sync.py          Pull yesterday + today's Garmin data → Supabase
09:00   (moved to 09:00)        Captures full sleep data
10:00   scale_sync.py           Pull Xiaomi weight → body_composition
10:05   morning_briefing.py     Check recovery signals → Slack briefing
        ├── HRV status + sleep hours + resting HR
        ├── Subjective wellness (if submitted)
        ├── Today's planned workout from planned_workouts
        └── Green/amber/red verdict

If GREEN:
  → Push today's workout to Garmin (workout_push.py)
  → Athlete does workout
  → Garmin syncs next morning → mark_completed

If AMBER:
  → Jarvis asks via Slack: "Push as planned or adjust?"
  → If adjust: Jarvis updates planned_workouts row

If RED:
  → Jarvis swaps to rest/mobility
  → Updates planned_workouts: status='adjusted', adjustment_reason
```

## Weekly Coaching Cycle

```
Sunday 20:00    workout_generator.py --week [next Monday]
                ├── Query progression_engine for smart weights
                ├── Check mountain activities this week
                ├── If 2+ mountain days → switch to consolidated (A2/B2)
                ├── Update planned_workouts for next week
                └── Push week overview to Google Calendar (gcal.py)

Monday-Friday   Daily cycle (above)
                Jarvis adjusts individual days as needed

Saturday        Mountain day (auto-detected from Garmin)
Sunday          Rest / Opus review (Week 4 and 8)
```

## Adjustment Workflow

When Jarvis needs to adjust a session (snowboarding, fatigue, mountain day):

```
1. Jarvis detects trigger:
   - Mountain activity from Garmin data
   - Low recovery signals (HRV, sleep)
   - User message ("I'm going snowboarding Friday")

2. Jarvis updates planned_workouts in Supabase:
   UPDATE planned_workouts SET
     status = 'adjusted',
     adjustment_reason = 'Snowboarding morning — upper body + core only',
     workout_definition = '{ new exercises... }'::jsonb
   WHERE scheduled_date = '2026-04-04';

3. React app reflects change immediately:
   - Plan tab shows yellow "Adjusted" badge
   - Today tab shows new workout + coach's reason
   - No app deployment needed

4. For consolidated weeks (2+ mountain days):
   - Mark Monday session: status='skipped'
   - Update Wed to A2, Fri to B2
```

## Weight Progression Flow

```
After each workout:
  garmin_sync.py → training_sessions + training_sets (actual weights/reps)

Before next workout:
  progression_engine.py queries training_sets:
    ├── All sets hit target reps AND RPE < 9? → Increase weight
    ├── RPE >= 9 at target reps? → Hold weight
    ├── Stalled 2 weeks? → Hold one more
    ├── Stalled 3 weeks? → Drop 10%, rebuild
    └── Deload week? → Hold weight, halve sets

  Writes decision to exercise_progression table
  workout_generator.py reads → updates workout_definition in planned_workouts
  workout_push.py reads → builds Garmin workout with correct weights
```

## Completion Flow

```
garmin_sync.py runs → populates training_sessions + training_sets
workout_generator.py --mark-completed:
  ├── Match planned_workouts.scheduled_date to training_sessions.date
  ├── Found → status='completed', link garmin_activity_id
  ├── Past + not found → status='skipped'
  └── Compute compliance_score (planned vs actual exercises/weights)
```

---

## Script Responsibilities

| Script | Schedule | Purpose |
|--------|----------|---------|
| `garmin_sync.py` | Daily 09:00 | Pull all Garmin data → Supabase |
| `garmin_session_keepalive.py` | Every 30 min | Keep Garmin auth cookies alive |
| `scale_sync.py` | Daily 10:00 | Pull Xiaomi weight → body_composition |
| `morning_briefing.py` | Daily 10:05 | Recovery check → Slack briefing |
| `workout_generator.py` | Sunday + on demand | Populate/update planned_workouts |
| `workout_push.py` | On demand (Jarvis) | Push workout to Garmin watch |
| `progression_engine.py` | Called by generator/push | Calculate next weights |
| `egym_sync.py` | On demand | Pull eGym body scans |
| `mobility_workout.py` | One-time | Upload Protocol A yoga workout |
| `garmin_auth.py` | Library | Shared Garmin authentication |

## App Views & Data Sources

| Tab | Primary Data Source | Purpose |
|-----|-------------------|---------|
| **Today** | `planned_workouts` + `daily_summary` + `hrv` + `daily_metrics` | Today's workout, recovery signals, coaching verdict |
| **Week** | `activities` + `daily_metrics` + `sleep` | Weekly activity overview |
| **Plan** | `planned_workouts` + `training_sets` + `activities` | 8-week program, lift progression, mountain load |
| **Recovery** | `hrv` + `sleep` + `daily_metrics` + `readiness_composite` | HRV trends, sleep quality, body battery |
| **Trends** | `daily_summary` + `body_composition` + `training_status` | Long-term trends |
| **Goals** | `goals` | Active goal tracking |

---

## Key Files

| Category | File | Purpose |
|----------|------|---------|
| **Plan** | `openclaw/coaching-program.md` | Opus-authored training plan (READ-ONLY) |
| | `openclaw/coaching-context.md` | Coaching state, preferences, exceptions |
| **Scripts** | `scripts/workout_generator.py` | planned_workouts pipeline |
| | `scripts/workout_push.py` | SESSIONS definitions + Garmin push |
| | `scripts/progression_engine.py` | Smart weight progression |
| **Frontend** | `web/src/lib/program.ts` | Date math, week structure |
| | `web/src/lib/types.ts` | Shared TypeScript types |
| | `web/src/hooks/useSupabase.ts` | All data-fetching hooks |
| **Knowledge** | `docs/knowledge-base/domain-*.md` | Evidence base (9 domains) |

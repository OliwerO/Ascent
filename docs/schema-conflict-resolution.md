# Schema Conflict Resolution: Phase 1-2 vs Phase 7-10

> **Date:** 2026-03-30
> **Context:** The training expansion brief (Phases 7-10) proposed 6 new tables,
> but 3 overlap with existing Phase 1-2 tables. This document records the resolution.

## Redundant Tables (NOT created)

### `garmin_auth` → Not needed

The expansion brief proposed storing Garmin credentials in Supabase. However:
- `garmin_sync.py` handles auth via DI OAuth token persistence at `~/.garminconnect/`
- Tokens auto-refresh indefinitely (garth deprecated March 2026, replaced by garminconnect 0.3+)
- Storing passwords in a database (even "encrypted at rest") adds attack surface for no benefit
- Re-auth failure already triggers a logged warning; Phase 10 will add Telegram alerting

### `garmin_activities` → Already covered by `activities` + `activity_details`

| Proposed column | Already exists in |
|---|---|
| `garmin_activity_id` | `activities.garmin_activity_id` |
| `activity_type`, `started_at`, `duration_seconds` | `activities.*` |
| `distance_meters`, `elevation_gain_meters` | `activities.distance_meters`, `activities.elevation_gain` |
| `avg_hr`, `max_hr`, `calories` | `activities.*` |
| `training_effect`, `anaerobic_effect` | `activities.training_effect_aerobic`, `activities.training_effect_anaerobic` |
| `hr_zones`, `laps` | `activity_details.hr_zones`, `activity_details.splits` |
| `gps_summary` | Could be added to `activity_details` if needed (JSONB `raw_json` already stores it) |

### `garmin_daily_metrics` → Already covered by `daily_metrics` + `sleep` + `hrv`

| Proposed column | Already exists in |
|---|---|
| `hrv_status`, `hrv_value` | `hrv.status`, `hrv.weekly_avg` |
| `body_battery_morning`, `body_battery_evening` | `daily_metrics.body_battery_highest`, `body_battery_events.timeline` |
| `sleep_score`, `sleep_duration_seconds` | `sleep.overall_score`, `sleep.total_sleep_seconds` |
| `stress_avg` | `daily_metrics.avg_stress_level` |
| `resting_hr` | `daily_metrics.resting_hr` |

## `user_id` Columns — Dropped

All Phase 7-10 tables referenced `users(id)`, but:
- Ascent is explicitly a **single-user system** (Oliwer's personal health intelligence)
- No `users` table exists in the schema
- Adding multi-user support would require rethinking RLS, auth, and data isolation — not in scope

## Tables Created (genuinely new)

### `planned_workouts` (in `006_training_expansion.sql`)
- Workout planning, Garmin push tracking, Calendar sync, compliance scoring
- FK to `activities.garmin_activity_id` (TEXT) — matches existing schema
- No `user_id`

### `exercise_progression` (in `006_training_expansion.sql`)
- Planned vs actual tracking per exercise per day
- Progression decision logging (`weight_increase`, `hold`, `deload`, etc.)
- Complements `training_sets` (raw per-set data) — different abstraction level

## Impact on Scripts

| Script | Status | Notes |
|---|---|---|
| `garmin_sync.py` | **Already complete** — IS Phase 7a | Pulls all 11 data types, upserts to existing tables |
| `garmin_workout_push.py` | Needs creation | Blocked on Garmin Auth Spike (push API validation) |
| `workout_generator.py` | Needs creation | Blocked on Phase 6 (Opus plan in coaching-context.md) |

## Impact on `garmin_sync.py`

No changes needed. The script already writes to:
- `daily_metrics` (covers `garmin_daily_metrics`)
- `activities` + `activity_details` (covers `garmin_activities`)
- `sleep`, `hrv`, `body_composition`, `heart_rate_series`, `stress_series`
- `training_status`, `performance_scores`, `body_battery_events`, `personal_records`

Phase 8's `workout_generator.py` will read from these same tables.

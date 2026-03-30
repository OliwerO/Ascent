-- =============================================
-- Phase 8: Training Expansion Tables
-- Adds workout planning and exercise progression tracking
--
-- NOTE: Phase 7-10 originally proposed garmin_auth, garmin_activities,
-- and garmin_daily_metrics tables, but these are redundant:
--   - garmin_auth → auth handled by garth tokens on filesystem (~/.garth/)
--   - garmin_activities → covered by existing activities + activity_details
--   - garmin_daily_metrics → covered by daily_metrics + sleep + hrv
-- See docs/schema-conflict-resolution.md for full rationale.
--
-- Ascent is a single-user system — no users table or user_id columns.
-- =============================================

-- =============================================
-- PLANNED WORKOUTS
-- Generated weekly by workout_generator.py, pushed to Garmin + Calendar
-- =============================================

CREATE TABLE IF NOT EXISTS planned_workouts (
  id BIGSERIAL PRIMARY KEY,
  training_block TEXT NOT NULL,                -- e.g. 'Hypertrophy Block 2'
  week_number INTEGER NOT NULL,
  session_name TEXT NOT NULL,                  -- e.g. 'Upper Body A'
  session_type TEXT NOT NULL,                  -- 'strength', 'cardio_touring', 'mobility'
  scheduled_date DATE NOT NULL,
  scheduled_time TIME,
  estimated_duration_minutes INTEGER,
  workout_definition JSONB NOT NULL,           -- full exercise list with targets
  garmin_workout_id TEXT,                      -- returned after Garmin push
  calendar_event_id TEXT,                      -- Google Calendar event ID
  status TEXT DEFAULT 'planned',               -- 'planned', 'adjusted', 'completed', 'skipped'
  actual_garmin_activity_id TEXT               -- links to activities.garmin_activity_id
    REFERENCES activities(garmin_activity_id),
  compliance_score REAL,                       -- 0-1, how closely athlete followed plan
  adjustment_reason TEXT,                      -- if status='adjusted', why
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- EXERCISE PROGRESSION
-- Tracks planned vs actual performance + progression decisions
-- Complements training_sets (raw per-set data) with planning layer
-- =============================================

CREATE TABLE IF NOT EXISTS exercise_progression (
  id BIGSERIAL PRIMARY KEY,
  exercise_name TEXT NOT NULL,
  date DATE NOT NULL,
  planned_sets INTEGER,
  planned_reps INTEGER,
  planned_weight_kg REAL,
  planned_rpe REAL,
  actual_sets INTEGER,
  actual_reps_per_set JSONB,                   -- e.g. [8, 8, 7, 6]
  actual_weight_kg REAL,
  actual_rpe REAL,
  progression_applied TEXT,                    -- 'weight_increase', 'rep_increase', 'hold', 'deload'
  progression_amount REAL,                     -- e.g. 2.5 (kg added)
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(exercise_name, date)
);

-- =============================================
-- INDEXES
-- =============================================

CREATE INDEX IF NOT EXISTS idx_planned_workouts_date ON planned_workouts(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_planned_workouts_status ON planned_workouts(status);
CREATE INDEX IF NOT EXISTS idx_planned_workouts_block ON planned_workouts(training_block, week_number);
CREATE INDEX IF NOT EXISTS idx_planned_workouts_garmin ON planned_workouts(garmin_workout_id);
CREATE INDEX IF NOT EXISTS idx_exercise_progression_name ON exercise_progression(exercise_name);
CREATE INDEX IF NOT EXISTS idx_exercise_progression_date ON exercise_progression(date);

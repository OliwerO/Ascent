-- =============================================
-- Phase 2 Addendum: Additional Garmin data tables
-- Run after 001_schema.sql
-- =============================================

-- Training status: acute/chronic load, productive/detraining labels
CREATE TABLE IF NOT EXISTS training_status (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  training_status TEXT,              -- 'PRODUCTIVE', 'RECOVERY', 'PEAKING', 'DETRAINING', 'OVERREACHING', etc.
  training_load_7d REAL,             -- acute load (7-day)
  training_load_28d REAL,            -- chronic load (28-day)
  training_load_balance REAL,        -- load ratio
  vo2max_running REAL,
  vo2max_cycling REAL,
  raw_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance scores (endurance, hill) — time-series per day
CREATE TABLE IF NOT EXISTS performance_scores (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  endurance_score REAL,
  hill_score REAL,
  race_prediction_5k_seconds REAL,
  race_prediction_10k_seconds REAL,
  race_prediction_half_seconds REAL,
  race_prediction_marathon_seconds REAL,
  fitness_age REAL,
  raw_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Body battery time-series + events
CREATE TABLE IF NOT EXISTS body_battery_events (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  timeline JSONB,                    -- full body battery curve
  events JSONB,                      -- events that caused charge/drain
  raw_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Activity detail enrichments (HR zones, splits, weather)
CREATE TABLE IF NOT EXISTS activity_details (
  id BIGSERIAL PRIMARY KEY,
  garmin_activity_id TEXT UNIQUE NOT NULL,
  hr_zones JSONB,                    -- time in each HR zone
  splits JSONB,                      -- lap/split data
  weather JSONB,                     -- weather during activity
  raw_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Personal records from Garmin
CREATE TABLE IF NOT EXISTS personal_records (
  id BIGSERIAL PRIMARY KEY,
  record_type TEXT NOT NULL,
  value REAL,
  activity_id TEXT,
  recorded_at DATE,
  display_value TEXT,
  raw_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(record_type, recorded_at)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_training_status_date ON training_status(date);
CREATE INDEX IF NOT EXISTS idx_performance_scores_date ON performance_scores(date);
CREATE INDEX IF NOT EXISTS idx_body_battery_events_date ON body_battery_events(date);
CREATE INDEX IF NOT EXISTS idx_activity_details_garmin_id ON activity_details(garmin_activity_id);
CREATE INDEX IF NOT EXISTS idx_personal_records_type ON personal_records(record_type);

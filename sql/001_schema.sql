-- =============================================
-- ASCENT: Full Database Schema
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New Query)
-- =============================================

-- =============================================
-- GARMIN DAILY METRICS
-- =============================================

CREATE TABLE IF NOT EXISTS daily_metrics (
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

CREATE TABLE IF NOT EXISTS sleep (
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

CREATE TABLE IF NOT EXISTS hrv (
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

CREATE TABLE IF NOT EXISTS body_composition (
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

CREATE TABLE IF NOT EXISTS activities (
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

CREATE TABLE IF NOT EXISTS heart_rate_series (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  readings JSONB,
  resting_hr INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stress_series (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  readings JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- FOOD LOGGING
-- =============================================

CREATE TABLE IF NOT EXISTS foods (
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

CREATE TABLE IF NOT EXISTS food_log (
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

CREATE TABLE IF NOT EXISTS meal_templates (
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

CREATE TABLE IF NOT EXISTS exercises (
  id BIGSERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  category TEXT,
  muscle_groups JSONB,
  equipment TEXT,
  is_compound BOOLEAN DEFAULT FALSE,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS training_sessions (
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

CREATE TABLE IF NOT EXISTS training_sets (
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

CREATE TABLE IF NOT EXISTS exercise_prs (
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

CREATE TABLE IF NOT EXISTS blood_test_panels (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  lab_name TEXT,
  fasting BOOLEAN,
  notes TEXT,
  pdf_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS blood_test_results (
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

CREATE TABLE IF NOT EXISTS biomarker_definitions (
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

CREATE TABLE IF NOT EXISTS goals (
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

CREATE TABLE IF NOT EXISTS coaching_log (
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

CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date);
CREATE INDEX IF NOT EXISTS idx_sleep_date ON sleep(date);
CREATE INDEX IF NOT EXISTS idx_hrv_date ON hrv(date);
CREATE INDEX IF NOT EXISTS idx_body_comp_date ON body_composition(date);
CREATE INDEX IF NOT EXISTS idx_activities_date ON activities(date);
CREATE INDEX IF NOT EXISTS idx_activities_type ON activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_food_log_date ON food_log(date);
CREATE INDEX IF NOT EXISTS idx_food_log_meal ON food_log(date, meal_type);
CREATE INDEX IF NOT EXISTS idx_training_sessions_date ON training_sessions(date);
CREATE INDEX IF NOT EXISTS idx_training_sets_session ON training_sets(session_id);
CREATE INDEX IF NOT EXISTS idx_training_sets_exercise ON training_sets(exercise_id);
CREATE INDEX IF NOT EXISTS idx_blood_results_panel ON blood_test_results(panel_id);
CREATE INDEX IF NOT EXISTS idx_blood_results_biomarker ON blood_test_results(biomarker);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
CREATE INDEX IF NOT EXISTS idx_coaching_log_date ON coaching_log(date);
CREATE INDEX IF NOT EXISTS idx_coaching_log_type ON coaching_log(type);

-- =============================================
-- USEFUL VIEWS
-- =============================================

CREATE OR REPLACE VIEW daily_summary AS
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

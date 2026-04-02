-- Migration 009: Research Integration Tables
-- Date: 2026-04-02
-- Purpose: Add tables from evidence-based implementation guide findings
-- Dependencies: None (new tables only)

-- =============================================
-- SUBJECTIVE WELLNESS DAILY QUESTIONNAIRE
-- =============================================
-- Highest-evidence unbuilt feature per research findings.
-- 5 items (1-5 scale), all oriented so 5 = best.
-- Composite is simple average since all scales point same direction.

CREATE TABLE IF NOT EXISTS subjective_wellness (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  sleep_quality INTEGER CHECK (sleep_quality BETWEEN 1 AND 5),
  energy INTEGER CHECK (energy BETWEEN 1 AND 5),
  muscle_soreness INTEGER CHECK (muscle_soreness BETWEEN 1 AND 5),
  motivation INTEGER CHECK (motivation BETWEEN 1 AND 5),
  stress INTEGER CHECK (stress BETWEEN 1 AND 5),
  composite_score REAL GENERATED ALWAYS AS (
    (sleep_quality + energy + muscle_soreness + motivation + stress) / 5.0
  ) STORED,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- DATA QUALITY TRACKING PER DAY
-- =============================================
-- Tracks wearable data completeness for gap-aware calculations.
-- is_valid_day requires >= 10 hours of wear time.

CREATE TABLE IF NOT EXISTS daily_data_quality (
  id BIGSERIAL PRIMARY KEY,
  date DATE UNIQUE NOT NULL,
  wear_hours REAL,
  completeness_score REAL,
  max_gap_minutes INTEGER,
  is_valid_day BOOLEAN GENERATED ALWAYS AS (wear_hours >= 10) STORED,
  data_issues JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- DEVICE/ALGORITHM EPOCH TRACKING
-- =============================================
-- When device changes, firmware updates, or algorithm shifts occur,
-- baselines must reset to prevent spurious drift signals.

CREATE TABLE IF NOT EXISTS data_epochs (
  id BIGSERIAL PRIMARY KEY,
  start_date DATE NOT NULL,
  device_model TEXT,
  firmware_version TEXT,
  trigger_type TEXT NOT NULL, -- 'device_change', 'firmware_update', 'algorithm_shift', 'manual'
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- ADD sRPE COLUMNS TO TRAINING_SESSIONS
-- =============================================
-- Session RPE (CR-10 scale) x duration = session load.
-- Unified training load metric across all modalities.

ALTER TABLE training_sessions ADD COLUMN IF NOT EXISTS srpe INTEGER;
ALTER TABLE training_sessions ADD COLUMN IF NOT EXISTS srpe_load REAL
  GENERATED ALWAYS AS (srpe * duration_minutes) STORED;

-- =============================================
-- INDEXES
-- =============================================

CREATE INDEX IF NOT EXISTS idx_subjective_wellness_date ON subjective_wellness(date);
CREATE INDEX IF NOT EXISTS idx_daily_data_quality_date ON daily_data_quality(date);
CREATE INDEX IF NOT EXISTS idx_daily_data_quality_valid ON daily_data_quality(is_valid_day);
CREATE INDEX IF NOT EXISTS idx_data_epochs_date ON data_epochs(start_date);

-- =============================================
-- VIEW: Daily readiness composite
-- =============================================
-- Joins all readiness signals using date spine for gap-aware calculations.

CREATE OR REPLACE VIEW readiness_composite AS
SELECT
  ds.date,
  h.last_night_avg AS hrv_value,
  h.status AS hrv_status,
  AVG(h.last_night_avg) OVER (ORDER BY ds.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS hrv_7d_avg,
  AVG(h.last_night_avg) OVER (ORDER BY ds.date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS hrv_60d_mean,
  STDDEV(h.last_night_avg) OVER (ORDER BY ds.date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS hrv_60d_sd,
  s.total_sleep_seconds / 3600.0 AS sleep_hours,
  AVG(s.total_sleep_seconds / 3600.0) OVER (ORDER BY ds.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS sleep_7d_avg,
  dm.resting_hr,
  AVG(dm.resting_hr) OVER (ORDER BY ds.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rhr_7d_avg,
  AVG(dm.resting_hr) OVER (ORDER BY ds.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS rhr_30d_mean,
  sw.composite_score AS wellness_score,
  dm.body_battery_highest AS body_battery,
  dm.training_readiness_score AS garmin_readiness,
  dq.is_valid_day
FROM generate_series(
  CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE, '1 day'::interval
) AS ds(date)
LEFT JOIN hrv h ON ds.date = h.date
LEFT JOIN sleep s ON ds.date = s.date
LEFT JOIN daily_metrics dm ON ds.date = dm.date
LEFT JOIN subjective_wellness sw ON ds.date = sw.date
LEFT JOIN daily_data_quality dq ON ds.date = dq.date
ORDER BY ds.date;

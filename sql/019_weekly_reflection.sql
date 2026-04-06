-- =============================================
-- 019: Weekly Reflection + Recomp Tracking
--
-- Adds:
-- 1. weekly_reflections — Sunday structured reflection input
-- 2. recomp_tracking — body recomposition analysis view
--    (7-day smoothed weight, BF%, lean mass, classification)
-- =============================================

-- =============================================
-- WEEKLY REFLECTIONS
-- Captured via React app on Sundays. Short structured input
-- that feeds into weekly review context.
-- =============================================

CREATE TABLE IF NOT EXISTS weekly_reflections (
  id BIGSERIAL PRIMARY KEY,
  week_start DATE NOT NULL UNIQUE,
  energy_trend TEXT CHECK (energy_trend IN ('improving', 'stable', 'declining')),
  training_satisfaction INTEGER CHECK (training_satisfaction BETWEEN 1 AND 5),
  top_highlight TEXT,
  biggest_challenge TEXT,
  next_week_focus TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weekly_reflections_week ON weekly_reflections(week_start);

-- RLS
ALTER TABLE weekly_reflections ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_read" ON weekly_reflections FOR SELECT TO anon USING (true);
CREATE POLICY "anon_insert" ON weekly_reflections FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "anon_update" ON weekly_reflections FOR UPDATE TO anon USING (true);
CREATE POLICY "service_all" ON weekly_reflections FOR ALL TO service_role USING (true);

-- =============================================
-- RECOMP TRACKING VIEW
-- 7-day smoothed weight and body composition trends.
-- Uses generate_series date spine for gap-aware calculations.
-- =============================================

CREATE OR REPLACE VIEW recomp_tracking AS
WITH
  date_range AS (
    SELECT generate_series(
      CURRENT_DATE - 90,
      CURRENT_DATE,
      '1 day'::interval
    )::date AS d
  ),
  -- Latest body comp per day (prefer scale source, fall back to garmin)
  daily_bc AS (
    SELECT DISTINCT ON (dr.d)
      dr.d AS date,
      bc.weight_kg,
      bc.body_fat_pct,
      bc.muscle_mass_grams,
      bc.source
    FROM date_range dr
    LEFT JOIN body_composition bc ON bc.date = dr.d
    ORDER BY dr.d, bc.source DESC  -- 'scale' > 'garmin' alphabetically
  ),
  -- Forward-fill weights for smoothing (carry last known value)
  filled AS (
    SELECT
      date,
      COALESCE(
        weight_kg,
        LAG(weight_kg) OVER (ORDER BY date),
        LEAD(weight_kg) OVER (ORDER BY date)
      ) AS weight_kg,
      body_fat_pct,
      muscle_mass_grams
    FROM daily_bc
  ),
  -- 7-day rolling averages
  smoothed AS (
    SELECT
      date,
      weight_kg AS raw_weight_kg,
      ROUND(AVG(weight_kg) OVER (
        ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
      )::numeric, 2) AS smoothed_weight_kg,
      body_fat_pct,
      muscle_mass_grams,
      -- Estimated lean mass (from body fat %)
      CASE WHEN weight_kg IS NOT NULL AND body_fat_pct IS NOT NULL
        THEN ROUND((weight_kg * (1 - body_fat_pct / 100.0))::numeric, 2)
        ELSE NULL
      END AS estimated_lean_mass_kg
    FROM filled
  ),
  -- Week-over-week deltas
  weekly AS (
    SELECT
      date,
      raw_weight_kg,
      smoothed_weight_kg,
      body_fat_pct,
      muscle_mass_grams,
      estimated_lean_mass_kg,
      smoothed_weight_kg - LAG(smoothed_weight_kg, 7) OVER (ORDER BY date) AS weight_delta_7d,
      body_fat_pct - LAG(body_fat_pct, 7) OVER (ORDER BY date) AS bf_delta_7d,
      estimated_lean_mass_kg - LAG(estimated_lean_mass_kg, 7) OVER (ORDER BY date) AS lean_mass_delta_7d
    FROM smoothed
  )
SELECT
  date,
  raw_weight_kg,
  smoothed_weight_kg,
  body_fat_pct,
  estimated_lean_mass_kg,
  ROUND(weight_delta_7d::numeric, 2) AS weight_change_7d_kg,
  ROUND(bf_delta_7d::numeric, 1) AS bf_change_7d_pct,
  ROUND(lean_mass_delta_7d::numeric, 2) AS lean_mass_change_7d_kg,
  -- Rate per week (using 30-day window)
  ROUND((
    smoothed_weight_kg - LAG(smoothed_weight_kg, 30) OVER (ORDER BY date)
  )::numeric / 4.3, 2) AS weight_rate_per_week,
  -- Classification
  CASE
    WHEN weight_delta_7d IS NULL OR bf_delta_7d IS NULL THEN 'insufficient_data'
    WHEN weight_delta_7d > 0.2 AND bf_delta_7d < -0.2 THEN 'recomp'
    WHEN weight_delta_7d < -0.3 THEN 'cutting'
    WHEN weight_delta_7d > 0.3 THEN 'gaining'
    ELSE 'maintaining'
  END AS phase_classification
FROM weekly
WHERE date >= CURRENT_DATE - 90
ORDER BY date DESC;

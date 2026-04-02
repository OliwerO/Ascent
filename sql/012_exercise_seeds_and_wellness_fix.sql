-- Migration 012: Add missing exercise seeds + fix composite_score NULL handling

-- Missing exercises referenced by workout_push.py via NAME_ALIASES
INSERT INTO exercises (name, category, muscle_groups, equipment, is_compound, notes) VALUES
  ('Kettlebell Swing', 'back', '["glutes","hamstrings","lower_back"]', 'kettlebell', true, 'Explosive hip extension'),
  ('Kettlebell Halo', 'shoulders', '["shoulders","core"]', 'kettlebell', false, 'Rotational shoulder mobility and stability')
ON CONFLICT (name) DO NOTHING;

-- Fix composite_score: only compute when all 5 fields are present
-- This allows partial saves but composite_score stays NULL until complete
-- Must drop dependent view first, then recreate

DROP VIEW IF EXISTS readiness_composite;

ALTER TABLE subjective_wellness
  DROP COLUMN IF EXISTS composite_score;

ALTER TABLE subjective_wellness
  ADD COLUMN composite_score REAL GENERATED ALWAYS AS (
    CASE WHEN sleep_quality IS NOT NULL
          AND energy IS NOT NULL
          AND muscle_soreness IS NOT NULL
          AND motivation IS NOT NULL
          AND stress IS NOT NULL
    THEN (sleep_quality + energy + muscle_soreness + motivation + stress) / 5.0
    ELSE NULL
    END
  ) STORED;

-- Recreate readiness_composite view
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

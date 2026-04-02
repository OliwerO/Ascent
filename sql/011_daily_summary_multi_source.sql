-- Migration 011: Update daily_summary view to show weight from any source
-- Priority: xiaomi (daily scale) > egym (gym scan) > garmin
-- Also adds RLS policies for tables from migration 009

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
  bc.muscle_mass_grams,
  bc.source AS weight_source
FROM daily_metrics dm
LEFT JOIN sleep s ON dm.date = s.date
LEFT JOIN hrv h ON dm.date = h.date
LEFT JOIN LATERAL (
  SELECT weight_kg, body_fat_pct, muscle_mass_grams, source
  FROM body_composition
  WHERE date = dm.date
  ORDER BY CASE source
    WHEN 'xiaomi' THEN 1
    WHEN 'egym' THEN 2
    WHEN 'garmin' THEN 3
    ELSE 4
  END
  LIMIT 1
) bc ON true;

-- RLS policies for migration 009 tables
ALTER TABLE subjective_wellness ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_data_quality ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_epochs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_read" ON subjective_wellness FOR SELECT TO anon USING (true);
CREATE POLICY "anon_write" ON subjective_wellness FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "anon_update" ON subjective_wellness FOR UPDATE TO anon USING (true) WITH CHECK (true);

CREATE POLICY "anon_read" ON daily_data_quality FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON data_epochs FOR SELECT TO anon USING (true);

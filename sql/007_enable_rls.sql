-- =============================================
-- Enable Row-Level Security on all tables
-- Single-user system: anon key = read-only, service role = full access
-- =============================================

-- Garmin auto-sync tables (read-only for dashboard)
ALTER TABLE daily_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE sleep ENABLE ROW LEVEL SECURITY;
ALTER TABLE hrv ENABLE ROW LEVEL SECURITY;
ALTER TABLE body_composition ENABLE ROW LEVEL SECURITY;
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE heart_rate_series ENABLE ROW LEVEL SECURITY;
ALTER TABLE stress_series ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE body_battery_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE personal_records ENABLE ROW LEVEL SECURITY;

-- Training tables
ALTER TABLE exercises ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE exercise_prs ENABLE ROW LEVEL SECURITY;
ALTER TABLE planned_workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE exercise_progression ENABLE ROW LEVEL SECURITY;

-- Food tables
ALTER TABLE foods ENABLE ROW LEVEL SECURITY;
ALTER TABLE food_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE meal_templates ENABLE ROW LEVEL SECURITY;

-- Health analytics
ALTER TABLE blood_test_panels ENABLE ROW LEVEL SECURITY;
ALTER TABLE blood_test_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE biomarker_definitions ENABLE ROW LEVEL SECURITY;

-- Coaching & goals
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE coaching_log ENABLE ROW LEVEL SECURITY;

-- =============================================
-- Read-only policies for anon role (React dashboard)
-- =============================================

CREATE POLICY "anon_read" ON daily_metrics FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON sleep FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON hrv FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON body_composition FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON activities FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON heart_rate_series FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON stress_series FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON training_status FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON performance_scores FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON body_battery_events FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON activity_details FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON personal_records FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON exercises FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON training_sessions FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON training_sets FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON exercise_prs FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON planned_workouts FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON exercise_progression FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON foods FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON food_log FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON meal_templates FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON blood_test_panels FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON blood_test_results FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON biomarker_definitions FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON goals FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read" ON coaching_log FOR SELECT TO anon USING (true);

-- =============================================
-- Full access for service_role (Python scripts, Claude Code)
-- service_role bypasses RLS by default in Supabase,
-- but adding explicit policies for clarity
-- =============================================

-- Note: In Supabase, the service_role key bypasses RLS automatically.
-- No explicit policies needed for service_role.
-- The anon key is now restricted to SELECT only.

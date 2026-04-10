-- Allow the React app (anon role) to update planned_workouts
-- for reschedule and home/gym switching
CREATE POLICY "anon_update" ON planned_workouts
  FOR UPDATE TO anon
  USING (true)
  WITH CHECK (true);

-- Allow the React app to insert coaching_log entries
-- for home/gym switching and reschedule logging
CREATE POLICY "anon_insert" ON coaching_log
  FOR INSERT TO anon
  WITH CHECK (true);

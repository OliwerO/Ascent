-- Tighten RLS policies from 029_app_write_policies.sql
--
-- The original policies used USING (true) WITH CHECK (true) which is acceptable
-- for a single-user app, but lacked explicit service_role policies and did not
-- guard against accidental DELETE via anon.
--
-- Changes:
--   1. Re-create planned_workouts anon_update with a status guard:
--      anon can only update rows that are NOT already 'completed'
--   2. Add explicit service_role full-access policies for planned_workouts
--      and coaching_log (service_role bypasses RLS by default in Supabase,
--      but explicit policies document intent)
--   3. Confirm no anon DELETE policy exists (none created = none allowed)

-- planned_workouts: tighten anon_update to prevent modifying completed workouts
DROP POLICY IF EXISTS "anon_update" ON planned_workouts;
CREATE POLICY "anon_update" ON planned_workouts
  FOR UPDATE TO anon
  USING (status IS DISTINCT FROM 'completed')
  WITH CHECK (true);

-- planned_workouts: explicit service_role policy (documents intent)
DROP POLICY IF EXISTS "service_all" ON planned_workouts;
CREATE POLICY "service_all" ON planned_workouts
  FOR ALL TO service_role
  USING (true);

-- coaching_log: re-create anon_insert with channel guard
-- App inserts must identify themselves as channel = 'app'
DROP POLICY IF EXISTS "anon_insert" ON coaching_log;
CREATE POLICY "anon_insert" ON coaching_log
  FOR INSERT TO anon
  WITH CHECK (channel = 'app');

-- coaching_log: explicit service_role policy (documents intent)
DROP POLICY IF EXISTS "service_all" ON coaching_log;
CREATE POLICY "service_all" ON coaching_log
  FOR ALL TO service_role
  USING (true);

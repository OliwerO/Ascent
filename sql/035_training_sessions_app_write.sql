-- =============================================
-- 035_training_sessions_app_write.sql
-- =============================================
-- Allow the React app (anon role) to insert and update training_sessions.
-- Needed for the mark-as-done flow which upserts a training_sessions row
-- with the sRPE value, and for the existing RPEPrompt component.
-- =============================================

CREATE POLICY "anon_insert" ON training_sessions
  FOR INSERT TO anon
  WITH CHECK (true);

CREATE POLICY "anon_update" ON training_sessions
  FOR UPDATE TO anon
  USING (true)
  WITH CHECK (true);

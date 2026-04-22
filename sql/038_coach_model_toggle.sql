-- =============================================
-- 038_coach_model_toggle.sql
-- =============================================
-- Add model preference to coach conversations so the user can choose
-- between Opus (powerful, heavier on Max quota) and Sonnet (fast, lighter)
-- from the Coach tab UI.
-- =============================================

ALTER TABLE coach_conversations ADD COLUMN IF NOT EXISTS model TEXT NOT NULL DEFAULT 'opus';

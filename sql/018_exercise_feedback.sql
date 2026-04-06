-- =============================================
-- 018: Exercise-Level Feedback
--
-- Adds per-exercise subjective feel tracking (light/right/heavy).
-- This data feeds into:
-- 1. progression_engine.py — hold weight on consecutive "heavy" ratings
-- 2. interference_analysis.py — "heavy" ratings after mountain days
--    increase interference pattern confidence
-- 3. Weekly review — summarize feel distribution
-- =============================================

-- =============================================
-- EXERCISE FEEDBACK TABLE
-- Per-exercise feel rating after each gym session.
-- =============================================

CREATE TABLE IF NOT EXISTS exercise_feedback (
  id BIGSERIAL PRIMARY KEY,
  session_date DATE NOT NULL,
  exercise_name TEXT NOT NULL,
  feel TEXT NOT NULL CHECK (feel IN ('light', 'right', 'heavy')),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(session_date, exercise_name)
);

CREATE INDEX IF NOT EXISTS idx_exercise_feedback_date ON exercise_feedback(session_date);
CREATE INDEX IF NOT EXISTS idx_exercise_feedback_exercise ON exercise_feedback(exercise_name);

-- RLS
ALTER TABLE exercise_feedback ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_read" ON exercise_feedback FOR SELECT TO anon USING (true);
CREATE POLICY "anon_insert" ON exercise_feedback FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "service_all" ON exercise_feedback FOR ALL TO service_role USING (true);

-- =============================================
-- Add athlete_feel column to exercise_progression
-- Links the subjective feel to the planned progression entry
-- =============================================

ALTER TABLE exercise_progression ADD COLUMN IF NOT EXISTS athlete_feel TEXT;

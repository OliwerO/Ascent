-- =============================================
-- 007: planned_workouts observability + non-strength day support
--
-- Context: 2026-04-07 audit found the health-coach skill silently no-ops
-- on mid-week adjustments. Fix is a single coach_adjust.py write path that
-- needs (a) an updated_at column to detect mutations vs creations, and
-- (b) the freedom to write non-strength rows (rest, mountain tours,
-- cross-training) so the table is the single source of truth for the
-- React app's training plan display.
--
-- See: project_coach_write_path_broken.md
-- =============================================

-- 1. updated_at column with auto-bump trigger
ALTER TABLE planned_workouts
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS planned_workouts_set_updated_at ON planned_workouts;
CREATE TRIGGER planned_workouts_set_updated_at
  BEFORE UPDATE ON planned_workouts
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 2. Backfill existing rows so updated_at is non-null and equals created_at
UPDATE planned_workouts SET updated_at = created_at WHERE updated_at IS NULL;

-- 3. Index for "what changed since X" queries (daily briefing, audits)
CREATE INDEX IF NOT EXISTS idx_planned_workouts_updated_at
  ON planned_workouts(updated_at DESC);

-- 4. session_type vocabulary expansion is enforced in coach_adjust.py,
--    not via CHECK constraint. Documented values:
--      'strength'        — gym session (existing)
--      'cardio_touring'  — planned ski/touring (existing)
--      'mobility'        — light recovery (existing)
--      'rest'            — explicit rest day, no activity expected (NEW)
--      'mountain_tour'   — mountain day, leg-loaded (NEW)
--      'cross_training'  — easy non-mountain cardio (NEW)

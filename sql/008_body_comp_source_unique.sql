-- =============================================
-- Add unique constraint on (date, source) for body_composition
-- Allows multiple sources (garmin, egym) per date
-- =============================================

-- Drop old unique constraint on date alone (if it exists)
ALTER TABLE body_composition DROP CONSTRAINT IF EXISTS body_composition_date_key;
DROP INDEX IF EXISTS body_composition_date_key;

-- Add composite unique constraint
ALTER TABLE body_composition
  ADD CONSTRAINT body_composition_date_source_key UNIQUE (date, source);

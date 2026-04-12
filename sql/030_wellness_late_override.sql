-- =============================================
-- 030_wellness_late_override.sql
-- =============================================
-- Handles the timing gap where wellness is logged AFTER the 09:43 daily
-- coaching decision has already run. When a critically low wellness
-- composite arrives and today's session is still planned/pushed, this
-- trigger updates the session's adjustment_reason and logs the override.
--
-- Threshold: composite_score <= 2.0 (stricter than the view's 2.5 hard_override
-- because we're overriding an already-made coaching decision — only fire on
-- clearly bad wellness, not borderline).
--
-- This adds a writer to planned_workouts beyond coach_adjust.py. This is
-- intentional and narrowly scoped. Chapter 9 will add DB-level status
-- transition constraints that govern all writers including this trigger.
-- =============================================

CREATE OR REPLACE FUNCTION fn_wellness_late_override()
RETURNS TRIGGER AS $$
DECLARE
  v_workout_id BIGINT;
  v_current_reason TEXT;
BEGIN
  -- Only act on critically low wellness
  IF NEW.composite_score IS NULL OR NEW.composite_score > 2.0 THEN
    RETURN NEW;
  END IF;

  -- Find today's planned/pushed workout
  SELECT id, adjustment_reason
    INTO v_workout_id, v_current_reason
    FROM planned_workouts
   WHERE scheduled_date = NEW.date
     AND status IN ('planned', 'pushed')
   LIMIT 1;

  -- No actionable workout today
  IF v_workout_id IS NULL THEN
    RETURN NEW;
  END IF;

  -- Update the workout with wellness override
  UPDATE planned_workouts
     SET status = 'adjusted',
         adjustment_reason = COALESCE(v_current_reason || ' | ', '')
           || 'Wellness override: composite ' || ROUND(NEW.composite_score::numeric, 1)
           || ' — consider rest or light movement'
   WHERE id = v_workout_id;

  -- Log the override
  INSERT INTO coaching_log (date, type, channel, message, decision_type, rule, inputs)
  VALUES (
    NEW.date,
    'adjustment',
    'wellness_trigger',
    'Late wellness override: composite ' || ROUND(NEW.composite_score::numeric, 1)
      || ' flagged critically low after coaching decision',
    'adjust',
    'wellness.late_arrival.critical_low',
    jsonb_build_object(
      'composite_score', NEW.composite_score,
      'sleep_quality', NEW.sleep_quality,
      'energy', NEW.energy,
      'muscle_soreness', NEW.muscle_soreness,
      'motivation', NEW.motivation,
      'stress', NEW.stress,
      'trigger', 'fn_wellness_late_override'
    )
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Fire after insert (new wellness entry) or update (user corrects their scores)
DROP TRIGGER IF EXISTS trg_wellness_late_override ON subjective_wellness;
CREATE TRIGGER trg_wellness_late_override
  AFTER INSERT OR UPDATE ON subjective_wellness
  FOR EACH ROW
  EXECUTE FUNCTION fn_wellness_late_override();

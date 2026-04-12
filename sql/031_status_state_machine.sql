-- =============================================
-- 031_status_state_machine.sql
-- =============================================
-- Enforces a state machine on planned_workouts.status. Any UPDATE that
-- attempts an invalid transition is rejected with a descriptive error.
--
-- Valid transitions:
--   planned  → pushed, adjusted, skipped, completed
--   pushed   → adjusted, completed, skipped, pushed (re-push)
--   adjusted → pushed, adjusted (re-adjust), completed, skipped
--   skipped  → planned (reschedule back)
--   completed → (terminal — no status changes allowed)
--
-- Non-status UPDATEs (e.g. updating workout_definition or garmin_workout_id
-- without changing status) are always allowed.
--
-- Logs rejected transitions to coaching_log for debugging.
-- =============================================

CREATE OR REPLACE FUNCTION fn_planned_workouts_status_guard()
RETURNS TRIGGER AS $$
BEGIN
  -- Allow if status hasn't changed
  IF OLD.status = NEW.status THEN
    RETURN NEW;
  END IF;

  -- Define the state machine
  IF (OLD.status, NEW.status) IN (
    -- From planned
    ('planned', 'pushed'),
    ('planned', 'adjusted'),
    ('planned', 'skipped'),
    ('planned', 'completed'),
    -- From pushed
    ('pushed', 'adjusted'),
    ('pushed', 'completed'),
    ('pushed', 'skipped'),
    ('pushed', 'pushed'),       -- re-push (updated workout)
    -- From adjusted
    ('adjusted', 'pushed'),
    ('adjusted', 'adjusted'),   -- re-adjust (wellness override on top of coach adjust)
    ('adjusted', 'completed'),
    ('adjusted', 'skipped'),
    -- From skipped (reschedule only)
    ('skipped', 'planned')
  ) THEN
    RETURN NEW;
  END IF;

  -- Rejected — log for debugging
  INSERT INTO coaching_log (date, type, channel, message, decision_type, inputs)
  VALUES (
    NEW.scheduled_date,
    'system_error',
    'status_guard',
    'Rejected status transition: ' || OLD.status || ' → ' || NEW.status
      || ' on planned_workout ' || OLD.id,
    'guard_reject',
    jsonb_build_object(
      'workout_id', OLD.id,
      'old_status', OLD.status,
      'new_status', NEW.status,
      'scheduled_date', NEW.scheduled_date,
      'session_name', COALESCE(NEW.session_name, 'unknown')
    )
  );

  RAISE EXCEPTION 'Invalid status transition: % → % on planned_workout %',
    OLD.status, NEW.status, OLD.id;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_planned_workouts_status_guard ON planned_workouts;
CREATE TRIGGER trg_planned_workouts_status_guard
  BEFORE UPDATE ON planned_workouts
  FOR EACH ROW
  EXECUTE FUNCTION fn_planned_workouts_status_guard();

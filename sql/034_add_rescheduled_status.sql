-- =============================================
-- 034_add_rescheduled_status.sql
-- =============================================
-- Adds 'rescheduled' as a valid status in the planned_workouts state machine.
-- Previously the rescheduleWorkout() app function set status='rescheduled'
-- but the trigger rejected it because 'rescheduled' wasn't in the allowed
-- transitions.
--
-- New transitions added:
--   planned    → rescheduled
--   pushed     → rescheduled
--   adjusted   → rescheduled
--   rescheduled → pushed, adjusted, rescheduled (re-move), completed, skipped
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
    ('planned', 'rescheduled'),
    -- From pushed
    ('pushed', 'adjusted'),
    ('pushed', 'completed'),
    ('pushed', 'skipped'),
    ('pushed', 'pushed'),          -- re-push (updated workout)
    ('pushed', 'rescheduled'),
    -- From adjusted
    ('adjusted', 'pushed'),
    ('adjusted', 'adjusted'),      -- re-adjust
    ('adjusted', 'completed'),
    ('adjusted', 'skipped'),
    ('adjusted', 'rescheduled'),
    -- From rescheduled
    ('rescheduled', 'pushed'),
    ('rescheduled', 'adjusted'),
    ('rescheduled', 'rescheduled'), -- re-move
    ('rescheduled', 'completed'),
    ('rescheduled', 'skipped'),
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

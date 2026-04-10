-- Migration 022: Replace session_exceptions references with coaching_log
--
-- session_exceptions was seeded once (sql/015) but never written to by
-- coach_adjust.py. All coaching decisions now land in coaching_log.
-- The todays_exception CTE in daily_coaching_context always returned empty.
-- The exceptions_applied count in weekly_coaching_summary was always 0.
--
-- Changes:
--   1. daily_coaching_context.todays_exception CTE: session_exceptions → coaching_log
--   2. weekly_coaching_summary.exceptions_applied: session_exceptions → coaching_log
-- Does NOT drop session_exceptions table.

-- 1. Recreate daily_coaching_context (only todays_exception CTE changed)
CREATE OR REPLACE VIEW daily_coaching_context AS
WITH
  today AS (SELECT CURRENT_DATE AS d),
  current_block AS (
    SELECT
      pb.id AS block_id,
      pb.block_number,
      pb.name AS block_name,
      pb.rpe_low,
      pb.rpe_high,
      pb.deload_week,
      pb.progression_rule,
      pb.stall_protocol,
      GREATEST(1, (CURRENT_DATE - pb.start_date) / 7 + 1) AS current_week,
      CASE WHEN GREATEST(1, (CURRENT_DATE - pb.start_date) / 7 + 1) = pb.deload_week
           THEN TRUE ELSE FALSE END AS is_deload_week
    FROM program_blocks pb, today t
    WHERE t.d BETWEEN pb.start_date AND pb.end_date
    LIMIT 1
  ),
  todays_session AS (
    SELECT
      ps.session_key,
      ps.name AS session_name,
      ps.session_type,
      ps.estimated_duration_minutes,
      ps.exercises,
      ps.warmup
    FROM program_sessions ps
    JOIN current_block cb ON ps.block_id = cb.block_id
    WHERE ps.day_of_week = TRIM(INITCAP(TO_CHAR(CURRENT_DATE, 'Day')))
    LIMIT 1
  ),
  -- CHANGED (migration 022): was session_exceptions, now coaching_log
  todays_exception AS (
    SELECT
      cl.message AS original_session,
      to_jsonb(cl.message) AS modified_workout,
      cl.decision_type AS modification_type,
      cl.message AS exception_reason,
      false AS pushed_to_garmin
    FROM coaching_log cl, today t
    WHERE cl.date = t.d
      AND cl.type = 'adjustment'
    ORDER BY cl.created_at DESC
    LIMIT 1
  ),
  recovery AS (
    SELECT
      ds.date AS recovery_date,
      ds.resting_hr,
      ds.body_battery_highest,
      ds.body_battery_lowest,
      ds.training_readiness_score,
      ds.sleep_score,
      ds.total_sleep_seconds,
      ds.hrv_avg,
      ds.hrv_weekly_avg,
      ds.hrv_status,
      ds.weight_kg,
      CASE WHEN ds.date < CURRENT_DATE THEN TRUE ELSE FALSE END AS is_fallback_data
    FROM daily_summary ds
    WHERE ds.date <= CURRENT_DATE
    ORDER BY ds.date DESC
    LIMIT 1
  ),
  active_injuries AS (
    SELECT
      COALESCE(json_agg(json_build_object(
        'issue', il.issue,
        'body_area', il.body_area,
        'severity', il.severity,
        'accommodations', il.accommodations
      )), '[]'::json) AS injuries
    FROM injury_log il
    WHERE il.status IN ('active', 'monitoring')
  ),
  recent_mountain AS (
    SELECT
      COUNT(*) AS mountain_days_3d,
      COALESCE(SUM(a.elevation_gain), 0) AS elevation_3d,
      COALESCE(SUM(a.duration_seconds), 0) AS mountain_duration_3d
    FROM activities a
    WHERE a.date >= CURRENT_DATE - 3
      AND a.activity_type IN (
        'backcountry_skiing', 'backcountry_snowboarding',
        'hiking', 'mountaineering', 'splitboarding'
      )
  ),
  week_gym AS (
    SELECT COUNT(*) AS gym_sessions_this_week
    FROM activities a
    WHERE a.date >= DATE_TRUNC('week', CURRENT_DATE)
      AND a.activity_type IN ('strength_training', 'indoor_cardio')
  ),
  recovery_rule AS (
    SELECT
      rr.action,
      rr.rpe_adjustment,
      rr.volume_adjustment
    FROM recovery_rules rr, recovery r
    WHERE rr.hrv_status = COALESCE(r.hrv_status, 'BALANCED')
      AND (
        (rr.sleep_condition = '>=7h' AND r.total_sleep_seconds >= 25200) OR
        (rr.sleep_condition = '6-7h' AND r.total_sleep_seconds >= 21600 AND r.total_sleep_seconds < 25200) OR
        (rr.sleep_condition = '<6h' AND r.total_sleep_seconds < 21600)
      )
    ORDER BY rr.priority
    LIMIT 1
  ),
  current_season AS (
    SELECT
      sp.name AS season_name,
      sp.primary_focus,
      sp.secondary_focus
    FROM season_phases sp
    WHERE CURRENT_DATE >= sp.start_date
      AND (sp.end_date IS NULL OR CURRENT_DATE <= sp.end_date)
    ORDER BY sp.start_date DESC
    LIMIT 1
  )
SELECT
  cb.block_number,
  cb.block_name,
  cb.current_week,
  cb.is_deload_week,
  cb.rpe_low AS block_rpe_low,
  cb.rpe_high AS block_rpe_high,
  cb.progression_rule,
  ts.session_key,
  ts.session_name,
  ts.session_type,
  ts.estimated_duration_minutes,
  ts.exercises AS session_exercises,
  ts.warmup AS session_warmup,
  te.original_session AS exception_original,
  te.modified_workout AS exception_workout,
  te.modification_type AS exception_type,
  te.exception_reason,
  r.recovery_date,
  r.is_fallback_data,
  r.resting_hr,
  r.body_battery_highest,
  r.body_battery_lowest,
  r.training_readiness_score,
  r.sleep_score,
  r.total_sleep_seconds,
  ROUND((r.total_sleep_seconds / 3600.0)::numeric, 1) AS sleep_hours,
  r.hrv_avg,
  r.hrv_weekly_avg,
  r.hrv_status,
  r.weight_kg,
  rr.action AS recovery_action,
  rr.rpe_adjustment AS recovery_rpe,
  rr.volume_adjustment AS recovery_volume,
  CASE
    WHEN r.body_battery_highest < 30 THEN 'body_battery_critical'
    WHEN r.training_readiness_score < 40 THEN 'training_readiness_low'
    WHEN r.hrv_status = 'LOW' AND r.total_sleep_seconds < 21600 THEN 'multi_signal_degraded'
    ELSE NULL
  END AS hard_override,
  ai.injuries AS active_injuries,
  rm.mountain_days_3d,
  rm.elevation_3d,
  wg.gym_sessions_this_week,
  cs.season_name,
  cs.primary_focus AS season_focus
FROM current_block cb
CROSS JOIN recovery r
LEFT JOIN todays_session ts ON TRUE
LEFT JOIN todays_exception te ON TRUE
LEFT JOIN active_injuries ai ON TRUE
LEFT JOIN recent_mountain rm ON TRUE
LEFT JOIN week_gym wg ON TRUE
LEFT JOIN recovery_rule rr ON TRUE
LEFT JOIN current_season cs ON TRUE;


-- 2. Recreate weekly_coaching_summary (only exceptions_applied changed)
CREATE OR REPLACE VIEW weekly_coaching_summary AS
WITH week_range AS (
  SELECT
    DATE_TRUNC('week', CURRENT_DATE)::date AS week_start,
    (DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 days')::date AS week_end
)
SELECT
  wr.week_start,
  wr.week_end,
  (SELECT COUNT(*) FROM activities a
   WHERE a.date BETWEEN wr.week_start AND wr.week_end
     AND a.activity_type = 'strength_training') AS gym_sessions,
  (SELECT COUNT(*) FROM activities a
   WHERE a.date BETWEEN wr.week_start AND wr.week_end
     AND a.activity_type IN ('backcountry_skiing','backcountry_snowboarding','resort_skiing','resort_snowboarding','hiking','mountaineering','splitboarding')) AS mountain_days,
  (SELECT COALESCE(SUM(a.elevation_gain), 0) FROM activities a
   WHERE a.date BETWEEN wr.week_start AND wr.week_end
     AND a.activity_type IN ('backcountry_skiing','backcountry_snowboarding','hiking','mountaineering','splitboarding')) AS total_elevation,
  (SELECT ROUND(AVG(s.total_sleep_seconds / 3600.0)::numeric, 1) FROM sleep s
   WHERE s.date BETWEEN wr.week_start AND wr.week_end) AS avg_sleep_hours,
  (SELECT ROUND(AVG(s.overall_score)::numeric, 0) FROM sleep s
   WHERE s.date BETWEEN wr.week_start AND wr.week_end) AS avg_sleep_score,
  (SELECT ROUND(AVG(h.last_night_avg)::numeric, 1) FROM hrv h
   WHERE h.date BETWEEN wr.week_start AND wr.week_end) AS avg_hrv,
  (SELECT h.weekly_avg FROM hrv h
   WHERE h.date BETWEEN wr.week_start AND wr.week_end
   ORDER BY h.date DESC LIMIT 1) AS hrv_weekly_rolling,
  (SELECT ROUND(AVG(dm.resting_hr)::numeric, 0) FROM daily_metrics dm
   WHERE dm.date BETWEEN wr.week_start AND wr.week_end) AS avg_resting_hr,
  (SELECT bc.weight_kg FROM body_composition bc
   WHERE bc.date BETWEEN wr.week_start AND wr.week_end
   ORDER BY bc.date DESC LIMIT 1) AS latest_weight,
  (SELECT ROUND(AVG(dm.training_readiness_score)::numeric, 0) FROM daily_metrics dm
   WHERE dm.date BETWEEN wr.week_start AND wr.week_end) AS avg_training_readiness,
  (SELECT COUNT(*) FROM planned_workouts pw
   WHERE pw.scheduled_date BETWEEN wr.week_start AND wr.week_end
     AND pw.status = 'completed') AS planned_completed,
  (SELECT COUNT(*) FROM planned_workouts pw
   WHERE pw.scheduled_date BETWEEN wr.week_start AND wr.week_end) AS planned_total,
  (SELECT COUNT(*) FROM coaching_log cl
   WHERE cl.date BETWEEN wr.week_start AND wr.week_end
     AND cl.type = 'adjustment') AS adjustments_made,
  -- CHANGED (migration 022): was session_exceptions, now coaching_log
  (SELECT COUNT(*) FROM coaching_log cl
   WHERE cl.date BETWEEN wr.week_start AND wr.week_end
     AND cl.type = 'adjustment') AS exceptions_applied
FROM week_range wr;

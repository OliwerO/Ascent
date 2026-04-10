-- Migration 023: Wire subjective wellness + yesterday's RPE into daily_coaching_context
--
-- The wellness questionnaire UI and RPE logger exist in the React app but
-- their data was never surfaced in the coaching view. This migration adds:
--   1. Today's subjective_wellness composite + individual scores
--   2. Yesterday's session RPE (srpe) from training_sessions
-- Both feed into the coaching cron's decision matrix.

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
  ),
  -- NEW (migration 023): today's subjective wellness check-in
  todays_wellness AS (
    SELECT
      sw.composite_score AS wellness_composite,
      sw.sleep_quality AS wellness_sleep,
      sw.energy AS wellness_energy,
      sw.muscle_soreness AS wellness_soreness,
      sw.motivation AS wellness_motivation,
      sw.stress AS wellness_stress,
      sw.notes AS wellness_notes
    FROM subjective_wellness sw, today t
    WHERE sw.date = t.d
    LIMIT 1
  ),
  -- NEW (migration 023): most recent session RPE (typically yesterday)
  last_session_rpe AS (
    SELECT
      ts.date AS last_session_date,
      ts.name AS last_session_name,
      ts.srpe AS last_srpe,
      ts.rating AS last_session_rating
    FROM training_sessions ts, today t
    WHERE ts.date < t.d
      AND ts.srpe IS NOT NULL
    ORDER BY ts.date DESC
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
    -- NEW (migration 023): wellness composite override
    WHEN tw.wellness_composite IS NOT NULL AND tw.wellness_composite < 2.5 THEN 'subjective_poor'
    ELSE NULL
  END AS hard_override,
  ai.injuries AS active_injuries,
  rm.mountain_days_3d,
  rm.elevation_3d,
  wg.gym_sessions_this_week,
  cs.season_name,
  cs.primary_focus AS season_focus,
  -- NEW (migration 023): subjective wellness
  tw.wellness_composite,
  tw.wellness_sleep,
  tw.wellness_energy,
  tw.wellness_soreness,
  tw.wellness_motivation,
  tw.wellness_stress,
  tw.wellness_notes,
  -- NEW (migration 023): last session RPE
  lr.last_session_date,
  lr.last_session_name,
  lr.last_srpe,
  lr.last_session_rating
FROM current_block cb
CROSS JOIN recovery r
LEFT JOIN todays_session ts ON TRUE
LEFT JOIN todays_exception te ON TRUE
LEFT JOIN active_injuries ai ON TRUE
LEFT JOIN recent_mountain rm ON TRUE
LEFT JOIN week_gym wg ON TRUE
LEFT JOIN recovery_rule rr ON TRUE
LEFT JOIN current_season cs ON TRUE
LEFT JOIN todays_wellness tw ON TRUE
LEFT JOIN last_session_rpe lr ON TRUE;

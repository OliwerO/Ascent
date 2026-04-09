-- =============================================
-- 024: Feedback Loop Views
--
-- Adds analytical views that wire existing data into actionable signals:
--
-- 1. exercise_feedback_trends — per-exercise feel streaks and distribution
--    (feeds daily_coaching_context for coaching visibility)
-- 2. stall_early_warning — compound risk signal before stalls happen
--    (RPE trend + heavy feel + sleep decline → stall incoming)
-- 3. sleep_performance_correlation — sleep bucket vs gym performance
--    (personal insight: "you lift better after 7.5h+ sleep")
--
-- Also updates daily_coaching_context to include exercise_feel_alerts.
-- =============================================


-- =============================================
-- EXERCISE FEEDBACK TRENDS
-- Per-exercise feel distribution and streak detection over last 3 weeks.
-- Surfaces only noteworthy trends (persistent heavy or light feel).
-- =============================================

CREATE OR REPLACE VIEW exercise_feedback_trends AS
WITH recent_feedback AS (
  SELECT
    exercise_name,
    session_date,
    feel,
    ROW_NUMBER() OVER (PARTITION BY exercise_name ORDER BY session_date DESC) AS recency
  FROM exercise_feedback
  WHERE session_date >= CURRENT_DATE - 21
),
streaks AS (
  SELECT
    exercise_name,
    feel,
    COUNT(*) AS consecutive_sessions
  FROM (
    SELECT
      exercise_name,
      feel,
      session_date,
      recency,
      recency - ROW_NUMBER() OVER (PARTITION BY exercise_name, feel ORDER BY session_date DESC) AS grp
    FROM recent_feedback
  ) g
  WHERE grp = 0  -- only count from most recent
  GROUP BY exercise_name, feel
),
distribution AS (
  SELECT
    exercise_name,
    COUNT(*) FILTER (WHERE feel = 'heavy') AS heavy_count,
    COUNT(*) FILTER (WHERE feel = 'right') AS right_count,
    COUNT(*) FILTER (WHERE feel = 'light') AS light_count,
    COUNT(*) AS total_sessions
  FROM recent_feedback
  WHERE recency <= 6  -- last 6 sessions
  GROUP BY exercise_name
)
SELECT
  d.exercise_name,
  d.heavy_count,
  d.right_count,
  d.light_count,
  d.total_sessions,
  COALESCE(s.consecutive_sessions, 0) AS heavy_streak,
  CASE
    WHEN COALESCE(s.consecutive_sessions, 0) >= 3 THEN 'persistently_heavy'
    WHEN d.heavy_count >= 4 AND d.total_sessions >= 6 THEN 'mostly_heavy'
    WHEN d.light_count >= 4 AND d.total_sessions >= 6 THEN 'mostly_light'
    ELSE 'normal'
  END AS feel_trend
FROM distribution d
LEFT JOIN streaks s ON d.exercise_name = s.exercise_name AND s.feel = 'heavy'
WHERE d.heavy_count >= 2 OR d.light_count >= 4;


-- =============================================
-- STALL EARLY WARNING
-- Compound risk signal combining:
-- - exercises at 2-3 sessions at current weight (pre-stall)
-- - per-exercise heavy feel trend
-- - session RPE trend (last 3 sessions)
-- - sleep trend (7d vs 30d average)
--
-- Surfaces moderate+ risk before a stall is officially detected.
-- =============================================

CREATE OR REPLACE VIEW stall_early_warning AS
WITH
  at_risk AS (
    SELECT exercise_name, planned_weight_kg, sessions_at_current_weight, current_e1rm
    FROM progression_velocity
    WHERE sessions_at_current_weight BETWEEN 2 AND 3
      AND progression_status = 'on_track'
  ),
  feel AS (
    SELECT exercise_name, feel, session_date
    FROM exercise_feedback
    WHERE session_date >= CURRENT_DATE - 14
  ),
  feel_agg AS (
    SELECT
      exercise_name,
      COUNT(*) FILTER (WHERE feel = 'heavy') AS recent_heavy,
      COUNT(*) AS recent_total
    FROM feel
    GROUP BY exercise_name
  ),
  rpe_trend AS (
    SELECT
      AVG(srpe) AS avg_recent_srpe,
      MAX(srpe) AS max_recent_srpe
    FROM (
      SELECT srpe FROM training_sessions
      WHERE srpe IS NOT NULL
      ORDER BY date DESC LIMIT 3
    ) t
  ),
  sleep_trend AS (
    SELECT
      AVG(CASE WHEN date >= CURRENT_DATE - 7 THEN total_sleep_seconds END) / 3600.0 AS sleep_7d_avg,
      AVG(total_sleep_seconds) / 3600.0 AS sleep_30d_avg
    FROM sleep
    WHERE date >= CURRENT_DATE - 30
  )
SELECT
  ar.exercise_name,
  ar.planned_weight_kg,
  ar.sessions_at_current_weight,
  ar.current_e1rm,
  fa.recent_heavy,
  fa.recent_total,
  rt.avg_recent_srpe,
  st.sleep_7d_avg,
  st.sleep_30d_avg,
  CASE
    WHEN COALESCE(fa.recent_heavy, 0) >= 2
      AND rt.avg_recent_srpe >= 8
      AND st.sleep_7d_avg < st.sleep_30d_avg - 0.3
    THEN 'high'
    WHEN COALESCE(fa.recent_heavy, 0) >= 1
      AND (rt.avg_recent_srpe >= 8 OR st.sleep_7d_avg < st.sleep_30d_avg - 0.3)
    THEN 'moderate'
    ELSE 'low'
  END AS stall_risk
FROM at_risk ar
LEFT JOIN feel_agg fa ON ar.exercise_name = fa.exercise_name
CROSS JOIN rpe_trend rt
CROSS JOIN sleep_trend st
WHERE
  (COALESCE(fa.recent_heavy, 0) >= 1 AND rt.avg_recent_srpe >= 7.5)
  OR (rt.avg_recent_srpe >= 8.5 AND st.sleep_7d_avg < st.sleep_30d_avg - 0.5);


-- =============================================
-- SLEEP PERFORMANCE CORRELATION
-- Buckets sleep duration and shows aggregate gym performance per bucket.
-- Personal insight: "you lift X% more volume after 7.5h+ sleep"
-- =============================================

CREATE OR REPLACE VIEW sleep_performance_correlation AS
WITH session_data AS (
  SELECT
    ts.id,
    ts.date AS session_date,
    s.total_sleep_seconds / 3600.0 AS prev_night_sleep_hours,
    s.overall_score AS prev_night_sleep_score,
    ts.total_volume_kg,
    ts.srpe,
    ts.total_sets
  FROM training_sessions ts
  JOIN sleep s ON s.date = ts.date
  WHERE ts.total_volume_kg > 0
    AND s.total_sleep_seconds IS NOT NULL
),
bucketed AS (
  SELECT *,
    CASE
      WHEN prev_night_sleep_hours >= 7.5 THEN 'good (7.5h+)'
      WHEN prev_night_sleep_hours >= 6.5 THEN 'ok (6.5-7.5h)'
      ELSE 'poor (<6.5h)'
    END AS sleep_bucket
  FROM session_data
)
SELECT
  sleep_bucket,
  COUNT(*) AS sessions,
  ROUND(AVG(total_volume_kg)::numeric, 0) AS avg_volume_kg,
  ROUND(AVG(srpe)::numeric, 1) AS avg_srpe,
  ROUND(AVG(prev_night_sleep_hours)::numeric, 1) AS avg_sleep_hours
FROM bucketed
GROUP BY sleep_bucket
ORDER BY avg_sleep_hours DESC;


-- =============================================
-- UPDATE daily_coaching_context: add exercise_feel_alerts
-- Aggregates noteworthy exercise feel trends into a JSONB column
-- so the coaching agent sees "bench heavy 3 sessions running".
-- =============================================

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
  ),
  -- NEW (migration 024): exercise feel alerts for coaching agent
  feel_alerts AS (
    SELECT
      COALESCE(
        jsonb_agg(jsonb_build_object(
          'exercise', eft.exercise_name,
          'feel_trend', eft.feel_trend,
          'heavy_streak', eft.heavy_streak,
          'heavy_count', eft.heavy_count,
          'total_sessions', eft.total_sessions
        )),
        '[]'::jsonb
      ) AS exercise_feel_alerts
    FROM exercise_feedback_trends eft
    WHERE eft.feel_trend != 'normal'
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
    WHEN tw.wellness_composite IS NOT NULL AND tw.wellness_composite < 2.5 THEN 'subjective_poor'
    ELSE NULL
  END AS hard_override,
  ai.injuries AS active_injuries,
  rm.mountain_days_3d,
  rm.elevation_3d,
  wg.gym_sessions_this_week,
  cs.season_name,
  cs.primary_focus AS season_focus,
  tw.wellness_composite,
  tw.wellness_sleep,
  tw.wellness_energy,
  tw.wellness_soreness,
  tw.wellness_motivation,
  tw.wellness_stress,
  tw.wellness_notes,
  lr.last_session_date,
  lr.last_session_name,
  lr.last_srpe,
  lr.last_session_rating,
  -- NEW (migration 024): exercise feel alerts
  fa.exercise_feel_alerts
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
LEFT JOIN last_session_rpe lr ON TRUE
LEFT JOIN feel_alerts fa ON TRUE;

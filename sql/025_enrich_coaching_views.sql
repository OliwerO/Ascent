-- =============================================
-- 025: Enrich coaching views for CCD migration
--
-- Folds feedback-loop data into the two main coaching views so that
-- CCD scheduled sessions get everything in a single query. This is the
-- "smart views, thin prompts" pattern — new data sources go into these
-- views via SQL migrations; the CCD prompts never need to change.
--
-- Changes:
--   daily_coaching_context  — adds progression_alerts, mountain_interference_patterns
--   weekly_coaching_summary — adds avg_srpe, poor_sleep_nights, progression_highlights,
--                             stall_warnings, interference_observations, decision_quality
-- =============================================


-- =============================================
-- DAILY COACHING CONTEXT — enriched
-- Adds two JSONB columns that the daily CCD session uses for
-- gym-day progression context and mountain interference awareness.
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
  -- Exercise feel alerts (from migration 024)
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
  ),
  -- NEW (migration 025): progression alerts from progression_velocity + stall_early_warning
  prog_alerts AS (
    SELECT
      COALESCE(
        jsonb_agg(jsonb_build_object(
          'exercise', pv.exercise_name,
          'weight_kg', pv.planned_weight_kg,
          'status', pv.progression_status,
          'sessions_at_weight', pv.sessions_at_current_weight,
          'kg_per_week', pv.kg_per_week,
          'e1rm', pv.current_e1rm,
          'stall_risk', sew.stall_risk
        )),
        '[]'::jsonb
      ) AS progression_alerts
    FROM progression_velocity pv
    LEFT JOIN stall_early_warning sew ON pv.exercise_name = sew.exercise_name
    WHERE pv.progression_status IN ('stalled', 'behind')
       OR sew.stall_risk IN ('moderate', 'high')
       OR pv.kg_per_week > 0  -- include progressing exercises too for context
  ),
  -- NEW (migration 025): mountain interference patterns (medium/high confidence)
  mountain_patterns AS (
    SELECT
      COALESCE(
        jsonb_agg(jsonb_build_object(
          'pattern', arp.observation,
          'confidence', arp.confidence,
          'key', arp.pattern_key,
          'sample_size', arp.sample_size
        )),
        '[]'::jsonb
      ) AS mountain_interference_patterns
    FROM athlete_response_patterns arp
    WHERE arp.pattern_type = 'mountain_interference'
      AND arp.confidence IN ('medium', 'high')
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
  fa.exercise_feel_alerts,
  -- NEW (migration 025)
  pa.progression_alerts,
  mp.mountain_interference_patterns
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
LEFT JOIN feel_alerts fa ON TRUE
LEFT JOIN prog_alerts pa ON TRUE
LEFT JOIN mountain_patterns mp ON TRUE;


-- =============================================
-- WEEKLY COACHING SUMMARY — enriched
-- Adds feedback-loop columns so the weekly CCD session gets a complete
-- picture in one query. Keeps the current-week-only scope.
-- =============================================

CREATE OR REPLACE VIEW weekly_coaching_summary AS
WITH week_range AS (
  SELECT
    DATE_TRUNC('week', CURRENT_DATE)::date AS week_start,
    (DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 days')::date AS week_end
),
-- NEW (025): session RPE this week
week_srpe AS (
  SELECT
    ROUND(AVG(ts.srpe)::numeric, 1) AS avg_srpe,
    COUNT(*) AS srpe_count
  FROM training_sessions ts, week_range wr
  WHERE ts.date BETWEEN wr.week_start AND wr.week_end
    AND ts.srpe IS NOT NULL
),
-- NEW (025): poor sleep nights this week
week_sleep_quality AS (
  SELECT
    COUNT(*) FILTER (WHERE s.total_sleep_seconds < 21600) AS poor_sleep_nights,
    COUNT(*) AS total_sleep_nights
  FROM sleep s, week_range wr
  WHERE s.date BETWEEN wr.week_start AND wr.week_end
),
-- NEW (025): progression highlights from exercise_progression this week
week_progression AS (
  SELECT
    COALESCE(
      jsonb_agg(jsonb_build_object(
        'exercise', ep.exercise_name,
        'weight_kg', ep.planned_weight_kg,
        'action', ep.progression_applied,
        'change_kg', ep.progression_amount,
        'date', ep.date
      ) ORDER BY ep.date),
      '[]'::jsonb
    ) AS progression_highlights
  FROM exercise_progression ep, week_range wr
  WHERE ep.date BETWEEN wr.week_start AND wr.week_end
),
-- NEW (025): stall warnings snapshot
week_stalls AS (
  SELECT
    COALESCE(
      jsonb_agg(jsonb_build_object(
        'exercise', sew.exercise_name,
        'weight_kg', sew.planned_weight_kg,
        'sessions_at_weight', sew.sessions_at_current_weight,
        'risk', sew.stall_risk,
        'avg_srpe', sew.avg_recent_srpe,
        'sleep_7d', sew.sleep_7d_avg
      )),
      '[]'::jsonb
    ) AS stall_warnings
  FROM stall_early_warning sew
  WHERE sew.stall_risk IN ('moderate', 'high')
),
-- NEW (025): interference patterns (all medium/high confidence)
week_interference AS (
  SELECT
    COALESCE(
      jsonb_agg(jsonb_build_object(
        'observation', arp.observation,
        'confidence', arp.confidence,
        'key', arp.pattern_key,
        'sample_size', arp.sample_size
      )),
      '[]'::jsonb
    ) AS interference_observations
  FROM athlete_response_patterns arp
  WHERE arp.confidence IN ('medium', 'high')
),
-- NEW (025): decision quality from retrospective (this week's decisions)
week_decisions AS (
  SELECT
    COUNT(*) AS decisions_evaluated,
    COUNT(*) FILTER (WHERE cdo.outcome_quality = 'good') AS good_decisions,
    COUNT(*) FILTER (WHERE cdo.outcome_quality = 'poor') AS poor_decisions
  FROM coaching_decision_outcomes cdo, week_range wr
  WHERE cdo.decision_date BETWEEN wr.week_start AND wr.week_end
)
SELECT
  wr.week_start,
  wr.week_end,
  -- Gym sessions
  (SELECT COUNT(*) FROM activities a
   WHERE a.date BETWEEN wr.week_start AND wr.week_end
     AND a.activity_type = 'strength_training') AS gym_sessions,
  -- Mountain activities
  (SELECT COUNT(*) FROM activities a
   WHERE a.date BETWEEN wr.week_start AND wr.week_end
     AND a.activity_type IN ('backcountry_skiing','backcountry_snowboarding','resort_skiing','resort_snowboarding','hiking','mountaineering','splitboarding')) AS mountain_days,
  (SELECT COALESCE(SUM(a.elevation_gain), 0) FROM activities a
   WHERE a.date BETWEEN wr.week_start AND wr.week_end
     AND a.activity_type IN ('backcountry_skiing','backcountry_snowboarding','hiking','mountaineering','splitboarding')) AS total_elevation,
  -- Sleep averages
  (SELECT ROUND(AVG(s.total_sleep_seconds / 3600.0)::numeric, 1) FROM sleep s
   WHERE s.date BETWEEN wr.week_start AND wr.week_end) AS avg_sleep_hours,
  (SELECT ROUND(AVG(s.overall_score)::numeric, 0) FROM sleep s
   WHERE s.date BETWEEN wr.week_start AND wr.week_end) AS avg_sleep_score,
  -- HRV
  (SELECT ROUND(AVG(h.last_night_avg)::numeric, 1) FROM hrv h
   WHERE h.date BETWEEN wr.week_start AND wr.week_end) AS avg_hrv,
  (SELECT h.weekly_avg FROM hrv h
   WHERE h.date BETWEEN wr.week_start AND wr.week_end
   ORDER BY h.date DESC LIMIT 1) AS hrv_weekly_rolling,
  -- Resting HR trend
  (SELECT ROUND(AVG(dm.resting_hr)::numeric, 0) FROM daily_metrics dm
   WHERE dm.date BETWEEN wr.week_start AND wr.week_end) AS avg_resting_hr,
  -- Body weight
  (SELECT bc.weight_kg FROM body_composition bc
   WHERE bc.date BETWEEN wr.week_start AND wr.week_end
   ORDER BY bc.date DESC LIMIT 1) AS latest_weight,
  -- Training readiness
  (SELECT ROUND(AVG(dm.training_readiness_score)::numeric, 0) FROM daily_metrics dm
   WHERE dm.date BETWEEN wr.week_start AND wr.week_end) AS avg_training_readiness,
  -- Planned vs actual
  (SELECT COUNT(*) FROM planned_workouts pw
   WHERE pw.scheduled_date BETWEEN wr.week_start AND wr.week_end
     AND pw.status = 'completed') AS planned_completed,
  (SELECT COUNT(*) FROM planned_workouts pw
   WHERE pw.scheduled_date BETWEEN wr.week_start AND wr.week_end) AS planned_total,
  -- Coaching decisions this week
  (SELECT COUNT(*) FROM coaching_log cl
   WHERE cl.date BETWEEN wr.week_start AND wr.week_end
     AND cl.type = 'adjustment') AS adjustments_made,
  -- Exceptions applied
  (SELECT COUNT(*) FROM coaching_log cl
   WHERE cl.date BETWEEN wr.week_start AND wr.week_end
     AND cl.type = 'adjustment') AS exceptions_applied,
  -- NEW (migration 025)
  ws.avg_srpe,
  wsq.poor_sleep_nights,
  wp.progression_highlights,
  wst.stall_warnings,
  wi.interference_observations,
  wd.decisions_evaluated,
  wd.good_decisions,
  wd.poor_decisions
FROM week_range wr
CROSS JOIN week_srpe ws
CROSS JOIN week_sleep_quality wsq
CROSS JOIN week_progression wp
CROSS JOIN week_stalls wst
CROSS JOIN week_interference wi
CROSS JOIN week_decisions wd;

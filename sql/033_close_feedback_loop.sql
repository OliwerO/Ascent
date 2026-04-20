-- =============================================
-- 033: Close the feedback loop + wire missing signals
--
-- Chapters 22-24 of the coaching design audit.
--
-- Changes to daily_coaching_context:
--   1. learned_patterns — ALL athlete_response_patterns (not just mountain),
--      replacing the mountain-only mountain_patterns CTE.
--      Backwards-compat alias: mountain_interference_patterns extracted from
--      the broader learned_patterns array.
--   2. decision_quality_30d — 30-day summary from coaching_decision_outcomes
--   3. deep_sleep_pct, rem_sleep_pct — from daily_summary sleep stage data
--   4. avg_stress_level, respiration_avg — from daily_metrics
--   5. poor_sleep_nights_7d — count of sub-6h nights in last 7 days
--
-- These close the write-only learning loop (interference_analysis.py and
-- decision_retrospective.py now feed BACK into daily decisions) and wire
-- sleep quality, stress, and respiration into the coaching view.
-- =============================================

DROP VIEW IF EXISTS daily_coaching_context CASCADE;

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
  -- Recovery data with freshness tracking + sleep stages (NEW: deep/rem)
  recovery AS (
    SELECT
      ds.date AS recovery_date,
      ds.resting_hr,
      ds.body_battery_highest,
      ds.body_battery_lowest,
      ds.training_readiness_score,
      ds.sleep_score,
      ds.total_sleep_seconds,
      ds.deep_sleep_seconds,
      ds.rem_sleep_seconds,
      ds.hrv_avg,
      ds.hrv_weekly_avg,
      ds.hrv_status,
      ds.weight_kg,
      ds.avg_stress_level,
      CASE WHEN ds.date < CURRENT_DATE THEN TRUE ELSE FALSE END AS is_fallback_data
    FROM daily_summary ds
    WHERE ds.date <= CURRENT_DATE
    ORDER BY ds.date DESC
    LIMIT 1
  ),
  -- Data freshness from daily_metrics.synced_at (from migration 026)
  data_freshness AS (
    SELECT
      ROUND(
        EXTRACT(EPOCH FROM (NOW() - dm.synced_at)) / 3600.0
      , 1) AS data_age_hours
    FROM daily_metrics dm
    WHERE dm.date <= CURRENT_DATE
    ORDER BY dm.date DESC
    LIMIT 1
  ),
  -- NEW (033): Respiration from daily_metrics (not in daily_summary)
  vitals AS (
    SELECT
      dm.respiration_avg
    FROM daily_metrics dm
    WHERE dm.date <= CURRENT_DATE
    ORDER BY dm.date DESC
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
       OR pv.kg_per_week > 0
  ),
  -- NEW (033): All learned patterns — mountain_interference, recovery_response,
  -- progression_velocity. Replaces the mountain-only CTE from migration 025.
  learned_patterns AS (
    SELECT
      COALESCE(
        jsonb_agg(jsonb_build_object(
          'type', arp.pattern_type,
          'key', arp.pattern_key,
          'pattern', arp.observation,
          'confidence', arp.confidence,
          'sample_size', arp.sample_size,
          'effect_size', arp.effect_size
        )),
        '[]'::jsonb
      ) AS learned_patterns
    FROM athlete_response_patterns arp
    WHERE arp.confidence IN ('medium', 'high')
  ),
  -- NEW (033): Decision quality summary from last 30 days
  decision_quality AS (
    SELECT jsonb_build_object(
      'total', COUNT(*),
      'good', COUNT(*) FILTER (WHERE outcome_quality = 'good'),
      'neutral', COUNT(*) FILTER (WHERE outcome_quality = 'neutral'),
      'poor', COUNT(*) FILTER (WHERE outcome_quality = 'poor'),
      'poor_decisions', COALESCE(
        (SELECT jsonb_agg(sub.entry)
         FROM (
           SELECT jsonb_build_object(
             'date', cdo2.decision_date,
             'type', cdo2.decision_type,
             'notes', cdo2.assessment_notes
           ) AS entry
           FROM coaching_decision_outcomes cdo2
           WHERE cdo2.outcome_quality = 'poor'
             AND cdo2.decision_date >= CURRENT_DATE - 30
           ORDER BY cdo2.decision_date DESC
           LIMIT 3
         ) sub),
        '[]'::jsonb
      )
    ) AS decision_quality_30d
    FROM coaching_decision_outcomes
    WHERE decision_date >= CURRENT_DATE - 30
  ),
  -- NEW (033): Poor sleep nights in last 7 days (for recovery recommendations)
  recent_sleep_trend AS (
    SELECT
      COUNT(*) FILTER (WHERE total_sleep_seconds < 21600) AS poor_sleep_nights_7d
    FROM daily_summary
    WHERE date >= CURRENT_DATE - 7
      AND date < CURRENT_DATE
      AND total_sleep_seconds IS NOT NULL
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
  -- Data freshness (from migration 026)
  df.data_age_hours,
  -- Hard override gated on data freshness (from migration 026)
  CASE
    WHEN r.body_battery_highest < 30
         AND COALESCE(df.data_age_hours, 999) < 12
      THEN 'body_battery_critical'
    WHEN r.training_readiness_score < 40
         AND COALESCE(df.data_age_hours, 999) < 12
      THEN 'training_readiness_low'
    WHEN r.hrv_status = 'LOW' AND r.total_sleep_seconds < 21600
      THEN 'multi_signal_degraded'
    WHEN tw.wellness_composite IS NOT NULL AND tw.wellness_composite < 2.5
      THEN 'subjective_poor'
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
  pa.progression_alerts,
  -- NEW (033): sleep stages
  r.deep_sleep_seconds,
  r.rem_sleep_seconds,
  CASE WHEN r.total_sleep_seconds > 0
    THEN ROUND((r.deep_sleep_seconds::numeric / r.total_sleep_seconds) * 100, 1)
    ELSE NULL END AS deep_sleep_pct,
  CASE WHEN r.total_sleep_seconds > 0
    THEN ROUND((r.rem_sleep_seconds::numeric / r.total_sleep_seconds) * 100, 1)
    ELSE NULL END AS rem_sleep_pct,
  -- NEW (033): stress and respiration
  r.avg_stress_level,
  v.respiration_avg,
  -- NEW (033): all learned patterns (replaces mountain-only)
  lp.learned_patterns,
  -- Backwards-compat: extract mountain_interference from learned_patterns
  (SELECT COALESCE(
    jsonb_agg(elem) FILTER (WHERE elem->>'type' = 'mountain_interference'),
    '[]'::jsonb
  ) FROM jsonb_array_elements(lp.learned_patterns) AS elem
  ) AS mountain_interference_patterns,
  -- NEW (033): decision quality from retrospective
  dq.decision_quality_30d,
  -- NEW (033): poor sleep nights for recovery recommendations
  rst.poor_sleep_nights_7d
FROM current_block cb
CROSS JOIN recovery r
LEFT JOIN data_freshness df ON TRUE
LEFT JOIN vitals v ON TRUE
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
LEFT JOIN learned_patterns lp ON TRUE
LEFT JOIN decision_quality dq ON TRUE
LEFT JOIN recent_sleep_trend rst ON TRUE;

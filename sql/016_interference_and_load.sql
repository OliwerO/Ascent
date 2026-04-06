-- =============================================
-- 016: Mountain-Gym Interference + Cumulative Load + Learning Store
--
-- Adds analytical views for:
-- 1. Mountain-gym interference tracking (72h window)
-- 2. Weekly training load with spike detection
-- 3. Athlete response patterns (learned over time)
--
-- These power the feedback loop: data → analysis → patterns → better decisions.
--
-- ALSO FIXES: daily_coaching_context and weekly_coaching_summary views from
-- migration 014 used wrong activity type names (backcountry_skiing instead of
-- backcountry_snowboarding, resort_skiing instead of resort_snowboarding).
-- These views are recreated with correct types.
-- =============================================

-- =============================================
-- ATHLETE RESPONSE PATTERNS
-- Central learning store. Every analysis script writes here.
-- The coaching agent reads before every daily decision.
-- Patterns gain confidence as more data accumulates.
-- =============================================

CREATE TABLE IF NOT EXISTS athlete_response_patterns (
  id BIGSERIAL PRIMARY KEY,
  pattern_type TEXT NOT NULL,               -- 'mountain_interference', 'recovery_response', 'progression_velocity', 'exercise_feel'
  pattern_key TEXT NOT NULL,                -- e.g. 'elevation_gt_1500m', 'rest_after_hrv_low'
  observation TEXT NOT NULL,                -- natural language summary for coaching agent
  confidence TEXT NOT NULL DEFAULT 'low',   -- 'low' (<5 samples), 'medium' (5-15), 'high' (>15)
  sample_size INTEGER NOT NULL DEFAULT 0,
  effect_size REAL,                         -- Cohen's d when applicable
  data_summary JSONB,                       -- supporting statistics (means, medians, percentiles)
  first_observed DATE NOT NULL DEFAULT CURRENT_DATE,
  last_updated DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(pattern_type, pattern_key)
);

CREATE INDEX IF NOT EXISTS idx_response_patterns_type ON athlete_response_patterns(pattern_type);

-- =============================================
-- RLS for new table
-- =============================================

ALTER TABLE athlete_response_patterns ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_read" ON athlete_response_patterns FOR SELECT TO anon USING (true);
CREATE POLICY "service_all" ON athlete_response_patterns FOR ALL TO service_role USING (true);

-- =============================================
-- MOUNTAIN-GYM INTERFERENCE VIEW
--
-- For each gym session, looks back 72h (3 days) at mountain activity.
-- Computes mountain load metrics and gym performance relative to
-- the athlete's 30-day rolling baseline for that session type.
--
-- Mountain activity types: backcountry_skiing, backcountry_snowboarding,
-- hiking, mountaineering, splitboarding (self-powered elevation).
-- Resort skiing/snowboarding counts as a mountain day for load but
-- elevation is NOT counted (gondola/lift-served).
-- =============================================

CREATE OR REPLACE VIEW mountain_gym_interference AS
WITH
  -- All gym sessions with their aggregate performance
  gym_sessions AS (
    SELECT
      ts.id AS session_id,
      ts.date AS gym_date,
      ts.name AS session_name,
      ts.total_volume_kg,
      ts.srpe,
      ts.srpe_load,
      ts.duration_minutes,
      -- Per-set aggregates for this session
      (SELECT AVG(tsets.rpe) FROM training_sets tsets WHERE tsets.session_id = ts.id AND tsets.set_type = 'working') AS avg_set_rpe,
      (SELECT MAX(tsets.estimated_1rm) FROM training_sets tsets WHERE tsets.session_id = ts.id AND tsets.set_type = 'working') AS max_e1rm
    FROM training_sessions ts
    WHERE ts.total_volume_kg > 0  -- only actual gym sessions
  ),

  -- Mountain activity in the 72h window before each gym session
  mountain_load AS (
    SELECT
      gs.session_id,
      gs.gym_date,
      COUNT(a.id) AS mountain_days_72h,
      COALESCE(SUM(
        CASE WHEN a.activity_type NOT IN ('resort_skiing', 'resort_snowboarding')
             THEN a.elevation_gain ELSE 0 END
      ), 0)::INTEGER AS mountain_elevation_72h,
      COALESCE(SUM(a.duration_seconds), 0) AS mountain_duration_sec_72h,
      COALESCE(SUM(a.calories), 0) AS mountain_calories_72h,
      MAX(a.training_effect_aerobic) AS max_aerobic_te_72h,
      -- Include resort days in day count but not elevation
      COUNT(CASE WHEN a.activity_type IN ('resort_skiing', 'resort_snowboarding') THEN 1 END) AS resort_days_72h
    FROM gym_sessions gs
    LEFT JOIN activities a
      ON a.date >= gs.gym_date - 3
      AND a.date < gs.gym_date
      AND a.activity_type IN (
        'backcountry_skiing', 'backcountry_snowboarding', 'hiking', 'mountaineering',
        'splitboarding', 'resort_skiing', 'resort_snowboarding'
      )
    GROUP BY gs.session_id, gs.gym_date
  ),

  -- Rolling 30-day baseline per gym session (for comparison)
  session_baseline AS (
    SELECT
      gs.session_id,
      gs.gym_date,
      -- 30-day average volume for comparison
      (SELECT AVG(ts2.total_volume_kg)
       FROM training_sessions ts2
       WHERE ts2.date >= gs.gym_date - 30
         AND ts2.date < gs.gym_date
         AND ts2.total_volume_kg > 0
      ) AS baseline_volume_30d,
      -- 30-day average sRPE
      (SELECT AVG(ts2.srpe)
       FROM training_sessions ts2
       WHERE ts2.date >= gs.gym_date - 30
         AND ts2.date < gs.gym_date
         AND ts2.srpe IS NOT NULL
      ) AS baseline_srpe_30d
    FROM gym_sessions gs
  )

SELECT
  gs.gym_date,
  gs.session_name,
  gs.total_volume_kg,
  gs.srpe,
  gs.srpe_load,
  gs.avg_set_rpe,
  gs.max_e1rm,
  gs.duration_minutes,
  -- Mountain load in preceding 72h
  ml.mountain_days_72h,
  ml.mountain_elevation_72h,
  ROUND(ml.mountain_duration_sec_72h / 3600.0, 1) AS mountain_hours_72h,
  ml.mountain_calories_72h,
  ml.max_aerobic_te_72h,
  ml.resort_days_72h,
  -- Performance vs baseline
  sb.baseline_volume_30d,
  sb.baseline_srpe_30d,
  CASE WHEN sb.baseline_volume_30d > 0
    THEN ROUND(((gs.total_volume_kg - sb.baseline_volume_30d) / sb.baseline_volume_30d * 100)::numeric, 1)
    ELSE NULL
  END AS volume_vs_baseline_pct,
  CASE WHEN sb.baseline_srpe_30d > 0
    THEN ROUND(((gs.srpe - sb.baseline_srpe_30d) / sb.baseline_srpe_30d * 100)::numeric, 1)
    ELSE NULL
  END AS srpe_vs_baseline_pct,
  -- Categorize mountain load level
  CASE
    WHEN ml.mountain_days_72h = 0 THEN 'none'
    WHEN ml.mountain_elevation_72h >= 2000 OR ml.mountain_duration_sec_72h >= 18000 THEN 'heavy'
    WHEN ml.mountain_elevation_72h >= 1000 OR ml.mountain_duration_sec_72h >= 10800 THEN 'moderate'
    ELSE 'light'
  END AS mountain_load_category
FROM gym_sessions gs
JOIN mountain_load ml ON ml.session_id = gs.session_id
LEFT JOIN session_baseline sb ON sb.session_id = gs.session_id
ORDER BY gs.gym_date DESC;


-- =============================================
-- WEEKLY TRAINING LOAD VIEW
--
-- Aggregates ALL training load per ISO week across modalities.
-- Includes 4-week rolling average and spike detection (>15%).
-- Uses generate_series date spine for gap-aware calculation.
-- =============================================

CREATE OR REPLACE VIEW weekly_training_load AS
WITH
  -- Generate weekly date spine from earliest activity
  week_spine AS (
    SELECT d::date AS week_start
    FROM generate_series(
      (SELECT DATE_TRUNC('week', MIN(date))::date FROM activities),
      DATE_TRUNC('week', CURRENT_DATE)::date,
      '7 days'::interval
    ) d
  ),

  -- Weekly activity aggregates
  weekly_raw AS (
    SELECT
      ws.week_start,
      -- Gym
      COUNT(DISTINCT CASE WHEN a.activity_type = 'strength_training' THEN a.id END) AS gym_sessions,
      -- Mountain (self-powered only)
      COUNT(DISTINCT CASE WHEN a.activity_type IN ('backcountry_skiing','backcountry_snowboarding','hiking','mountaineering','splitboarding')
                          THEN a.id END) AS mountain_days,
      -- Resort (counted separately)
      COUNT(DISTINCT CASE WHEN a.activity_type IN ('resort_skiing','resort_snowboarding') THEN a.id END) AS resort_days,
      -- Elevation (self-powered only)
      COALESCE(SUM(CASE WHEN a.activity_type IN ('backcountry_skiing','backcountry_snowboarding','hiking','mountaineering','splitboarding')
                        THEN a.elevation_gain ELSE 0 END), 0)::INTEGER AS total_elevation_m,
      -- Duration (all activities)
      COALESCE(SUM(a.duration_seconds), 0) AS total_duration_sec,
      -- Calories (all activities)
      COALESCE(SUM(a.calories), 0) AS total_calories
    FROM week_spine ws
    LEFT JOIN activities a
      ON a.date >= ws.week_start
      AND a.date < ws.week_start + 7
    GROUP BY ws.week_start
  ),

  -- Gym volume from training_sessions
  weekly_gym AS (
    SELECT
      ws.week_start,
      COALESCE(SUM(ts.total_volume_kg), 0) AS total_gym_volume_kg,
      COALESCE(SUM(ts.srpe_load), 0) AS total_srpe_load
    FROM week_spine ws
    LEFT JOIN training_sessions ts
      ON ts.date >= ws.week_start
      AND ts.date < ws.week_start + 7
    GROUP BY ws.week_start
  ),

  -- Combined with rolling averages
  combined AS (
    SELECT
      wr.week_start,
      wr.gym_sessions,
      wr.mountain_days,
      wr.resort_days,
      wr.total_elevation_m,
      ROUND(wr.total_duration_sec / 3600.0, 1) AS total_hours,
      wr.total_calories,
      wg.total_gym_volume_kg,
      wg.total_srpe_load,
      -- 4-week rolling averages (gap-aware: only count weeks with data)
      AVG(wr.total_elevation_m) FILTER (WHERE wr.total_elevation_m > 0 OR wr.gym_sessions > 0)
        OVER (ORDER BY wr.week_start ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING) AS avg_elevation_4w,
      AVG(wg.total_gym_volume_kg) FILTER (WHERE wg.total_gym_volume_kg > 0)
        OVER (ORDER BY wr.week_start ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING) AS avg_gym_volume_4w,
      AVG(wg.total_srpe_load) FILTER (WHERE wg.total_srpe_load > 0)
        OVER (ORDER BY wr.week_start ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING) AS avg_srpe_load_4w,
      AVG(wr.total_duration_sec / 3600.0) FILTER (WHERE wr.total_duration_sec > 0)
        OVER (ORDER BY wr.week_start ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING) AS avg_hours_4w
    FROM weekly_raw wr
    JOIN weekly_gym wg ON wg.week_start = wr.week_start
  )

SELECT
  c.*,
  -- Spike detection: >15% above 4-week average on any key metric
  CASE WHEN c.avg_elevation_4w > 0 AND c.total_elevation_m > c.avg_elevation_4w * 1.15 THEN TRUE ELSE FALSE END AS elevation_spike,
  CASE WHEN c.avg_gym_volume_4w > 0 AND c.total_gym_volume_kg > c.avg_gym_volume_4w * 1.15 THEN TRUE ELSE FALSE END AS gym_volume_spike,
  CASE WHEN c.avg_srpe_load_4w > 0 AND c.total_srpe_load > c.avg_srpe_load_4w * 1.15 THEN TRUE ELSE FALSE END AS srpe_load_spike,
  CASE WHEN c.avg_hours_4w > 0 AND c.total_hours > c.avg_hours_4w * 1.15 THEN TRUE ELSE FALSE END AS duration_spike,
  -- Any spike flag
  CASE WHEN
    (c.avg_elevation_4w > 0 AND c.total_elevation_m > c.avg_elevation_4w * 1.15) OR
    (c.avg_gym_volume_4w > 0 AND c.total_gym_volume_kg > c.avg_gym_volume_4w * 1.15) OR
    (c.avg_srpe_load_4w > 0 AND c.total_srpe_load > c.avg_srpe_load_4w * 1.15) OR
    (c.avg_hours_4w > 0 AND c.total_hours > c.avg_hours_4w * 1.15)
  THEN TRUE ELSE FALSE END AS any_spike,
  -- Week-over-week changes
  c.total_elevation_m - LAG(c.total_elevation_m) OVER (ORDER BY c.week_start) AS elevation_wow_delta,
  c.total_gym_volume_kg - LAG(c.total_gym_volume_kg) OVER (ORDER BY c.week_start) AS gym_volume_wow_delta
FROM combined c
ORDER BY c.week_start DESC;


-- =============================================
-- FIX: Update daily_coaching_context view with correct activity types
-- The original (migration 014) used backcountry_skiing/resort_skiing
-- but actual Garmin data uses backcountry_snowboarding/resort_snowboarding.
-- CREATE OR REPLACE VIEW safely replaces the existing view.
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
      se.original_session,
      se.modified_workout,
      se.modification_type,
      se.reason AS exception_reason,
      se.pushed_to_garmin
    FROM session_exceptions se, today t
    WHERE se.date = t.d
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
  -- FIXED: added backcountry_snowboarding, resort_snowboarding
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


-- =============================================
-- FIX: Update weekly_coaching_summary with correct activity types
-- =============================================

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
  -- FIXED: added backcountry_snowboarding, resort_snowboarding
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
  (SELECT COUNT(*) FROM session_exceptions se
   WHERE se.date BETWEEN wr.week_start AND wr.week_end) AS exceptions_applied
FROM week_range wr;

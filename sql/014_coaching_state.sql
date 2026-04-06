-- =============================================
-- 014: Coaching State Tables
-- Moves structured coaching data from markdown into the database.
-- Replaces: coaching-context.md sections for injuries, exceptions,
-- decisions, preferences, and program structure.
-- coaching-program.md (read-only templates) → program_blocks + program_sessions.
--
-- The coaching agent queries these tables instead of reading markdown files,
-- cutting ~30K input tokens per daily run.
-- =============================================

-- =============================================
-- PROGRAM BLOCKS
-- Opus-authored training blocks (read-only to coach).
-- Maps 1:1 to sections in coaching-program.md.
-- =============================================

CREATE TABLE IF NOT EXISTS program_blocks (
  id BIGSERIAL PRIMARY KEY,
  block_number INTEGER NOT NULL,
  name TEXT NOT NULL,                          -- e.g. 'Base Rebuild Block 1'
  focus TEXT,                                  -- e.g. 'hypertrophy/strength base'
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  rpe_low REAL NOT NULL,                       -- target RPE floor
  rpe_high REAL NOT NULL,                      -- target RPE ceiling
  deload_week INTEGER,                         -- week number within block that is deload
  progression_rule TEXT,                       -- e.g. '+2.5kg/week barbell, +1kg accessories'
  stall_protocol TEXT,                         -- what to do on plateau
  notes TEXT,
  created_by TEXT DEFAULT 'opus',              -- 'opus' or 'user'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_program_blocks_num ON program_blocks(block_number);

-- =============================================
-- PROGRAM SESSIONS
-- Template definitions for each session type (A, B, C, A2, B2, mobility).
-- Exercises stored as JSONB array with full detail.
-- =============================================

CREATE TABLE IF NOT EXISTS program_sessions (
  id BIGSERIAL PRIMARY KEY,
  block_id BIGINT NOT NULL REFERENCES program_blocks(id) ON DELETE CASCADE,
  session_key TEXT NOT NULL,                   -- 'A', 'B', 'C', 'A2', 'B2', 'mobility'
  name TEXT NOT NULL,                          -- 'Strength A: Full Body'
  day_of_week TEXT NOT NULL,                   -- 'Monday', 'Wednesday', etc.
  estimated_duration_minutes INTEGER,
  session_type TEXT NOT NULL DEFAULT 'strength', -- 'strength', 'mobility', 'intervals'
  exercises JSONB NOT NULL,                    -- [{name, sets, reps, rpe_low, rpe_high, rest_s, start_kg, equipment, notes}]
  warmup JSONB,                                -- [{name, duration_s, reps, notes}]
  cooldown JSONB,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(block_id, session_key)
);

CREATE INDEX IF NOT EXISTS idx_program_sessions_block ON program_sessions(block_id);
CREATE INDEX IF NOT EXISTS idx_program_sessions_day ON program_sessions(day_of_week);

-- =============================================
-- SESSION EXCEPTIONS
-- One-day overrides to standard templates.
-- Coach can create these; they expire after the date passes.
-- =============================================

CREATE TABLE IF NOT EXISTS session_exceptions (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL UNIQUE,
  original_session TEXT NOT NULL,               -- what was scheduled, e.g. 'Strength C'
  modified_workout JSONB,                       -- replacement exercise list, or null for full skip
  modification_type TEXT NOT NULL DEFAULT 'swap', -- 'swap', 'reduce', 'skip', 'rest'
  reason TEXT NOT NULL,
  pushed_to_garmin BOOLEAN DEFAULT FALSE,
  created_by TEXT DEFAULT 'coach',              -- 'coach', 'user', 'opus'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_session_exceptions_date ON session_exceptions(date);

-- =============================================
-- INJURY LOG
-- Active injuries and accommodations.
-- Coach checks this before prescribing exercises.
-- =============================================

CREATE TABLE IF NOT EXISTS injury_log (
  id BIGSERIAL PRIMARY KEY,
  reported_date DATE NOT NULL,
  issue TEXT NOT NULL,                          -- 'broken rib', 'shoulder impingement'
  body_area TEXT,                               -- 'ribs', 'left shoulder', 'lower back'
  status TEXT NOT NULL DEFAULT 'active',        -- 'active', 'monitoring', 'resolved'
  severity TEXT DEFAULT 'moderate',             -- 'mild', 'moderate', 'severe'
  accommodations TEXT,                          -- 'avoid overhead pressing, no heavy bracing'
  resolved_date DATE,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_injury_log_status ON injury_log(status);

-- =============================================
-- COACHING PREFERENCES
-- Learned preferences from user interactions.
-- Key-value with category for structured access.
-- =============================================

CREATE TABLE IF NOT EXISTS coaching_preferences (
  id BIGSERIAL PRIMARY KEY,
  category TEXT NOT NULL,                       -- 'delivery', 'training', 'nutrition', 'calendar'
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  source TEXT DEFAULT 'user',                   -- 'user', 'observed', 'opus'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(category, key)
);

-- =============================================
-- SEASON CONTEXT
-- Current and upcoming season phases.
-- Drives transition triggers and activity classification.
-- =============================================

CREATE TABLE IF NOT EXISTS season_phases (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,                           -- 'Winter/Spring Mountain Primary'
  start_date DATE NOT NULL,
  end_date DATE,                                -- null = ongoing
  primary_focus TEXT NOT NULL,                  -- 'mountain', 'gym', 'mixed'
  secondary_focus TEXT,
  transition_triggers TEXT,                     -- conditions that end this phase
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- RECOVERY DECISION MATRIX
-- Pre-defined rules from coaching-context.md.
-- Agent looks up the matching rule instead of parsing markdown.
-- =============================================

CREATE TABLE IF NOT EXISTS recovery_rules (
  id BIGSERIAL PRIMARY KEY,
  hrv_status TEXT NOT NULL,                     -- 'BALANCED', 'UNBALANCED', 'LOW'
  sleep_condition TEXT NOT NULL,                -- '>=7h', '6-7h', '<6h'
  action TEXT NOT NULL,                         -- 'train_as_planned', 'moderate_rpe', 'reduce_30pct', 'rest_or_mobility'
  rpe_adjustment TEXT,                          -- 'RPE 7-8', 'RPE 6-7', 'RPE 5-6'
  volume_adjustment TEXT,                       -- null, 'reduce 30%', 'mobility only'
  override_note TEXT,                           -- 'body_battery <30 OR training_readiness <40 → hard override to rest'
  priority INTEGER DEFAULT 10,                  -- lower = higher priority, for override rules
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(hrv_status, sleep_condition)
);

-- =============================================
-- DAILY COACHING CONTEXT VIEW
-- Single query gives the agent everything it needs for today.
-- Replaces reading 3 markdown files (~30K tokens).
-- =============================================

CREATE OR REPLACE VIEW daily_coaching_context AS
WITH
  today AS (SELECT CURRENT_DATE AS d),
  -- Current block and week
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
  -- Today's scheduled session
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
  -- Any exception for today
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
  -- Recovery data (today or most recent)
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
  -- Active injuries
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
  -- Recent mountain activity (last 3 days)
  recent_mountain AS (
    SELECT
      COUNT(*) AS mountain_days_3d,
      COALESCE(SUM(a.elevation_gain), 0) AS elevation_3d,
      COALESCE(SUM(a.duration_seconds), 0) AS mountain_duration_3d
    FROM activities a
    WHERE a.date >= CURRENT_DATE - 3
      AND a.activity_type IN ('backcountry_skiing', 'hiking', 'mountaineering', 'splitboarding')
  ),
  -- Week's gym session count
  week_gym AS (
    SELECT COUNT(*) AS gym_sessions_this_week
    FROM activities a
    WHERE a.date >= DATE_TRUNC('week', CURRENT_DATE)
      AND a.activity_type IN ('strength_training', 'indoor_cardio')
  ),
  -- Matching recovery rule
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
  -- Current season
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
  -- Program context
  cb.block_number,
  cb.block_name,
  cb.current_week,
  cb.is_deload_week,
  cb.rpe_low AS block_rpe_low,
  cb.rpe_high AS block_rpe_high,
  cb.progression_rule,
  -- Today's session
  ts.session_key,
  ts.session_name,
  ts.session_type,
  ts.estimated_duration_minutes,
  ts.exercises AS session_exercises,
  ts.warmup AS session_warmup,
  -- Exception override
  te.original_session AS exception_original,
  te.modified_workout AS exception_workout,
  te.modification_type AS exception_type,
  te.exception_reason,
  -- Recovery
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
  -- Recovery rule match
  rr.action AS recovery_action,
  rr.rpe_adjustment AS recovery_rpe,
  rr.volume_adjustment AS recovery_volume,
  -- Hard overrides
  CASE
    WHEN r.body_battery_highest < 30 THEN 'body_battery_critical'
    WHEN r.training_readiness_score < 40 THEN 'training_readiness_low'
    WHEN r.hrv_status = 'LOW' AND r.total_sleep_seconds < 21600 THEN 'multi_signal_degraded'
    ELSE NULL
  END AS hard_override,
  -- Context
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
-- WEEKLY COACHING SUMMARY VIEW
-- Pre-aggregated data for the weekly review cron job.
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
  -- Gym sessions
  (SELECT COUNT(*) FROM activities a
   WHERE a.date BETWEEN wr.week_start AND wr.week_end
     AND a.activity_type = 'strength_training') AS gym_sessions,
  -- Mountain activities
  (SELECT COUNT(*) FROM activities a
   WHERE a.date BETWEEN wr.week_start AND wr.week_end
     AND a.activity_type IN ('backcountry_skiing','resort_skiing','hiking','mountaineering','splitboarding')) AS mountain_days,
  (SELECT COALESCE(SUM(a.elevation_gain), 0) FROM activities a
   WHERE a.date BETWEEN wr.week_start AND wr.week_end
     AND a.activity_type IN ('backcountry_skiing','hiking','mountaineering','splitboarding')) AS total_elevation,
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
  (SELECT COUNT(*) FROM session_exceptions se
   WHERE se.date BETWEEN wr.week_start AND wr.week_end) AS exceptions_applied
FROM week_range wr;

-- =============================================
-- INDEXES ON EXISTING TABLES (if missing)
-- =============================================

CREATE INDEX IF NOT EXISTS idx_activities_type_date ON activities(activity_type, date);
CREATE INDEX IF NOT EXISTS idx_coaching_log_type_date ON coaching_log(type, date);

-- =============================================
-- 017: Coaching Decision Retrospective + Progression Velocity
--
-- Adds:
-- 1. coaching_decision_outcomes — evaluates whether rest/train/adjust
--    decisions led to better or worse outcomes
-- 2. progression_velocity — tracks if exercise progression matches
--    expected rates, flags stalls and ahead-of-schedule lifts
--
-- Together with athlete_response_patterns (016), this closes the
-- coaching decision feedback loop: decide → observe outcome → learn.
-- =============================================

-- =============================================
-- COACHING DECISION OUTCOMES
-- Links coaching_log decisions to measurable results.
-- Populated by scripts/decision_retrospective.py
-- =============================================

CREATE TABLE IF NOT EXISTS coaching_decision_outcomes (
  id BIGSERIAL PRIMARY KEY,
  coaching_log_id BIGINT REFERENCES coaching_log(id),
  decision_date DATE NOT NULL,
  decision_type TEXT NOT NULL,            -- 'train_as_planned', 'train_moderate', 'volume_reduction', 'rest_override', 'session_swap', 'schedule_change'
  recovery_signals JSONB,                 -- HRV, sleep, wellness at decision time
  next_session_performance JSONB,         -- volume, RPE, compliance of next gym session
  recovery_trajectory JSONB,              -- HRV/sleep change 24-48h after decision
  outcome_quality TEXT,                   -- 'good', 'neutral', 'poor'
  assessment_notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(coaching_log_id)
);

CREATE INDEX IF NOT EXISTS idx_decision_outcomes_date ON coaching_decision_outcomes(decision_date);
CREATE INDEX IF NOT EXISTS idx_decision_outcomes_type ON coaching_decision_outcomes(decision_type);
CREATE INDEX IF NOT EXISTS idx_decision_outcomes_quality ON coaching_decision_outcomes(outcome_quality);

-- RLS
ALTER TABLE coaching_decision_outcomes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_read" ON coaching_decision_outcomes FOR SELECT TO anon USING (true);
CREATE POLICY "service_all" ON coaching_decision_outcomes FOR ALL TO service_role USING (true);

-- =============================================
-- PROGRESSION VELOCITY VIEW
-- Tracks whether each exercise is progressing at the expected rate.
-- Joins exercise_progression (planned decisions) with training_sets
-- (actual performance) over time.
-- =============================================

CREATE OR REPLACE VIEW progression_velocity AS
WITH
  -- Get the latest progression entry per exercise (current planned state)
  latest_progression AS (
    SELECT DISTINCT ON (exercise_name)
      exercise_name,
      date AS latest_date,
      planned_weight_kg,
      planned_reps,
      planned_sets,
      progression_applied,
      progression_amount
    FROM exercise_progression
    ORDER BY exercise_name, date DESC
  ),
  -- Count consecutive sessions at the same weight (stall detection)
  weight_history AS (
    SELECT
      exercise_name,
      date,
      planned_weight_kg,
      LAG(planned_weight_kg) OVER (PARTITION BY exercise_name ORDER BY date) AS prev_weight
    FROM exercise_progression
    WHERE planned_weight_kg IS NOT NULL
  ),
  stall_count AS (
    SELECT
      exercise_name,
      COUNT(*) AS sessions_at_weight
    FROM (
      SELECT
        exercise_name,
        planned_weight_kg,
        date,
        SUM(CASE WHEN planned_weight_kg != COALESCE(prev_weight, planned_weight_kg) THEN 1 ELSE 0 END)
          OVER (PARTITION BY exercise_name ORDER BY date DESC) AS weight_group
      FROM weight_history
    ) grouped
    WHERE weight_group = 0
    GROUP BY exercise_name
  ),
  -- First recorded weight per exercise (to compute total progress)
  first_weight AS (
    SELECT DISTINCT ON (exercise_name)
      exercise_name,
      date AS first_date,
      planned_weight_kg AS start_weight_kg
    FROM exercise_progression
    WHERE planned_weight_kg IS NOT NULL AND planned_weight_kg > 0
    ORDER BY exercise_name, date ASC
  ),
  -- E1RM trend: compute estimated 1RM from training_sets over last 30 days
  recent_e1rm AS (
    SELECT
      e.name AS exercise_name,
      ts.date AS session_date,
      MAX(tsets.estimated_1rm) AS max_e1rm
    FROM training_sets tsets
    JOIN training_sessions ts ON tsets.session_id = ts.id
    JOIN exercises e ON tsets.exercise_id = e.id
    WHERE ts.date >= CURRENT_DATE - 30
      AND tsets.set_type = 'working'
      AND tsets.estimated_1rm IS NOT NULL
    GROUP BY e.name, ts.date
  ),
  e1rm_trend AS (
    SELECT
      exercise_name,
      -- Simple slope: (last - first) / days
      CASE
        WHEN COUNT(*) >= 2
        THEN (MAX(max_e1rm) - MIN(max_e1rm)) / NULLIF(MAX(session_date) - MIN(session_date), 0)
        ELSE NULL
      END AS e1rm_slope_per_day,
      MAX(max_e1rm) AS current_e1rm,
      COUNT(*) AS sessions_30d
    FROM recent_e1rm
    GROUP BY exercise_name
  )
SELECT
  lp.exercise_name,
  lp.latest_date,
  lp.planned_weight_kg,
  lp.planned_reps,
  lp.planned_sets,
  lp.progression_applied AS last_action,
  fw.start_weight_kg,
  fw.first_date AS tracking_since,
  -- Total progress
  ROUND((lp.planned_weight_kg - COALESCE(fw.start_weight_kg, lp.planned_weight_kg))::numeric, 1) AS total_weight_gain_kg,
  -- Weeks tracked
  GREATEST(1, (lp.latest_date - COALESCE(fw.first_date, lp.latest_date)) / 7) AS weeks_tracked,
  -- Weight gain per week
  CASE
    WHEN fw.first_date IS NOT NULL AND lp.latest_date > fw.first_date
    THEN ROUND(
      ((lp.planned_weight_kg - fw.start_weight_kg) / NULLIF((lp.latest_date - fw.first_date) / 7.0, 0))::numeric,
      2
    )
    ELSE NULL
  END AS kg_per_week,
  -- Stall info
  COALESCE(sc.sessions_at_weight, 1) AS sessions_at_current_weight,
  -- Progression status
  CASE
    WHEN COALESCE(sc.sessions_at_weight, 1) >= 4 THEN 'stalled'
    WHEN COALESCE(sc.sessions_at_weight, 1) >= 3 THEN 'behind'
    WHEN lp.progression_applied = 'weight_increase' THEN 'on_track'
    WHEN lp.progression_applied IN ('deload_reset', 'deload_week') THEN 'deloading'
    ELSE 'on_track'
  END AS progression_status,
  -- E1RM data
  et.current_e1rm,
  et.e1rm_slope_per_day,
  et.sessions_30d AS e1rm_data_points
FROM latest_progression lp
LEFT JOIN first_weight fw ON lp.exercise_name = fw.exercise_name
LEFT JOIN stall_count sc ON lp.exercise_name = sc.exercise_name
LEFT JOIN e1rm_trend et ON lp.exercise_name = et.exercise_name
ORDER BY
  CASE
    WHEN COALESCE(sc.sessions_at_weight, 1) >= 4 THEN 0  -- stalled first
    WHEN COALESCE(sc.sessions_at_weight, 1) >= 3 THEN 1
    ELSE 2
  END,
  lp.exercise_name;

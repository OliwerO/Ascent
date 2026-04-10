-- Fix progression_velocity: don't flag exercises at their starting weight as "stalled"
--
-- Before: 4+ sessions at same weight → "stalled" regardless
-- After:  4+ sessions at same weight AND weight > start_weight → "stalled"
--         4+ sessions at same weight AND weight = start_weight → "building" (still at starting weight)
--
-- This prevents false stall alerts in the first weeks of a new program.

CREATE OR REPLACE VIEW progression_velocity AS
WITH
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
  first_weight AS (
    SELECT DISTINCT ON (exercise_name)
      exercise_name,
      date AS first_date,
      planned_weight_kg AS start_weight_kg
    FROM exercise_progression
    WHERE planned_weight_kg IS NOT NULL AND planned_weight_kg > 0
    ORDER BY exercise_name, date ASC
  ),
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
  ROUND((lp.planned_weight_kg - COALESCE(fw.start_weight_kg, lp.planned_weight_kg))::numeric, 1) AS total_weight_gain_kg,
  GREATEST(1, (lp.latest_date - COALESCE(fw.first_date, lp.latest_date)) / 7) AS weeks_tracked,
  CASE
    WHEN fw.first_date IS NOT NULL AND lp.latest_date > fw.first_date
    THEN ROUND(
      ((lp.planned_weight_kg - fw.start_weight_kg) / NULLIF((lp.latest_date - fw.first_date) / 7.0, 0))::numeric,
      2
    )
    ELSE NULL
  END AS kg_per_week,
  COALESCE(sc.sessions_at_weight, 1) AS sessions_at_current_weight,
  -- FIX: only flag "stalled" if weight has increased at least once from start
  -- If still at starting weight, it's "building" (not enough time to progress yet)
  CASE
    WHEN COALESCE(sc.sessions_at_weight, 1) >= 4
      AND lp.planned_weight_kg > COALESCE(fw.start_weight_kg, lp.planned_weight_kg)
    THEN 'stalled'
    WHEN COALESCE(sc.sessions_at_weight, 1) >= 4
      AND lp.planned_weight_kg <= COALESCE(fw.start_weight_kg, lp.planned_weight_kg)
    THEN 'building'
    WHEN COALESCE(sc.sessions_at_weight, 1) >= 3
      AND lp.planned_weight_kg > COALESCE(fw.start_weight_kg, lp.planned_weight_kg)
    THEN 'behind'
    WHEN lp.progression_applied = 'weight_increase' THEN 'on_track'
    WHEN lp.progression_applied IN ('deload_reset', 'deload_week') THEN 'deloading'
    ELSE 'on_track'
  END AS progression_status,
  et.current_e1rm,
  et.e1rm_slope_per_day,
  et.sessions_30d AS e1rm_data_points
FROM latest_progression lp
LEFT JOIN first_weight fw ON lp.exercise_name = fw.exercise_name
LEFT JOIN stall_count sc ON lp.exercise_name = sc.exercise_name
LEFT JOIN e1rm_trend et ON lp.exercise_name = et.exercise_name
ORDER BY
  CASE
    WHEN COALESCE(sc.sessions_at_weight, 1) >= 4
      AND lp.planned_weight_kg > COALESCE(fw.start_weight_kg, lp.planned_weight_kg) THEN 1
    WHEN COALESCE(sc.sessions_at_weight, 1) >= 3
      AND lp.planned_weight_kg > COALESCE(fw.start_weight_kg, lp.planned_weight_kg) THEN 2
    ELSE 3
  END,
  lp.exercise_name;

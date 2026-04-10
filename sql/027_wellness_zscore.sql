-- =============================================
-- 027: Wellness Z-score normalization
--
-- KB §4.3 specifies normalizing wellness scores to individual Z-scores
-- against a 14-day rolling baseline. This migration adds a view that
-- computes Z-scores and a consecutive-degraded-days flag.
--
-- Also updates daily_coaching_context with wellness_zscore and
-- wellness_degraded_streak columns.
-- =============================================


-- Standalone view for wellness Z-score tracking
CREATE OR REPLACE VIEW wellness_zscore AS
WITH
  baselines AS (
    SELECT
      sw.date,
      sw.composite_score,
      sw.sleep_quality,
      sw.energy,
      sw.muscle_soreness,
      sw.motivation,
      sw.stress,
      -- 14-day rolling baseline (requires >=5 data points)
      AVG(sw2.composite_score) AS baseline_mean,
      STDDEV_SAMP(sw2.composite_score) AS baseline_sd,
      COUNT(sw2.composite_score) AS baseline_n
    FROM subjective_wellness sw
    LEFT JOIN subjective_wellness sw2
      ON sw2.date BETWEEN sw.date - 14 AND sw.date - 1
    GROUP BY sw.date, sw.composite_score, sw.sleep_quality,
             sw.energy, sw.muscle_soreness, sw.motivation, sw.stress
  )
SELECT
  b.date,
  b.composite_score,
  b.baseline_mean,
  b.baseline_sd,
  b.baseline_n,
  -- Z-score: only compute when we have enough baseline data and non-zero SD
  CASE
    WHEN b.baseline_n >= 5 AND b.baseline_sd > 0.01
    THEN ROUND(((b.composite_score - b.baseline_mean) / b.baseline_sd)::numeric, 2)
    ELSE NULL
  END AS composite_zscore,
  -- Flag: is this day degraded (Z < -1.0)?
  CASE
    WHEN b.baseline_n >= 5 AND b.baseline_sd > 0.01
         AND (b.composite_score - b.baseline_mean) / b.baseline_sd < -1.0
    THEN TRUE
    ELSE FALSE
  END AS is_degraded
FROM baselines b
ORDER BY b.date DESC;


-- View for consecutive degraded days (for alerting)
CREATE OR REPLACE VIEW wellness_degraded_streak AS
WITH
  daily_status AS (
    SELECT
      wz.date,
      wz.composite_zscore,
      wz.is_degraded,
      -- Count consecutive degraded days ending on this date
      ROW_NUMBER() OVER (ORDER BY wz.date DESC) -
      ROW_NUMBER() OVER (
        PARTITION BY wz.is_degraded
        ORDER BY wz.date DESC
      ) AS grp
    FROM wellness_zscore wz
    WHERE wz.date >= CURRENT_DATE - 14
  )
SELECT
  CURRENT_DATE AS check_date,
  COUNT(*) FILTER (WHERE is_degraded) AS degraded_streak,
  MIN(date) FILTER (WHERE is_degraded) AS streak_start
FROM daily_status
WHERE is_degraded = TRUE
  AND grp = (
    SELECT ds2.grp
    FROM daily_status ds2
    WHERE ds2.date = CURRENT_DATE AND ds2.is_degraded = TRUE
    LIMIT 1
  );

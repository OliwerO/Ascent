# Ascent — Grafana Dashboard Spec

> Created: 2026-03-28
> Data source: Supabase (PostgreSQL)
> Platform: Grafana Cloud
> Primary device: Phone (mobile-first layout)

-----

## Dashboard 1: Daily Overview

**Purpose:** Morning check-in dashboard. Glanceable on phone without scrolling. Shows today's recovery state + yesterday's activity.

**Design note:** This dashboard must be scannable in <30 seconds on a phone. Every panel must answer: *should I train normally today?* Maximum 5–6 panels. Use Grafana Stat panel background color mode (entire panel turns green/amber/red) rather than small color indicators.

**Layout:** Single-column, mobile-optimized. 6 panels stacked vertically.

### Panel 1: Recovery Status (Stat panel, full width)

Three stat values side by side. **Use personal rolling baselines** (30-day mean ± 1 SD), not fixed population thresholds, for all color coding:

- **HRV** — last_night_avg from `hrv` table. Color: green if within baseline balanced range, yellow if below balanced_low, red if >15% below baseline_low_upper.
- **Sleep Score** — overall_score from `sleep` table. Color: green >75, yellow 60-75, red <60.
- **Training Readiness** — training_readiness_score from `daily_metrics`. Color: green >60, yellow 40-60, red <40.

**Future addition:** Once the Telegram/Slack subjective wellness questionnaire is implemented, add subjective wellness composite score to this panel as the primary readiness metric (strongest evidence base).

```sql
SELECT
  h.last_night_avg AS "HRV",
  s.overall_score AS "Sleep",
  dm.training_readiness_score AS "Readiness"
FROM daily_metrics dm
LEFT JOIN hrv h ON dm.date = h.date
LEFT JOIN sleep s ON dm.date = s.date
WHERE dm.date = CURRENT_DATE
```

### Panel 2: Body Battery (Gauge panel)

- Shows current day's body_battery_highest and body_battery_lowest
- Gauge from 0–100
- Thresholds: green >60, yellow 30-60, red <30

### Panel 3: Weight (Stat + sparkline)

- Current weight from `body_composition` (most recent)
- 7-day sparkline trend
- Show delta from 7 days ago

```sql
SELECT date, weight_kg
FROM body_composition
WHERE source = 'garmin'
AND date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date
```

### Panel 4: HRV 30-Day Rolling Average (Time series, compact)

- Line chart: last_night_avg daily values
- Overlay: 30-day rolling average line
- Baseline band (balanced_low to balanced_upper) as shaded region

```sql
SELECT
  date,
  last_night_avg,
  AVG(last_night_avg) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS rolling_30d_avg,
  baseline_balanced_low,
  baseline_balanced_upper
FROM hrv
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY date
```

### Panel 5: Sleep Score Trend (Time series, compact)

- Line chart: 14-day sleep scores
- Horizontal reference line at 60 (alert threshold)
- Color-coded: green >75, yellow 60-75, red <60

```sql
SELECT date, overall_score, quality_score, duration_score
FROM sleep
WHERE date >= CURRENT_DATE - INTERVAL '14 days'
ORDER BY date
```

### Panel 6: Yesterday's Activity (Table, compact)

- List of activities from yesterday
- Columns: type, duration, calories, avg HR, elevation gain

```sql
SELECT
  activity_type,
  activity_name,
  (duration_seconds / 60)::INTEGER AS duration_min,
  calories,
  avg_hr,
  elevation_gain
FROM activities
WHERE date = CURRENT_DATE - 1
ORDER BY start_time
```

-----

## Dashboard 2: Training Detail

**Purpose:** Weekly/on-demand deep dive. Training volume analysis, progression tracking, body comp trends. Check during weekly review or when curious.

**Design note:** Default to collapsed rows on mobile; expand on tap. Use progressive disclosure — summary stats visible, detail charts collapsed.

**Layout:** Single-column mobile-first, scrollable. 7 panels.

### Panel 1: Weekly Training Volume — Gym vs Mountain (Bar chart)

- Stacked bar chart, one bar per week
- Two series: "Gym" (sum of training_sets.volume_kg per week) and "Mountain" (sum of elevation_gain from activities where type in splitboarding, snowboarding, hiking, ski touring)
- Last 12 weeks

```sql
-- Gym volume per week
SELECT
  date_trunc('week', ts.date) AS week,
  SUM(tset.volume_kg) AS gym_volume_kg
FROM training_sessions ts
JOIN training_sets tset ON tset.session_id = ts.id
WHERE ts.date >= CURRENT_DATE - INTERVAL '12 weeks'
GROUP BY week
ORDER BY week;

-- Mountain volume per week (elevation gain as proxy)
SELECT
  date_trunc('week', date) AS week,
  SUM(elevation_gain) AS mountain_elevation_m
FROM activities
WHERE activity_type IN ('splitboarding', 'snowboarding', 'hiking', 'ski_touring', 'resort_skiing', 'backcountry_skiing')
AND date >= CURRENT_DATE - INTERVAL '12 weeks'
GROUP BY week
ORDER BY week;
```

### Panel 2: Elevation Gain Per Week (Bar chart)

- Simple bar chart, one bar per week
- Total elevation gain from all activities
- Last 12 weeks
- Useful for tracking touring volume and endurance load

```sql
SELECT
  date_trunc('week', date) AS week,
  SUM(elevation_gain) AS total_elevation_m,
  COUNT(*) AS activity_count
FROM activities
WHERE elevation_gain > 0
AND date >= CURRENT_DATE - INTERVAL '12 weeks'
GROUP BY week
ORDER BY week
```

### Panel 3: Weight vs Body Fat % Over Time (Dual-axis time series)

- Left axis: weight_kg (line)
- Right axis: body_fat_pct (line, different color)
- Last 90 days
- Annotations for DEXA/BIA scan dates if available
- Target lines: weight ~87-88 kg, body fat ~13-14%

```sql
SELECT
  date,
  weight_kg,
  body_fat_pct,
  muscle_mass_grams / 1000.0 AS muscle_mass_kg
FROM body_composition
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY date
```

### Panel 4: Estimated 1RM Progression Per Lift (Multi-line time series)

- One line per compound lift: bench press, squat, deadlift, overhead press, rows
- Y axis: estimated_1rm (best per session)
- Last 16 weeks
- Only show working sets (set_type = 'working')
- **Note:** Normal session-to-session e1RM variation is ±3–5%. Only flag plateaus after ≥4 weeks of flat/declining trend. Cross-reference with mountain activity log before concluding "plateau."

```sql
SELECT
  ts.date,
  e.name AS exercise,
  MAX(tset.estimated_1rm) AS best_e1rm
FROM training_sets tset
JOIN training_sessions ts ON tset.session_id = ts.id
JOIN exercises e ON tset.exercise_id = e.id
WHERE e.name IN ('Bench Press', 'Squat', 'Deadlift', 'Overhead Press', 'Barbell Row')
AND tset.set_type = 'working'
AND ts.date >= CURRENT_DATE - INTERVAL '16 weeks'
GROUP BY ts.date, e.name
ORDER BY ts.date
```

### Panel 5: Sleep Architecture (Stacked area chart)

- Stacked areas: deep, light, REM, awake (in seconds → hours)
- Last 14 days
- Useful for spotting deep sleep deficits
- **Label as "approximate — ±45 min accuracy per stage"** and never color-code individual stages red/green. Garmin correctly classifies only ~69% of sleep epochs vs PSG; REM detection is only 33% accurate (Schyvens et al. 2025).

```sql
SELECT
  date,
  deep_sleep_seconds / 3600.0 AS deep_hrs,
  light_sleep_seconds / 3600.0 AS light_hrs,
  rem_sleep_seconds / 3600.0 AS rem_hrs,
  awake_seconds / 3600.0 AS awake_hrs
FROM sleep
WHERE date >= CURRENT_DATE - INTERVAL '14 days'
ORDER BY date
```

### Panel 6: Activity Calendar (Heatmap or table)

- Last 30 days
- Color by activity type (gym = blue, mountain = green, rest = gray)
- Shows training distribution and rest day patterns

```sql
SELECT
  date,
  activity_type,
  duration_seconds / 60 AS duration_min,
  elevation_gain
FROM activities
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC
```

### Panel 7: VO2max Trend (Time series)

- Line chart from daily_metrics.vo2max
- Last 90 days
- Slow-moving metric but important for endurance goal tracking

```sql
SELECT date, vo2max
FROM daily_metrics
WHERE vo2max IS NOT NULL
AND date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY date
```

-----

## Dashboard 3: Quarterly Strategic Review

**Purpose:** Deep analysis for seasonal planning and goal review. 20–30 minute session, ideally quarterly (or at end of each training block). This dashboard is for detailed analysis, not phone glance — wider panels, multi-axis charts acceptable.

**Layout:** Wider panels, multi-axis charts, scrollable. Best viewed on tablet or desktop.

### Panel 1: Training Volume & Intensity Evolution (Stacked area, 90 days)

- Stacked area chart: weekly training volume by type (strength volume in kg, mountain elevation in m, other cardio in minutes)
- Overlay: average weekly sRPE load (once sRPE capture is implemented)
- 90-day view

```sql
SELECT
  date_trunc('week', date) AS week,
  SUM(CASE WHEN activity_type = 'strength_training' THEN duration_seconds / 60.0 ELSE 0 END) AS gym_minutes,
  SUM(CASE WHEN activity_type IN ('ski_touring', 'splitboarding', 'hiking', 'resort_skiing', 'backcountry_skiing')
      THEN elevation_gain ELSE 0 END) AS mountain_elevation_m,
  SUM(CASE WHEN activity_type NOT IN ('strength_training', 'ski_touring', 'splitboarding', 'hiking', 'resort_skiing', 'backcountry_skiing')
      THEN duration_seconds / 60.0 ELSE 0 END) AS other_minutes
FROM activities
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY week
ORDER BY week
```

### Panel 2: Fitness Progression (Multi-line time series, 90 days)

- VO2max 90-day trend (running-derived only — filter by activity_type)
- Display as "48 ± 5 ml/kg/min" with confidence band
- Flag single-session changes >3 ml/kg/min as noise

```sql
SELECT date, vo2max
FROM daily_metrics
WHERE vo2max IS NOT NULL
AND date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY date
```

### Panel 3: e1RM Trajectories for Compound Lifts (Multi-line, 90 days)

- One line per lift: squat, deadlift, bench press, overhead press, barbell row
- Best e1RM per session, with 30-day rolling average overlay
- Flag lifts with ≥4 weeks flat/declining as "plateau detected"

### Panel 4: Body Composition Trend (Dual-axis, 90 days)

- Weight 90-day EWMA trend line with target band
- Body fat % overlay if available (from eGym scans)
- Muscle mass overlay if available

```sql
SELECT date, weight_kg, body_fat_pct, muscle_mass_grams / 1000.0 AS muscle_mass_kg, source
FROM body_composition
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY date
```

### Panel 5: Season Periodization Timeline (Annotated)

- Annotated timeline showing training blocks (strength focus, pre-season, in-season, transition)
- Key events: races, multi-day trips, illness, deload weeks
- Manual annotations from coaching_log or goals table

### Panel 6: Goal Progress (Stat panels)

- Current vs target for each active goal
- Progress percentage and projected completion date

```sql
SELECT category, metric, target_value, current_value,
  ROUND((current_value / NULLIF(target_value, 0)) * 100) AS progress_pct
FROM goals
WHERE status = 'active'
ORDER BY category
```

-----

## Alerts (via Grafana → Telegram)

All alerts delivered via Grafana alerting → webhook to Jarvis/Telegram.

**Design principles:**
- **Compound conditions required:** Alerts should fire only when 2+ signals converge (e.g., HRV drop AND poor sleep, not HRV drop alone). Compound conditions dramatically reduce false positives.
- **Time-delay filtering:** Require 2–3 consecutive concerning days before alerting. Single-day anomalies are noise.
- **Three-tier structure:** Red (push notification — requires action), Amber (dashboard badge — visible at next check), Informational (weekly summary only — no real-time alert).
- **Target:** No more than 1–2 genuine alerts per week. If exceeding this, thresholds are too sensitive.

### Alert 1: Recovery Compound Alert (RED tier)

```
Condition: 7-day rolling ln(rMSSD) drops >1.5 SD below 60-day baseline
         for 2+ consecutive days
         AND sleep quality below threshold (total_sleep < 6h OR overall_score < 60)
Evaluation: Daily at 07:00
Message: "Recovery Alert: HRV has been significantly below your baseline for {days} days,
         and sleep quality is also compromised. Consider a lighter session or rest day today."
Cooldown: 48 hours
```

### Alert 2: Sleep Score <60 (AMBER tier)

```
Condition: overall_score < 60 for 2+ consecutive nights
Evaluation: Daily at 07:00
Message: "Sleep Alert: Score below 60 for {count} consecutive nights. Recovery may be accumulating a deficit."
Cooldown: 48 hours
Delivery: Dashboard badge (not push notification unless 3+ nights)
```

### Alert 3: Training Status = Detraining (INFORMATIONAL tier)

```
Condition: training_readiness field or Garmin training_status indicates 'detraining'
Evaluation: Daily
Message: Included in weekly summary only — "Garmin reported 'detraining' on {dates}. Note: this can be triggered by GPS/HR artifacts."
Delivery: Weekly summary only (Garmin Training Status is Tier 3 — contextual, never drives decisions)
```

### Alert 4: Weight Trend Shift (AMBER tier)

```
Condition: 7-day rolling average shifts >0.5 kg sustained over 2+ weeks
         (compared to previous 30-day rolling average)
Evaluation: Weekly (Sunday)
Message: "Weight Trend: 7-day average has shifted {direction} by {delta}kg over the past {weeks} weeks (now {current}kg)."
Cooldown: 1 week
Delivery: Dashboard badge + weekly summary
```

### Alert 5: Training Load Spike (RED tier)

```
Condition: Current week's total sRPE load > 115% of 28-day rolling average
         (once sRPE capture is implemented)
Evaluation: Daily
Message: "Load Alert: This week's training load is {pct}% above your 4-week average. Consider moderating remaining sessions."
Cooldown: 1 week
```

-----

## Implementation Notes

### Data Source

- Grafana Cloud → PostgreSQL data source → Supabase connection string
- Use the **anon key** (read-only after RLS is applied) — Grafana only needs SELECT access
- Connection: `postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`

### Mobile Optimization

- All panels: single column layout
- Stat panels: use large font, minimal labels
- Time series: default to 14-day or 30-day view (not 90 — too compressed on phone)
- Avoid tables with many columns — 4 max on mobile
- Use Grafana's mobile app or browser bookmarks for quick access

### Grafana Alert → Telegram Integration

- Option A: Grafana webhook → OpenClaw endpoint → Jarvis → Telegram
- Option B: Grafana webhook → Telegram Bot API directly (simpler but bypasses Jarvis context)
- **Recommended: Option A** — routes through Jarvis so the coach can add context to the alert message (e.g., "HRV is low AND you had a hard mountain day yesterday, so this is expected" vs. a raw number alert)

### Dashboard Variables

- `$timerange` — adjustable time window (7d, 14d, 30d, 90d)
- `$activity_type` — filter activities by type (all, gym, mountain, cardio)

-----

## Pending Decisions

- [ ] Exact Garmin activity_type strings — need to confirm from actual synced data (e.g., is it 'splitboarding' or 'backcountry_snowboarding'?)
- [ ] Grafana Cloud plan — free tier supports 3 users, 10k metrics, 14 days retention. Should be sufficient for single user.
- [ ] Alert webhook URL — depends on OpenClaw endpoint setup
- [ ] Whether to add a third dashboard later for blood work / biomarker tracking

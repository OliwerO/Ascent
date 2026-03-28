# Ascent — Grafana Dashboard Spec

> Created: 2026-03-28
> Data source: Supabase (PostgreSQL)
> Platform: Grafana Cloud
> Primary device: Phone (mobile-first layout)

-----

## Dashboard 1: Daily Overview

**Purpose:** Morning check-in dashboard. Glanceable on phone without scrolling. Shows today's recovery state + yesterday's activity.

**Layout:** Single-column, mobile-optimized. 6 panels stacked vertically.

### Panel 1: Recovery Status (Stat panel, full width)

Three stat values side by side:

- **HRV** — last_night_avg from `hrv` table. Color: green if within baseline balanced range, yellow if below balanced_low, red if >15% below baseline_low_upper.
- **Sleep Score** — overall_score from `sleep` table. Color: green >75, yellow 60-75, red <60.
- **Training Readiness** — training_readiness_score from `daily_metrics`. Color: green >60, yellow 40-60, red <40.

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

## Alerts (via Grafana → Telegram)

All alerts delivered via Grafana alerting → webhook to Jarvis/Telegram.

### Alert 1: HRV Drop >15% from Baseline

```
Condition: last_night_avg < (baseline_balanced_low * 0.85)
Evaluation: Daily at 07:00
Message: "HRV Alert: Last night's HRV ({value}) is >15% below your baseline. Consider a lighter session today."
Cooldown: 24 hours (don't repeat same-day)
```

### Alert 2: Sleep Score <60

```
Condition: overall_score < 60
Evaluation: Daily at 07:00
Message: "Sleep Alert: Score was {value} last night. Recovery may be impaired — consider adjusting today's training intensity."
Cooldown: 24 hours
```

### Alert 3: Training Status = Detraining

```
Condition: training_readiness field or Garmin training_status indicates 'detraining'
Evaluation: Daily
Message: "Training Status: Garmin reports 'detraining'. You may need to increase training stimulus this week."
Cooldown: 48 hours (this status persists, don't spam)
```

### Alert 4: Weight Change >1kg in 3 Days

```
Condition: ABS(today_weight - weight_3_days_ago) > 1.0
Evaluation: Daily at 07:00
Message: "Weight Alert: {direction} {delta}kg in 3 days (now {current}kg). Check hydration and nutrition."
Cooldown: 48 hours
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

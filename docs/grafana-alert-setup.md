# Grafana Alert Setup Guide

> Data source: PostgreSQL (Supabase session pooler)
> Alerts evaluate at 09:10 daily (after sync at 09:00)
> Notifications: Slack webhook via contact point

## Step 1: Create Contact Point

Grafana → Alerting → Contact points → New contact point

- **Name:** ascent-slack-daily
- **Type:** Slack
- **Webhook URL:** (use Slack incoming webhook — see below)
- **Channel:** #ascent-daily

To create the webhook:
1. Go to https://api.slack.com/apps (find the OpenClaw app)
2. Features → Incoming Webhooks → Add New Webhook
3. Select #ascent-daily channel
4. Copy the webhook URL into Grafana

Create a second contact point:
- **Name:** ascent-slack-training
- **Channel:** #ascent-training

## Step 2: Create Notification Policy

Grafana → Alerting → Notification policies

- Default policy → ascent-slack-daily
- Add sub-policy: label `channel=training` → ascent-slack-training

## Step 3: Create Alert Rules

### Alert 1: HRV Drop >15% Below Baseline

Grafana → Alerting → Alert rules → New alert rule

**Query A:**
```sql
SELECT
  date,
  last_night_avg,
  baseline_balanced_low,
  baseline_balanced_low * 0.85 AS threshold
FROM hrv
WHERE date = CURRENT_DATE
AND last_night_avg < baseline_balanced_low * 0.85
AND last_night_avg IS NOT NULL
```

- **Condition:** Query returns rows (count > 0)
- **Evaluation interval:** 1h
- **Pending period:** 0s
- **Labels:** severity=warning, channel=daily
- **Annotations:**
  - Summary: `HRV Alert: Last night's HRV ({{ $values.last_night_avg }}) is >15% below baseline. Consider lighter intensity today.`
- **No data state:** OK
- **Mute timing:** 00:00–09:00 (don't fire before sync)

### Alert 2: Sleep Score <60

**Query A:**
```sql
SELECT date, overall_score
FROM sleep
WHERE date = CURRENT_DATE
AND overall_score < 60
AND overall_score IS NOT NULL
```

- **Condition:** Query returns rows
- **Labels:** severity=warning, channel=daily
- **Annotations:**
  - Summary: `Sleep was rough ({{ $values.overall_score }}/100). Recovery may be impaired — consider adjusting today's intensity.`

### Alert 3: No Activity for 3+ Days

**Query A:**
```sql
SELECT
  CURRENT_DATE AS check_date,
  MAX(date) AS last_activity,
  CURRENT_DATE - MAX(date) AS days_since
FROM activities
HAVING CURRENT_DATE - MAX(date) >= 3
```

- **Condition:** Query returns rows
- **Labels:** severity=info, channel=training
- **Annotations:**
  - Summary: `No recorded activity for {{ $values.days_since }} days. Planned rest or should we adjust the week?`

### Alert 4: Weight Change >1kg in 3 Days

**Query A:**
```sql
WITH recent AS (
  SELECT date, weight_kg
  FROM body_composition
  WHERE weight_kg IS NOT NULL
  ORDER BY date DESC
  LIMIT 2
),
comparison AS (
  SELECT
    (SELECT weight_kg FROM recent ORDER BY date DESC LIMIT 1) AS current_weight,
    (SELECT weight_kg FROM body_composition
     WHERE date <= CURRENT_DATE - 3 AND weight_kg IS NOT NULL
     ORDER BY date DESC LIMIT 1) AS prev_weight
)
SELECT *
FROM comparison
WHERE ABS(current_weight - prev_weight) > 1.0
```

- **Condition:** Query returns rows
- **Labels:** severity=warning, channel=daily
- **Note:** This alert won't fire until body comp data is being tracked (no Garmin scale). Will activate when gym scan data flows in.

## Step 4: Verify

After setup, go to Alerting → Alert rules and check:
- All 4 rules show "Normal" state (no current alerts)
- Contact points show "OK" test result
- Check #ascent-daily in Slack for test notifications

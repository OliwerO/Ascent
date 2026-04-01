# Ascent — Dashboard & Channels Spec

> Created: 2026-03-31
> Status: Approved, ready to build

-----

## Daily Schedule

| Time | Event | Detail |
|------|-------|--------|
| 09:00 | Garmin sync | `garmin_sync.py` via launchd — pulls all data to Supabase |
| 09:15 | Morning briefing | Jarvis posts to `#ascent-daily` (Slack) |
| Every 4h | Session refresh | `garmin_session_refresh.sh` — keeps Safari auth alive |
| Sunday 20:00 | Weekly analysis | Jarvis posts to `#ascent-training` (Slack) |

-----

## Slack Channels

### #ascent-daily

**Purpose:** Morning dashboard + real-time health status. The channel you check first thing.

**Automated posts:**
- **Morning briefing (09:15):** Recovery triad (HRV, sleep score, training readiness) with color indicators, Body Battery, resting HR, yesterday's activity summary. Ends with today's recommendation (train hard / moderate / rest).
- **Alerts** (as they fire): HRV drop >15%, sleep score <60, weight shift >1kg/3d, no activity 3+ days.

**Interactive — you can chat here:**
- "Shoulder feels off today" → Jarvis adjusts today's plan
- "I'm sore from yesterday" → Jarvis factors into readiness assessment
- "Feeling great, can I push harder?" → Jarvis gives the green light (or not) based on data
- Any subjective input about how you feel right now

**Tone:** Concise, status-oriented. Morning briefing is 5-8 lines max.

### #ascent-training

**Purpose:** The coach's notebook. Session plans, workout feedback, progression tracking, weekly analysis.

**Automated posts:**
- **Weekly analysis (Sunday 20:00):** Training volume (gym + mountain), HRV trend, sleep quality trend, activity distribution, progression notes, plan compliance.
- **Pre-session plan** (when workout generator is live): Today's workout with exercises, sets, reps, target weights.
- **Post-session feedback** (when Garmin push is live): How the session went vs plan, volume comparison, notable PRs.

**Interactive — you can chat here:**
- "Can we add more core work to Fridays?" → plan adjustment
- "I'll be traveling next week, no gym" → Jarvis restructures the week
- "Replace overhead press, shoulder bothers me" → exercise swap
- Any plan modifications or training questions

**Tone:** More detailed. Numbers, progressions, analysis. Threads for multi-turn discussions.

### Telegram (unchanged)

**Purpose:** Quick ad-hoc queries on the go.
- "How was my sleep?" → quick answer
- "What's my HRV trend?" → data lookup
- Not for structured coaching — that's Slack

-----

## Webapp (React on Vercel) — Phase 4b

**Purpose:** Your daily driver dashboard. The visual equivalent of what the YNAB dashboard is for finances.

**Tech:** React + Vite + Tailwind, deployed on Vercel. Reads from Supabase directly (REST API, anon key).

### View 1: Today (default landing page, mobile-first)

```
┌─────────────────────────────┐
│  Recovery Triad             │
│  HRV: 103  Sleep: 6h  TR:40│
│  [green]   [yellow]  [red] │
├─────────────────────────────┤
│  Body Battery    92 → 19    │
│  ████████████░░░░░░  charge │
├─────────────────────────────┤
│  Resting HR      45 bpm     │
│  ▁▂▁▂▃▂▁  (7d sparkline)   │
├─────────────────────────────┤
│  Yesterday                  │
│  Storfjord Backcountry      │
│  4h18m · 765m↑ · 1920 kcal │
├─────────────────────────────┤
│  Current Phase              │
│  Winter/Spring — Mountain   │
│  Post-rib recovery · Wk 4  │
│  Goal: Endurance base +     │
│        Body recomp          │
└─────────────────────────────┘
```

### View 2: Week (swipe or tab)

```
┌─────────────────────────────┐
│  This Week                  │
│  Mon Tue Wed Thu Fri Sat Sun│
│  rest  ·   ·   ·   · 🏔 🏔│
│                              │
│  Elevation: 2,438m total    │
│  Gym sessions: 0            │
│  Active calories: 8,200     │
├─────────────────────────────┤
│  HRV Trend (14d)            │
│  ▃▅▅▆▅▄▃▅▆▆▇▆▅▆            │
│  Avg: 95 · Baseline: 85-105│
├─────────────────────────────┤
│  Sleep (14d)                │
│  ■■■■■■■■■■■■■■ stacked    │
│  deep | light | REM | awake │
│  Avg: 5.8h (target: 7-8h)  │
├─────────────────────────────┤
│  Activity Log               │
│  Mar 28 · Storfjord · 765m↑│
│  Mar 27 · Balsfjord · 571m↑│
│  Mar 26 · Alta · 385m↑     │
│  ...                        │
└─────────────────────────────┘
```

### View 3: Trends (monthly/quarterly)

- HRV 90-day rolling average with baseline band
- Body composition over time (weight + body fat %)
- Weekly elevation gain (12-week bar chart)
- Training volume: gym kg vs mountain elevation (stacked bars)
- VO2max trend
- e1RM progression per lift (when training data available)

### View 4: Goals

- Current goals with progress indicators
- Body recomp: weight + body fat % vs targets
- Endurance: VO2max trend, weekly elevation targets
- Strength: e1RM for key lifts vs targets
- Season context and phase info

### Future interactive features (Phase 9+):

- Food logging (text/photo input)
- Body comp scan upload (photo → Claude Vision parsing)
- Training log corrections
- Goal management

-----

## Grafana Cloud — Alert Engine

Grafana's primary role is **alert evaluation**, not daily viewing. The webapp replaces Grafana as the visual interface.

### Alert 1: HRV Drop >15% from Baseline

```
Condition: last_night_avg < (baseline_balanced_low * 0.85)
Evaluation: Daily at 09:10 (after sync)
→ Webhook → OpenClaw → #ascent-daily
Message: "HRV Alert: Last night {value} is significantly below your baseline ({baseline}). Consider lighter intensity today."
Cooldown: 24h
```

### Alert 2: Sleep Score <60

```
Condition: overall_score < 60
Evaluation: Daily at 09:10
→ #ascent-daily
Message: "Sleep was rough ({value}/100). Recovery may be impaired — adjust today's plan if needed."
Cooldown: 24h
```

### Alert 3: No Activity for 3+ Days

```
Condition: No rows in activities for last 3 days
Evaluation: Daily at 09:10
→ #ascent-training
Message: "No recorded activity for 3 days. Is this planned rest or should we adjust the week?"
Cooldown: 72h
```

### Alert 4: Weight Shift >1kg in 3 Days

```
Condition: ABS(today - 3_days_ago) > 1.0 kg
Evaluation: Daily at 09:10
→ #ascent-daily
Message: "Weight moved {direction} {delta}kg in 3 days ({current}kg). Check hydration and intake."
Cooldown: 48h
```

### Alert webhook routing

Grafana webhook → OpenClaw HTTP endpoint → Jarvis formats with coaching context → posts to appropriate Slack channel.

-----

## Pending Decisions

- [ ] Webapp domain: ascent.jarvis.app? health.oliwer.dev? Or Vercel default?
- [ ] Grafana webhook URL — depends on OpenClaw endpoint config
- [ ] Whether to build Grafana dashboards as interim MVP while webapp is developed
- [ ] Auth for webapp (Supabase auth? Or just anon key since single user?)

-----

## Activity Types in Data (confirmed from actual sync)

| Garmin type | Category | Notes |
|-------------|----------|-------|
| `backcountry_snowboarding` | Mountain | Splitboard touring — primary winter activity |
| `resort_snowboarding` | Mountain | Resort days |
| `hang_gliding` | Mountain/Air | Paragliding (Garmin maps it to hang_gliding) |
| `strength_training` | Gym | Weight training |
| `stair_climbing` | Gym/Cardio | Stair stepper |
| `yoga` | Mobility | Stretching/yoga sessions |
| `multi_sport` | Mixed | Multi-activity days |

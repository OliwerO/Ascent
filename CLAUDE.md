# Ascent — AI-Coached Training Intelligence

## Purpose

Ascent is a closed-loop training system for a single athlete (Oliwer). It collects wearable data from Garmin, applies evidence-based coaching logic, generates and adjusts workouts, and surfaces everything through a mobile-first React dashboard. The system runs autonomously — daily coaching decisions, weekly analysis, and Garmin workout pushes happen without human intervention.

**The goal:** Make every training decision data-informed. No guessing what weight to use, whether to train or rest, or how mountain weekends affect gym performance. The system answers these questions automatically.

## Architecture (What's Actually Running)

```
Garmin Watch → Garmin Connect API
                    │
                    ▼
        garmin_sync.py (daily 09:00, launchd)
                    │
                    ▼
              Supabase (PostgreSQL)
             ╱    │    │    ╲
            ╱     │    │     ╲
    React App   CCD    CCD    Slack
    (Vercel)   Daily  Weekly  Briefing
               09:43  Sun 20  09:15
                │
                ▼
         coach_adjust.py → planned_workouts → Garmin push
```

| Component | What it does | Status |
|-----------|-------------|--------|
| `garmin_sync.py` | Pulls HRV, sleep, activities, body battery, VO2max to Supabase | Running |
| `scale_sync.py` | Daily weight from Xiaomi Mi Scale | Running |
| CCD health-coach-daily | Reads recovery data, decides train/rest/adjust, pushes workout to Garmin | Running |
| CCD health-coach-weekly | Runs decision retrospective, interference analysis, recomp tracking | Running |
| `morning_briefing.py` | Posts health snapshot to Slack at 09:15 | Running |
| `coach_adjust.py` | Single write-path for all workout mutations | Running |
| `workout_push.py` | Builds workout JSON, pushes to Garmin, tracks progression | Running |
| React app (6 views) | Today, Week, Plan, Recovery, Trends, Goals | Deployed on Vercel |

## Key Files

| File | Purpose | Read before modifying |
|------|---------|----------------------|
| `scripts/coach_adjust.py` | **Single write-path** for planned_workouts mutations | Any coaching logic |
| `scripts/workout_push.py` | Session templates, progression, Garmin push, home workout map | Exercises, weights, Garmin |
| `scripts/workout_generator.py` | Populates 8-week planned_workouts | Program structure |
| `openclaw/coaching-context.md` | Current goals, injuries, decisions log (mutable) | Coaching decisions |
| `openclaw/coaching-program.md` | Training program templates (READ-ONLY, Opus only) | Never — read only |
| `openclaw/skills/health-coach/SKILL.md` | Coaching decision matrix and protocol | Coaching behavior |
| `docs/knowledge-base/knowledge-base.md` | 7200-line evidence-based training rules | Exercise selection, recovery |
| `web/src/views/TodayView.tsx` | Primary mobile view with coaching card | UI changes |

## Critical Rules

These are locked. Do not change without an explicit Opus session.

1. **Coach executes plans, never creates them.** Plan creation/redesign is Opus's role in interactive sessions.
2. **`coach_adjust.py` is the only write-path** for `planned_workouts`, `coaching_log`, and session exceptions. No other script or UI component writes coaching decisions to the DB outside this path (React app may write user-initiated actions like RPE, wellness, and home/gym switching directly).
3. **`planned_workouts` is the single source of truth** for workout display in the React app.
4. **Micro-adjustments (<=15% volume) happen at Claude Code tier.** Structural changes (split, progression scheme, block design) require Opus.
5. **Body Battery and Training Readiness are safety guardrails only** — hard rest override at BB<30 or TR<40, gated on data freshness (<12h). Not used for graduated decisions.
6. **Mountain activities ARE training** — never flag as "missed gym." Treat elevation + zone time as cardio load.
7. **Autonomy-supportive language only** — no "should," "must," "need to" in coaching messages.
8. **Home workout substitution map** must be updated when new exercises are added to any block (see `HOME_SUBSTITUTIONS` in `workout_push.py` and `web/src/lib/homeWorkout.ts`).

## Development Standards

**Approach every change like a senior developer.** This means:

### Before Writing Code
- **Read first.** Understand existing patterns before proposing changes. Check how similar things are already done in the codebase.
- **Check for existing solutions.** Before adding a new utility, search if one exists. Before creating a new table, check if an existing one covers the need.
- **Understand the blast radius.** A change to `workout_push.py` affects workout generation, Garmin push, home workouts, and the React app. Trace the dependency chain.

### While Writing Code
- **No dead code.** Don't leave commented-out blocks, unused imports, or TODO stubs. If something is removed, remove it completely.
- **No premature abstraction.** Three similar lines are better than a helper used once. Extract only when there's a clear pattern.
- **Explicit over clever.** Name variables and functions so the next reader (or future Claude session) understands without comments.
- **TypeScript strict mode.** No `any` types. Fix type errors, don't suppress them.
- **SQL migrations are append-only.** Never modify an applied migration. Create `sql/NNN_description.sql` for changes.
- **Secrets in `.env` only.** Never in code, never in commits. Service key stays server-side.
- **Rate-limit external APIs.** 1s between Garmin calls. Respect 429 responses with exponential backoff.

### After Writing Code
- **Always run `cd web && npm run build`** before committing frontend changes. TypeScript errors block Vercel.
- **Always commit and push** after frontend changes so Vercel deploys. Don't leave changes local.
- **Test with real data.** Run Python scripts with `--dry-run` or against a known date. Check the React app on your phone after deploy.

### Guardrails — Push Back When Needed

If the user (Oliwer) requests something that conflicts with good practices, **say so clearly and explain why.** Specifically:

- **"Just make it work"** — If a hack creates tech debt or data integrity risk, propose the clean solution first. Implement the hack only if the user explicitly accepts the tradeoff after understanding it.
- **Skipping tests** — `npm run build` is non-negotiable. For Python changes that touch data writes, verify with a dry-run.
- **Giant commits** — Split logically distinct changes. One feature per commit.
- **Duplicating logic** — If the same logic exists in Python and TypeScript (e.g., home workout map), flag that they must stay in sync and note it in both files.
- **Modifying locked decisions** — The 8 critical rules above exist for evidence-based reasons. If the user wants to change one, recommend an Opus session to evaluate the tradeoff properly rather than making an ad-hoc change.
- **Adding complexity for hypothetical futures** — Build for what's needed now. The user is not a developer; unnecessary abstraction layers create maintenance burden that falls on Claude Code sessions.

## Data Integrity

### Validation Rules (applied in garmin_sync.py)

| Metric | Reject if |
|--------|-----------|
| rMSSD (ms) | < 5 or > 250 |
| Resting HR (bpm) | < 25 or > 120 |
| Sleep duration (h) | < 2 or > 16 |
| Daily weight change (kg) | > +/- 3.0 in 24h |
| VO2max change | > 5 ml/kg/min in one session |

### Gap-Aware Calculations
- Never use `ROWS BETWEEN N PRECEDING` — it counts rows, not dates.
- Always use `generate_series()` date spine with LEFT JOIN.
- Minimum valid-day thresholds: 4/7 weekly, 20/30 monthly, 60/90 quarterly.

## What's NOT Built Yet

These are known gaps. Don't build them unless explicitly asked.

| Feature | Status | Notes |
|---------|--------|-------|
| Google Calendar integration | CLI exists (`gcal.py`), not wired into coaching | Medium priority |
| Food logging | DB tables exist, no UI or sync | Low priority |
| Grafana dashboards | Spec exists, web app replaced the need | Low priority |
| Blood test UI | DB tables + seed data, no parsing or display | Low priority |

## Database

28 SQL migrations, ~40 tables, 14 views. Key views for coaching:

- `daily_coaching_context` — single row with today's session, recovery data, progression alerts, mountain interference
- `weekly_coaching_summary` — week's training + recovery + decision quality
- `stall_early_warning` — exercises at stall risk
- `readiness_composite` — HRV + sleep + body battery composite

Schema is the source of truth. Don't duplicate the full DDL here — read `sql/001_schema.sql` through `sql/028_home_workout.sql` for current state.

## Infrastructure

**Cron (launchd on Mac):**

| Time | Script | Purpose |
|------|--------|---------|
| 09:00 | garmin_sync.py | Fetch Garmin data |
| 09:15 | morning_briefing.py | Post Slack briefing |
| 10:00 | scale_sync.py | Fetch body weight |
| 15min | health_check.py | Verify syncs completed |
| 18:00 | consistency_watchdog.py | Alert on job misses |
| 20:00 | rpe_reminder.py | Slack RPE log reminder |
| Sun 20:00 | weekly_analysis_runner.py | Weekly analysis suite |

**CCD Scheduled Sessions (Anthropic ACP):**

| Time | Session | Purpose |
|------|---------|---------|
| 09:43 daily | health-coach-daily | Autoregulation decision + Garmin push |
| Sun 20:03 | health-coach-weekly | Weekly review + coaching adjustments |
| End of block | block-review | Strategic review with Opus (manual trigger) |

## Working With This Codebase

- **Python scripts** are in `scripts/`, use `venv/bin/python`, load `.env` from project root.
- **React app** is in `web/`, deployed on Vercel from `main` branch.
- **SQL migrations** are in `sql/`, applied via `scripts/deploy_schema.py`.
- **Coaching docs** are in `openclaw/` — `coaching-program.md` is READ-ONLY.
- **Knowledge base** is in `docs/knowledge-base/` — evidence-based rules referenced by coaching agents.
- **CCD prompts** are in `ccd-prompts/` — these are the autonomous agent definitions.
- **Tests** are in `tests/` — run with `pytest tests/`.

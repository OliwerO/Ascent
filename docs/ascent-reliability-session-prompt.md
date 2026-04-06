# Ascent Reliability: Analysis & Implementation Prompt

> **For:** New Claude Code session
> **Repo:** oliwero/ascent
> **Date:** 2026-04-06
> **Reference:** Read `docs/ascent-reliability-audit-prompt.md` for detailed bug descriptions and root causes

---

## Your Task

Ascent is a personal training intelligence app (React/Vite frontend on Vercel, Supabase backend, Python sync scripts). It currently shows wrong and stale data. Your job is to:

1. **Analyse** the full codebase — frontend, data hooks, scripts, coaching files
2. **Build a plan** to make the app a reliable, always-live source of truth
3. **Execute** that plan

Work on a feature branch based on `main`. The web frontend is in `web/`. Backend scripts are in `scripts/`. Coaching config is in `openclaw/`.

---

## Step 1: Analyse the Codebase

Read every file listed below. For each one, document:
- What data does it read? From where? (Supabase table, hardcoded constant, file?)
- What data does it write? Where?
- What happens when the data source is empty, stale, or unreachable?
- Are there hardcoded values that will become wrong over time?
- Does it have realtime updates or does the user need to refresh?

### Files to read

**Frontend — lib & hooks:**
- `web/src/lib/program.ts` — program dates, week calculation, session maps
- `web/src/lib/types.ts` — TypeScript interfaces for all data
- `web/src/lib/supabase.ts` — Supabase client setup
- `web/src/lib/format.ts` — check if this file exists (it may be missing)
- `web/src/hooks/useSupabase.ts` — all data-fetching hooks, realtime subscriptions

**Frontend — views:**
- `web/src/views/TodayView.tsx` — today's training, coaching card, wellness, recovery signals
- `web/src/views/TrainingPlanView.tsx` — 8-week program view, progress tracking
- `web/src/views/WeekView.tsx` — weekly schedule
- `web/src/views/RecoveryView.tsx` — recovery metrics
- `web/src/views/TrendsView.tsx` — trend charts
- `web/src/views/GoalsView.tsx` — goals tracking
- `web/src/App.tsx` — app shell, navigation, routing

**Backend — scripts:**
- `scripts/morning_briefing.py` — daily readiness check, where does it write?
- `scripts/workout_generator.py` — generates planned_workouts rows
- `scripts/workout_push.py` — pushes workouts to Garmin, has replicated constants
- `scripts/progression_engine.py` — weight progression logic

**Coaching & config:**
- `openclaw/coaching-context.md` — coaching rules, decision matrix, session exceptions
- `openclaw/coaching-program.md` — current program definition (if it exists)
- `sql/006_training_expansion.sql` — planned_workouts and exercise_progression schema

### What to look for specifically

1. **Data flow map:** For each Supabase table, trace: what writes to it → what reads from it → what the user sees. Identify any table that is read but never written to (stale).

2. **Hardcoded expiry:** Find every date, block name, session map, or program constant that's hardcoded in source code. When does each one become wrong?

3. **Realtime gaps:** Which `useSupabase.ts` hooks have `useRealtimeRefresh()`? Which don't? For the ones that don't — does the user expect live data there?

4. **Fallback chains:** When `planned_workouts` is empty for a date, what does each view show? Is that fallback correct or misleading?

5. **Duplication:** Where are the same constants (session names, day mappings, deload weeks) defined in multiple files? List every instance.

6. **Error handling:** Which hooks silently return `[]` on error vs properly propagate? What does the user see when Supabase is unreachable?

7. **Coaching ↔ DB sync:** When coaching makes an adjustment (via Telegram/coaching-context.md), does that change reach the `planned_workouts` table? Trace the exact flow.

---

## Step 2: Build the Plan

Based on your analysis, create an implementation plan. The plan must address **all** of the following categories. If your analysis found additional issues, add them.

### Category A: Immediate Bug Fixes

These are confirmed bugs from a previous session's analysis (see `docs/ascent-reliability-audit-prompt.md` for full details):

| # | Bug | File | Summary |
|---|-----|------|---------|
| 1 | Wrong week number | `program.ts` | BLOCK_1_START is Wednesday, weeks should be Monday-aligned |
| 2 | Adjusted training not showing | `TodayView.tsx` | Falls back to hardcoded session when planned_workouts has no row |
| 3 | Missing format.ts | `lib/format.ts` | File doesn't exist, TodayView imports from it — build fails |
| 4 | RPE logging loses data | `TodayView.tsx` | Nested try-catch swallows error, data not saved |
| 5 | Green card with no wellness | `TodayView.tsx` | Missing wellness data defaults to "all clear" |
| 6 | Decision tree mismatch | `TodayView.tsx` | Coaching card logic doesn't match rules in coaching-context.md |

### Category B: Realtime & Data Freshness

- Add realtime subscriptions to all hooks that serve data changing during the day
- Fix silent error swallowing in hooks
- Ensure the app never requires a manual page refresh to show current data

### Category C: Eliminate Hardcoded Program Config

- Move program dates, session maps, deload schedule from source code to Supabase
- Ensure the app continues working after May 26 (current program end date)
- Single source of truth for program config — frontend, scripts, and coaching all read from one place
- Remove duplicated constants across files

### Category D: Fix the Adjustment Pipeline

- Ensure coaching adjustments write to `planned_workouts` in Supabase
- Ensure session exceptions (reschedules, skips) update `planned_workouts`
- Make `planned_workouts` the single source of truth for what training is scheduled
- Remove reliance on coaching_log as a fallback data source

### Category E: Anything Else Found in Analysis

- Add any additional issues your analysis uncovered
- Prioritize by impact on data reliability

### Plan format

For each fix, specify:
- File(s) to change
- What to change (be specific — not "fix the bug" but "change line X from Y to Z")
- Order of operations (what depends on what)
- What to verify after the change

---

## Step 3: Execute the Plan

Implement the plan. Work incrementally — commit after each category. Verify each fix doesn't break other things.

**Commit strategy:**
- One commit per category (A, B, C, D, E)
- Clear commit messages describing what changed and why
- Push to the feature branch after each commit

**Constraints:**
- Don't rewrite the whole app — fix what's broken, add what's missing
- Don't add new infrastructure (no new databases, services, build tools)
- Don't add features that aren't in the plan
- Supabase is the source of truth, not files or hardcoded constants
- Keep the coaching flow architecture: Opus creates plans → Claude Code generates workouts → Haiku adjusts daily → app displays

---

## Do NOT Skip the Analysis

It's tempting to jump straight to the known fixes. Don't. The analysis step will likely uncover issues beyond the 6 bugs and 7 systemic problems already documented. The plan should be informed by what you actually find, not just what's listed here.

Read every file. Map every data flow. Then build the plan. Then execute.

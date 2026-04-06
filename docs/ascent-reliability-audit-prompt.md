# Ascent App Reliability Audit & Fix Plan

> **Purpose:** Handoff prompt for a new Claude Code session to audit the Ascent web app + data pipeline, fix all known bugs, and make Ascent an always-live, reliable source of truth.
>
> **Created:** 2026-04-06
> **Context:** User reported Today view showing wrong week (1 instead of 2) and stale training (original session instead of adjusted one). Root cause analysis + full codebase audit revealed systemic issues.

---

## Session Goal

Fix all identified bugs in the Ascent React app (`web/`) and data pipeline. Then harden the system so it never shows stale, wrong, or missing data again. The app must be a reliable, always-current source of truth for training — no hardcoded values that expire, no silent fallbacks to wrong data, no broken imports, no incomplete data flows.

**Important:** The web frontend lives on `origin/main`. Your working branch should be based on main. Only change the files needed — don't rewrite the whole app.

---

## Known Bugs (Confirmed, with root causes and fixes)

### Bug 1: Wrong Week Number — Shows "Week 1" instead of "Week 2"

**File:** `web/src/lib/program.ts`

**Root cause:** `BLOCK_1_START` is `new Date(2026, 3, 1)` — April 1, a **Wednesday**. `getProgramWeek()` calculates `Math.floor(differenceInDays(date, BLOCK_1_START) / 7) + 1`. On Monday April 6, that's `Math.floor(5/7) + 1 = 1`. But training weeks run Mon–Sun, so April 6 is the start of Week 2.

**Fix:** Change `BLOCK_1_START` to `new Date(2026, 2, 30)` — Monday March 30, the Monday of the week containing April 1. Use `startOfWeek(date, { weekStartsOn: 1 })` to align the input date to its Monday before computing the delta. Import `startOfWeek` from `date-fns`. Also add `ended: boolean` to the return type — TodayView already destructures it but the function doesn't return it (currently `undefined`).

Also fix `getWeekSchedule()` — it currently does `addDays(weekStart, -2)` to manually convert Wed→Mon. Once `BLOCK_1_START` is Monday, remove this offset. Update `BLOCK_2_START` to `new Date(2026, 3, 27)` (Mon Apr 27) and `BLOCK_2_END` to `new Date(2026, 4, 24)` (Sun May 24) to stay Monday-aligned.

### Bug 2: Adjusted Training Not Showing on Today View

**File:** `web/src/views/TodayView.tsx`

**Root cause:** Lines 334-337 check `planned_workouts` for today's date. If no row exists (or row wasn't updated with `status: 'adjusted'`), it falls back to the **hardcoded static session map** (`Monday → B → "Strength B: Upper + Core"`). Coaching adjustments made via Telegram write to `coaching_log` but never update `planned_workouts`.

**Fix (immediate):** Add `useCoachingLog()` to TodayView. Check for today's entries with `type === 'adjustment'` or `type === 'daily_adjustment'`. Use `data_context.session_name` / `data_context.session_label` from coaching log as fallback. Display `message` as the adjustment reason.

**Fix (proper, Phase E):** Ensure all coaching adjustments write to `planned_workouts` directly so the fallback is never needed.

### Bug 3: Missing `format.ts` — Build Will Fail

**File:** `web/src/lib/format.ts` — does not exist

**Root cause:** `TodayView.tsx` line 13 imports `{ formatDuration, formatActivityType }` from `'../lib/format'`. The file was never created. These functions exist as inline duplicates in `TrainingPlanView.tsx` and `WeekView.tsx`.

**Fix:** Create `web/src/lib/format.ts`:
```ts
export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return '--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

export function formatActivityType(type: string): string {
  return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}
```
Then remove the inline duplicates from `TrainingPlanView.tsx` and `WeekView.tsx`, replacing them with imports.

### Bug 4: RPE Logging Has Nested Try-Catch — Silently Loses Data

**File:** `web/src/views/TodayView.tsx`, RPEPrompt component

**Root cause:** Inner `catch` block sets error message but doesn't re-throw. The outer `finally` sets `setSaving(false)` and execution continues. If the Supabase update fails, user sees "Save failed" briefly but the component acts as if it succeeded.

**Fix:** Restructure to a single try-catch. On failure, don't set `setRated(true)`.

### Bug 5: Coaching Card Shows "Green" When Wellness Data Is Missing

**File:** `web/src/views/TodayView.tsx`, coaching card decision tree

**Root cause:** When `todayWellness` is null (user hasn't done check-in), `wellnessLow` evaluates to `false`, and the coaching card defaults to "green". This means the coaching recommendation is based on incomplete data but presents as fully confident.

**Fix:** When wellness check-in is missing, add a coaching point: "Complete wellness check-in for full assessment" with an amber/info indicator. Don't let missing data default to "all clear."

### Bug 6: Coaching Decision Tree Doesn't Match coaching-context.md

**File:** `web/src/views/TodayView.tsx` vs `openclaw/coaching-context.md`

**Root cause:** The coaching-context.md decision matrix says:
- UNBALANCED + sleep <6h → rest (red)
- BALANCED + sleep <6h → reduce volume 30%, drop RPE by 1

But the code checks `hrvDegraded` (which includes UNBALANCED) separately from sleep. It doesn't implement "UNBALANCED + sleep <6h = red" as a combined condition. The decision tree logic doesn't match the documented coaching rules.

**Fix:** Align the code's decision tree with the documented matrix in coaching-context.md. Add specific combined condition checks.

---

## Systemic Issues (Audit Findings)

### S1. Hardcoded Program Dates — App Breaks After May 26

**Files:** `web/src/lib/program.ts`, `scripts/workout_push.py`, `scripts/workout_generator.py`

All program dates, session maps, deload weeks, and block names are hardcoded in multiple files. After May 26, `getProgramWeek()` returns `{ block: 2, week: 8 }` forever. RPE ranges, deload badges, progress bars — all freeze.

The same data is replicated in 3+ places:
- `program.ts` — frontend constants
- `workout_push.py` — `DAY_TO_SESSION`, `SESSION_NAMES`, `DELOAD_WEEKS` (identical copies)
- `workout_generator.py` — same constants again
- Supabase `program_sessions` table — canonical DB version

**Fix:** Move program configuration to Supabase. Create a `program_config` table (or use existing `program_sessions`). Frontend reads from Supabase via a `useProgramConfig()` hook. Scripts read from the same table. One source of truth. When Opus creates a new training block, it updates the DB — no code deploy needed.

### S2. Realtime Subscriptions Are Incomplete

**File:** `web/src/hooks/useSupabase.ts`

Only 2 of 11 data hooks have realtime subscriptions:
- `daily_metrics` — has realtime
- `planned_workouts` — has realtime
- `hrv` — **no realtime**
- `sleep` — **no realtime**
- `activities` — **no realtime**
- `subjective_wellness` — **no realtime**
- `coaching_log` — **no realtime**
- `body_composition` — **no realtime**
- `training_sessions` — **no realtime**
- `training_sets` — **no realtime**
- `goals` — **no realtime**

**Impact:** After Garmin syncs new data (every ~5 min), the app won't update until the user refreshes. HRV, sleep, and activity data are stale. Coaching log adjustments don't appear. This is a primary cause of the "adjusted training not showing" bug.

**Fix:** Add `useRealtimeRefresh()` to at minimum: `useHRV`, `useSleep`, `useActivities`, `useCoachingLog`, `useSubjectiveWellness`. These are the tables that change during a normal day. Lower priority: `useBodyComposition`, `useGoals`, `useTrainingSessions`.

### S3. Silent Error Swallowing

**File:** `web/src/hooks/useSupabase.ts`

Two hooks silently return `[]` on error instead of propagating:
```ts
// useSubjectiveWellness
if (error) return []  // ← Silently swallows error

// useGoals
if (error) return []  // ← Same
```

If Supabase is down or the table doesn't exist, the app shows empty state with no error indicator. User doesn't know why data is missing.

**Fix:** Propagate errors consistently. Show an error indicator in the UI when data fails to load, not just empty state.

### S4. Adjustment Pipeline Doesn't Write to planned_workouts

The designed flow:
```
Haiku checks readiness → suggests adjustment → user confirms via Telegram →
update planned_workouts → push to Garmin → update calendar
```

Current reality: Adjustments may be logged in `coaching_log` and/or `coaching-context.md` (the markdown file), but the `planned_workouts` table in Supabase is not updated. The `morning_briefing.py` script posts recommendations but doesn't close the loop by writing back to the DB.

**Fix:** Audit `scripts/morning_briefing.py`. When an adjustment is confirmed, it must upsert the `planned_workouts` row for that date with `status = 'adjusted'`, updated `workout_definition`, and `adjustment_reason`.

### S5. Session Exceptions Only in Markdown, Not in DB

**File:** `openclaw/coaching-context.md` documents session exceptions in a markdown table:
```
| 2026-04-07 | Strength B (Monday) | Rescheduled to Tuesday Apr 8 | Big tour on Monday |
```

But this isn't in `planned_workouts`. The app doesn't read coaching-context.md — it reads Supabase. So exceptions aren't reflected in the UI.

**Fix:** Every coaching exception must be written to `planned_workouts` (set the original date's row to `status: 'skipped'` with reason, create a new row for the rescheduled date).

### S6. Garmin Benchmark Weights Are Stale

**File:** `scripts/workout_push.py`

```python
GARMIN_BENCHMARKS = {
    "BARBELL_BACK_SQUAT": 133.3,      # From Feb 2026 Garmin Connect
    "BARBELL_BENCH_PRESS": 102.9,
    ...
}
```

These were manually copied from Garmin Connect in February 2026 and never updated. As user gets stronger, these become inaccurate.

**Fix:** Either auto-pull from Garmin Connect API, or derive from actual training data in `training_sets` table (most recent max-effort test or calculated e1RM).

### S7. Mountain Load Thresholds Are Arbitrary

**File:** `web/src/views/TodayView.tsx`

```ts
const category = elevation >= 2000 || hours >= 5 ? 'heavy'
  : elevation >= 1000 || hours >= 3 ? 'moderate' : 'light'
```

These thresholds are hardcoded and don't adapt to fitness level or recent training context.

**Fix (minimal):** Move thresholds to a config constant at the top of the file with a comment. **Fix (proper):** Base categories on recent mountain activity volume — if user's 4-week average is 2000m/week, then 2000m in 72h is normal, not "heavy."

---

## Execution Plan

### Phase A: Fix Known Bugs (Targeted, minimal changes)

These are the immediate fixes. Touch only the files listed.

1. **`web/src/lib/program.ts`** — Monday-aligned week calculation (Bug 1)
2. **`web/src/lib/format.ts`** — Create missing file (Bug 3)
3. **`web/src/views/TodayView.tsx`** — Coaching log fallback for adjustments (Bug 2), fix RPE logging (Bug 4), add missing-wellness indicator (Bug 5), align decision tree with coaching-context.md (Bug 6)
4. **`web/src/views/TrainingPlanView.tsx`** — Remove inline `formatDuration`/`formatActivityType` duplicates, import from `lib/format`
5. **`web/src/views/WeekView.tsx`** — Same dedup as above if applicable

### Phase B: Add Realtime Subscriptions

6. **`web/src/hooks/useSupabase.ts`** — Add `useRealtimeRefresh()` to `useHRV`, `useSleep`, `useActivities`, `useCoachingLog`, `useSubjectiveWellness`
7. Fix silent error swallowing in `useSubjectiveWellness` and `useGoals`

### Phase C: Data-Driven Program Config

8. Design and create a `program_config` table in Supabase (or document how to use existing `program_sessions`)
9. Create a `useProgramConfig()` hook that replaces hardcoded constants in `program.ts`
10. Update `getProgramWeek()`, `getSessionForDate()`, `SESSION_NAMES` etc. to read from Supabase
11. Ensure `workout_push.py` and `workout_generator.py` read from the same source

### Phase D: Fix Adjustment Pipeline

12. Audit `scripts/morning_briefing.py` — trace the full adjustment flow
13. Ensure coaching adjustments write to `planned_workouts` in Supabase
14. Ensure session exceptions (reschedules, skips) write to `planned_workouts`
15. Document the expected data flow end-to-end

---

## Key Files to Read

| File | Why |
|------|-----|
| `web/src/lib/program.ts` | Hardcoded dates, week calc, session maps — Bug 1, S1 |
| `web/src/lib/format.ts` | Missing file — Bug 3 |
| `web/src/views/TodayView.tsx` | Training display, coaching card, RPE — Bugs 2,4,5,6 |
| `web/src/views/TrainingPlanView.tsx` | Plan view, inline format dupes — Bug 3 |
| `web/src/views/WeekView.tsx` | Week schedule, possible format dupes |
| `web/src/views/RecoveryView.tsx` | Recovery metrics — check for staleness |
| `web/src/views/TrendsView.tsx` | Trend charts — check for staleness |
| `web/src/views/GoalsView.tsx` | Goals — check for hardcoded week thresholds |
| `web/src/hooks/useSupabase.ts` | All data hooks, realtime gaps — S2, S3 |
| `web/src/lib/types.ts` | TypeScript interfaces |
| `web/src/App.tsx` | App shell, routing |
| `scripts/morning_briefing.py` | Daily readiness + adjustment flow — S4 |
| `scripts/workout_push.py` | Garmin push, stale benchmarks — S1, S6 |
| `scripts/workout_generator.py` | Workout generation, replicated constants — S1 |
| `scripts/progression_engine.py` | Progression logic |
| `openclaw/coaching-context.md` | Current coaching rules, exceptions — Bug 6, S5 |
| `openclaw/coaching-program.md` | Current program definition — S1 |
| `sql/006_training_expansion.sql` | planned_workouts schema |

---

## Constraints

- Work on a feature branch based on `main`
- Fix what's broken, add what's missing — don't rewrite the whole app
- No new infrastructure (no new databases, services, or build tools)
- Supabase is the source of truth — the app reads from Supabase, not hardcoded files
- Coaching flows must write to Supabase — scripts and workflows write to `planned_workouts` and `coaching_log`
- Realtime where it matters — data that changes during the day needs realtime subscriptions
- Keep Phase A changes minimal and focused. Phases B-D can be larger but should be incremental commits

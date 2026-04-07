# Ascent — Open Tasks & Bugs

> Greppable bug/task log for Claude Code sessions. Each entry has a `[tag]` — search by tag to find it. Each bug lists the user-visible symptom so a future bug report can be matched back here.
>
> This file is separate from `TASKS.md` (which tracks high-level phase status). New bugs/asks land here.

---

## [open-task: goals-block1-seed] Apply Block 1 goals seed to Supabase

**Created:** 2026-04-07
**File:** `sql/seed_goals_block1.sql` (idempotent — `DELETE FROM goals WHERE notes LIKE '[block1-seed]%'` then insert)

**Why this is open:** GoalsView reads strength/endurance/milestones from the `goals` table. Until applied, Strength card shows "awaiting data" and Milestones card is empty.

**Bug-report hint:** "Goals tab Strength is empty / no milestones / VO2max bar empty" → check `SELECT count(*) FROM goals WHERE notes LIKE '[block1-seed]%';` first.

**Execution rules (user explicitly said: do NOT fabricate values):**
1. Pull from Supabase first: max `estimated_1rm` per lift from `training_sets` joined to `exercises` (last 90d); latest `vo2max` from `daily_metrics`; current weekly elevation from `activities` (mountain types only, last 7d).
2. Show user what was found and which lifts have NO data.
3. **Stop and ask** for missing current 1RMs and target values. Never invent.
4. Edit `sql/seed_goals_block1.sql`: `target_value` = user-provided, `current_value` = real DB value or NULL. Drop rows with neither current data nor a user-provided target.
5. Apply via `SUPABASE_DB_URL` from `.env`. Don't hardcode creds.
6. Verify: `SELECT category, metric, current_value, target_value, target_date FROM goals WHERE notes LIKE '[block1-seed]%' ORDER BY category, metric;`
7. Commit any SQL edits on the working branch, no PR.

---

## [bug-today-gym-mountain] Today tab counts mountain time as "gym" hours

**Reported:** 2026-04-07 (after Apr 6 backcountry tour)
**File:** `web/src/views/TodayView.tsx` lines 599–684, render at 965–977

**Symptom:** "Today tab Weekly Load shows 7h 7m gym" but the user did a backcountry tour Monday, not a gym session. `−50% vs last wk` is comparing against last week's resort gondola days that should not count as load either.

**Root cause:** `thisWeekDuration` / `lastWeekDuration` (line 680–684) sum `duration_seconds` across **all** activities; the UI labels the result `gym`. There is no filter by `activity_type === 'strength_training'`. Resort vs self-powered mountain isn't distinguished.

**Fix sketch:**
- Split the weekly load into three buckets:
  - `gymSeconds` — `activity_type === 'strength_training'`
  - `selfPoweredMountainSeconds` — types in `SELF_POWERED_MOUNTAIN_TYPES` (already imported line 13)
  - `resortSeconds` — remaining mountain types (resort skiing/snowboarding, gondola rides). Display ONLY in Recovery context. NEVER in planning load.
- `loadChangePct` should compare `gymSeconds + selfPoweredMountainSeconds` week-over-week, excluding resort.
- Render at lines 965–977 needs separate `gym` and `mountain` chips, not one combined "gym" number.
- Apply same split to `WeekView.tsx` "Load This Week" card (see [bug-week-mon-strength-vs-tour]) and `TrainingPlanView.tsx` mountain load card.

**Sub-issue — renamed activity not reflected:** User renamed Apr 6 "Mühlbachl Backcountry Snowboarding" → "Serles ..." in Garmin Connect, but the app still shows the old name. `scripts/garmin_sync.py` line 394/417 upserts `activity_name` keyed on `garmin_activity_id`, so a re-sync of that day would pick the rename up. Likely the sync only fetches the most recent N activities and doesn't re-pull already-stored ones. Add a `--refresh DAYS` flag (or always re-pull the last 14 days of activity metadata) so renames propagate.

---

## [bug-week-mon-strength-vs-tour] Week tab still shows Strength B on Monday after a tour was done

**Reported:** 2026-04-07
**File:** `web/src/views/WeekView.tsx` lines 109–155 (`dayCells` useMemo)

**Symptom:** Monday cell renders "Strength B: Upper + Core" with status `planned`, but the user actually did a backcountry tour that day (week stats correctly show 1228 m elevation and 7h 7m). The schedule grid should have flipped Monday to the actual activity name and status `mountain` (or new status `replaced`).

**Root cause:** In `dayCells`, the `if (planned)` branch wins unconditionally. The mountain detection branch (line 130) only runs when there's no planned row, so a planned strength session blocks recognition that the day was actually spent in the mountains.

**Fix sketch:**
- Reorder the logic: if `dayActivities` contains a self-powered mountain activity, mark status as `mountain` (or new `replaced`) regardless of `planned`. The planned strength row for that day should be auto-updated to `skipped` or `adjusted` in `planned_workouts` (or at minimum shown as such in UI).
- Cell label should use `activities[0].activity_name` (after the rename fix above) instead of the planned session title.
- Apply same gym / self-powered-mountain / resort split as [bug-today-gym-mountain] to the "Load This Week" card on lines ~270–310.

---

## [bug-plan-weight-mismatch] Plan tab: first-session "starting at" weight differs from Weight column

**Reported:** 2026-04-07
**File:** `web/src/views/TrainingPlanView.tsx` lines 437–453 (renderer); root cause in `scripts/workout_generator.py`

**Symptom:** For exercises tagged as first-session in week 2 (e.g. "Overhead Press (first session — starting at 35.8kg)"), the small grey note string says one number but the Weight column shows a totally different number (e.g. note: `35.8kg`, column: `47.5kg`).

**Root cause:** `ex.note` (free text) and `ex.weight_kg` come from different sources in the `workout_definition` JSON written by `scripts/workout_generator.py`. The note string is built at one stage; `weight_kg` is set separately. They drift apart when one path is updated and the other isn't.

**Fix sketch:**
- In `scripts/workout_generator.py`, when generating a first-session exercise, build the note string FROM the chosen `weight_kg` value — don't compute the note independently.
- Add an assertion: any `"starting at Xkg"` substring in `note` must match `weight_kg`.
- Re-generate week 2 (and any other already-generated weeks affected) after the fix.
- Renderer is fine — no UI change needed.

---

## [bug-plan-yaxis-clipped] Plan tab: lift progression chart Y-axis clipped

**Reported:** 2026-04-07
**File:** `web/src/views/TrainingPlanView.tsx` lines 929–937

**Symptom:** The lift progression LineChart Y-axis labels (kg values) are not fully visible on the left edge.

**Root cause:** `<LineChart margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>` has a negative `left` margin combined with `<YAxis width={40} unit="kg" />`. The `kg` suffix pushes labels wider than the 40 px allowance, and the negative margin clips the rest.

**Fix:** Set `margin.left` to `0` or `5`, bump `YAxis width` to `50`–`55`. Check the mountain-load chart at line ~1067 for the same issue while you're there.

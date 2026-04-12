# Ascent Code Review Analysis — 2026-04-12

**Auditor:** Claude (Opus 4.6, 1M ctx)
**Scope:** Four-lens review — senior developer, coach/sports-science, process/operations, user experience
**Branch:** claude/code-review-analysis-9PgMY
**Baseline:** Post-PR #30, including TrendsView hardening, reschedule confirmation, sync trigger auth fix

---

## Top 10 Prioritized Fixes

| Rank | Fix | Lens | Severity | Effort |
|------|-----|------|----------|--------|
| 1 | Wire subjective wellness into coaching decision matrix | Coach | HIGH | S-M |
| 2 | Enforce single write-path in DB (trigger/constraint) | Dev | HIGH | M |
| 3 | Surface coaching rationale in TodayView UI | User | HIGH | S |
| 4 | Add data-freshness banner to App.tsx | User | HIGH | S |
| 5 | Collapse post-workout logging into one card | User | HIGH | M |
| 6 | Extract HOME_SUBSTITUTIONS to shared config | Dev | MED | S |
| 7 | Add minimal CI (GitHub Actions) | Process | MED | S |
| 8 | Apply coaching_log traceability migration + wire mark_train_as_planned | Coach | MED | S |
| 9 | Split workout_push.py god-file | Dev | MED | L |
| 10 | Write real README.md runbook | Process | MED | S |

---

## Lens 1: Senior Developer

### 1.1 Single write-path contract is violated — HIGH

CLAUDE.md rule #2 says `coach_adjust.py` is the only writer to `planned_workouts`. Four writers exist:

- `scripts/garmin_sync.py:669-678` — writes `status`, `actual_garmin_activity_id`, `synced_at`
- `scripts/workout_generator.py:372-376` — writes `status=completed|skipped`
- `scripts/workout_push.py:1485-1498` — writes `garmin_workout_id` + `status=pushed`
- `scripts/garmin_workout_push.py:150-152` and `scripts/mobility_workout.py:537` — `garmin_workout_id` writes

No locking. A `garmin_sync` run between two `coach_adjust` calls can flip a rescheduled session back to `completed`. Fix: DB trigger or check constraint enforcing status transitions, not gentleman's agreement.

### 1.2 workout_push.py is a 1700-line god-file — HIGH

Bundles 8 concerns: date-to-block/week math, day-to-session mapping, Garmin exercise metadata, 70-line home-gym substitution map, session templates, progression calculation, Garmin JSON building, markdown file I/O, `planned_workouts` writes, Garmin API wrappers, CLI. Each could be its own module.

### 1.3 Python and TypeScript duplication — HIGH

`HOME_SUBSTITUTIONS` in `scripts/workout_push.py:260-330` AND `web/src/lib/homeWorkout.ts:15-120`. CLAUDE.md rule #8 documents the risk but doesn't solve it. Fix: single JSON in `config/`, imported by both.

### 1.4 Hardcoded constants that should be data — MED

- `workout_push.py:50-55` — `BLOCK_1_START`, `BLOCK_2_START`, `DELOAD_WEEKS` locked to Q2 2026
- `workout_push.py:178-191` — `GARMIN_BENCHMARKS` (1RM estimates) hardcoded
- `progression_engine.py:30-37` — plate increments
- `garmin_sync.py:109-114` — validation ranges (max HR 230; athlete's max could be 235)
- SKILL.md HRV/BB/TR thresholds in prompt, KB, and `progression_engine` with no common index

### 1.5 Garmin API error handling half-finished — MED

`garmin_sync.py:57-66` sleeps 1s, catches `GarminConnectTooManyRequestsError`, re-raises without retry. `RateLimitCooldownError` defined (`garmin_auth.py:64`) but never caught. No exponential backoff, no circuit breaker.

### 1.6 Test coverage — HIGH

`tests/` has 4 files (`conftest`, `test_progression_engine`, `test_decision_retrospective`, `test_interference_analysis`). NOT tested: `coach_adjust.py`, `workout_push.py`, `garmin_sync.py`, `workout_generator.py`, home workout substitution parity, date-to-block/week edge cases. No integration tests.

### 1.7 No CI, no linting, no type-check gate — MED

No `.github/workflows/`. No `pre-commit`. No mypy config. Vercel build is the only gate (frontend only). Python drift lands on main unopposed.

### 1.8 Frontend issues

- **Supabase write errors swallowed (HIGH):** `TodayView.tsx:241-290` — home/gym switch failures not surfaced to user
- **RLS overly permissive (MED):** `sql/029_app_write_policies.sql` uses `USING (true) WITH CHECK (true)`
- **God components (MED):** `TrainingPlanView` (1179 lines), `WeekView` (853), `TrendsView` (758), `TodayView` (618)
- **No query cache/offline (MED):** `useSupabase.ts` has no retries, no SWR, no persisted cache
- **No frontend tests (MED)**
- **`any` types (MED):** `web/src/lib/flying.ts:32,57-58`

---

## Lens 2: Coach / Sports-Science

### 2.1 Thresholds cited unevenly — MED

- HRV LOW — Plews et al. 2014 (IJSPP 8(4): 354-366). Citable.
- Mountain 6h+ separation — Doma et al. 2017. Citable.
- BB<30 hard rest override — Garmin-proprietary, no peer-reviewed threshold. Guessed.
- TR<40 — Garmin-proprietary. Guessed.
- 15% max micro-adjustment (CLAUDE.md rule #4) conflicts with KB Domain 1.1 "10% weekly cap" (different scope, naming collision creates confusion).

### 2.2 Subjective wellness captured but ignored — HIGH

React app collects wellness (sleep quality, energy, soreness, motivation, stress). Data lands in DB. SKILL.md cites Saw et al. 2016 ("self-report overrides wearables"). But the decision matrix (`SKILL.md:32-39`) has NO wellness term. The highest-evidence recovery signal in sports science is collected and discarded.

**Timing issue:** Wellness usually arrives after the 09:43 coaching decision. Agreed approach: Option A (re-evaluate on arrival) — Supabase trigger on wellness insert re-evaluates if composite is critically low.

### 2.3 Missing signals for mountain athlete on deficit — MED

- Previous-session residual fatigue / DOMS not asked
- Circadian/travel/altitude acclimatization not modeled
- Nutrition: `food_log` exists, no caloric/protein target, no deficit-aware load modulation. KB Integration #14 (carb scaling by mountain duration) documented, not enforced
- Sleep quality (deep/REM split): Garmin provides it, code only uses duration + efficiency
- Niggles/acute pain: `injury_log` table exists, no runtime link to exercise selection
- Hydration: not captured

### 2.4 Progression engine slightly over-conservative — LOW

`progression_engine.py:287-320` is well-designed (heavy-streak holds, sRPE>=9 holds, stall detection). But 10% cap at line 374 clashes with mesocycle-scoped 10% from KB. 2.5kg jump on 20kg accessory = 12.5%, gets blocked. Intent mismatch.

### 2.5 Feedback loop is open — MED

`interference_analysis.py` writes learned patterns to `athlete_response_patterns`. `decision_retrospective.py` writes outcomes to `coaching_decision_outcomes`. Nothing reads those outputs and updates decision rules. Learning is write-only.

### 2.6 Recovery side absent — MED

Coach optimizes load going in but nothing for recovery coming out. No sleep-hygiene prescriptions, no nutrition targets, no sauna/cold/compression guidance, no deload-week recovery content. For body-recomp on 300-500 kcal deficit with high mountain volume, this is the biggest lever not being pulled.

### 2.7 Locked decisions #2 and #4 need revisiting

Rule #2 violated by four writers (see 1.1). Rule #4 conflicts with KB (see 2.1). Both deserve an Opus session.

---

## Lens 3: Process / Operations

### 3.1 Single-Mac SPOF — HIGH

launchd on one Mac. Lid closed = nothing fires. `health_check.py` writes heartbeat every 15 min but rate-limits alerts — 60-min outage invisible. No "backend unreachable" indicator in React app. Options: move Garmin sync to VPS/GitHub Actions cron, or add "last heartbeat" banner to App.tsx.

### 3.2 2026-04-08 audit findings likely still open — HIGH

Prod Garmin auth was dead, 4-writer race unresolved, `sql/021` unapplied. No evidence these are fixed 4 days later.

### 3.3 Garmin auth rotation brittle — MED

`garmin_browser_bootstrap.py` requires interactive MFA. Auth window ~36h. `com.ascent.garmin-refresh` launchd agent crash-looped 71 times invisibly. Every trip = system dies.

### 3.4 No CI, no backups, no DR runbook — MED

No GitHub Actions. No test gate before merge. Supabase has automated backups, but no runbook tells Oliwer how to restore. No scheduled export of irreplaceable tables (`training_sessions`, `training_sets`, `coaching_log`, `exercise_feedback`).

### 3.5 SQL migrations: append-only yes, idempotent yes, reversible no — LOW

No down-migrations. Bad migration has no rollback except manual surgery.

### 3.6 Alert channel discipline good, escalation missing — LOW

`health_check` at 15-min can loop "Garmin auth locked" for 24h = ~95 identical messages. Need escalating alerts.

### 3.7 README.md is 75 bytes — MED

No runbook, no bootstrap guide, no "what to do when Garmin auth dies."

---

## Lens 4: User Experience (Oliwer)

### 4.1 No first-run story — HIGH

New phone/laptop is a blocker. `setup_phase3.sh` assumes dev environment. No one-page runbook for "open app, grant Supabase, tap Sync, done."

### 4.2 Silent degradation is the biggest trust leak — HIGH

When Garmin auth dies, React app shows yesterday's state with today's date. `TodayView.tsx:86-88` only shows empty state if BOTH summary and metrics are empty. Slack morning brief has stale warning; app does not. A sticky banner ("Data last synced 18h ago") costs 5 lines and buys back trust.

### 4.3 Coaching decisions are opaque — HIGH

`TodayView.tsx:367` renders `Coach: {adjustment_reason}` — the action, not the WHY. Phase 7 audit added `rule`, `kb_refs`, `inputs` columns to `coaching_log` — not surfaced in UI. Even one line ("Why: HRV LOW 55ms vs 85ms baseline, 5.5h sleep, 1500m climb yesterday") turns black box into coach.

### 4.4 Post-workout logging friction — HIGH

~25-30 taps across 3 separate cards (wellness sliders, sRPE, exercise feel). Predictable outcome: user stops logging. Single "Log session" card combining all inputs = <10 taps. The system collects LESS of the signal that would most improve coaching.

### 4.5 TodayView information overload — MED

618 lines, 11 distinct cards, same visual weight. No "focus on what to do next." Stacked "Before/After training" sections with collapsible rest would reduce cognitive load.

### 4.6 Tone violations vs CLAUDE.md rule #7 — MED

- `morning_briefing.py:284` — "Rest day recommended..." (directive)
- `morning_briefing.py:329-335` — "Rest day or very light movement" / "Green light..." (directive)

Easy copy fix to autonomy-supportive language.

### 4.7 Home-workout switching has no preview — MED

`TodayView.tsx:331-354` — single button, no preview of what changes, no weight-cap warnings. `countSubstitutions` exists in `homeWorkout.ts:182` and is unused. Add confirm modal with diff.

### 4.8 Goals, progression, system-status invisible — MED

- `GoalsView`: progress bars only, no "on pace / stalled / at risk"
- No per-exercise progression mini-card on TodayView
- No system-status panel
- No "ask coach" conversational surface

### 4.9 Notification load — LOW

5+ attention interrupts/day. Single daily summary with deep links would cut in half.

---

## Delta Scan (changes since 2026-04-08 audit)

| Issue | Status post-PR#30 |
|-------|-------------------|
| TrendsView crash | FIXED — SectionErrorBoundary added |
| WeekView reschedule | FIXED — confirmation step + error catching |
| Pull-to-refresh | FIXED — removed, refresh button only |
| Realtime channel leak | FIXED — removeChannel() on unmount |
| Sync trigger auth | PARTIALLY FIXED — server-side uses SUPABASE_ANON_KEY, VITE_SUPABASE_KEY still in bundle |
| RLS overly permissive | STILL PRESENT |
| HOME_SUBSTITUTIONS duplication | STILL PRESENT |
| No CI pipeline | STILL PRESENT |
| README stub | STILL PRESENT |
| flying.ts any types | STILL PRESENT |

---

## Remaining Issues (below top 10)

| Issue | Lens | Severity | Status |
|-------|------|----------|--------|
| RLS USING(true) on planned_workouts | Dev | MED | Still present |
| `any` types in flying.ts:32,57-58 | Dev | MED | Still present |
| Tone violations in morning_briefing.py | User/Coach | MED | Still present |
| TodayView cognitive overload (11 cards) | User | MED | Still present |
| Write error handling in TodayView switches | Dev | MED | Still present |
| Garmin retry/backoff on 429 | Dev | MED | Still present |
| useSupabase no offline/retry strategy | Dev | MED | Still present |
| God components (TrainingPlanView 1179 lines) | Dev | MED | Still present |
| Missing indexes on coaching_log, activities | DB | LOW | Acceptable at current scale |
| No down-migrations | Process | LOW | Acceptable risk |
| Alert escalation (health_check spam) | Process | LOW | Still present |
| Feedback loop not closing (write-only patterns) | Coach | MED | Still present |
| Recovery-side coaching absent | Coach | MED | Still present |
| Progression engine 10% cap vs KB 10% weekly | Coach | LOW | Conservative, safe |
| Garmin auth rotation brittleness | Process | MED | Structural issue |
| Single-Mac SPOF | Process | HIGH | Structural issue |

---

## Implementation Handover

### Chapter 1: Wire subjective wellness (Option A — re-evaluate on arrival)

**Decision:** Oliwer approved. Wellness usually arrives after the 09:43 coach decision, so approach is:
1. SQL migration `sql/030_wellness_in_coaching_context.sql` — add `wellness_composite` to `daily_coaching_context` view
2. Supabase trigger on wellness table INSERT: if composite <= 2.0 AND today's `planned_workouts.status` IN ('planned','pushed'), update `adjustment_reason` with wellness-override message
3. TodayView already renders `adjustment_reason` — override appears automatically
4. CCD at 09:43 reads `daily_coaching_context` — wellness included if logged early, trigger handles late logging

**Key files to read first:**
- `sql/016_interference_and_load.sql:280-352` — current view definition
- `web/src/components/WellnessInput.tsx` — find wellness table name
- `web/src/views/TodayView.tsx:360-370` — verify adjustment_reason rendering
- `sql/023_wire_wellness_and_rpe.sql` — existing wellness SQL
- `sql/027_wellness_zscore.sql` — existing wellness z-score logic

### Chapters 2-10: Present one at a time, describe impact, wait for go/defer

Each chapter follows the same pattern:
1. Describe what changes and why
2. Describe impact on user/app
3. Wait for Oliwer's go or defer
4. Implement if go
5. Move to next chapter

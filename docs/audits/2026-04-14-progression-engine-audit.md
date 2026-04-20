# Progression Engine Audit — 2026-04-14

## Summary

Thorough audit of the weight progression system: `progression_engine.py`, `workout_push.py`, related DB views, and Garmin integration. The engine is well-designed for conservative progression but has significant gaps relative to the knowledge base.

## What Works

- **Double progression**: reps first, then weight increase when all sets hit target
- **Stall detection**: 3+ sessions at same weight → 10% drop + reps to 12
- **Heavy feel veto**: 2+ consecutive "heavy" exercise_feedback ratings block weight increase
- **Session sRPE veto**: sRPE ≥9 blocks increase; sRPE 8 blocks on recent jumps
- **Deload**: same weight, 50% sets on weeks 4 and 8
- **Plate rounding**: correct per equipment type (2.5kg barbell, 1.25kg DB, KB snap)
- **Mixed-weight handling**: KB ramp-up correctly waits until all sets at top weight hit target

## Critical Gaps

### 1. No RPE-based acceleration (HIGH)
**KB says**: When avg RPE 6-7 for 2+ sessions → offer accelerated progression
**Code does**: Only uses RPE as a veto (≥9 blocks, 8 slows). No "you're fresh, go faster" path.
**Impact**: Athlete may plateau at suboptimal weights when recovery is excellent.
**Fix**: If sRPE ≤ 7 AND exercise_feedback = 'light' or 'right' for 2+ sessions → allow 2× standard increment.

### 2. Light feel completely ignored (HIGH)
**KB says**: 4+ "light" ratings should accelerate progression
**Code does**: Only heavy feel is checked (`_count_heavy_streak`). No `_count_light_streak` or similar.
**Impact**: Asymmetric autoregulation — conservative on heavy, indifferent on light.
**Fix**: Add light-feel acceleration: if 3+ consecutive "light" AND sRPE ≤ 7 → jump 2× standard increment.

### 3. Weekly volume cap not enforced (HIGH)
**KB says**: ≤10% week-over-week total volume increase
**Code does**: Only checks individual weight jumps >10% when weight ≥50kg. No aggregate weekly volume check.
**Impact**: Barbell Row jumped 25→50kg (100% increase) unchecked.
**Note**: The 25→50kg jump came from Garmin recording 50kg when planned was 25kg — the engine trusted the actual data.
**Fix**: Add weekly_training_load view check before accepting progression decisions.

### 4. No "add sets" before stall deload (MEDIUM)
**KB says**: When stalled 3+ sessions → try +1 set per exercise for 2 weeks first, THEN deload
**Code does**: Goes directly to -10% weight + 12 reps (deload_reset)
**Impact**: More aggressive deloading than necessary, may lose strength gains.
**Fix**: Add intermediate step: on stall, first try `applied="add_set"` for 2 weeks, then deload_reset.

### 5. Actual performance not recorded (HIGH)
**KB says**: Close the loop between planned and actual
**Code does**: `exercise_progression.actual_*` columns exist but are never written to. Only planned values recorded.
**Impact**: No way to verify if athlete actually hit planned weight/reps. Coaching context can't surface "athlete missed planned targets 3 sessions in a row."
**Fix**: After Garmin sync completes training_sets, backfill `exercise_progression.actual_*` from the matched sets.

### 6. Wellness data ignored in progression (MEDIUM)
**KB says**: Subjective wellness overrides wearables (Saw et al. 2016)
**Code does**: `subjective_wellness` (sleep, energy, soreness, motivation, stress) is collected but `progression_engine.py` never reads it.
**Impact**: A session on a day with soreness=1/5 gets same progression treatment as soreness=5/5.
**Fix**: Wire wellness composite into sRPE modifier: if composite < 2.5 → treat as sRPE 8 (mild conservatism).

### 7. Natural deloads not recognized (LOW)
**KB says**: Weeks with 3+ mountain days and 1 gym session function as partial deloads
**Code does**: Deload weeks hard-coded to 4 and 8, regardless of mountain activity.
**Impact**: Over-deloading when a mountain-heavy week already provided natural recovery.
**Fix**: If previous week had mountain_days ≥ 3 AND gym_sessions ≤ 1, skip planned deload week.

### 8. Turkish Get-Up weight entry on Garmin (MEDIUM)
**Issue**: Garmin watch doesn't show weight entry prompt for CORE category exercises
**Root cause**: Turkish Get-Up mapped to `("CORE", "TURKISH_GET_UP")` — firmware limitation
**Fix**: Reclassify to `("TOTAL_BODY", "TURKISH_GET_UP")` which reliably shows weight prompts.
**Same issue may affect**: Ab Wheel Rollout (CORE), Dead Bugs (HIP_STABILITY)

### 9. Flat progression chart (MEDIUM)
**Issue**: Lift progression chart shows same weight for weeks 1-8 because the engine computes the same answer for each week from the same "last session" data.
**Root cause**: `calculate_weight()` is called N times for N future weeks but always returns the same result because there's no future data to differentiate.
**Fix**: For future weeks, apply the formula fallback (+2.5kg/week) UNLESS actual data exists. Show projected progression as a lighter line.

### 10. Missing weight data not flagged (LOW)
**Issue**: When Garmin doesn't record `weight_kg` for a working set, the engine silently skips it.
**Impact**: Coach doesn't know data was incomplete.
**Fix**: Surface "incomplete session data" in `daily_coaching_context.progression_alerts`.

## Data Flow

```
Athlete completes workout
    → Garmin records sets (weight, reps, RPE)
    → garmin_sync.py writes to training_sets + training_sessions
    → Athlete logs sRPE (0-10) and exercise_feedback (light/right/heavy)
    → Next push: calculate_weight() calls progression_engine
    → Engine reads: training_sets, training_sessions.srpe, exercise_feedback
    → Engine decides: weight_increase / hold / rep_increase / deload_reset / deload_week
    → Records to exercise_progression table (planned_* only)
    → workout_push.py builds Garmin JSON with calculated weight
    → sync_progressed_weights() writes back to planned_workouts
```

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `scripts/progression_engine.py` | Core progression algorithm | 583 |
| `scripts/workout_push.py` | Integration, Garmin push, weight sync | 1713 |
| `sql/006_training_expansion.sql` | exercise_progression table | |
| `sql/017_decision_retrospective.sql` | progression_velocity view | |
| `sql/024_feedback_loops.sql` | stall_early_warning, exercise_feedback_trends views | |
| `sql/025_enrich_coaching_views.sql` | daily_coaching_context (progression_alerts) | |
| `tests/test_progression_engine.py` | Unit tests | 287 |

## Test Coverage Gaps

- ❌ Mixed-weight KB ramping
- ❌ Light feel handling (doesn't exist yet)
- ❌ Formula fallback edge cases
- ❌ Null weight_kg scenarios
- ❌ Integration with planned_workouts sync
- ❌ Natural deload detection

---

## Deep Research Findings (2026-04-14 evening)

### Coach LLM ↔ Progression Engine Boundary

The coaching LLM (daily/weekly) **reads but never overrides** the progression engine:

- **Coach CAN**: hold weights proactively (via context: high sRPE, heavy feel), reduce volume/RPE, swap exercises, reschedule sessions
- **Coach CANNOT**: change `weight_kg` in `workout_definition`. No action in `coach_adjust.py` modifies weight.
- **Coach flags**: stall warnings, progression alerts, feel trends → surfaces in daily card and weekly review
- **When 3+ exercises stall simultaneously**: coach flags for block review (Opus session), doesn't fix itself

This means ALL weight progression improvements must happen in `progression_engine.py`, not in the coaching prompts.

### KB Autoregulation Thresholds (exact values)

**Double progression protocol** (KB §1.1, lines 80-101):
- Train at fixed weight until ALL sets hit TOP of rep range with ≥2 RIR
- Increase weight by minimum increment (2.5kg compounds, 1-2kg isolation)
- Reset reps to bottom of range
- If reps DECREASE from previous session at same weight → flag fatigue
- Stall 3+ sessions → add one set per exercise (max per-session) for 3-4 weeks, THEN retry load

**RPE-based load modulation** (KB §1.3, lines 206-277):
- RPE consistently overshoots target by >1 for ≥2 weeks → reduce loads 2.5-5%
- No explicit "accelerate when RPE low" rule — but absence of high RPE + hitting all reps = green light for increase

**Three-tier deload response** (KB §5, lines 2226-2267):
- Tier 1 (micro): RPE inflated 1 point → reduce 1-2 sets, cap RPE by 1
- Tier 2 (deload): RPE inflated ≥2 points consistently → 50% volume week
- Tier 3 (restructure): 3+ exercises stalled, e1RM plateau 6+ weeks → block review

**Training age determines model** (KB §1.1, lines 102-108):
- <6 months: linear session-to-session increments
- 6-12 months: double progression, tight ranges (4-6 compounds, 8-15 isolation)
- 1-3 years: DUP/weekly undulating with RPE autoregulation
- This athlete is ~3 months into structured training → between linear and double progression

### Database State (2026-04-14)

**`exercise_progression` table**: 30 entries since 2026-04-02. All `actual_*` columns NULL.

Key recent decisions:
- OHP: 35→45kg (+10kg, week 3) — data-driven from recorded 40kg
- Cable Row: 35→42.5kg (+7.5kg) — data-driven from recorded 40kg  
- Turkish Get-Up: 12→10→8kg — GOING DOWN (Garmin not recording weight correctly for CORE exercises)
- Kettlebell Halo: 12→14→12kg — oscillating (deload drops, but deload should keep weight same)
- DI Press: stuck at 20kg for 3 sessions ("behind" status)

**`progression_velocity` view**: 22 exercises tracked
- DI Press: "behind" (3 sessions at 20kg, kg/week=2.92)
- KB Swing: "building" (6 sessions at same weight, 0 kg/week)
- Trap Bar Deadlift: "building" (5 sessions, 0 kg/week)
- Bulgarian Split Squat: "building" (5 sessions, 0 kg/week)

**`stall_early_warning` view**: EMPTY — no exercises flagged. This seems wrong given DI Press at 3 sessions.

### Garmin Weight Entry by Category

Confirmed via firmware testing:
- SQUAT, BENCH_PRESS, ROW, DEADLIFT, SHOULDER_PRESS, CARRY, LATERAL_RAISE → weight entry works
- CORE → weight entry BLOCKED by firmware (Turkish Get-Up, Ab Wheel affected)
- HIP_STABILITY → weight entry BLOCKED (Dead Bugs, Bird Dogs — but these are bodyweight anyway)
- WARM_UP → no weight entry (expected)
- TOTAL_BODY → weight entry WORKS (Kettlebell Swing mapped here correctly)

**Fix**: Remap Turkish Get-Up from CORE to TOTAL_BODY. In both push map AND reverse map.

---

## Kickoff Prompt for Next Session

Copy this into a new Claude Code session to continue the work:

```
Read /Users/jarvisforoli/projects/ascent/docs/audits/2026-04-14-progression-engine-audit.md — this is a thorough audit of the progression engine with 10 identified gaps. Then read the code files listed in the audit (progression_engine.py, workout_push.py, coach_adjust.py, SKILL.md).

Your job is to plan and implement the progression engine improvements, prioritized by impact:

**Phase 1 — Quick fixes (do first):**
1. Turkish Get-Up: reclassify from CORE to TOTAL_BODY in workout_push.py GARMIN_EXERCISE_MAP (both push and sync maps)
2. Deload weight bug: verify deload returns same weight (audit found some exercises dropping weight on deload weeks — KB says "same weight, 50% sets")
3. Actual performance recording: after Garmin sync, backfill exercise_progression.actual_* from training_sets

**Phase 2 — RPE-informed progression:**
4. Light-feel acceleration: if 3+ consecutive "light" ratings AND sRPE ≤ 7 → allow 2× standard increment (5kg instead of 2.5kg for compounds)
5. RPE-based modulation: if average sRPE ≤ 6.5 for 2+ sessions AND all reps hit → offer accelerated progression
6. RPE overshoot detection: if RPE consistently >1 above target for ≥2 weeks → auto-reduce loads 2.5-5%

**Phase 3 — Structural improvements:**
7. Stall protocol: add intermediate "add_set" step (try +1 set for 2 weeks before deload_reset)
8. Weekly volume cap: check aggregate weekly volume ≤10% increase before accepting progression
9. Wellness integration: if subjective_wellness.composite < 2.5 → treat as sRPE 8 (mild conservatism)
10. Natural deload recognition: if previous week had mountain_days ≥ 3 + gym ≤ 1, consider skipping planned deload

**Constraints:**
- progression_engine.py owns all weight decisions — coaching LLM reads but never overrides
- All changes must pass existing tests in tests/test_progression_engine.py + add new tests for new features
- Use the KB thresholds exactly (docs/knowledge-base/knowledge-base.md §1.1, §1.3, §5)
- Run `cd web && npm run build` after any frontend changes
- Commit and push after each phase

Start with /plan to propose the approach before implementing.
```

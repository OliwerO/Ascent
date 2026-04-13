# Audit Chapters 22-24: Coaching Design Improvements + Metrics Credibility Integration

## Context

The Ascent coaching system has a write-only learning problem: `interference_analysis.py` and `decision_retrospective.py` analyze historical data and write patterns to `athlete_response_patterns` and outcomes to `coaching_decision_outcomes`, but only mountain interference patterns are read back into daily decisions. Recovery-response patterns and decision quality data sit unused. Meanwhile, the coach optimizes training load going in but offers zero recovery guidance coming out — no sleep-hygiene nudges, no nutrition awareness, no deload recovery content. For body recomp on a 300-500 kcal deficit with high mountain volume, this is the biggest lever not being pulled. Finally, several captured signals (sleep stages, injury accommodations, stress, respiration) aren't wired into coaching logic.

The user has also produced a comprehensive Garmin metrics credibility classification that formalizes which signals deserve decision-making weight. This needs to be stored in the repo and integrated into the coaching protocol.

## Current state

```
              WRITES                           READS BACK
interference_analysis.py ──► athlete_response_patterns ──► daily_coaching_context
  (mountain_interference)        (mountain_interference        (mountain patterns only)
                                  recovery_response    ──► NOTHING
                                  progression_velocity ──► NOTHING)

decision_retrospective.py ──► coaching_decision_outcomes ──► weekly_coaching_summary
                                                         ──► NOT daily_coaching_context

Sleep stages (deep/REM)    ──► daily_summary (available) ──► Not in coaching view
Stress / respiration       ──► daily_metrics (available)  ──► Not in coaching view
Injury log                 ──► active_injuries (in view)  ──► Not linked to exercises
```

## Target state

```
              WRITES                           READS BACK
interference_analysis.py ──► athlete_response_patterns ──► daily_coaching_context
decision_retrospective.py     (ALL pattern types)            (learned_patterns JSONB)
                          ──► coaching_decision_outcomes ──► daily_coaching_context
                                                             (decision_quality_30d JSONB)

Sleep stages ──► daily_coaching_context (deep_sleep_pct, rem_sleep_pct)
Stress       ──► daily_coaching_context (avg_stress_level)
Respiration  ──► daily_coaching_context (respiration_avg)
Injury log   ──► SKILL.md rules (check injuries vs today's exercises)

Recovery coaching ──► coachingDecision.ts (recovery tips in React)
                  ──► SKILL.md (recovery section for CCD daily)
                  ──► CCD daily prompt (recovery line in card)

Metrics credibility ──► docs/knowledge-base/garmin-metrics-credibility.md
                    ──► SKILL.md (signal credibility tiers)
```

---

## Implementation

### Step 1: Store metrics credibility document
**File:** `docs/knowledge-base/garmin-metrics-credibility.md`

Save the user's research document as-is. This becomes a reference for SKILL.md and future coaching logic.

### Step 2: SQL migration — close the feedback loop + wire missing signals
**File:** `sql/033_close_feedback_loop.sql`

Recreate `daily_coaching_context` view with these additions:

**a) All learned patterns (not just mountain_interference):**
Replace the `mountain_patterns` CTE with a broader `learned_patterns` CTE:
```sql
learned_patterns AS (
  SELECT
    COALESCE(
      jsonb_agg(jsonb_build_object(
        'type', arp.pattern_type,
        'key', arp.pattern_key,
        'pattern', arp.observation,
        'confidence', arp.confidence,
        'sample_size', arp.sample_size,
        'effect_size', arp.effect_size
      )),
      '[]'::jsonb
    ) AS learned_patterns
  FROM athlete_response_patterns arp
  WHERE arp.confidence IN ('medium', 'high')
)
```

**b) Decision quality summary (last 30 days):**
```sql
decision_quality AS (
  SELECT jsonb_build_object(
    'total', COUNT(*),
    'good', COUNT(*) FILTER (WHERE outcome_quality = 'good'),
    'neutral', COUNT(*) FILTER (WHERE outcome_quality = 'neutral'),
    'poor', COUNT(*) FILTER (WHERE outcome_quality = 'poor'),
    'poor_decisions', COALESCE(jsonb_agg(
      jsonb_build_object('date', decision_date, 'type', decision_type, 'notes', assessment_notes)
    ) FILTER (WHERE outcome_quality = 'poor'), '[]'::jsonb)
  ) AS decision_quality_30d
  FROM coaching_decision_outcomes
  WHERE decision_date >= CURRENT_DATE - 30
)
```

**c) Sleep stage data from daily_summary:**
Expand the `recovery` CTE to also select `deep_sleep_seconds` and `rem_sleep_seconds`. Add computed columns in the final SELECT:
```sql
r.deep_sleep_seconds,
r.rem_sleep_seconds,
CASE WHEN r.total_sleep_seconds > 0
  THEN ROUND((r.deep_sleep_seconds::numeric / r.total_sleep_seconds) * 100, 1)
  ELSE NULL END AS deep_sleep_pct,
CASE WHEN r.total_sleep_seconds > 0
  THEN ROUND((r.rem_sleep_seconds::numeric / r.total_sleep_seconds) * 100, 1)
  ELSE NULL END AS rem_sleep_pct,
```

**d) Stress and respiration from daily_metrics:**
Add a new CTE:
```sql
vitals AS (
  SELECT
    dm.avg_stress_level,
    dm.respiration_avg
  FROM daily_metrics dm
  WHERE dm.date <= CURRENT_DATE
  ORDER BY dm.date DESC
  LIMIT 1
)
```

**e) Final SELECT changes:**
- Replace `mp.mountain_interference_patterns` with `lp.learned_patterns`
- Add `dq.decision_quality_30d`
- Add `r.deep_sleep_pct`, `r.rem_sleep_pct`
- Add `v.avg_stress_level`, `v.respiration_avg`
- Keep `mountain_interference_patterns` as a backwards-compatible alias (filtered from learned_patterns) so CCD prompt doesn't break

### Step 3: Update SKILL.md — recovery coaching + injury linking + signal credibility
**File:** `openclaw/skills/health-coach/SKILL.md`

**a) New section: "Signal Credibility Tiers"** (after Decision Matrix)

Reference `docs/knowledge-base/garmin-metrics-credibility.md`. Summarize the three tiers:
- **PRIMARY** (drive decisions): Overnight HRV 7d trend, RHR 7d trend, LTHR, sleep duration
- **SUPPORTING** (context): VO2max trend, sleep stages, stress score, respiration rate, recovery time
- **DEMOTED** (guardrails only or ignore): Body Battery, Training Readiness, Training Status, ACWR, SpO2

This formalizes what CLAUDE.md rule #5 already partially says, and gives the CCD daily coach explicit guidance.

**b) New section: "Recovery Recommendations"** (after Auto-Adjustment Triggers)

Conditional recovery tips the coach includes in the daily card when relevant. Rules:
- Sleep: deep_sleep_pct < 15% for 2+ nights -> "Deep sleep has been low -- cooler room, earlier screen cutoff, and consistent bedtime tend to help"
- Sleep: rem_sleep_pct < 18% for 2+ nights -> "REM sleep trending low -- alcohol, late caffeine, and irregular sleep times are common culprits"
- Sleep: total < 6h -> "Short sleep tonight -- a 20-min nap before training can partially compensate"
- Post-mountain (mountain_days_3d > 0): "Hydration and protein intake support recovery after mountain days -- 1.6-2.2g/kg/day protein target"
- Deload week: "Deload week -- extra sleep and light mobility maximize adaptation from the training block"
- Stress: avg_stress_level > 50 sustained -> "Stress has been elevated -- even 10 min of walking or breathing exercises can shift the balance"
- Respiration: respiration_avg elevated 2+ brpm above baseline -> "Overnight breathing rate is up -- could signal incomplete recovery or early illness"

All tips use autonomy-supportive language (no "should", "must", "need to"). Max 1 recovery tip per card to avoid spam.

**c) New section: "Injury-Aware Exercise Selection"** (after Recovery Recommendations)

When `active_injuries` is non-empty:
- Cross-reference each injury's `body_area` and `accommodations` against today's `session_exercises`
- If any exercise targets an injured body area, apply accommodations (e.g., "avoid overhead pressing" -> flag shoulder press, suggest alternative)
- Surface in card: "Active: [issue] -- [accommodation applied]"
- This is advisory -- the CCD coach flags and adjusts, doesn't skip silently

**d) New section: "Learned Patterns"** (update existing Feedback Loop Data section)

Update the `mountain_interference_patterns` reference to `learned_patterns` which now includes:
- `recovery_response` patterns (e.g., "rest on HRV LOW days -> good outcome 80% of the time")
- `progression_velocity` patterns (e.g., "3+ exercises stalled simultaneously")
- Decision quality: "Recent decision quality: 8 good, 2 neutral, 1 poor out of 11"

### Step 4: Update CCD daily prompt — recovery line in card
**File:** `ccd-prompts/health-coach-daily.md`

**a) STEP 2 update:** Add the new fields to the list of fields to read from daily_coaching_context:
`deep_sleep_pct, rem_sleep_pct, avg_stress_level, respiration_avg, learned_patterns, decision_quality_30d`

**b) STEP 4 update:** Add injury check:
"Check active_injuries against today's session_exercises. If any exercise involves an injured body area, apply the accommodation from the injury_log entry (swap, modify, or flag)."

**c) STEP 6 update:** Add a recovery line to the card format:
```
<conditional -- max 1 recovery tip based on signals:>
recovery tip from SKILL.md Recovery Recommendations section
```

Add learned patterns context:
```
<if learned_patterns contains recovery_response patterns relevant to today's decision:>
Past decisions: <brief summary, e.g., "rest on HRV LOW -> good outcome 4/5 times">
```

### Step 5: Update React coaching decision + TodayView — recovery tips
**Files:**
- `web/src/lib/coachingDecision.ts`
- `web/src/views/TodayView.tsx`

**a) `coachingDecision.ts`:** Add `recoveryTip` to `CoachingDecision` interface. Add inputs for `deepSleepPct`, `remSleepPct`, `mountainDays3d`, `isDeload`. Compute a single recovery tip string (same rules as SKILL.md section, null if nothing applies).

**b) `TodayView.tsx`:** After existing coaching points, if `decision.recoveryTip` is non-null, push it as a coaching point with icon and muted color. The sleep data is already fetched via `useSleep` -- compute deep/REM percentages from the hook data.

### Step 6: Update TASKS.md
Mark chapters 22-24 as complete. Add any new items discovered during implementation.

---

## File change summary

| File | Change type | Chapter |
|------|------------|---------|
| `docs/knowledge-base/garmin-metrics-credibility.md` | New file | Metrics |
| `sql/033_close_feedback_loop.sql` | New migration | Ch 22 + 24 |
| `openclaw/skills/health-coach/SKILL.md` | Edit (4 new sections) | Ch 22 + 23 + 24 |
| `ccd-prompts/health-coach-daily.md` | Edit (3 sections) | Ch 22 + 23 + 24 |
| `web/src/lib/coachingDecision.ts` | Edit (add recoveryTip) | Ch 23 |
| `web/src/views/TodayView.tsx` | Edit (pass sleep data, show tip) | Ch 23 |
| `TASKS.md` | Edit (mark done) | All |

## Order of operations

1. Save metrics credibility doc (standalone, no dependencies)
2. SQL migration (must deploy before CCD reads new fields)
3. SKILL.md updates (CCD reads this -- update before next CCD run)
4. CCD daily prompt updates (references SKILL.md and new view fields)
5. React changes (coachingDecision.ts then TodayView.tsx)
6. `cd web && npm run build` -- verify no TypeScript errors
7. Update TASKS.md
8. Commit + push each chapter separately

## Verification

1. **SQL:** Run migration against Supabase. Query `daily_coaching_context` and verify:
   - `learned_patterns` returns array with both `mountain_interference` and `recovery_response` entries
   - `decision_quality_30d` returns object with good/neutral/poor counts
   - `deep_sleep_pct` and `rem_sleep_pct` are non-null when sleep data exists
   - `avg_stress_level` and `respiration_avg` are populated
   - `mountain_interference_patterns` still works (backwards compat)
2. **React:** `npm run build` passes. Open app, check Today view shows recovery tip when sleep stages are low or on rest/mountain days.
3. **CCD dry run:** Run `coach_adjust.py --dry-run` to verify the new fields are accessible.
4. **SKILL.md:** Read through to verify autonomy-supportive language (no "should"/"must"/"need to" in recovery tips).

---
name: health-coach
description: Coaching protocol reference for Ascent training system
---

# Ascent Coaching Protocol

This document is the authoritative protocol reference for all coaching
decisions in the Ascent system. It is read by:
- **CCD daily session** (09:43) — for autoregulation decisions
- **CCD weekly session** (Sun 20:03) — for review context
- **CCD block review** (on-demand) — for program evaluation
- **Jarvis** (on-demand) — for ad-hoc user requests and adjustments

The CCD prompts handle their own execution flow (data queries, Slack posting,
Garmin push). This document defines the RULES, not the steps.

## Hierarchy

Coach EXECUTES the plan from coaching-context.md. Coach does NOT create new
programs or make structural changes (that is the block-review session's role).
Coach CAN make day-to-day adjustments: intensity scaling, session swaps, volume
reduction, rest day overrides.

## Decision Matrix

Use recovery data from `daily_coaching_context` to determine today's action.

### Recovery → Action Mapping

| HRV Status | Sleep | Action |
|------------|-------|--------|
| BALANCED + above weekly avg | >7h | Full send. RPE 7-8. |
| BALANCED + within range | 6-7h | Train as planned. RPE 6-7. |
| BALANCED | <6h | Reduce volume 30%. Drop RPE by 1. Swap to mobility via `coach_adjust.py --action mark_mobility`. |
| UNBALANCED | >6h | Train but cap RPE at 6. |
| UNBALANCED | <6h | Rest or mobility only. |
| LOW | Any | Rest day. Mobility or easy walk only. |
| LOW 2+ consecutive days | Any | Extended rest. Skip gym until BALANCED returns. |

### Hard Overrides (from `daily_coaching_context.hard_override`)

These override the matrix above regardless of other signals:

| `hard_override` value | Action |
|---|---|
| `body_battery_critical` | Body battery <30 → rest/mobility. |
| `training_readiness_low` | Training readiness <40 → rest/mobility. |
| `multi_signal_degraded` | HRV LOW + sleep <6h → force rest day. |
| `subjective_poor` | Wellness composite <2.5 → rest day (athlete self-report overrides wearable data per Saw et al. 2016). |

### Multi-Signal Convergence (3+ degraded → force rest)

When 3+ of these are simultaneously degraded, force a rest day. No exceptions:
- HRV: LOW or UNBALANCED
- Sleep: <6h
- Body battery: <30
- Training readiness: <40
- Subjective wellness composite: <2.5

### Block-Specific RPE and Progression

- Block 1 (Weeks 1-3): RPE 6-7, linear progression
- Block 1 Week 4: Deload (50% volume, same weight)
- Block 2 (Weeks 5-7): RPE 7-8, continued linear
- Block 2 Week 8: Deload + assessment

Block/week calculation:
- Block 1 starts April 1, 2026. Block 2 starts April 29, 2026.
- `week = floor((today - block_start_date) / 7) + 1`
- Weeks 4 and 8 are deload weeks
- `daily_coaching_context` provides `current_week` and `is_deload_week`

## Signal Credibility Tiers

Not all Garmin metrics deserve equal decision-making weight.
See `docs/knowledge-base/garmin-metrics-credibility.md` for the full analysis.

### PRIMARY signals (drive decisions)
- **Overnight HRV 7-day trend** — most reliable recovery indicator
- **Resting HR 7-day trend** — elevated RHR signals incomplete recovery
- **Sleep duration** — hours of sleep, highly reliable
- **Subjective wellness composite** — athlete self-report overrides wearable data

### SUPPORTING signals (context, not decisive)
- **VO2max trend** — directional over weeks, noisy day-to-day
- **Sleep stages (deep/REM split)** — useful for recovery recommendations
- **Stress score (daily average)** — correlates with HRV but noisier
- **Respiration rate** — elevated rate can signal illness or incomplete recovery
- **Recovery time estimate** — directional guidance only

### DEMOTED signals (guardrails only or ignore)
- **Body Battery** — proprietary composite, used only as hard override at <30
- **Training Readiness** — used only as hard override at <40
- **Training Status** — too slow to react, not used in daily decisions
- **ACWR** — not computed (insufficient structured load data)
- **SpO2** — too noisy for daily use

When signals conflict, trust the PRIMARY tier. SUPPORTING signals add context
but do not override PRIMARY. DEMOTED signals only fire as safety guardrails.

## Feedback Loop Data

The `daily_coaching_context` view includes these feedback-loop columns.
Use them to inform daily decisions:

### `progression_alerts` (JSONB array)

Each entry: `{exercise, weight_kg, status, sessions_at_weight, kg_per_week, e1rm, stall_risk}`

- **`status: "stalled"`** (4+ sessions at same weight) — flag in the coaching card.
  If 3+ exercises stall simultaneously, flag for block review (systemic fatigue).
- **`status: "behind"`** (3 sessions at weight) — mention as "stall watch" in card.
- **`stall_risk: "high"`** — exercise is about to stall (RPE climbing, sleep declining,
  feel trending heavy). Consider holding weight proactively.
- **`stall_risk: "moderate"`** — monitor. Mention if relevant to today's session.
- Progressing exercises (`kg_per_week > 0`) — mention weight increases in coaching card.

### `exercise_feel_alerts` (JSONB array)

Each entry: `{exercise, feel_trend, heavy_streak, heavy_count, total_sessions}`

- **`feel_trend: "persistently_heavy"`** — 3+ consecutive sessions rated "heavy".
  Hold weight for this exercise even if reps are being hit.
- **`feel_trend: "mostly_heavy"`** — 4+ of last 6 sessions heavy. Watch closely.

### `last_srpe` (integer, 1-10)

Session-level RPE from the most recent training session.

- **sRPE >= 9** — hold ALL weights today. Session was a grinder. Surface this:
  "Last session RPE 9 — holding weights to consolidate."
- **sRPE 8 + recent weight increase** (exercise at <= 2 sessions at current weight) —
  hold that exercise's weight. Surface this.
- **sRPE <= 7** — no constraint from session RPE.

### `learned_patterns` (JSONB array)

Each entry: `{type, key, pattern, confidence, sample_size, effect_size}`

All learned patterns from the athlete's own data, across three categories:

- **`mountain_interference`** — how mountain activity affects gym performance
  (e.g., "Gym volume drops 12% within 48h of >1500m elevation"). When
  `mountain_days_3d > 0`, include relevant mountain patterns in the card.
- **`recovery_response`** — how the athlete responds to coaching decisions
  (e.g., "Rest on HRV LOW days led to good outcomes 80% of the time").
  Use these to calibrate confidence in rest vs train decisions.
- **`progression_velocity`** — load progression patterns
  (e.g., "3+ exercises stalled simultaneously — consider program redesign").
  Cross-reference with `progression_alerts` for today's exercises.

Only medium/high confidence patterns appear. Use them as context, not overrides.

### `decision_quality_30d` (JSONB object)

Fields: `{total, good, neutral, poor, poor_decisions}`

Summary of coaching decision outcomes from the last 30 days. `poor_decisions`
is an array of the 3 most recent poor outcomes with date, type, and notes.

- If `good/total < 60%`, mention calibration concern in the coaching card.
- Review `poor_decisions` to avoid repeating the same mistake.

### `mountain_interference_patterns` (JSONB array, backwards-compat)

Filtered subset of `learned_patterns` where `type = 'mountain_interference'`.
Same format as before: `{pattern, confidence, key, sample_size}`.

### Sleep Quality Signals

- **`deep_sleep_pct`** — percentage of total sleep in deep sleep stage. Below
  15% indicates poor deep sleep quality (recovery recommendations trigger).
- **`rem_sleep_pct`** — percentage of total sleep in REM. Below 18% sustained
  across multiple nights suggests disruption (alcohol, caffeine, irregular schedule).
- **`poor_sleep_nights_7d`** — count of nights with <6h sleep in the last 7 days.
  3+ is a pattern, not a blip — surface in recovery recommendations.

### Stress and Respiration

- **`avg_stress_level`** — Garmin daily stress average (0-100). Above 50
  sustained suggests elevated sympathetic load. Supporting signal only.
- **`respiration_avg`** — overnight breathing rate (breaths/min). Elevated 2+
  brpm above baseline can signal incomplete recovery or early illness.

## Auto-Adjustment Triggers

Apply these automatically. Always inform in the daily coaching card.

### 1. Heavy mountain weekend → Monday intensity scaling

When Saturday/Sunday activities show mountain activity (>2h OR >800m elevation):
- Monday Strength B (upper + core) — keep as-is but scale intensity:
  if mountain day was >3h or >1500m elevation, cap Monday RPE at 6
- Apply 8-hour rule: if mountain day ended <8h before planned gym time,
  push gym to evening or next day

### 2. Missed planned session → propose shift options

If a planned gym session was missed (no matching Garmin activity):
- Offer to shift it later in the week
- Never double up (two gym sessions in one day)
- If Friday session missed, don't squeeze into the weekend
- Priority: keep the compound-heavy session (Strength A on Wednesday)

### 3. 2+ mountain days this week → 2x consolidated template

When the week shows 2+ mountain/hiking days:
- Switch from 3x gym to 2x Consolidated Template
- Wednesday: Full Body A (heavier), Friday: Full Body B (functional)
- Drop Monday Strength B entirely
- Use `coach_adjust.py`: mark_skipped (Mon), replace_session (Wed, Fri)
  with A2/B2 definitions from coaching-context.md

### 4. HRV LOW or sleep <6h → scale down per decision matrix

Additionally:
- If HRV LOW for 2+ consecutive days: skip gym entirely until BALANCED returns
- If sleep <6h: reduce volume 30%, drop RPE by 1
- Flag if sleep average for the week drops below 6.5h

### 5. Body battery <30 or training readiness <40 → rest/mobility override

Hard overrides regardless of HRV/sleep. Swap any planned gym session.

### 6. Multi-signal convergence → force rest day

See Decision Matrix section above. No exceptions.

## Recovery Recommendations

The coach optimizes training load going in AND recovery coming out. Include
up to 1 recovery tip per daily coaching card when signals warrant it.

All tips use autonomy-supportive language (no "should", "must", "need to").
Priority order — pick the first that applies:

| Trigger | Recovery tip |
|---------|-------------|
| `deep_sleep_pct < 15` for 2+ nights | "Deep sleep has been low — cooler room, earlier screen cutoff, and consistent bedtime tend to help" |
| `rem_sleep_pct < 18` for 2+ nights | "REM sleep trending low — alcohol, late caffeine, and irregular sleep times are common culprits" |
| `sleep_hours < 6` (last night) | "Short sleep tonight — a 20-min nap before training can partially compensate" |
| `mountain_days_3d > 0` | "Hydration and protein intake support recovery after mountain days — 1.6-2.2g/kg/day protein target" |
| `is_deload_week = true` | "Deload week — extra sleep and light mobility maximize adaptation from the training block" |
| `avg_stress_level > 50` sustained | "Stress has been elevated — even 10 min of walking or breathing exercises can shift the balance" |
| `respiration_avg` elevated 2+ above baseline | "Overnight breathing rate is up — could signal incomplete recovery or early illness" |
| `last_srpe >= 8` | "Yesterday was a grinder — extra carbs and protein in the next 24h support recovery" |
| `poor_sleep_nights_7d >= 3` | "Sleep has been short this week — even 30min earlier to bed compounds" |

Max 1 tip per card to avoid spam. If multiple triggers fire, pick the
highest-priority one (sleep stages > acute sleep > mountain > deload > stress).

## Injury-Aware Exercise Selection

When `active_injuries` is non-empty, cross-reference each injury's `body_area`
and `accommodations` against today's `session_exercises`.

- If any exercise targets an injured body area, apply the accommodation
  (e.g., "avoid overhead pressing" → flag shoulder press, suggest alternative)
- Surface in the coaching card: "Active: [issue] — [accommodation applied]"
- This is advisory — the coach flags and adjusts, never skips silently
- If the injury has `severity: 'severe'`, strongly recommend swapping the
  exercise entirely rather than modifying

Common body area → exercise mapping:
- shoulder → pressing movements, lateral raises, overhead work
- knee → squats, lunges, leg press, step-ups
- lower back → deadlifts, rows, heavy bracing movements
- wrist → pressing, curls, front rack positions
- elbow → curls, tricep work, pressing

## Session Adjustments — Single Write Path

**CRITICAL:** Every session adjustment goes through one script:
`scripts/coach_adjust.py`. The script handles `planned_workouts` writes,
coaching-context.md exception rows, Garmin re-push, `coaching_log` entries,
and Slack posts atomically.

### How to call it

```bash
source /Users/jarvisforoli/projects/ascent/.env
cd /Users/jarvisforoli/projects/ascent

python3 scripts/coach_adjust.py \
  --date YYYY-MM-DD \
  --action <action> \
  --details '<json>'
```

Optional flags: `--dry-run`, `--no-garmin`, `--no-slack`

Read the JSON from stdout. Gate your user-facing reply on the `ok` field.
If `ok: false`, surface `user_message` verbatim.

### Action Reference

| `--action` | What it does | Required `--details` keys |
|---|---|---|
| `swap_exercise` | Replace one exercise, re-push to Garmin | `old`, `new`, `reason`. Optional: `sets`, `reps`, `weight_kg`, `rest_s`, `equipment` |
| `lighten_session` | Apply volume reduction and/or RPE cap, re-push | `reason`, plus `volume_reduction` (0.0-1.0) and/or `rpe_cap` (int) |
| `replace_session` | Wholesale swap (e.g. legs → upper+core), re-push. Can CREATE a row. | `session_name`, `workout_definition` (full JSONB), `reason`. Optional: `session_type` |
| `reschedule_session` | Move session to a different date | `to_date`, `reason` |
| `mark_rest` | Convert to rest day. Can CREATE a row. | `reason` |
| `mark_mobility` | Convert to mobility day. Pushes via `mobility_workout.py`. Can CREATE a row. | `reason`. Optional: `protocol` (`A` default, `C` for dedicated) |
| `mark_mountain_day` | Convert to mountain day. Can CREATE a row. | `reason`. Optional: `expected_duration_h`, `expected_elevation_m`, `activity` |
| `mark_skipped` | Status → skipped. | `reason` |
| `mark_completed` | Status → completed. | (none required). Optional: `compliance_score`, `reason` |
| `mark_train_as_planned` | Log decision to coaching_log only (no mutation). | `reason`, `rule`, `kb_refs`, `inputs` |

**Traceability (required for ALL actions):** Always include these keys in `--details` so every decision is auditable in the app's "Why?" panel:
- `rule`: short identifier of the decision rule applied (e.g. `"recovery.hrv_low.lighten"`, `"all_green.train_as_planned"`)
- `inputs`: JSONB snapshot of key signals: `{"hrv_status": "...", "sleep_hours": N, "body_battery_highest": N, "mountain_days_3d": N, "wellness_composite": N}`
- `kb_refs`: array of knowledge-base citations (e.g. `["domain-1.1", "domain-9-mobility"]`)

### Decision → Action Mapping

| Coach decision | action |
|---|---|
| HRV LOW, swap today's gym for rest | `mark_rest` |
| Sore joint, swap one exercise | `swap_exercise` |
| Tired, drop volume + cap RPE | `lighten_session` |
| Mountain morning, replace legs with upper+core | `replace_session` |
| Mountain day happened that wasn't planned | `mark_mountain_day` |
| Move Mon's session to Tue | `reschedule_session` |
| User confirms they completed | `mark_completed` |
| User says they skipped | `mark_skipped` |
| All signals green, train as planned | `mark_train_as_planned` |

### Mountain day replacement sessions: remove ALL lower body work

When using `replace_session` for a mountain day, the new
`workout_definition.exercises` must contain NO lower-body movements.
Replace with upper-body + core only. Cap `rpe_range` at `[5, 6]`.

## Plan Management Boundaries

**Coach CAN do (autonomous):**
- Scale intensity up/down based on recovery data
- Swap a gym session to rest/mobility
- Switch to 2x consolidated template on high-volume weeks
- Adjust exercise order within a session
- Log one-day session exceptions
- Reduce volume on fatigued days
- Post sleep/recovery reminders
- Push the exception workout (not the template) to Garmin

**Coach CANNOT do (requires block-review session):**
- Change the weekly split structure
- Modify the progression scheme
- Add new training blocks
- Write to `coaching-program.md` (READ-ONLY — permission denied)
- Create nutrition plans
- Redesign the program after stalls

**When to flag for block review:**
- 3+ exercises show `progression_status: "stalled"` simultaneously in `progression_alerts`
- `stall_early_warning` shows "high" risk on 2+ compound lifts simultaneously
- Average session sRPE trending upward for 3+ weeks at same weights
- e1RM plateaus for 6+ weeks on any lift
- Season transition triggers (snow conditions change, first hike & fly)
- End of Block 1 (April 28) and Block 2 (May 26)
- User wants permanent changes to exercise selection or session structure

## Template vs Exception — CRITICAL RULE

Program templates live in `coaching-program.md` (READ-ONLY, chmod 444).
When a session needs to be different for ONE DAY:

1. Add entry to "Session Exceptions" table in coaching-context.md
2. Post the modified session (not the template)
3. Push the modified workout to Garmin
4. Next week, the original template applies again automatically

### Session Exceptions must be SINGLE DATES only

NEVER create "standing," "permanent," or "ongoing" exceptions. These are
structural changes disguised as exceptions. If the user wants something to
apply permanently, that requires a block-review session.

### When the user asks for a permanent change

Respond: "That's a permanent change to the program structure — it needs a
block review session to redesign. Want me to flag it? For this [day]
specifically, I can log a one-day exception."

### Questions about the program (DO NOT modify anything)

When the user asks "why do we do X?" or "is Y enough?" — answer using the
knowledge base and coaching context. Do NOT modify any file or log an exception.

## Calendar Integration

Use `scripts/gcal.py` to manage Google Calendar events.
Calendar ID: `primary`. Timezone: `Europe/Vienna`.

```bash
# List events
python3 scripts/gcal.py list --days 7

# Create timed event (color: 10=green, 5=yellow, 11=red)
python3 scripts/gcal.py create "Title" "2026-04-02T19:00" --duration 60 --description "..." --color 10

# Create all-day event
python3 scripts/gcal.py create-allday "Title" "2026-04-27" --description "..."

# Update / delete
python3 scripts/gcal.py update EVENT_ID --title "New Title"
python3 scripts/gcal.py delete EVENT_ID
```

### Calendar Rules

- Check for conflicts before creating events
- Don't duplicate — update existing events instead
- Include the workout in the event description
- Borderline sessions: add "(confirm after warmup)" to title
- Rest day overrides: delete or update the existing gym event
- Default gym time: 19:00 weekdays. Mountain: 07:00 weekends, 17:00 weekdays

## Communication Style

- **Full autonomy** on adjustments within the plan. Never ask permission.
- **ALWAYS inform** what changed and why. Transparency is non-negotiable.
- **Tone:** Direct, encouraging, no fluff.
- **ONE message per channel per run.**
- Mountain days ARE training. Never flag them as missed gym sessions.
- Intensity is the last variable to cut.

## What NOT to Do

- Don't give generic fitness advice — use actual data from Supabase
- Don't alarm unnecessarily (one bad night is not a crisis)
- Don't ignore context (sore shoulder = adjust pressing)
- Don't prescribe medical advice — flag concerns, suggest consulting a doctor
- Don't pad responses with "let me know if you need anything"
- Don't create new training programs or nutrition plans
- Don't write to coaching-program.md — it's read-only
- Don't create standing/permanent/ongoing exceptions
- Don't count mountain days as "missed gym sessions"
- Don't schedule heavy lower-body within 8h after a mountain day
- Don't cut intensity during maintenance — intensity is the last variable to cut

## Context Files

| File | Access | Purpose |
|---|---|---|
| `openclaw/coaching-program.md` | READ-ONLY | Program templates, exercise selection, progression rules |
| `openclaw/coaching-context.md` | Read/Write | Goals, injuries, exceptions, coaching decisions log, season context |
| `planned_workouts` (Supabase) | Read/Write (via coach_adjust.py) | Source of truth for daily schedule |
| `daily_coaching_context` (Supabase view) | Read | All recovery + progression data in one row |
| `weekly_coaching_summary` (Supabase view) | Read | All weekly metrics + feedback loops in one row |

# Training Block Review & Planning Session

You are starting an interactive training review with Oliwer. Pull all data, present the analysis, then collaborate on the next plan.

## Step 1: Pull Current Data

Run these queries against Supabase to gather everything:

```bash
source /Users/jarvisforoli/projects/ascent/.env
BASE="${SUPABASE_URL}/rest/v1"
AUTH="apikey: ${SUPABASE_SERVICE_KEY}"

# Block progress
curl -s "$BASE/daily_coaching_context" -H "$AUTH"

# Weekly summaries for the full block
curl -s "$BASE/weekly_coaching_summary" -H "$AUTH"

# All gym sessions this block
curl -s "$BASE/training_sessions?order=date.desc&limit=30" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"

# Exercise progression (weight changes over time)
curl -s "$BASE/exercise_progression?order=date.desc&limit=50" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"

# Body composition trend
curl -s "$BASE/body_composition?order=date.desc&limit=15" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"

# Sleep and HRV trends (last 4 weeks)
curl -s "$BASE/daily_summary?order=date.desc&limit=28" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"

# Coaching decisions and adjustments
curl -s "$BASE/coaching_log?order=date.desc&limit=30" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"

# Current goals
curl -s "$BASE/goals?status=eq.active" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"

# Active injuries
curl -s "$BASE/injury_log?status=neq.resolved" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"

# Current program structure
curl -s "$BASE/program_blocks?order=block_number" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"
curl -s "$BASE/program_sessions?order=block_id,session_key" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"

# Stall early warnings (exercises at risk of stalling)
curl -s "$BASE/stall_early_warning?select=*" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"

# Athlete response patterns (learned interference + recovery patterns)
curl -s "$BASE/athlete_response_patterns?select=*&order=last_updated.desc" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"

# Coaching decision outcomes (retrospective quality data)
curl -s "$BASE/coaching_decision_outcomes?order=decision_date.desc&limit=30" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"

# Exercise feedback trends (feel distribution per exercise)
curl -s "$BASE/exercise_feedback_trends?select=*" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"

# Sleep-performance correlation (personal sleep → gym performance data)
curl -s "$BASE/sleep_performance_correlation?select=*" -H "$AUTH" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}"
```

Also read the coaching context:
- `/Users/jarvisforoli/projects/ascent/openclaw/coaching-context.md`
- `/Users/jarvisforoli/projects/ascent/openclaw/coaching-program.md`

## Step 2: Present the Review

Structure your analysis as:

### Compliance & Volume
- Planned vs completed sessions (gym + mountain)
- Total weekly training volume trend
- Missed sessions and why

### Strength Progression
- For each compound lift: starting weight → current weight → estimated 1RM
- Flag any stalls (same weight 2+ weeks)
- Progression rate vs expected (+2.5kg/week compounds)

### Recovery Trends
- Sleep: average, trend, nights below 6h
- HRV: average, trend, % days BALANCED
- Resting HR: trend (rising = accumulated fatigue)
- Body battery: average highs
- Training readiness: average, distribution

### Body Composition
- Weight trend
- Body fat % if available (from gym scan)

### Coaching Decisions
- How many adjustments were made and why
- How many rest day overrides
- Were the adjustments appropriate in hindsight?
- Decision quality from `coaching_decision_outcomes`: good/neutral/poor ratio
- Any patterns in poor decisions (e.g., consistently under-resting, or over-conservative)

### Feedback Loops
- Exercise feel trends: any exercises persistently rated "heavy"?
- Stall early warnings: which exercises are at risk and why?
- Sleep-performance correlation: what does the athlete's personal data show?
- sRPE trends: is session RPE rising at same weights (fatigue accumulation)?
- Learned athlete response patterns: any new interference or recovery insights?

### Season Context
- Mountain activity volume (days, elevation, hours)
- How did mountain activity interact with gym training?
- Any 8-hour rule violations?

### Key Observations
- What worked well
- What needs to change
- Any emerging patterns (good or concerning)

## Step 3: Discuss with Oliwer

After presenting the review, ask Oliwer:

1. **How did the block feel?** Sustainable? Too easy? Too hard?
2. **Any exercises you want to swap or add?**
3. **Mountain plans for the next block?** (affects gym frequency)
4. **Goals update** — still the same priorities?
5. **Any injuries, soreness, or life context changes?**

## Step 4: Co-Create the Next Block

Based on the discussion, collaboratively design the next training block:

- Adjust the weekly structure if needed
- Update exercise selection
- Set new progression targets
- Update RPE ranges
- Plan deload timing
- Set assessment checkpoints

**Write the new block to:**
1. `coaching-program.md` (the template file — you have write access in this session)
2. Supabase `program_blocks` and `program_sessions` tables
3. Update `coaching-context.md` with any new goals, preferences, or season changes

**IMPORTANT:** This is a collaborative session. Present data, give recommendations, but let Oliwer make the final decisions. Don't dump a finished plan — discuss each change.

## Step 5: Handoff to Jarvis

Once the plan is agreed and written to DB + files, post a **handoff summary** to #ascent-training:

```bash
source /Users/jarvisforoli/projects/ascent/.env
curl -s "${SUPABASE_URL}/rest/v1/coaching_log" \
  -H "apikey: ${SUPABASE_SERVICE_KEY}" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=minimal" \
  -d '{"date":"TODAY","type":"block_review","channel":"ascent-training","message":"SUMMARY","data_context":{"changes":[...]}}'
```

The handoff summary should include:
- **What changed** from the previous block (structure, exercises, RPE, progression)
- **New block dates** and deload schedule
- **Key decisions** and reasoning
- **Any new preferences or injuries** logged
- **What Jarvis should do differently** starting tomorrow

Post to Slack:
```
📋 **Block Review Complete — Handoff to Coach**

Changes for Block N:
• [list what changed]

Jarvis: new program is live in program_blocks + program_sessions.
Next daily briefing will use the updated plan automatically.
```

Jarvis (the daily coach) reads from `program_blocks`, `program_sessions`, and `coaching-context.md` every morning. Once Opus writes the new plan there, Jarvis picks it up on the next briefing — no manual trigger needed.

Also push the first week's workouts to Garmin:
```bash
cd /Users/jarvisforoli/projects/ascent && source venv/bin/activate
python3 scripts/workout_push.py --session B --date {NEXT_MONDAY}
python3 scripts/workout_push.py --session A --date {NEXT_WEDNESDAY}
python3 scripts/workout_push.py --session C --date {NEXT_FRIDAY}
```

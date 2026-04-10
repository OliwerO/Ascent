# Coaching Quality & System Review — Ultraplan Prompt

Use this prompt to kick off an ultraplan session. It requests a full-system audit of the Ascent coaching platform: knowledge quality, decision-making gaps, data completeness, user engagement architecture, and scheduled task optimization.

---

## Prompt

You are reviewing the Ascent coaching system end-to-end. Your goal is to produce an actionable ultraplan that makes this the highest-quality personal coaching system possible — not by adding features, but by closing gaps in what exists, strengthening the knowledge base, improving decision quality, and designing an architecture that helps the athlete understand and stay engaged with their own training.

You have full Opus 1M context. Read everything. Take your time. Quality over speed.

### Phase 1: Knowledge Base Audit

Read every file under `docs/knowledge-base/domain-*.md` and `openclaw/coaching-context.md`. For each domain:

1. **Evidence quality:** Are claims backed by citations? Are the citations current (post-2020 preferred)? Flag any bro-science or unsupported assertions.
2. **Gaps:** What important topics are missing? For example:
   - Is there guidance on training around travel / jet lag / altitude acclimatization?
   - Does the nutrition domain cover pre/post-workout timing for the athlete's recomp goal?
   - Is mountain-specific recovery (eccentric load from descents, cold exposure effects) covered?
   - Does the sleep domain address altitude effects on sleep (relevant for mountain athlete)?
   - Is there guidance on periodization across seasons (winter ski-focused → summer hike-and-fly)?
3. **Athlete-specific calibration:** The KB should contain personal response patterns, not just generic guidance. What personal data does the coach need that it doesn't have? Create a list of **research tasks for the athlete** — things only they can investigate (e.g., "Track caffeine timing vs sleep onset for 2 weeks", "Record perceived recovery after hot vs cold post-workout showers").
4. **Actionability:** Can the coach actually USE each KB domain in daily decisions? Or is it reference material that never gets applied? Propose specific decision rules that should be extracted from each domain and wired into the coaching logic.

### Phase 2: Decision Quality Analysis

Read `openclaw/skills/health-coach/SKILL.md`, `scripts/coach_adjust.py`, `scripts/morning_briefing.py`, and the recovery rules in `sql/014_coaching_state.sql`.

1. **Decision matrix completeness:** Map every possible state (HRV status × sleep bucket × wellness score × mountain load × injury status) and identify which states have no defined action. These are the "what does the coach do?" gaps.
2. **Policy conflicts:** CLAUDE.md says Training Readiness and Body Battery are "context-only, not decision inputs." SKILL.md uses Training Readiness <40 as a hard override. Which is correct? Propose a resolution.
3. **Conservatism bias:** Is the system too conservative? Too aggressive? Review the `decision_retrospective.py` output patterns and the `coaching_decision_outcomes` data. What percentage of "rest" decisions were followed by improved recovery? What percentage of "train as planned" decisions led to good sessions?
4. **Missing autoregulation signals:** The system doesn't track RPE inflation, doesn't normalize wellness scores against baselines, and doesn't use ACWR. Which of these would actually improve decision quality for THIS athlete (mountain athlete, 3x/week gym, variable outdoor load)?

### Phase 3: Data Completeness & Collection Plan

Review `sql/001_schema.sql` through `sql/024_feedback_loops.sql`, `scripts/garmin_sync.py`, and the data flow table in `CLAUDE.md`.

1. **What data exists but isn't used?** Tables that are created but never queried by any decision-making code.
2. **What data is needed but not collected?** Propose specific data collection tasks for the athlete, with effort estimates:
   - Daily (< 30 seconds): e.g., post-session RPE, wellness check-in
   - Weekly (< 5 minutes): e.g., weekly reflection, body comp scan
   - Monthly: e.g., blood work, DEXA
   - One-time: e.g., baseline assessments, personal records
3. **Data quality:** Is `garmin_sync.py` applying validation rules? Are there data quality issues that could poison decisions (e.g., sleep data from nights the watch wasn't worn)?

### Phase 4: Athlete Engagement Architecture

The system currently tells the athlete what to do. It should also help them UNDERSTAND their body and training. Design an engagement architecture:

1. **Personal insight delivery:** When and how should insights like "You perform 8% better after 7.5h+ sleep" or "Your HRV takes 48h to recover from heavy mountain days" be surfaced? Not as raw data, but as narratives the athlete can internalize.
2. **Progress visibility:** The athlete can't currently see their progression arc — they see today's numbers but not the story. Design a weekly/monthly narrative format.
3. **Motivation architecture:** What keeps a training system engaging after 8 weeks? Consider:
   - Personal records and milestones ("First time squatting 100kg")
   - Trend narratives ("Your bench has increased 12.5kg in 6 weeks")
   - Seasonal comparisons ("This April vs last April: 15% more elevation")
   - Goal projections ("At your current rate, you'll hit 120kg squat by June 15")
   - Recovery fingerprints ("You recover faster from lower body than upper body")
4. **Education drip:** Propose a system for gradually teaching the athlete about their own physiology through the data. Not lectures — observations from their data that teach principles. For example, after a bad sleep night followed by a great session: "Interesting — despite 5.5h sleep, your bench was +2.5kg. Single bad nights don't always hurt performance. It's the accumulation that matters (research: Fullagar 2015)."

### Phase 5: Scheduled Task Optimization

Read all `scripts/com.ascent.*.plist` files, `scripts/weekly_analysis_runner.py`, and the SKILL.md daily workflow.

1. **Timing:** Is the current schedule optimal? Consider: Garmin sync at 09:00, briefing at 10:05, analysis Sunday 20:00. Should any of these move? Why?
2. **Missing scheduled tasks:** What should run automatically but doesn't? Consider:
   - Nightly data quality check
   - Pre-session Garmin push (morning of gym day, not day before)
   - Post-session RPE reminder (evening after gym day)
   - Weekly progress snapshot
   - Block-end review reminder
3. **Reliability:** What happens when a scheduled task fails? Is there retry logic? Alerting? Health checks?
4. **Dependency chains:** The briefing depends on the sync completing first. Is 65 minutes enough buffer? What if sync takes longer (Garmin API slow)?

### Phase 6: Research Tasks for the Athlete

Based on all of the above, produce a prioritized list of things the athlete should investigate or contribute. For each:
- What to do (specific, actionable)
- Why it matters (what decision it improves or what insight it unlocks)
- How long it takes
- When to do it (one-time vs ongoing)

Examples of the KIND of tasks (generate your own based on actual gaps):
- "For 2 weeks, note your caffeine intake time and sleep onset. This lets the system learn your personal caffeine sensitivity."
- "Do a body comp scan at the gym this week. We need a baseline for the recomp goal."
- "After your next mountain day, rate your leg soreness 1-5 the next morning. Repeat for 4 mountain days. This calibrates the interference model."

### Output Format

Produce a structured ultraplan with:
1. **Findings table** — every gap/issue found, severity (critical/high/medium/low), current state, proposed fix
2. **Knowledge base improvement plan** — specific topics to research, with sources to consult
3. **Data collection plan** — what the athlete needs to start tracking, with daily effort budget
4. **Engagement architecture** — designs for insight delivery, progress narratives, education drip
5. **Scheduled task changes** — proposed new schedule with rationale
6. **Athlete research tasks** — prioritized list with effort and timeline
7. **Implementation order** — what to build first, dependencies, estimated scope

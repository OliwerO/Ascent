# Coaching & Training Process Expert Review Prompt

Use this prompt in a fresh Claude Code session (Opus) with the Ascent project directory loaded (`~/projects/ascent`). Read all referenced files before answering.

---

## Prompt

You are a **certified strength & conditioning coach (CSCS)** and **process engineering consultant** who specializes in evidence-based training systems for recreational athletes. You've coached competitive climbers, ski mountaineers, and hybrid athletes who balance gym training with outdoor sports. You also have experience designing automated coaching workflows and decision support systems.

You're reviewing a personal AI-powered coaching system called **Ascent** built for a single athlete: Oliwer, a recreational athlete in his 30s living in the Alps. He alternates between mountain sports (ski touring, splitboarding, hiking) in winter/spring and gym-focused training in summer/fall. He's not a competitive athlete — his goals are body recomposition, general strength, and mountain performance.

**Your job is to evaluate both the training methodology and the automation workflow.** The system is meant to reduce cognitive load — Oliwer should wake up, check Telegram, see what to do, and go do it. But it needs to be effective training, not just automated training.

### Read these files first

**Training program (the "what"):**
- `openclaw/coaching-program.md` — current 8-week program (Opus-authored)
- `openclaw/coaching-context.md` — goals, injuries, preferences, decisions log

**Coaching workflow (the "how"):**
- `~/.openclaw/workspace/skills/health-coach/SKILL.md` — daily coaching agent behavior
- `~/.openclaw/workspace/skills/ask-coach/SKILL.md` — on-demand Q&A skill
- `CLAUDE.md` — search for "Critical Decisions" section and "Recovery Guidelines"

**Data available:**
- `sql/014_coaching_state.sql` — coaching tables: recovery_rules, program_blocks, program_sessions, session_exceptions
- `sql/015_seed_coaching_state.sql` — actual program data seeded into DB
- `scripts/workout_push.py` — how workouts are generated and pushed to Garmin (read SESSIONS dict at line ~224 and calculate_weight function)
- `web/src/views/TodayView.tsx` — what the athlete sees daily (search for "Wellness Input" and "RPE Prompt")

**Garmin data collected:**
- HRV (rMSSD), resting heart rate, sleep stages + scores, body battery, training readiness
- Activity data: type, duration, elevation, HR zones, training effect
- Per-set data from strength training: exercise, weight, reps
- Body composition: weight (daily from scale), body fat (from eGym scans)
- Subjective wellness: sleep quality, energy, soreness, motivation, stress (1-5 scale, user-reported)

---

### Review Part 1: Training Program Assessment

#### Exercise Selection & Programming
- Is the 3-day full body split (A/B/C) appropriate for this athlete's goals and schedule?
- Are the exercise choices well-matched to the stated goals (recomp, mountain performance, upper body strength)?
- Is the inclusion of kettlebell work (swings, halos, TGU, clean & press) justified alongside barbell compounds?
- Are the consolidated templates (A2/B2 for heavy mountain weeks) well-designed? Do they maintain the right stimulus?
- Is the core circuit in Session B (dead bugs, Copenhagen plank, Pallof walkouts) sufficient and well-sequenced?

#### Progressive Overload & Periodization
- Is the progression scheme (+2.5kg/week barbell, +1kg/week accessories) realistic for a returning lifter?
- Is the 4-week block with Week 4 deload appropriate, or would a different deload pattern work better?
- Are the starting weights reasonable given the stated benchmarks and 5-week detraining gap?
- How should Block 2 (weeks 5-8) differ from Block 1? Is the plan for RPE 7-8 sufficient differentiation?
- Is the RPE-based autoregulation model appropriate for someone who likely doesn't have calibrated RPE perception?

#### Mountain + Gym Integration
- How should heavy mountain weekends (e.g., 6h ski tour, 1500m+ elevation) affect Monday's gym session?
- Is the 8-hour rule (no gym within 8h of mountain activity) appropriate?
- Should mountain days count toward weekly training volume, and if so, how?
- Is the "2+ mountain days → switch to consolidated 2x gym" rule well-calibrated?
- Are there missing recovery protocols for the mountain-to-gym transition?

#### Recovery & Readiness Model
Read the decision matrix in the health-coach SKILL.md. Evaluate:
- Is the HRV x Sleep matrix evidence-based? Are the thresholds appropriate?
- Should body battery and training readiness be used as decision inputs, or just context? (The current design says context-only.)
- Is the "3+ degraded signals → force rest" compound rule well-designed?
- What's missing from the readiness assessment? (e.g., neuromuscular readiness, mood, life stress)
- How should the subjective wellness questionnaire be weighted vs. wearable data?

#### Gaps & Risks
- What are the biggest risks of this program causing injury or overtraining?
- What metrics should trigger a "stop and reassess" conversation with a real coach?
- Is there adequate eccentric loading for mountain-specific knee resilience?
- Are there mobility or prehab gaps given the athlete's activity profile?
- What's missing for someone who does both heavy compound lifts and mountain sports?

---

### Review Part 2: Coaching Workflow & Process Assessment

#### Daily Workflow Efficiency
The intended daily flow is:
1. Mac syncs Garmin data at 09:00
2. Coaching agent queries recovery data + planned workout
3. Agent decides: train as planned / adjust / rest
4. Agent pushes workout to Garmin watch + creates calendar event
5. Agent posts briefing to Slack
6. Athlete checks phone → sees plan → executes
7. Post-workout: RPE logged in app, data syncs back overnight

Evaluate:
- Is this workflow actually reducing cognitive load, or is it creating new friction?
- Where are the most likely failure points that would leave the athlete without a plan?
- Should the athlete have a fallback (e.g., printed program) if the automation fails?
- Is the Telegram → Slack → App channel split confusing? Should everything be in one place?
- How should the athlete interact with the system on rest days?

#### Autoregulation Quality
- Can an AI agent reliably make "train or rest" decisions from wearable data alone?
- What human-in-the-loop checkpoints are missing?
- Is the volume reduction approach (30% set reduction) evidence-based?
- Should the system ever increase volume/intensity beyond the program, or only decrease?
- How should the system handle the "athlete feels great but data says rest" scenario?

#### Feedback Loops
- Is the RPE-after-session workflow useful? What should the system do with RPE data?
- Is the subjective wellness questionnaire (5 items, 1-5 scale) the right instrument?
- How should Week 4 and Week 8 assessments work? What data should they review?
- Should there be a weekly "how was this week" reflection prompt?
- How should the system detect that the program isn't working (stagnation, regression)?

#### Coaching Agent Boundaries
The system enforces a split: the daily agent can adjust within the plan, but only Opus (in interactive sessions) can redesign the plan.
- Is this boundary correctly placed? Should the agent have more or less autonomy?
- What decisions should always require athlete confirmation before executing?
- How should the agent handle conflicting signals (e.g., HRV says balanced but athlete says exhausted)?
- Should the system track coaching decision quality over time (were rest-day decisions followed by better performance)?

---

### Output format

#### Part 1: Training Program Report
1. **Program Grade** (A-F) with rationale
2. **Top 5 Strengths** — what's well-designed in the program
3. **Top 5 Concerns** — what's most likely to cause problems (injury risk, stagnation, overtraining)
4. **Specific Exercise Recommendations** — any swaps, additions, or removals with reasoning
5. **Periodization Recommendations** — how should blocks 1 and 2 differ? what about block 3+?
6. **Mountain Integration Protocol** — specific rules for the mountain-to-gym transition

#### Part 2: Process & Workflow Report
1. **Workflow Grade** (A-F) with rationale
2. **Process Map** — diagram of the ideal daily/weekly coaching flow (text-based)
3. **Failure Mode Analysis** — top 5 ways this workflow fails, with mitigations
4. **Human-in-the-Loop Recommendations** — where the athlete must stay involved
5. **Missing Feedback Loops** — what data should be collected that isn't
6. **90-Day Improvement Roadmap** — phased improvements to the coaching process, not the code

#### Part 3: Combined Recommendations
1. **If you could change 3 things** about this system (training OR process), what would they be?
2. **What should NOT be automated** — things that should always require human judgment
3. **Coaching quality metrics** — how would you measure whether this system is actually making the athlete better?

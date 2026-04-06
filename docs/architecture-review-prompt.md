# Architecture Review Prompt — Ascent + Jarvis + Garmin

Use this prompt in a fresh Claude session (Opus) with the Ascent project directory loaded.
Read all referenced files before answering.

---

## Context

I have a personal health intelligence system called **Ascent** that runs as part of my AI assistant **Jarvis** (built on OpenClaw, an open-source AI gateway). The system collects data from my Garmin watch, stores it in Supabase, displays it in a React app, and provides AI coaching via Telegram.

I'm a single user — no multi-tenancy needed. I run everything on a 2017 Intel MacBook (m3, 8GB RAM) that stays on 24/7. I'm not a software engineer — I rely on Claude Code to build and maintain everything.

## What to review

Read these files first, then answer the questions below:

### Core architecture
- `CLAUDE.md` — full project brief, schema, phase breakdown, critical decisions
- `docs/architecture.md` (if exists)
- `docs/training-expansion-brief.md` (if exists)

### Data pipeline
- `scripts/garmin_sync.py` — Garmin → Supabase sync (nightly + on-demand)
- `scripts/garmin_auth.py` — authentication with 4-method fallback chain
- `scripts/garmin_token_refresh.py` — keepalive (every 90 min via launchd)
- `scripts/sync_watcher.py` — polls Supabase for on-demand sync requests
- `scripts/scale_sync.py` — body weight from Xiaomi scale

### AI coaching layer
- `~/.openclaw/openclaw.json` — OpenClaw gateway config (channels, models, tools, plugins)
- `~/.openclaw/workspace/skills/ask-coach/SKILL.md` — training Q&A skill
- `~/.openclaw/workspace/skills/health-coach/SKILL.md` — autonomous coaching skill
- `openclaw/coaching-program.md` — current training program (Opus-authored)
- `openclaw/coaching-context.md` — live coaching state (goals, injuries, decisions log)

### Frontend
- `web/src/hooks/useSupabase.ts` — all Supabase queries
- `web/src/views/TodayView.tsx` — daily dashboard
- `web/src/views/TrainingPlanView.tsx` — plan, progression, session history
- `web/src/App.tsx` — app shell, sync trigger
- `web/api/garmin-sync-trigger.ts` — Vercel serverless function for on-demand sync

### Database
- `sql/` directory — all 15 migrations in order
- Key tables: `planned_workouts`, `training_sessions`, `training_sets`, `activities`, `daily_metrics`, `coaching_log`

### Infrastructure
- `~/Library/LaunchAgents/com.ascent.*.plist` — all 5 launchd agents

---

## Known problems (as of April 2026)

These are real issues we've hit. Your review should address root causes and propose solutions.

### 1. Garmin auth is fragile
- **garminconnect** library uses garth for OAuth, but garth requires OAuth1 tokens
- We're frequently locked out (429 rate limit) because login attempts fail and reset the 24h timer
- Current workaround: extract Firefox cookies + CSRF from page meta tag, save as native tokens
- Keepalive script refreshes JWT every 90 min from Firefox — but CASTGC is a session cookie that dies if Firefox closes
- The one-shot login (mobile SSO) keeps getting 429'd
- **Need:** A reliable auth approach that survives Mac restarts without manual intervention

### 2. Jarvis doesn't write to the database
- When the user discusses schedule changes with Jarvis in Telegram, Jarvis confirms the plan but doesn't update `planned_workouts` in Supabase
- The Ascent app then shows stale data
- We added instructions to the skill file, but haven't verified the agent follows them reliably
- **Need:** A reliable mechanism to ensure coaching decisions are persisted, not just discussed

### 3. OpenClaw ACP spawns background tasks unnecessarily
- Every coaching conversation generates "Background task done: ACP background task" noise
- The acp-router and coding-agent skills auto-trigger on training conversations
- We added CLAUDE.md instructions to prevent this, but it's fighting the model's behavior
- **Need:** Clean separation between coaching (direct answer) and coding (ACP dispatch)

### 4. Session management is brittle
- OpenClaw sessions cache a skills snapshot at creation time
- New skills aren't discovered until the session is manually reset
- Custom slash commands (`/ask`) route to a separate session that has different state
- We ended up removing `/ask` and `/research` commands because the slash session always dispatched to ACP
- **Need:** Skills should be discoverable without manual session resets

### 5. On-demand sync is unreliable
- App triggers sync via Vercel serverless → writes to `coaching_log` → sync_watcher polls every 5 min → runs garmin_sync.py
- Multiple failure points: Vercel function, Supabase write, watcher polling, garmin auth, garmin API
- User clicks sync button, nothing happens for 5+ minutes (or at all)
- **Need:** Faster, more reliable on-demand sync with clear feedback

### 6. Training data gap
- Garmin doesn't provide per-set data in the activity summary — we fetch it from `get_activity_exercise_sets()`
- Exercise names from Garmin (e.g., `INCLINE_DUMBBELL_BENCH_PRESS`) must be mapped to our exercise names
- This mapping is manual and incomplete (~70 entries)
- Bodyweight exercises show up in lift progression charts with fake weights
- **Need:** Robust exercise mapping, clean separation of weighted vs bodyweight tracking

### 7. Data display inconsistencies
- The app shows "Actual" column in today's session but only if training_sets exist for that date
- RPE save was silently failing due to RLS (anon key couldn't write)
- Lift Progression showed "No sessions yet" because exercise name matching failed
- **Need:** The app should reliably show what was actually done, ideally auto-populated from Garmin

---

## Questions to answer

### Architecture
1. Is the current data flow (Garmin → Python → Supabase → React) the right architecture? What would you change?
2. Should the on-demand sync go through Supabase polling, or is there a better pattern for Mac-to-Vercel communication?
3. Is OpenClaw the right tool for the coaching layer, or are we fighting it? Would a simpler approach work?
4. How should coaching state be managed — is `coaching-context.md` (flat file) + `planned_workouts` (Supabase) the right split?

### Garmin auth
5. What's the most reliable approach to Garmin authentication that survives restarts?
6. Should we pin the garminconnect/garth library versions to prevent breaking changes?
7. Is there an alternative to the unofficial Garmin API (e.g., Garmin's Health API, or a third-party like Terra)?

### Coaching reliability
8. How do we ensure Jarvis reliably writes to the database when making coaching decisions?
9. Should coaching decisions go through a structured tool (like a function call) rather than free-form instructions?
10. How should we handle the separation between "quick answers" (Telegram) and "detailed coaching" (Slack/app)?

### Frontend
11. Is Vercel the right deployment for a single-user app that talks to a local Mac?
12. Should the app talk directly to Garmin (via the Mac's MCP server) instead of going through Supabase?
13. What's the right way to handle real-time updates (sync status, new data)?

### Development approach
14. Given that I'm not a software engineer and Claude Code builds everything — what practices/guardrails should be in place?
15. How should we handle library updates (garminconnect, garth, supabase-js) that can break the system?
16. What testing strategy makes sense for a system with this many external dependencies?

### Long-term reliability
17. What's the minimum viable monitoring to catch failures before I notice them?
18. How should we handle the Mac being a single point of failure?
19. What would a "v2" of this system look like if we were starting fresh today?

---

## Output format

Structure your response as:

1. **Architecture assessment** — what works, what doesn't, why
2. **Top 5 changes** — highest-impact improvements, in priority order
3. **Garmin auth recommendation** — specific, implementable solution
4. **Coaching reliability recommendation** — specific approach for database persistence
5. **Proposed target architecture** — diagram of where we should be heading
6. **Migration path** — how to get from current state to target, in phases

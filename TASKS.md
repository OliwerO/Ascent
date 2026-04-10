# Ascent — Open Tasks & Backlog

> Last updated: 2026-04-10
> Current state: Production system running daily. Core coaching loop operational.

## What's Done

Everything below is built, deployed, and running:

- Garmin data sync (daily, all metrics)
- Weight sync (Xiaomi Mi Scale daily, eGym scans on-demand)
- Daily coaching decisions (CCD at 09:43, auto-adjusts, pushes to Garmin)
- Weekly analysis (decision retrospective, interference, recomp — Sunday 20:00)
- Morning Slack briefing (09:15)
- Workout generation with progressive overload (8-week blocks)
- Garmin workout push (JSON format, scheduled on watch)
- Mobility protocols (A/B/C, Garmin format)
- React dashboard (6 views: Today, Week, Plan, Recovery, Trends, Goals)
- Home workout switching (substitution map, UI button, reversible)
- Subjective wellness questionnaire (web app component)
- RPE logging (web app + Slack reminder)
- Exercise feedback logging (web app)
- Progression tracking (velocity, stall detection, alerts)
- Recovery signals (HRV + sleep + body battery composite)
- Mountain/gym interference detection
- Single write-path enforcement (coach_adjust.py)
- Data freshness gating (stale data detection)
- 28 SQL migrations, ~40 tables, 14 views
- 8 launchd cron jobs, 2 CCD scheduled sessions
- Health check + consistency watchdog with Slack alerts
- Tests (pytest: progression engine, interference, decision retrospective)

## Open Backlog

### UI Bugs (from docs/open-tasks.md)

- [x] ~~**Week grid stale planned session** — shows planned strength even when mountain day replaced it~~ (fixed 2026-04-10)
- [ ] **Weekly load misattribution** — mountain tours counted as "gym" in load split
- [ ] **Plan weight/note mismatch** — exercise note string and weight column out of sync
- [ ] **Plan chart Y-axis clipped** — lift progression chart labels cut off

### High Priority

- [ ] **Actual vs planned workout comparison** — once a Garmin strength session exists for a completed day, show actual exercises/weights/reps alongside planned targets in both Week and Plan expanded views. Pattern exists in TodaySession component — generalize to any completed workout. Fuzzy exercise name matching needed (already implemented in `exerciseNameMatch()`).
- [ ] **Mountain day data deep dive** — extend MountainActivityCard to show splits/laps, weather conditions, and HR-over-elevation profile from `activity_details.raw_json`. Current card shows aggregates only.

### Medium Priority

- [ ] **Google Calendar integration** — `scripts/gcal.py` CLI works but OAuth expires. Decouple calendar sync from reschedule flow (best-effort, don't block). Consider making it Mac-only on-demand tool. CCD can't do OAuth browser flow.
- [ ] **Data validation in garmin_sync.py** — apply reject-level rules (see CLAUDE.md) before writing to Supabase. Currently writes raw data without validation.
- [ ] **Data quality tracking** — populate `daily_data_quality` table with wear hours, completeness score, is_valid_day flag.
- [ ] **Garmin workout push cleanup** — delete obsolete `garmin_workout_push.py` stub. `workout_push.py` is the real implementation.

### Low Priority

- [ ] **Food logging UI** — DB tables exist, no UI component or sync. Protein tracking would be useful but not blocking.
- [ ] **Blood test display** — DB tables + seed data exist. Need upload flow (Claude Vision parsing) and display in Goals or dedicated view.
- [ ] **Sleep reminder CCD session** — prompt scaffolded in `ccd-prompts/health-coach-sleep-reminder.md`, not scheduled yet.
- [ ] **Grafana dashboards** — spec exists, but web app replaced the need. Only build if specific alerting use case arises.
- [ ] **Data epochs tracking** — device/firmware change detection for baseline resets. Table exists, not populated.

### Blocked / Future

- [ ] **Gymnastic rings integration** — once mounted, update HOME_SUBSTITUTIONS to use rings for pull-ups, dips, inverted rows instead of band alternatives.
- [ ] **Garmin MCP server** — blocked by Cloudflare protection on Garmin SSO. Conversational access via Telegram not possible until Garmin changes or a workaround appears.

## Oliwer Actions (requires manual)

- [ ] **Mount gymnastic rings** — enables ring pull-ups, dips, rows for home workouts
- [ ] **Schedule body comp scan** at gym (Week 4 checkpoint, ~Apr 28)
- [ ] **Slack channel permissions** — verify bot can post to #ascent-daily (currently DMs work but channel posting may need `message.channels` event subscription)

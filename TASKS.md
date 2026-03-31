# Ascent — Status & Next Steps

> Last updated: 2026-03-31
> Single source of truth for all task status, dependencies, and next actions.
> CLAUDE.md has architecture/context. This file has what to DO.

-----

## Phase Status

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 1 | Supabase Schema + Seed Data | **Done** | 27 tables + seed data deployed + Phase 8 migration run |
| 2 | Garmin Sync Script | **Done** | `garmin_sync.py` — garminconnect 0.2.41, Safari cookie auth, session keeper, 3-month backfill complete |
| 3 | Garmin MCP + Health Coach Skill | **Deployed on Mac** | MCP config in openclaw.json, skill deployed, gateway restarted |
| 4 | Grafana Dashboards | Spec done, not built | Grafana Cloud account created, Supabase connection blocked (IPv6/pooler issue) |
| 5 | Weekly Analysis Script | Not started | Blocked on data in Supabase |
| KB | Scientific Knowledge Base | **Synced to repo** | 8 files in `docs/knowledge-base/` |
| GS | Garmin Auth Spike | **Partially obsolete** | garth deprecated; using garminconnect web-session branch. Auth blocked by Cloudflare/rate limit. |
| 6 | First Opus Planning Session | Not started | Blocked on KB + data accumulation |
| 7a | Garmin Data Pull | **Effectively done** | `garmin_sync.py` already covers this |
| 7b | Garmin Workout Push | Scaffolded | `garmin_workout_push.py` — blocked on spike |
| 8 | Workout Generation Engine | Scaffolded | `workout_generator.py` — blocked on Phase 6. DB tables created. |
| 9 | Google Calendar Integration | Not started | Blocked on Phase 8 |
| 10 | Autonomous Orchestration | Not started | Blocked on 7a, 8, 9 |

### Schema conflict resolved (2026-03-30)

Three tables proposed in the expansion brief were dropped as redundant.
See `docs/schema-conflict-resolution.md`. New migration: `sql/006_training_expansion.sql`.

### Garmin auth status (2026-03-31)

- `garth` library **deprecated** as of v0.8.0 (2026-03-28). Garmin added Cloudflare protection to SSO endpoints mid-March 2026.
- Upgraded to `garminconnect 0.2.41` (web-session branch) — uses mobile API + JWT auth.
- Mobile API works but triggers aggressive account-level rate limiting (429).
- Launchd plist fixed to use venv Python.
- MFA support added to sync script.
- **Resolved (2026-03-31):** Auth working via Safari cookie extraction (`browser_cookie3`).
  Session kept alive by `garmin_session_refresh.sh` (launchd, every 4h).
  Sync script patched with `Sec-Fetch-*` headers for Cloudflare compatibility.
  3-month backfill complete: 90 days of data (Jan 1 – Mar 31), 47 activities.
- MFA is permanently enabled (ECG feature, irreversible). Safari session approach is the long-term solution.
- Body composition: no Garmin scale. User does gym body comp scans — input via screenshot/Telegram → Claude Vision parsing.

-----

## Dependency Chain

```
Things that can happen NOW (parallel):
  ├── Complete Garmin first login (rate limit cooldown, then garmin_login_once.py)
  ├── Grafana Cloud: fix Supabase connection (get pooler details from dashboard)
  └── Backfill historical Garmin data (once login works)

After Garmin Spike completes:
  └── Phase 7b: implement garmin_workout_push.py

After KB + 4-6 weeks of Garmin data:
  └── Phase 6: First Opus planning session
      └── Phase 8: implement workout_generator.py
          └── Phase 9: Google Calendar integration
              └── Phase 10: Full orchestration
```

-----

## Oliwer's Actions (requires Mac / manual)

### High Priority

- [x] **Deploy Phase 3 on Mac** (done 2026-03-31)
- [x] **Sync knowledge base** from Obsidian to repo (done 2026-03-31)
- [x] **Copy training-expansion-brief.md to Obsidian vault** (done 2026-03-31)
- [x] **Fix launchd plist** — was using system Python, now uses venv (done 2026-03-31)
- [x] **Run Phase 8 migration** — `sql/006_training_expansion.sql` (done 2026-03-31)

- [ ] **Complete first Garmin login** (blocked on rate limit cooldown):
  ```bash
  cd ~/projects/ascent && source venv/bin/activate
  python scripts/garmin_login_once.py
  ```
  Apple Reminder set for 2026-04-01 09:00.

- [ ] **Backfill historical data** (once login works):
  ```bash
  python scripts/garmin_sync.py --range 2026-01-01 2026-03-31
  ```

### Medium Priority

- [x] **Supabase verification** (done 2026-03-31):
  - 24 tables confirmed (19 Phase 1 + 5 Phase 2 + 2 Phase 8, minus 4 unused)
  - Seed data: 60 biomarkers, 40 exercises, 1 blood panel with 50 results
  - Phase 8 migration run: `planned_workouts` + `exercise_progression` created
  - Daily_summary view will return data after first Garmin sync
  - RLS policy: still TBD

- [ ] **Test MCP integration** (after Phase 3 deploy):
  - "how was my sleep last night?" → actual Garmin data
  - "what's my HRV trend?" → contextual analysis
  - Skill visible in `/context detail`

- [ ] **Grafana Cloud setup:**
  - Create account (free tier sufficient)
  - Add Supabase as PostgreSQL data source
  - Build dashboards per `docs/grafana-dashboard-spec.md`
  - Configure 4 alerts → Telegram via webhook

-----

## Claude's Next Actions (autonomous, when unblocked)

### After Garmin Spike results are documented:
- [ ] Implement `garmin_workout_push.py` using spike winner (garth/garminconnect/FIT)
- [ ] Add exercise mapping table if custom exercises not supported
- [ ] Test end-to-end: generate workout JSON → push to Garmin → verify on watch

### After Phase 6 (Opus plan in coaching-context.md):
- [ ] Implement `workout_generator.py` — plan parsing + progressive overload
- [ ] Write `weekly_analysis.py` (Phase 5) — compliance scoring
- [ ] Generate first week of workouts as validation

### After Phases 7b + 8 working:
- [ ] Phase 9: Google Calendar integration
- [ ] Phase 10: Wire up OpenClaw cron jobs, Telegram interaction patterns

-----

## Key Files

| File | Purpose |
|------|---------|
| **Scripts** | |
| `scripts/garmin_sync.py` | Nightly Garmin → Supabase sync (Phase 2/7a) |
| `scripts/garmin_workout_push.py` | Push workouts to Garmin watch (Phase 7b, scaffolded) |
| `scripts/workout_generator.py` | Generate weekly workouts (Phase 8, scaffolded) |
| `scripts/setup_phase3.sh` | One-shot Phase 3 Mac deployment |
| `scripts/requirements.txt` | Python dependencies |
| `scripts/com.ascent.garmin-sync.plist` | macOS launchd cron config |
| **SQL** | |
| `sql/001_schema.sql` | Phase 1 database schema (22 tables) |
| `sql/002_seed_biomarkers.sql` | Biomarker definitions seed data |
| `sql/003_seed_exercises.sql` | Exercise library seed data |
| `sql/004_seed_blood_test_2026_02_26.sql` | Blood test results |
| `sql/005_additional_garmin_tables.sql` | Phase 2 additional tables (5 tables) |
| `sql/006_training_expansion.sql` | Phase 8 tables (planned_workouts, exercise_progression) |
| **Docs** | |
| `docs/training-expansion-brief.md` | Full Phase 7-10 specification |
| `docs/schema-conflict-resolution.md` | Why 3 tables were dropped |
| `docs/grafana-dashboard-spec.md` | Dashboard & alert specifications |
| `spikes/garmin-auth-spike.md` | Garmin auth test plan (run on Mac) |
| **OpenClaw** | |
| `openclaw/garmin-mcp-config.json` | MCP server config |
| `openclaw/skills/health-coach/SKILL.md` | Health coach skill definition |
| `openclaw/coaching-context.md` | Coaching context (goals, program, preferences) |
| **Config** | |
| `CLAUDE.md` | Architecture, context, decisions (always loaded) |
| `TASKS.md` | This file — operational status & next actions |
| `.env.example` | Required environment variables |

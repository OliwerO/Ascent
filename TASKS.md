# Ascent — Status & Next Steps

> Last updated: 2026-03-30
> Single source of truth for all task status, dependencies, and next actions.
> CLAUDE.md has architecture/context. This file has what to DO.

-----

## Phase Status

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 1 | Supabase Schema + Seed Data | **Done** | 27 tables + seed data deployed |
| 2 | Garmin Sync Script | **Done** | `garmin_sync.py` — 11 data types, backfill, cron |
| 3 | Garmin MCP + Health Coach Skill | **Done** | Config + skill in repo, needs Mac deploy |
| 4 | Grafana Dashboards | Spec done, not built | `docs/grafana-dashboard-spec.md` |
| 5 | Weekly Analysis Script | Not started | Blocked on data in Supabase |
| KB | Scientific Knowledge Base | **Exists in Obsidian** | Needs sync to repo |
| GS | Garmin Auth Spike | **Auth fixed** | garth→DI OAuth upgrade done; push spike still needed |
| 6 | First Opus Planning Session | Not started | Blocked on KB + data accumulation |
| 7a | Garmin Data Pull | **Effectively done** | `garmin_sync.py` already covers this |
| 7b | Garmin Workout Push | Scaffolded | `garmin_workout_push.py` — blocked on spike |
| 8 | Workout Generation Engine | Scaffolded | `workout_generator.py` — blocked on Phase 6 |
| 9 | Google Calendar Integration | Not started | Blocked on Phase 8 |
| 10 | Autonomous Orchestration | Not started | Blocked on 7a, 8, 9 |

### Schema conflict resolved (2026-03-30)

Three tables proposed in the expansion brief were dropped as redundant.
See `docs/schema-conflict-resolution.md`. New migration: `sql/006_training_expansion.sql`.

-----

## Dependency Chain

```
Things that can happen NOW (parallel):
  ├── Garmin Auth Spike (Mac, real credentials)
  ├── Knowledge Base sync (Obsidian → repo)
  ├── Mac deployment (Phase 3 setup, first sync, backfill)
  └── Grafana Cloud setup

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

- [ ] **Deploy Phase 3 on Mac:**
  ```bash
  cd ~/projects/ascent
  git pull origin claude/save-ascent-spec-ob2rG
  bash scripts/setup_phase3.sh
  ```
  Add `openclaw/garmin-mcp-config.json` to openclaw.json under `mcp_servers`, restart gateway.

- [ ] **Verify first Garmin sync** (check after 06:00):
  ```bash
  cat ~/projects/ascent/logs/sync.log
  ```
  If rate limit active, manually retry:
  ```bash
  cd ~/projects/ascent && source venv/bin/activate
  python scripts/garmin_sync.py --date 2026-03-29
  ```

- [ ] **Backfill historical data** (once sync works):
  ```bash
  python scripts/garmin_sync.py --range 2026-01-01 2026-03-29
  ```

- [ ] **Stop the cron job** — it perpetuates 429 rate limits on auth failure:
  ```bash
  launchctl unload ~/Library/LaunchAgents/com.ascent.garmin-sync.plist
  ```

- [ ] **Upgrade garminconnect and test auth** (after 429 cooldown, ~24-48h):
  ```bash
  cd ~/projects/ascent && source venv/bin/activate
  pip install --upgrade garminconnect
  # First run is interactive (MFA prompt)
  python scripts/garmin_sync.py --date 2026-04-05
  ```

- [ ] **Re-enable cron** (only after auth test passes):
  ```bash
  launchctl load ~/Library/LaunchAgents/com.ascent.garmin-sync.plist
  ```

- [ ] **Run Garmin Push Spike** — still needed for workout upload:
  ```bash
  # Follow spikes/garmin-auth-spike.md write tests
  # Tests: workout push, watch sync, per-set data
  ```

- [ ] **Sync knowledge base** from Obsidian to repo:
  ```bash
  cp -r ~/vault/second-brain/projects/ascent/knowledge-base/ ~/projects/ascent/docs/knowledge-base/
  ```

- [ ] **Copy training-expansion-brief.md to Obsidian vault:**
  ```bash
  cp ~/projects/ascent/docs/training-expansion-brief.md ~/vault/second-brain/projects/ascent/
  ```

### Medium Priority

- [ ] **Supabase verification:**
  - Confirm all 27 tables + generated columns work
  - Run `sql/006_training_expansion.sql` to add Phase 8 tables
  - Verify daily_summary view returns data after first sync
  - Decide on RLS policy (read-only anon key vs service_role)

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
- [ ] Implement `garmin_workout_push.py` using garminconnect 0.3+ (DI OAuth)
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

# Ascent — Status & Next Steps

> Last updated: 2026-04-02
> Single source of truth for all task status, dependencies, and next actions.
> CLAUDE.md has architecture/context. This file has what to DO.

-----

## Phase Status

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 1 | Supabase Schema + Seed Data | **Done** | 27 tables + seed data deployed + Phase 8 migration run |
| 2 | Garmin Sync Script | **Done** | `garmin_sync.py` — garminconnect 0.2.41, Safari cookie auth, session keeper, 3-month backfill complete |
| 3 | Health Coach Skill | **Deployed** | Supabase REST API (Garmin MCP broken by Cloudflare). Skill on OpenClaw, Telegram working. |
| 4a | Grafana Alerts | Ready to build | Grafana Cloud connected via session pooler (IPv4). Alert engine role only. |
| 4b | Health Webapp (React/Vercel) | Not started | Replaces Grafana as primary visual dashboard. Spec: `docs/dashboard-and-channels-spec.md` |
| 4c | Slack Channels | Ready to build | `#ascent-daily` (briefing + alerts) + `#ascent-training` (plans + analysis) |
| 5 | Weekly Analysis Script | Not started | Posts to `#ascent-training` on Sundays |
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

### Garmin auth hardening (2026-04-02)

- **Auth rewrite complete.** All login()/SSO fallbacks removed from all scripts.
- `garmin_auth.py` — shared auth module with exception-based API:
  - Auth chain: cached cookies → live Safari extraction → garth.resume() → fail+alert
  - Custom exceptions: `AuthExpiredError`, `RateLimitCooldownError` (callers handle gracefully)
  - Auto-detects 429 during session verification → sets cooldown automatically
  - Cookie freshness checking (6h stale warning)
  - `NK: NT` header for Garmin API compatibility
  - CLI status check: `python garmin_auth.py` shows all auth method status
  - Backward-compatible `get_garmin_client()` alias for existing code
- `garmin_session_keepalive.py` — **replaces** `garmin_session_refresh.sh`:
  - Actively hits Garmin API to **extend** the session server-side (not just cookie extraction)
  - Caches cookies with timestamps to `~/.garmin-cookies.json`
  - Tracks consecutive failures, alerts to Slack after ~8h dead
  - Auto-sets cooldown on 429 detection
  - `--status` flag for diagnostics
  - **Needs launchd plist update** (see Oliwer's Actions below)
- Rate limit cooldown lock: `~/.garth/.auth_cooldown` (25h window). All scripts check before auth.
- `garmin_login_once.py` deleted.
- Slack alerts on auth failure / rate limit → `#ascent-daily`.

### Garmin auth history (2026-03-31)

- `garth` library **deprecated** as of v0.8.0 (2026-03-28). Garmin added Cloudflare protection to SSO endpoints mid-March 2026.
- Upgraded to `garminconnect 0.2.41` (web-session branch) — uses mobile API + JWT auth.
- Mobile API works but triggers aggressive account-level rate limiting (429).
- **Resolved (2026-03-31):** Auth working via Safari cookie extraction (`browser_cookie3`).
  Session kept alive by `garmin_session_refresh.sh` (launchd, every 4h).
  3-month backfill complete: 90 days of data (Jan 1 – Mar 31), 47 activities.
- MFA is permanently enabled (ECG feature, irreversible).
- Body composition: daily weight from Xiaomi Mi Scale via Zepp Life (`scale_sync.py`). Full body comp scans from eGym (`egym_sync.py`).

### Terra API — shelved (2026-04-02)

- Terra's cheapest plan is $399/month (Quick Start). No free tier available as of April 2026.
- Not viable for a single-user personal project (~1.2k credits/month usage).
- `terra_sync.py` built and in repo as a backup if a free tier appears or Garmin breaks cookies again.
- `docs/terra-field-mapping.md` documents the full field mapping for future reference.
- **Decision: Stay with hardened direct Garmin auth** (`garmin_auth.py`). Safari cookies + garth.resume() for all reads/writes. No SSO calls ever.

### Research integration (2026-04-02)

- Evidence-based implementation guide integrated across all project files.
- Knowledge base updated to v1.2: added Domain 7 (Metric Hierarchy & Signal Quality), Domain 8 (Dashboard & Communication Design), updated Domains 1, 3, 4.
- Health coach skill updated with communication principles, data trust hierarchy, expanded what-not-to-do.
- Grafana dashboard spec updated: Dashboard 1/2 design notes, new Dashboard 3 (Quarterly Strategic Review), alerts rewritten with compound conditions.
- CLAUDE.md updated with data validation rules and new critical decisions.
- Migration `009_research_integration.sql` created: `subjective_wellness`, `daily_data_quality`, `data_epochs` tables + `srpe`/`srpe_load` columns on `training_sessions`.

### Xiaomi Mi Scale sync (2026-04-02)

- `scale_sync.py` pulls daily weight from Zepp Life cloud via SmartScaleConnect (Go binary).
- Binary: `bin/scaleconnect` (Darwin arm64, v0.4.1, gitignored). Source: `github.com/AlexxIT/SmartScaleConnect`.
- Inline config (no credentials on disk) — pulls from Zepp Life using Xiaomi account auth.
- Parses CSV export, upserts to `body_composition` with `source='xiaomi'`. Weight only (kg→grams).
- Body fat, muscle mass, etc. left NULL — those come from eGym scans.
- Skips rows already in Supabase (match on date + source).
- Supports `--dry-run` and `--skip-export` flags.
- Launchd: `com.ascent.scale-sync.plist` — daily at 10:00 (after weigh-in window 06:30–09:30), logs to `logs/scale-sync.log`.
- Env vars: `XIAOMI_EMAIL`, `XIAOMI_PASSWORD`.
- **Note:** Zepp Life sync logs you out of the Zepp Life mobile app each time.

### eGym body scan sync (2026-04-01)

- `egym_sync.py` pulls body composition from eGym via `egym-exporter` (Go binary, Prometheus metrics).
- Binary: `bin/egym_exporter` (Darwin arm64, gitignored). Source: `github.com/soerenuhrbach/egym-exporter`.
- Upserts to `body_composition` with `source='egym'`. Migration `008_body_comp_source_unique.sql` adds unique constraint on `(date, source)` to support multiple sources per date.
- Env vars: `EGYM_BRAND`, `EGYM_USERNAME`, `EGYM_PASSWORD`.
- Captures: weight, body fat %, BMI, muscle mass, bone mass, body water %, visceral fat, metabolic age, lean body mass, plus bio age metrics in raw_json.

-----

## Dependency Chain

```
Things that can happen NOW (parallel):
  ├── Re-establish Safari cookie auth (April 3 ~13:00 Vienna, after cooldown)
  │     1. Log into Garmin Connect in Safari
  │     2. Wait for garmin_session_refresh.sh (4h cycle)
  │     3. Test: python garmin_sync.py --date 2026-04-02
  ├── Grafana Cloud: fix Supabase connection (get pooler details from dashboard)
  ├── Run migration 009_research_integration.sql
  ├── Implement subjective wellness questionnaire (highest-evidence unbuilt feature)
  ├── Add data validation to garmin_sync.py
  └── Add sRPE capture to training workflow

After Garmin Spike completes:
  └── Phase 7b: implement garmin_workout_push.py

After KB + 4-6 weeks of Garmin data:
  └── Phase 6: First Opus planning session
      └── Phase 8: implement workout_generator.py
          └── Phase 9: Google Calendar integration
              └── Phase 10: Full orchestration

After Grafana connected:
  ├── Build Dashboard 1 (Daily Overview) + Dashboard 2 (Training Detail)
  ├── Implement compound alert conditions
  └── Build Dashboard 3 (Quarterly Strategic Review)
```

-----

## Oliwer's Actions (requires Mac / manual)

### High Priority

- [x] **Deploy Phase 3 on Mac** (done 2026-03-31)
- [x] **Sync knowledge base** from Obsidian to repo (done 2026-03-31)
- [x] **Copy training-expansion-brief.md to Obsidian vault** (done 2026-03-31)
- [x] **Fix launchd plist** — was using system Python, now uses venv (done 2026-03-31)
- [x] **Run Phase 8 migration** — `sql/006_training_expansion.sql` (done 2026-03-31)

- [ ] **Re-establish Safari cookie auth** (April 3 ~13:00 Vienna, after cooldown):
  1. Log into Garmin Connect in Safari (normal browser login — handles MFA, Cloudflare)
  2. Run keepalive manually to extract + verify cookies:
     ```bash
     cd ~/projects/ascent && source venv/bin/activate
     python scripts/garmin_session_keepalive.py
     ```
  3. Check auth status:
     ```bash
     python scripts/garmin_auth.py
     ```
  4. Test hardened sync:
     ```bash
     python scripts/garmin_sync.py --date 2026-04-02
     ```

- [x] **Keepalive launchd plist deployed** (done 2026-04-02):
  `com.ascent.garmin-keepalive` runs every 30 minutes. Old `garmin-session-refresh` unloaded.

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

### Research Integration (2026-04-02)

**High priority:**
- [ ] **Implement daily subjective wellness questionnaire via Slack/Telegram** — 5 items (sleep quality, fatigue, muscle soreness, motivation, stress), 1–5 scale, stored in `subjective_wellness` table (migration 009), Z-score normalized against 14–28 day rolling baseline. Highest-evidence unbuilt feature.

**Medium priority:**
- [ ] **Add data validation layer to garmin_sync.py** — apply reject/flag rules from the validation table before writing to Supabase (see CLAUDE.md "Data Integrity" section)
- [ ] **Create data_quality tracking** — populate `daily_data_quality` table (migration 009) with wear hours, completeness score, max gap duration, is_valid_day flag
- [ ] **Create data_epochs tracking** — populate `data_epochs` table (migration 009) with device changes, firmware updates for baseline reset triggers
- [ ] **Implement date-spine pattern for gap-aware rolling calculations** — update Grafana queries and weekly analysis to use `generate_series()` with minimum valid-day thresholds (4/7 weekly, 20/30 monthly)
- [ ] **Add sRPE capture to training workflow** — CR-10 × duration for every session, stored in `training_sessions.srpe` and `.srpe_load` columns (migration 009)
- [ ] **Update Grafana alert conditions** to compound multi-signal rules with 2-day time-delay filtering (see updated `docs/grafana-dashboard-spec.md`)
- [ ] **Add Quarterly Strategic Review dashboard to Grafana** per new Dashboard 3 spec

### Coaching & Infrastructure
- [ ] **Fix Slack channel messaging** — bot responds to DMs but not #ascent-daily. Needs `message.channels` event subscription on api.slack.com (user action)
- [ ] **Test on-demand Garmin sync button** — verify watch icon in app triggers sync_watcher → garmin_sync.py pipeline
- [ ] **Add data validation to garmin_sync.py** — reject/flag rules from CLAUDE.md "Data Integrity" section before writing to Supabase
- [ ] **Verify readiness_composite view** works end-to-end with new tables from migration 009

### After Phases 7b + 8 working:
- [ ] Phase 9: Google Calendar integration
- [ ] Phase 10: Wire up OpenClaw cron jobs, Telegram interaction patterns

-----

## Key Files

| File | Purpose |
|------|---------|
| **Scripts** | |
| `scripts/garmin_auth.py` | Shared auth module — cached cookies → Safari → garth.resume() → fail+Slack alert. No login(). |
| `scripts/garmin_session_keepalive.py` | Every 4h: extract Safari cookies, hit Garmin API to extend session, cache cookies. Replaces .sh version. |
| `scripts/garmin_sync.py` | **Primary read pipeline.** Nightly Garmin → Supabase sync (hardened auth, no SSO) |
| `scripts/terra_sync.py` | Backup: Terra API → Supabase (shelved — $399/mo, no free tier) |
| `scripts/egym_sync.py` | eGym body scan → Supabase sync (body composition) |
| `scripts/scale_sync.py` | Xiaomi Mi Scale → Supabase sync (daily weight via Zepp Life) |
| `config/scaleconnect.yaml` | SmartScaleConnect config (template — credentials passed inline) |
| `scripts/com.ascent.scale-sync.plist` | macOS launchd: scale sync daily at 05:30 |
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
| `sql/008_body_comp_source_unique.sql` | Unique constraint on (date, source) for multi-source body comp |
| `sql/009_research_integration.sql` | subjective_wellness, daily_data_quality, data_epochs tables + sRPE columns |
| `sql/011_daily_summary_multi_source.sql` | daily_summary view updated for multi-source weight + RLS for 009 tables |
| `sql/012_exercise_seeds_and_wellness_fix.sql` | Missing exercise seeds + composite_score NULL fix |
| **Docs** | |
| `docs/knowledge-base/domain-9-mobility.md` | Mobility & flexibility evidence base (7 sections, 3 protocols) |
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

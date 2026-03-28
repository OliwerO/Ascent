# Ascent — Status & Next Steps

> Last updated: 2026-03-28

-----

## Completed

- [x] **Phase 1: Supabase Schema** — All tables deployed, seed data loaded, Phase 2 migration (005) applied
- [x] **Phase 2: Garmin Sync Script** — `scripts/garmin_sync.py` with 11 data types, backfill flags, launchd cron at 06:00
- [x] **Phase 3: Garmin MCP + Health Coach Skill** — Config, skill, setup script in repo (PR #4 merged)
- [x] **Coaching Context** — Full context file at `openclaw/coaching-context.md` (goals, program, preferences, injury log)
- [x] **Grafana Dashboard Spec** — Two dashboards + 4 alerts documented at `docs/grafana-dashboard-spec.md`

-----

## Next Steps

### Immediate (Jarvis on Mac)

1. **Pull latest and deploy Phase 3:**
   ```bash
   cd ~/projects/ascent
   git pull origin claude/save-ascent-spec-ob2rG
   bash scripts/setup_phase3.sh
   ```
   Then add `openclaw/garmin-mcp-config.json` contents to openclaw.json under `mcp_servers` and restart the gateway.

2. **Verify first Garmin sync (tomorrow after 06:00):**
   ```bash
   cat ~/projects/ascent/logs/sync.log
   ```
   If rate limit is still active, manually retry:
   ```bash
   cd ~/projects/ascent && source venv/bin/activate
   rm -rf ~/.garth/
   python scripts/garmin_sync.py --date 2026-03-27
   ```

3. **Backfill historical data** (once sync works):
   ```bash
   python scripts/garmin_sync.py --range 2026-01-01 2026-03-27
   ```

### Requires Computer Access (Oliwer)

4. **Supabase schema verification:**
   - Confirm all 27 tables exist (22 from Phase 1 + 5 from Phase 2 migration)
   - Test generated columns (weight_kg, volume_kg, estimated_1rm)
   - Verify daily_summary view returns data
   - Check seed data: biomarker_definitions, exercises
   - Decide on RLS: add read-only policy for anon key, service_role for sync script?

5. **Test MCP integration:**
   - Ask Jarvis "how was my sleep last night?" — should return actual Garmin data
   - Ask Jarvis "what's my HRV trend?" — should give contextual analysis
   - Verify skill visible in `/context detail`

### Build Next

6. **Grafana Cloud setup:**
   - Create Grafana Cloud account (free tier is sufficient)
   - Add Supabase as PostgreSQL data source
   - Build Dashboard 1 (Daily Overview) per `docs/grafana-dashboard-spec.md`
   - Build Dashboard 2 (Training Detail)
   - Configure 4 alerts → Telegram via Jarvis webhook

7. **Calendar integration:**
   - Explore pushing daily training plan to Google Calendar
   - Claude has Google Calendar MCP access; OpenClaw does not yet
   - Options: Claude pushes events, or add calendar MCP to OpenClaw

8. **First Opus session** (after 4-6 weeks of data):
   - Design detailed training program with progression scheme
   - Create nutrition plan
   - Structure mobility routine
   - Set specific targets based on baseline data

-----

## Key Files

| File | Purpose |
|------|---------|
| `scripts/garmin_sync.py` | Nightly Garmin → Supabase sync |
| `scripts/requirements.txt` | Python dependencies |
| `scripts/com.ascent.garmin-sync.plist` | macOS launchd cron config |
| `scripts/setup_phase3.sh` | One-shot Phase 3 deployment |
| `openclaw/garmin-mcp-config.json` | MCP server config for OpenClaw |
| `openclaw/skills/health-coach/SKILL.md` | Health coach skill definition |
| `openclaw/coaching-context.md` | Coaching context (goals, program, preferences) |
| `docs/grafana-dashboard-spec.md` | Dashboard & alert specifications |
| `sql/001_schema.sql` | Phase 1 database schema |
| `sql/005_additional_garmin_tables.sql` | Phase 2 additional tables |
| `.env.example` | Required environment variables |

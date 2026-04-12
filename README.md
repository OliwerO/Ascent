# Ascent

AI-coached training intelligence for a single athlete. Collects wearable data from Garmin, applies evidence-based coaching logic, generates and adjusts workouts, and surfaces everything through a mobile-first React dashboard. The system runs autonomously — daily coaching decisions, weekly analysis, and Garmin workout pushes happen without human intervention.

## Quick access

- **Web app:** Open on your phone (deployed on Vercel, auto-deploys from `main`)
- **Slack:** Morning briefing arrives at 09:15, RPE reminder at 20:00
- **Garmin:** Workouts pushed to your watch automatically after the daily coaching decision

## What runs automatically

All cron jobs run via macOS launchd on your Mac. **The Mac must be open and awake** for these to fire.

| Time | Script | What it does |
|------|--------|-------------|
| 09:00 | `garmin_sync.py` | Pulls HRV, sleep, activities, body battery, VO2max from Garmin |
| 09:15 | `morning_briefing.py` | Posts health snapshot to Slack |
| 09:43 | CCD health-coach-daily | Reads recovery data, decides train/rest/adjust, pushes workout to Garmin |
| 10:00 | `scale_sync.py` | Fetches body weight from Xiaomi Mi Scale |
| Every 15 min | `health_check.py` | Verifies syncs completed, alerts on failures |
| 18:00 | `consistency_watchdog.py` | Alerts if any scheduled job missed its window |
| 20:00 | `rpe_reminder.py` | Slack reminder to log RPE if a workout was completed |
| Sunday 20:00 | `weekly_analysis_runner.py` | Weekly retrospective: interference analysis, decision quality, recomp tracking |
| Sunday 20:03 | CCD health-coach-weekly | Weekly coaching review + adjustments |

## Troubleshooting

### "Data looks stale" / app shows old numbers

The app shows a warning banner when data is >6h old. Common causes:

1. **Mac was asleep or lid closed** — Open it. Jobs will resume on next scheduled time. To force a sync now, tap the watch icon in the app header.
2. **Garmin auth expired** — See below.
3. **garmin_sync.py crashed** — Check logs: `cat ~/Library/Logs/ascent/garmin_sync.log`

### Garmin auth died

Garmin auth uses session cookies that expire roughly every 36 hours. When it dies:

1. You'll see "Garmin auth locked" alerts in Slack
2. Run the bootstrap script to re-authenticate:
   ```bash
   cd ~/projects/ascent
   venv/bin/python scripts/garmin_browser_bootstrap.py
   ```
3. Complete MFA in the browser window that opens
4. Verify sync works: `venv/bin/python scripts/garmin_sync.py --dry-run`

### Morning briefing didn't arrive

1. Check Mac was awake at 09:15
2. Check logs: `cat ~/Library/Logs/ascent/morning_briefing.log`
3. Manual run: `venv/bin/python scripts/morning_briefing.py`

### Workout wasn't pushed to Garmin

1. Check CCD health-coach-daily ran (coaching_log in Supabase should have today's entry)
2. Check Garmin auth is valid (see above)
3. Manual push: `venv/bin/python scripts/workout_push.py --date today --dry-run` (remove `--dry-run` to actually push)

### A launchd job stopped running

List all Ascent agents and their status:
```bash
launchctl list | grep ascent
```

If one shows an error code, reload it:
```bash
launchctl unload ~/Library/LaunchAgents/com.ascent.<name>.plist
launchctl load ~/Library/LaunchAgents/com.ascent.<name>.plist
```

## Project structure

```
scripts/          Python scripts (sync, coaching, analysis)
web/              React app (Vite + TypeScript, deployed on Vercel)
sql/              Database migrations (append-only)
openclaw/         Coaching docs and CCD skill definitions
docs/             Specs, audits, knowledge base
tests/            Python tests (pytest)
config/           Shared configuration
```

## Local development

```bash
# Python
cd ~/projects/ascent
source venv/bin/activate
pip install -r requirements.txt

# Web app
cd web
npm install
npm run dev          # local dev server
npm run build        # must pass before pushing
```

Environment variables are in `.env` at the project root. Never commit this file.

## Key rules

1. `coach_adjust.py` is the single write-path for coaching decisions
2. `planned_workouts` is the source of truth for what the app displays
3. Mountain activities are training — never flag as "missed gym"
4. Always run `npm run build` before pushing frontend changes
5. SQL migrations are append-only — never modify an applied migration

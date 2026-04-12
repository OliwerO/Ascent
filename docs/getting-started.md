# Getting Started

Two scenarios: accessing the app on a new device, or setting up the backend on a new Mac.

## Scenario 1: New Phone / Tablet

The web app runs on Vercel — no install needed.

1. Open `https://web-woad-two-92.vercel.app` in Safari or Chrome
2. Tap **Share > Add to Home Screen** (Safari) or **Menu > Install app** (Chrome)
3. Done. The app loads from the home screen icon like a native app.

## Scenario 2: New Mac (Backend Setup)

The backend (Garmin sync, coaching decisions, Slack briefings, Garmin push) runs on your Mac via launchd. If the Mac is off or asleep, nothing runs.

### 1. Clone and set up Python

```bash
git clone <repo-url> ~/projects/ascent
cd ~/projects/ascent
python3 -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

For web development setup, see `README.md` (npm install, build commands).

### 2. Restore `.env`

Copy `.env` from your backup to the project root:

```bash
cp /path/to/backup/.env ~/projects/ascent/.env
```

This file contains Supabase keys, Garmin credentials, Slack tokens, and other secrets. Never commit it.

### 3. Authenticate with Garmin

```bash
cd ~/projects/ascent
venv/bin/python scripts/garmin_browser_bootstrap.py
```

Complete MFA in the browser window that opens. Garmin cookies expire roughly every 36 hours — you will need to re-run this periodically (the system alerts you via Slack when auth dies).

### 4. Install launchd agents

Copy all plist files and load them:

```bash
cp launchd/com.ascent.*.plist ~/Library/LaunchAgents/

# Load each agent
for plist in ~/Library/LaunchAgents/com.ascent.*.plist; do
  launchctl load "$plist"
done
```

The agents that should be running:

| Plist | Purpose |
|-------|---------|
| `com.ascent.garmin-sync` | Garmin data pull (09:00) |
| `com.ascent.garmin-refresh` | Garmin auth refresh |
| `com.ascent.morning-briefing` | Slack briefing (09:15) |
| `com.ascent.scale-sync` | Weight sync (10:00) |
| `com.ascent.health-check` | Sync verification (every 15 min) |
| `com.ascent.consistency-watchdog` | Missed-job alerts (18:00) |
| `com.ascent.rpe-reminder` | RPE logging reminder (20:00) |
| `com.ascent.weekly-analysis` | Weekly retrospective (Sun 20:00) |
| `com.ascent.daily-reconcile` | Daily data reconciliation |
| `com.ascent.sync-watcher` | Sync status monitoring |

### 5. Verify everything works

```bash
cd ~/projects/ascent

# Check all systems
venv/bin/python scripts/health_check.py

# Test Garmin sync
venv/bin/python scripts/garmin_sync.py --dry-run

# Confirm launchd agents are loaded
launchctl list | grep ascent
```

All health checks should pass and `launchctl list` should show each agent with a `0` exit status (or `-` if it hasn't run yet).

### 6. Run initial sync

Once verification passes, do a real sync to populate the database:

```bash
venv/bin/python scripts/garmin_sync.py
```

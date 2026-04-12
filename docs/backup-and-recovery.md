# Backup and Recovery Runbook

How to recover Ascent if something breaks. Written for Oliwer, not for developers.

---

## 1. What's backed up automatically

**Supabase** handles database backups:

- **Daily automated backups** run every 24 hours
- **Retention:** 7 days on the free/Pro plan (check your Supabase dashboard under Settings > Database > Backups)
- **Point-in-time recovery (PITR):** Available on Pro plan if enabled

You don't need to do anything for these to happen. They cover the full database.

## 2. Irreplaceable tables

These tables contain your actual training history and can't be regenerated:

| Table | What it holds |
|-------|---------------|
| `training_sessions` | Every completed workout session |
| `training_sets` | Every set (weight, reps, RPE) |
| `coaching_log` | All coaching decisions and reasoning |
| `exercise_feedback` | Your feedback on exercises |
| `subjective_wellness` | Daily wellness scores |
| `activities` | Garmin activities (runs, hikes, etc.) |
| `daily_health_summary` | HRV, sleep, body battery history |
| `athlete_response_patterns` | Learned patterns about your recovery |

Tables like `planned_workouts` and `exercises` can be regenerated from code if needed.

## 3. How to export key data manually

Do this periodically (monthly) as an extra safety net.

### Option A: Supabase dashboard (easiest)

1. Go to your Supabase project dashboard
2. Click **Table Editor** in the sidebar
3. Select a table (e.g., `training_sessions`)
4. Click the **Export** button (top right) and choose CSV
5. Repeat for each irreplaceable table listed above
6. Save the CSVs somewhere safe (iCloud, Google Drive)

### Option B: psql command line

```bash
cd ~/projects/ascent
source .env

# Export a single table
psql "$DATABASE_URL" -c "\COPY training_sessions TO '~/Desktop/training_sessions.csv' CSV HEADER"
psql "$DATABASE_URL" -c "\COPY training_sets TO '~/Desktop/training_sets.csv' CSV HEADER"
psql "$DATABASE_URL" -c "\COPY coaching_log TO '~/Desktop/coaching_log.csv' CSV HEADER"
```

## 4. How to restore from Supabase backup

If the database gets corrupted or data is accidentally deleted:

1. Go to **Supabase Dashboard > Settings > Database > Backups**
2. Find the backup from before the problem occurred
3. Click **Restore** on that backup
4. Wait for the restore to complete (can take a few minutes)

Full docs: https://supabase.com/docs/guides/platform/backups

**Important:** Restoring replaces the entire database. Any data added after the backup timestamp will be lost. If you only need to recover specific rows, use the CSV exports instead.

## 5. Garmin auth recovery

Garmin auth cookies expire roughly every 36 hours. When it breaks:

**Symptoms:** "Garmin auth locked" alerts in Slack, stale data in the app.

**Fix:**

```bash
cd ~/projects/ascent
venv/bin/python scripts/garmin_browser_bootstrap.py
```

1. A browser window opens -- log in to Garmin Connect
2. Complete MFA if prompted
3. The script saves new session cookies automatically
4. Verify it works:
   ```bash
   venv/bin/python scripts/garmin_sync.py --dry-run
   ```

## 6. Vercel (web app) recovery

The React app auto-deploys from the `main` branch on GitHub.

**If the app is down:**

1. Check [Vercel dashboard](https://vercel.com) for deployment errors
2. If a bad deploy broke it, click **Redeploy** on the last working deployment
3. If the repo is fine, Vercel just needs a push:
   ```bash
   cd ~/projects/ascent/web
   git commit --allow-empty -m "Trigger redeploy"
   git push
   ```

**If you need to set up Vercel from scratch:**

1. Import the GitHub repo at vercel.com
2. Set the root directory to `web`
3. Add environment variables from `web/.env.production` (mainly `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`)

## 7. Local Mac recovery

If you get a new Mac or need to reinstall:

### A. Clone the repo and set up Python

```bash
git clone <your-repo-url> ~/projects/ascent
cd ~/projects/ascent
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### B. Restore .env

The `.env` file contains all secrets (Supabase keys, Garmin credentials, Slack webhook). It's not in git. You'll need to recreate it with:

- `DATABASE_URL` -- from Supabase dashboard > Settings > Database
- `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` -- from Supabase dashboard > Settings > API
- `GARMIN_EMAIL` and `GARMIN_PASSWORD` -- your Garmin Connect credentials
- `SLACK_WEBHOOK_URL` -- from Slack app settings

### C. Reinstall launchd agents

The cron jobs are macOS launchd agents. Reinstall them:

```bash
# Copy all plist files to LaunchAgents
cp ~/projects/ascent/launchd/*.plist ~/Library/LaunchAgents/

# Load each one (or reboot, which loads them automatically)
launchctl load ~/Library/LaunchAgents/com.ascent.*.plist
```

If the plist files aren't in the repo, check `~/Library/LaunchAgents/` on your old Mac -- the files are named `com.ascent.*.plist`.

### D. Re-authenticate Garmin

```bash
cd ~/projects/ascent
venv/bin/python scripts/garmin_browser_bootstrap.py
```

### E. Verify everything works

```bash
venv/bin/python scripts/garmin_sync.py --dry-run   # Garmin data pull
venv/bin/python scripts/morning_briefing.py         # Slack message
cd web && npm install && npm run build              # React app builds
```

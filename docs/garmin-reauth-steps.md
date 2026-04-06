# Garmin Re-Authentication Steps

After the garth → DI OAuth upgrade, follow these steps to re-authenticate.

## Prerequisites
- `garminconnect>=0.3.0` installed (already done)
- At least 24-48h since last failed login attempt (to clear Garmin's 429 rate limit)
- OR: use a different IP (mobile hotspot) to bypass the rate limit

## Steps

### 1. Stop the cron job (if not already done)
```bash
launchctl unload ~/Library/LaunchAgents/com.ascent.garmin-sync.plist
```

### 2. Delete the auth lockfile (if it exists)
```bash
rm -f ~/projects/ascent/.garmin_auth_failed
```

### 3. Run the sync interactively
```bash
cd ~/projects/ascent && source venv/bin/activate
python scripts/garmin_sync.py --date 2026-04-05
```
You'll be prompted for your Garmin MFA code — check your email or authenticator app.

### 4. Verify it worked
- Check that `~/.garminconnect/garmin_tokens.json` exists
- Check stdout for "Garmin login successful" and synced row counts

### 5. Re-enable the cron job
```bash
launchctl load ~/Library/LaunchAgents/com.ascent.garmin-sync.plist
```

### 6. Verify next morning
Check the log after the 06:00 run:
```bash
cat ~/projects/ascent/logs/sync.log
```

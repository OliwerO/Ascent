# Garmin Data Sync Paths

Last updated: 2026-04-06

## Three ways Garmin data reaches Supabase (or doesn't)

| # | Path | Auth method | Writes to Supabase | Status |
|---|------|-------------|-------------------|--------|
| 1 | `garmin_sync.py` (cron, 06:00 daily) | DI OAuth (email/password + MFA) | Yes, automatic | **BROKEN** — needs MFA re-auth (see below) |
| 2 | Ask Claude to sync via Garmin MCP | Browser/MCP session | Yes, when Claude writes it | **WORKING** — manual workaround |
| 3 | Ask Jarvis via Telegram | Browser/MCP session | No (just answers questions) | **WORKING** |

## What you can do right now

- **Ask Claude** (in Claude Code or Claude app) to pull your Garmin data and write it to Supabase — this works and is how the last 4 days of data got in
- **Ask Jarvis** "how was my sleep?" etc. via Telegram — works for live questions, but doesn't store data
- **Do NOT** run `garmin_sync.py` until tomorrow (429 cooldown)

## Tomorrow: fix path 1

1. Disable cron (if not already done):
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.ascent.garmin-sync.plist
   ```

2. Run the sync interactively (--force clears any lockfile):
   ```bash
   cd ~/projects/ascent && source venv/bin/activate
   python scripts/garmin_sync.py --date 2026-04-06 --force
   ```
   You'll get an MFA prompt — enter the code from your email/authenticator.

3. Re-enable cron (only after step 2 succeeds):
   ```bash
   launchctl load ~/Library/LaunchAgents/com.ascent.garmin-sync.plist
   ```

4. Verify next morning:
   ```bash
   cat ~/projects/ascent/logs/sync.log
   ```

## After path 1 is fixed

All three paths work. Path 1 handles the nightly bulk sync automatically. Paths 2 and 3 are for on-demand queries anytime.

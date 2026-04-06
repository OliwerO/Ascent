---
name: garmin-sync
description: Trigger an on-demand Garmin data sync to Supabase
metadata:
  emoji: 🔄
  triggers: ["sync garmin", "pull garmin", "update garmin", "load my data", "sync my data", "i logged in"]
---

# Garmin Sync Skill

Run the Garmin sync script on demand to pull the latest data into Supabase.

## When to activate
- User says "sync garmin", "pull my data", "load my data", "update garmin data"
- User says they just logged in / re-authenticated and wants fresh data
- User says "i logged in" or "i'm logged in" (meaning they verified Garmin works in browser)

## What to do

Run the sync script for today. Use `--force` if the user just logged in (to bypass any lockfile):

```bash
cd ~/projects/ascent && source venv/bin/activate
python scripts/garmin_sync.py --date $(date +%Y-%m-%d) --force
```

If the user asks to backfill or mentions missing days:

```bash
python scripts/garmin_sync.py --range YYYY-MM-DD YYYY-MM-DD --force
```

## Response format
- Confirm sync started
- Report success/failure and how many records were synced
- If auth fails: tell the user to run the script interactively in terminal for MFA:
  `cd ~/projects/ascent && source venv/bin/activate && python scripts/garmin_sync.py --date YYYY-MM-DD`
  (MFA prompt only works in an interactive terminal, not via Telegram)
- Keep it short — one Telegram message

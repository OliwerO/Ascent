#!/usr/bin/env python3
"""Post-session RPE reminder → Slack.

Runs at 21:00 daily. Checks if today had a planned gym session and whether
sRPE has been submitted. Posts a Slack reminder if missing.

Usage:
    python rpe_reminder.py              # check today
    python rpe_reminder.py --dry-run    # print instead of posting
    python rpe_reminder.py --date 2026-04-10
"""

import argparse
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"]
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL_DAILY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("rpe_reminder")


def supabase_get(table: str, params: dict) -> list:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def check_rpe_needed(target_date: date) -> dict | None:
    """Return session info if today had a gym session without sRPE, else None."""
    # Check if there's a completed/adjusted strength session for today
    planned = supabase_get("planned_workouts", {
        "scheduled_date": f"eq.{target_date.isoformat()}",
        "select": "session_name,session_type,status",
        "status": "in.(completed,adjusted,pushed,planned)",
        "session_type": "neq.rest",
    })
    gym_sessions = [p for p in planned if p.get("session_type") in (
        "strength", "strength_a", "strength_b", "strength_c", None
    )]
    if not gym_sessions:
        return None

    # Check if sRPE was submitted for today
    ts = supabase_get("training_sessions", {
        "date": f"eq.{target_date.isoformat()}",
        "select": "id,name,srpe",
    })
    # If there's a training session with sRPE already, no reminder needed
    if ts and any(t.get("srpe") is not None for t in ts):
        return None

    # Also check subjective_wellness for an sRPE-like input
    # (some users submit via wellness check instead)
    return {
        "session_name": gym_sessions[0].get("session_name", "today's session"),
        "has_training_session": bool(ts),
    }


def post_reminder(session_info: dict, dry_run: bool = False) -> None:
    name = session_info["session_name"]
    msg = (
        f":memo: *RPE reminder* — {name} has no session RPE logged yet. "
        "How hard was it? Reply with a number (1-10) or open the app."
    )

    if dry_run:
        print(msg)
        return

    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL:
        log.warning("Slack not configured — reminder not sent")
        return

    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        json={"channel": SLACK_CHANNEL, "text": msg},
        timeout=10,
    )
    data = resp.json()
    if data.get("ok"):
        log.info("RPE reminder posted to Slack")
    else:
        log.warning("Slack post failed: %s", data.get("error"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=str, help="Check date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else date.today()

    info = check_rpe_needed(target)
    if info:
        log.info("RPE missing for %s on %s", info["session_name"], target)
        post_reminder(info, dry_run=args.dry_run)
    else:
        log.info("No RPE reminder needed for %s", target)


if __name__ == "__main__":
    main()

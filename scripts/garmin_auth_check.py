#!/usr/bin/env python3
"""Garmin browser-session health check + Slack notifier.

Runs the headless Playwright auth verify (the same one in garmin_auth.py)
and posts a structured result to Slack so the user can monitor session
health from anywhere (phone, laptop, etc.) without needing to be at the Mac.

Designed for two use cases:
  1. Empirical lifetime sampling — schedule via launchd at intervals to
     see how long a single bootstrap survives before needing re-auth.
  2. Long-term daily health check — once lifetime is known, run once a day
     to alert before sync runs hit a stale session.

Always exits 0 (Slack carries the result) so launchd doesn't spam logs.

Posts to SLACK_CHANNEL_DAILY (default) or SLACK_CHANNEL_HEALTH if set.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("garmin_auth_check")

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = (
    os.environ.get("SLACK_CHANNEL_HEALTH")
    or os.environ.get("SLACK_CHANNEL_DAILY")
    or ""
)
STORAGE_PATH = Path.home() / ".garminconnect" / "garmin_storage_state.json"


def report(text: str) -> None:
    """Always print to stdout (so a calling skill can capture the result),
    and optionally post to Slack if SLACK_NOTIFY=1 is set in the environment.

    The default is stdout-only because skill invocations want the message
    inline in the chat reply, not duplicated to Slack.
    """
    print(text)
    if os.environ.get("SLACK_NOTIFY") != "1":
        return
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL:
        print("[slack-skip] SLACK_NOTIFY=1 set but no token/channel configured")
        return
    try:
        import requests
        r = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"channel": SLACK_CHANNEL, "text": text},
            timeout=10,
        )
        data = r.json()
        if not data.get("ok"):
            print(f"[slack-fail] {data.get('error')}")
    except Exception as e:
        print(f"[slack-error] {e}")


def storage_state_age_hours() -> float | None:
    if not STORAGE_PATH.exists():
        return None
    age_s = time.time() - STORAGE_PATH.stat().st_mtime
    return age_s / 3600


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    age = storage_state_age_hours()
    if age is None:
        report(
            f":warning: *Garmin auth check ({now})* — no storage state file. "
            f"Run `python3 scripts/garmin_browser_bootstrap.py` to re-auth."
        )
        return 0

    age_str = f"{age:.1f}h" if age < 48 else f"{age/24:.1f}d"

    # Run the actual auth verification — this launches headless Firefox,
    # captures CSRF, hits socialProfile via in-page fetch.
    start = time.time()
    try:
        from garmin_auth import get_safe_client, AuthExpiredError, RateLimitCooldownError
        client = get_safe_client()
        elapsed = time.time() - start
        display = getattr(client, "display_name", "?")
        report(
            f":white_check_mark: *Garmin auth OK ({now})*\n"
            f"• storage_state age: {age_str}\n"
            f"• display_name: `{display}`\n"
            f"• verify took: {elapsed:.1f}s"
        )
        return 0
    except AuthExpiredError as e:
        elapsed = time.time() - start
        report(
            f":x: *Garmin auth EXPIRED ({now})*\n"
            f"• storage_state age: {age_str}\n"
            f"• verify took: {elapsed:.1f}s before failing\n"
            f"• error: `{str(e)[:200]}`\n"
            f"• *Action:* run `python3 scripts/garmin_browser_bootstrap.py` "
            f"on the Mac to re-authenticate."
        )
        return 0
    except RateLimitCooldownError as e:
        report(
            f":no_entry: *Garmin auth in cooldown ({now})*\n"
            f"• {str(e)[:200]}"
        )
        return 0
    except Exception as e:
        elapsed = time.time() - start
        report(
            f":warning: *Garmin auth check error ({now})*\n"
            f"• storage_state age: {age_str}\n"
            f"• unexpected: `{type(e).__name__}: {str(e)[:200]}`\n"
            f"• verify took: {elapsed:.1f}s"
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())

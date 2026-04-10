#!/usr/bin/env python3
"""Ascent system health check.

Runs every 15 minutes via launchd. Checks:
1. Garmin auth status (cooldown, token freshness)
2. Last sync timestamp (stale data detection)
3. Supabase connectivity
4. sync_watcher process running

Posts alerts to Slack on failure. Writes heartbeat to Supabase
so the React app can show a warning if the Mac is offline.
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("health_check")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY", "")


def check_garmin_auth() -> tuple[bool, str]:
    """Check Garmin auth status without making any API calls."""
    try:
        from garmin_auth import check_cooldown
        locked, hours_remaining = check_cooldown()
        if locked:
            return False, f"Garmin auth locked ({hours_remaining:.1f}h remaining)"

        # Check Playwright storage_state freshness (the new browser-session
        # auth path; replaces the old garmin_tokens.json check).
        storage_file = Path.home() / ".garminconnect" / "garmin_storage_state.json"
        if storage_file.exists():
            age_hours = (time.time() - storage_file.stat().st_mtime) / 3600
            # Storage state lifetime is currently unknown empirically; warn
            # past 7 days as a soft signal to re-bootstrap.
            if age_hours > 24 * 7:
                return False, f"Garmin storage state stale ({age_hours/24:.1f}d old)"
            return True, f"Storage state OK ({age_hours/24:.1f}d old)"
        return False, "No Garmin storage state — run garmin_browser_bootstrap.py"
    except Exception as e:
        return False, f"Auth check error: {e}"


def check_last_sync() -> tuple[bool, str]:
    """Check when the last successful Garmin sync happened."""
    try:
        import requests
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/daily_metrics?select=date,synced_at&order=synced_at.desc&limit=1",
            headers={"apikey": SUPABASE_KEY},
            timeout=10,
        )
        if resp.status_code != 200:
            return False, f"Supabase query failed ({resp.status_code})"
        data = resp.json()
        if not data:
            return False, "No sync data found"
        last_sync = data[0].get("synced_at", "")
        if last_sync:
            sync_time = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - sync_time).total_seconds() / 3600
            if age_hours > 36:
                return False, f"Last sync {age_hours:.0f}h ago (>{36}h threshold)"
            return True, f"Last sync {age_hours:.1f}h ago"
        return False, "No synced_at timestamp"
    except Exception as e:
        return False, f"Sync check error: {e}"


def check_supabase() -> tuple[bool, str]:
    """Check Supabase connectivity."""
    try:
        import requests
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/",
            headers={"apikey": SUPABASE_KEY},
            timeout=10,
        )
        if resp.status_code == 200:
            return True, "Supabase OK"
        return False, f"Supabase returned {resp.status_code}"
    except Exception as e:
        return False, f"Supabase unreachable: {e}"


def check_sync_watcher() -> tuple[bool, str]:
    """Check if sync_watcher daemon is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "sync_watcher"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            return True, f"sync_watcher running (PID {pids[0]})"
        return False, "sync_watcher not running"
    except Exception as e:
        return False, f"Process check error: {e}"


def write_heartbeat() -> None:
    """Write heartbeat timestamp to Supabase for SPOF detection."""
    try:
        import requests
        now = datetime.now(timezone.utc).isoformat()
        requests.post(
            f"{SUPABASE_URL}/rest/v1/coaching_log",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json={
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "type": "heartbeat",
                "channel": "system",
                "message": "Mac health check heartbeat",
                "data_context": {"timestamp": now},
                "acknowledged": True,
            },
            timeout=10,
        )
    except Exception:
        pass  # heartbeat failure shouldn't raise


def alert_slack(message: str) -> None:
    """Post alert to Slack (best effort)."""
    token = os.environ.get("SLACK_BOT_TOKEN")
    channel = os.environ.get("SLACK_CHANNEL_DAILY")
    if not token or not channel:
        return
    try:
        import requests
        requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": channel, "text": message},
            timeout=10,
        )
    except Exception:
        pass


def main():
    checks = [
        ("Garmin Auth", check_garmin_auth),
        ("Last Sync", check_last_sync),
        ("Supabase", check_supabase),
        ("Sync Watcher", check_sync_watcher),
    ]

    failures = []
    for name, check_fn in checks:
        ok, msg = check_fn()
        status = "OK" if ok else "FAIL"
        log.info("[%s] %s: %s", status, name, msg)
        if not ok:
            failures.append(f"{name}: {msg}")

    # Write heartbeat regardless of check results
    write_heartbeat()

    if failures:
        alert_msg = ":warning: *Ascent health check failures:*\n" + "\n".join(f"- {f}" for f in failures)
        alert_slack(alert_msg)
        sys.exit(1)

    log.info("All checks passed")
    sys.exit(0)


if __name__ == "__main__":
    main()

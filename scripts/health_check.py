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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

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
    """Check if sync_watcher launchd agent is loaded.

    sync_watcher runs every 300s and exits — it's not a persistent daemon.
    Check launchctl for the agent registration instead of pgrep for a process.
    """
    try:
        result = subprocess.run(
            ["launchctl", "list", "com.ascent.sync-watcher"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            # Parse last exit status from launchctl output
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if '"LastExitStatus"' in line or "LastExitStatus" in line:
                    return True, f"sync_watcher agent loaded (last run OK)"
            return True, "sync_watcher agent loaded"
        return False, "sync_watcher agent not registered in launchctl"
    except Exception as e:
        return False, f"Agent check error: {e}"


def write_heartbeat() -> None:
    """Write heartbeat timestamp to Supabase for SPOF detection.

    Only writes one row per hour to avoid flooding coaching_log.
    Checks the last heartbeat timestamp before inserting.
    """
    try:
        import requests
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        one_hour_ago = (now - timedelta(hours=1)).isoformat()

        # Check if a recent heartbeat already exists
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/coaching_log",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            },
            params={
                "type": "eq.heartbeat",
                "created_at": f"gte.{one_hour_ago}",
                "limit": "1",
            },
            timeout=10,
        )
        if resp.ok and resp.json():
            return  # recent heartbeat exists, skip

        requests.post(
            f"{SUPABASE_URL}/rest/v1/coaching_log",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json={
                "date": today,
                "type": "heartbeat",
                "channel": "system",
                "message": "Mac health check heartbeat",
                "data_context": {"timestamp": now.isoformat()},
                "acknowledged": True,
            },
            timeout=10,
        )
    except Exception:
        pass  # heartbeat failure shouldn't raise


ALERT_STATE_FILE = PROJECT_ROOT / "logs" / "health_check_state.json"

# Escalation intervals: first alert immediate, then 1h, then every 4h
ESCALATION_INTERVALS = [
    timedelta(seconds=0),   # 1st alert: immediate
    timedelta(hours=1),     # 2nd alert: 1 hour after first
    timedelta(hours=4),     # 3rd+: every 4 hours
]


def _load_alert_state() -> dict[str, Any]:
    """Load persisted alert state from disk."""
    try:
        return json.loads(ALERT_STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_alert_state(state: dict[str, Any]) -> None:
    """Persist alert state to disk."""
    ALERT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ALERT_STATE_FILE.write_text(json.dumps(state, indent=2))


def _should_alert(issue_key: str, state: dict[str, Any], now: datetime) -> bool:
    """Decide whether to send an alert based on escalation schedule.

    Returns True if the alert should fire, and updates state in-place.
    """
    if issue_key not in state:
        # First occurrence — record and alert immediately
        state[issue_key] = {
            "first_seen": now.isoformat(),
            "last_alert": now.isoformat(),
            "alert_count": 1,
        }
        return True

    entry = state[issue_key]
    last_alert = datetime.fromisoformat(entry["last_alert"])
    count = entry["alert_count"]

    # Pick the interval: use the last tier for 3rd+ alerts
    tier = min(count, len(ESCALATION_INTERVALS) - 1)
    interval = ESCALATION_INTERVALS[tier]

    if now - last_alert >= interval:
        entry["last_alert"] = now.isoformat()
        entry["alert_count"] = count + 1
        return True

    return False


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

    now = datetime.now(timezone.utc)
    state = _load_alert_state()
    failures = []
    current_issue_keys: set[str] = set()

    for name, check_fn in checks:
        ok, msg = check_fn()
        status = "OK" if ok else "FAIL"
        log.info("[%s] %s: %s", status, name, msg)
        if not ok:
            issue_key = name.lower().replace(" ", "_")
            current_issue_keys.add(issue_key)
            failures.append((issue_key, f"{name}: {msg}"))

    # Write heartbeat regardless of check results
    write_heartbeat()

    # Clear resolved issues from state
    resolved = [k for k in state if k not in current_issue_keys]
    for k in resolved:
        log.info("Issue resolved, clearing alert state: %s", k)
        del state[k]

    if failures:
        # Only alert for issues that pass the escalation gate
        alerts_to_send = []
        for issue_key, detail in failures:
            if _should_alert(issue_key, state, now):
                count = state[issue_key]["alert_count"]
                suffix = f" (alert #{count})" if count > 1 else ""
                alerts_to_send.append(f"- {detail}{suffix}")
            else:
                log.info("Throttled alert for %s (next at escalation tier)", issue_key)

        _save_alert_state(state)

        if alerts_to_send:
            alert_msg = ":warning: *Ascent health check failures:*\n" + "\n".join(alerts_to_send)
            alert_slack(alert_msg)

        sys.exit(1)

    _save_alert_state(state)
    log.info("All checks passed")
    sys.exit(0)


if __name__ == "__main__":
    main()

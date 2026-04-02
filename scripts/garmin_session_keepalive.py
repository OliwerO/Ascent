#!/usr/bin/env python3
"""Garmin session keep-alive — refreshes cookies without login().

Runs every 4 hours via launchd. Extracts Safari cookies, makes a
lightweight Garmin API call to EXTEND the session server-side, and
caches the cookies for other scripts (garmin_sync.py, etc.).

This script NEVER calls login(). If cookies are dead, it alerts
via Slack and exits. Fix by logging into connect.garmin.com in Safari.

Key insight: Just extracting cookies isn't enough — you must USE them
(hit a Garmin endpoint) to extend the session server-side. Otherwise
the server-side session times out even though cookies are still on disk.

Usage:
    python garmin_session_keepalive.py           # refresh + verify
    python garmin_session_keepalive.py --status   # just check status
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("session_keepalive")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

COOKIE_CACHE = Path.home() / ".garmin-cookies.json"
STATUS_FILE = Path.home() / ".garmin-session-status.json"
COOLDOWN_FILE = Path.home() / ".garth" / ".auth_cooldown"
GARMIN_BASE = "https://connect.garmin.com"

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_DAILY = os.environ.get("SLACK_CHANNEL_DAILY", "")

# Lightweight endpoints that extend the session without heavy data transfer
KEEPALIVE_ENDPOINTS = [
    "/userprofile-service/socialProfile",
    "/proxy/usersummary-service/usersummary/daily/{}",  # today's date
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "NK": "NT",
    "Origin": GARMIN_BASE,
    "Referer": f"{GARMIN_BASE}/modern/",
}


# ---------------------------------------------------------------------------
# Alerting
# ---------------------------------------------------------------------------


def alert_slack(message: str):
    """Post an alert to #ascent-daily. Best-effort, never raises."""
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_DAILY:
        log.warning("Slack not configured — alert not sent: %s", message)
        return
    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"channel": SLACK_CHANNEL_DAILY, "text": message},
            timeout=10,
        )
        data = resp.json()
        if not data.get("ok"):
            log.warning("Slack alert failed: %s", data.get("error"))
    except Exception as e:
        log.warning("Slack alert failed: %s", e)


# ---------------------------------------------------------------------------
# Cooldown (mirrors garmin_auth.py)
# ---------------------------------------------------------------------------


def _set_cooldown(reason: str):
    """Set rate limit cooldown."""
    COOLDOWN_FILE.parent.mkdir(exist_ok=True)
    data = {
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
    }
    COOLDOWN_FILE.write_text(json.dumps(data, indent=2))
    log.error("Rate limit cooldown set. Do NOT retry for 25 hours.")
    alert_slack(
        ":rotating_light: *Garmin 429 rate limit hit* during session keepalive. "
        "Cooldown set for 25 hours. All Garmin scripts blocked."
    )


# ---------------------------------------------------------------------------
# Cookie extraction
# ---------------------------------------------------------------------------


def extract_safari_cookies() -> dict | None:
    """Extract Garmin cookies from Safari's cookie store."""
    try:
        import browser_cookie3
    except ImportError:
        log.error("browser_cookie3 not installed: pip install browser-cookie3")
        return None

    try:
        jar = browser_cookie3.safari(domain_name=".garmin.com")
        cookies = {}
        for c in jar:
            if c.domain and "garmin" in c.domain:
                cookies[c.name] = c.value

        if not cookies:
            log.warning("No Garmin cookies in Safari")
            return None

        log.info("Extracted %d cookies from Safari", len(cookies))
        return cookies

    except Exception as e:
        log.error("Safari cookie extraction failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Session refresh
# ---------------------------------------------------------------------------


def refresh_session(cookies: dict) -> bool:
    """Make a lightweight Garmin API call to extend the session.

    This is the key operation — it extends the server-side session lifetime.
    Returns True if the session is alive, False if it's dead.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    for name, value in cookies.items():
        session.cookies.set(name, value, domain=".garmin.com")

    today = datetime.now().strftime("%Y-%m-%d")
    endpoints = [ep.format(today) for ep in KEEPALIVE_ENDPOINTS]

    for endpoint in endpoints:
        url = f"{GARMIN_BASE}{endpoint}"
        try:
            resp = session.get(url, timeout=15)

            if resp.status_code == 200:
                log.info("Session alive — %s returned 200", endpoint)
                return True
            elif resp.status_code == 401:
                log.warning("Session expired — %s returned 401", endpoint)
                return False
            elif resp.status_code == 403:
                log.warning("Blocked (Cloudflare?) — %s returned 403", endpoint)
                return False
            elif resp.status_code == 429:
                log.error("RATE LIMITED — %s returned 429. Stopping immediately.", endpoint)
                _set_cooldown("429 during session keepalive")
                return False
            else:
                log.info("Endpoint %s returned %d, trying next", endpoint, resp.status_code)
                continue

        except requests.RequestException as e:
            log.warning("Request to %s failed: %s", endpoint, e)
            continue

    log.warning("All keepalive endpoints failed")
    return False


# ---------------------------------------------------------------------------
# Cache + status management
# ---------------------------------------------------------------------------


def cache_cookies(cookies: dict, session_alive: bool):
    """Save cookies and status to cache files."""
    # Cookie cache (read by garmin_auth.py)
    data = {
        "cookies": cookies,
        "timestamp": time.time(),
        "source": "safari_extraction",
        "session_verified": session_alive,
    }
    COOKIE_CACHE.write_text(json.dumps(data, indent=2))

    # Status file
    failures = _get_failure_count()
    status = {
        "last_check": datetime.now(timezone.utc).isoformat(),
        "session_alive": session_alive,
        "cookie_count": len(cookies),
        "consecutive_failures": 0 if session_alive else failures + 1,
    }
    if session_alive:
        status["last_success"] = datetime.now(timezone.utc).isoformat()
    STATUS_FILE.write_text(json.dumps(status, indent=2))


def _get_failure_count() -> int:
    """Get the current consecutive failure count."""
    if STATUS_FILE.exists():
        try:
            data = json.loads(STATUS_FILE.read_text())
            return data.get("consecutive_failures", 0)
        except (json.JSONDecodeError, OSError):
            pass
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Garmin session keep-alive")
    parser.add_argument("--status", action="store_true", help="Just check status")
    args = parser.parse_args()

    if args.status:
        if STATUS_FILE.exists():
            data = json.loads(STATUS_FILE.read_text())
            print(json.dumps(data, indent=2))
        else:
            print("No status file found. Run without --status first.")
        return

    # Step 1: Extract cookies from Safari
    cookies = extract_safari_cookies()
    if not cookies:
        failures = _get_failure_count() + 1
        cache_cookies({}, session_alive=False)

        if failures >= 3:  # 3 consecutive failures = ~12 hours without cookies
            alert_slack(
                f":warning: *Garmin Safari cookies unavailable* for "
                f"{failures} consecutive checks (~{failures * 4}h).\n"
                f"Log into connect.garmin.com in Safari to restore the session."
            )
        sys.exit(1)

    # Step 2: Refresh session (hits Garmin API to extend session lifetime)
    alive = refresh_session(cookies)

    # Step 3: Cache cookies regardless (may still be valid even if verify hiccup)
    cache_cookies(cookies, session_alive=alive)

    if alive:
        log.info("Session refreshed successfully. Next check in 4 hours.")
    else:
        failures = _get_failure_count()
        log.warning("Session appears dead (%d consecutive failures)", failures)

        if failures >= 2:  # 2 failures = ~8 hours dead
            alert_slack(
                f":warning: *Garmin session dead* for {failures} consecutive "
                f"checks (~{failures * 4}h).\n"
                f"Log into connect.garmin.com in Safari to restore."
            )
        sys.exit(1)


if __name__ == "__main__":
    main()

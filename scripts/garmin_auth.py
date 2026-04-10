#!/usr/bin/env python3
"""Garmin auth via Playwright browser session.

Garmin's connectapi.garmin.com gateway validates JWT_WEB against a paired
HttpOnly+partitioned cookie (JWT_FGP) that no Python HTTP client can read.
The only auth path that works is making the requests from inside a real
browser process. This module loads a saved Playwright storage_state into
a headless Firefox and monkey-patches garminconnect.Client._run_request
to route every API call through the browser.

Public API (stable for callers like garmin_sync.py, garmin_workout_push.py,
mobility_workout.py, scale_sync.py, health_check.py):

    get_safe_client(require_garminconnect=True) -> Garmin
    save_tokens(client) -> None        # no-op (storage_state is the only persistence)
    alert_slack(message) -> None
    AuthExpiredError, RateLimitCooldownError
    check_cooldown() -> (locked, hours_remaining)
    record_cooldown(reason)
    clear_cooldown()

The cooldown machinery is kept as defense-in-depth, but the browser path
should never trip it (no plain HTTP login flows = no Cloudflare 429s).
"""

import json
import logging
import os
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

log = logging.getLogger("garmin_auth")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GARTH_HOME = Path.home() / ".garth"
COOLDOWN_FILE = GARTH_HOME / ".auth_cooldown"
COOLDOWN_HOURS = 25

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_DAILY = os.environ.get("SLACK_CHANNEL_DAILY", "")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AuthExpiredError(Exception):
    """Raised when the saved browser session is no longer valid."""


class RateLimitCooldownError(Exception):
    """Raised when we're still in a rate limit cooldown period."""


# ---------------------------------------------------------------------------
# Cooldown lock (kept as defense-in-depth)
# ---------------------------------------------------------------------------


def check_cooldown() -> tuple[bool, float]:
    """Return (is_locked, hours_remaining)."""
    if not COOLDOWN_FILE.exists():
        return False, 0.0
    try:
        data = json.loads(COOLDOWN_FILE.read_text())
        ts = data.get("locked_at") or data.get("timestamp", "")
        locked_at = datetime.fromisoformat(ts)
        if locked_at.tzinfo is None:
            locked_at = locked_at.replace(tzinfo=timezone.utc)
        elapsed = datetime.now(timezone.utc) - locked_at
        remaining = timedelta(hours=COOLDOWN_HOURS) - elapsed
        if remaining.total_seconds() > 0:
            return True, remaining.total_seconds() / 3600
        COOLDOWN_FILE.unlink(missing_ok=True)
        return False, 0.0
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        log.warning("Corrupted cooldown file, removing: %s", e)
        COOLDOWN_FILE.unlink(missing_ok=True)
        return False, 0.0


def check_cooldown_or_raise() -> None:
    locked, hours = check_cooldown()
    if locked:
        raise RateLimitCooldownError(
            f"Rate limit cooldown active. {hours:.1f} hours remaining. "
            f"Do NOT retry until cooldown expires."
        )


def record_cooldown(reason: str = "unknown") -> None:
    COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
    }
    COOLDOWN_FILE.write_text(json.dumps(data, indent=2))
    expires = datetime.now(timezone.utc) + timedelta(hours=COOLDOWN_HOURS)
    log.warning(
        "Rate limit cooldown set. Next safe attempt: %s",
        expires.strftime("%Y-%m-%d %H:%M UTC"),
    )


def clear_cooldown() -> None:
    COOLDOWN_FILE.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Slack alerting
# ---------------------------------------------------------------------------


def alert_slack(message: str) -> None:
    """Best-effort Slack notification. Never raises."""
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_DAILY:
        log.warning("Slack not configured — alert not sent: %s", message)
        return
    try:
        import requests as _requests
        resp = _requests.post(
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
        else:
            log.info("Slack alert sent to #ascent-daily")
    except Exception as e:
        log.warning("Slack alert failed: %s", e)


# ---------------------------------------------------------------------------
# Browser-session auth (the only auth path)
# ---------------------------------------------------------------------------


def _patched_run_request(browser_session):
    """Build a _run_request replacement that routes through Playwright.

    Returns a function with the same signature as
    garminconnect.Client._run_request: (self, method, path, **kwargs).

    Translates the library's requests-style kwargs (params, json, data,
    headers, timeout) into BrowserSession.fetch arguments.
    """
    from garminconnect.exceptions import GarminConnectConnectionError

    class _EmptyJSONResp:
        status_code = 204
        content = b""

        def json(self):  # noqa: D401
            return {}

        def __repr__(self):
            return "{}"

        def __str__(self):
            return "{}"

    def _run_request(self, method: str, path: str, **kwargs):
        url = f"{self._connectapi}/{path.lstrip('/')}"
        timeout = kwargs.pop("timeout", 15)
        headers = kwargs.pop("headers", None)
        params = kwargs.pop("params", None)
        json_body = kwargs.pop("json", None)
        data = kwargs.pop("data", None)
        # Drop anything else (e.g., 'api', 'allow_redirects') silently —
        # Playwright follows redirects by default and we don't need the rest.

        resp = browser_session.fetch(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json_body=json_body,
            data=data,
            timeout=timeout,
        )

        if resp.status_code == 204:
            return _EmptyJSONResp()

        if resp.status_code >= 400:
            error_msg = f"API Error {resp.status_code}"
            try:
                err_data = resp.json()
                if isinstance(err_data, dict):
                    msg = err_data.get("message") or err_data.get("error")
                    if msg:
                        error_msg += f" - {msg}"
            except Exception:
                if len(resp.text) < 500:
                    error_msg += f" - {resp.text}"
            raise GarminConnectConnectionError(error_msg)

        return resp

    return _run_request


def _try_browser_session():
    """Build an authenticated garminconnect.Garmin backed by Playwright.

    Returns a Garmin client whose every API call routes through a headless
    Firefox carrying the saved storage_state. Returns None on failure.
    """
    try:
        from garminconnect import Garmin
    except ImportError as e:
        log.error("garminconnect not installed: %s", e)
        return None

    try:
        from garmin_browser_session import (
            BrowserSession,
            StorageStateMissingError,
        )
    except ImportError as e:
        log.error("garmin_browser_session not importable: %s", e)
        return None

    try:
        session = BrowserSession()
    except StorageStateMissingError as e:
        log.warning("Browser session: %s", e)
        return None
    except Exception as e:
        log.error("Browser session: failed to launch Playwright: %s", e)
        return None

    garmin = Garmin()
    # Override the API host. The library defaults to connectapi.garmin.com
    # which is a different (cross-origin) gateway that the browser session
    # cannot authenticate against. The web SPA uses connect.garmin.com/gc-api
    # as a same-origin proxy and the gc-api gateway accepts our session
    # cookie + CSRF token. Routing all calls through that host is mandatory.
    from garmin_browser_session import GC_API_HOST
    garmin.client._connectapi = GC_API_HOST

    # Monkey-patch the one method that actually does HTTP. Every higher-level
    # method (get_stats, get_sleep_data, connectapi(...), request(...), etc.)
    # routes through _run_request, so this is the minimal-surface intercept.
    garmin.client._run_request = types.MethodType(
        _patched_run_request(session), garmin.client
    )

    # Verify + resolve display_name via socialProfile (the same call the
    # web SPA makes on dashboard load).
    try:
        prof = garmin.client.connectapi("/userprofile-service/socialProfile")
    except Exception as e:
        log.error("Browser session: socialProfile verify failed: %s", e)
        return None

    if not isinstance(prof, dict):
        log.error("Browser session: socialProfile returned non-dict: %r", prof)
        return None

    garmin.display_name = prof.get("displayName")
    garmin.full_name = prof.get("fullName", "")
    if not garmin.display_name:
        log.error("Browser session: socialProfile missing displayName")
        return None

    log.info(
        "Auth: browser session resume succeeded (display_name=%s)",
        garmin.display_name,
    )
    return garmin


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def get_safe_client(require_garminconnect: bool = True):
    """Return an authenticated Garmin client backed by a browser session.

    Args:
        require_garminconnect: Kept for backward-compat with old callers.
            Always returns a garminconnect.Garmin instance now.

    Raises:
        RateLimitCooldownError: cooldown lock is active
        AuthExpiredError: storage state missing or invalid
    """
    check_cooldown_or_raise()

    client = _try_browser_session()
    if client:
        return client

    alert_slack(
        ":warning: *Garmin auth failed* — browser session expired or missing.\n"
        "Run: `cd ~/projects/ascent && source venv/bin/activate && "
        "python3 scripts/garmin_browser_bootstrap.py`"
    )
    raise AuthExpiredError(
        "Browser session unavailable.\n"
        "Re-run the bootstrap to capture a fresh storage state:\n"
        "  cd ~/projects/ascent && source venv/bin/activate && "
        "python3 scripts/garmin_browser_bootstrap.py"
    )


def get_garmin_client():
    """Backward-compatible wrapper. Prefer get_safe_client()."""
    return get_safe_client(require_garminconnect=True)


def save_tokens(client) -> None:
    """No-op. Persistence lives in the Playwright storage_state file,
    which is written by garmin_browser_bootstrap.py — not by sync runs.

    Kept as a stub so existing callers (garmin_sync.py, garmin_workout_push.py)
    don't need to change.
    """
    return None


# ---------------------------------------------------------------------------
# CLI — auth status check
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    print("=== Garmin Auth Status Check ===\n")

    locked, hours = check_cooldown()
    if locked:
        print(f"RATE LIMIT COOLDOWN ACTIVE — {hours:.1f} hours remaining")
        sys.exit(3)
    print("No rate limit cooldown active\n")

    storage_paths = [
        Path.home() / ".garminconnect" / "garmin_storage_state.json",
        PROJECT_ROOT / ".garminconnect" / "garmin_storage_state.json",
    ]
    found = False
    for sp in storage_paths:
        if sp.exists():
            mtime = datetime.fromtimestamp(sp.stat().st_mtime, tz=timezone.utc)
            age = datetime.now(timezone.utc) - mtime
            print(f"  [ok] Storage state: {sp} (age: {age.total_seconds()/3600:.1f}h)")
            found = True
            break
    if not found:
        print("  [--] No storage state found")
        print("       Run: python3 scripts/garmin_browser_bootstrap.py")
        sys.exit(2)

    print()
    print("Attempting browser session resume...")
    try:
        client = get_safe_client()
        print(f"\nAuthentication successful!")
        print(f"  display_name: {client.display_name}")
        print(f"  full_name:    {client.full_name}")
    except AuthExpiredError as e:
        print(f"\nFAIL: {e}")
        sys.exit(2)
    except RateLimitCooldownError as e:
        print(f"\n{e}")
        sys.exit(3)

#!/usr/bin/env python3
"""Garmin auth safety layer — prevents accidental rate limit burns.

This module wraps all Garmin authentication for Ascent scripts.
It enforces three rules:
  1. NEVER call login() with credentials
  2. Cookie/token resume only — fail loudly if expired
  3. Cooldown lock file prevents retries within 25 hours of a failed auth

Auth priority:
  1. Cached cookies from ~/.garmin-cookies.json (written by keepalive script)
  2. Live Safari cookie extraction via browser_cookie3
  3. Saved garth OAuth tokens from ~/.garth/ (garth.resume, no network)
  4. FAIL → Slack alert to #ascent-daily + raise AuthExpiredError

Usage:
    from garmin_auth import get_safe_client, AuthExpiredError, RateLimitCooldownError

    try:
        client = get_safe_client()
    except RateLimitCooldownError as e:
        log.error(str(e))
        sys.exit(3)
    except AuthExpiredError as e:
        log.error(str(e))
        sys.exit(2)

NEVER calls garth.login(), client.login(), or any SSO endpoint.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

log = logging.getLogger("garmin_auth")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GARTH_HOME = Path.home() / ".garth"
GARTH_TOKEN_DIR = PROJECT_ROOT / ".garth"
COOLDOWN_FILE = GARTH_HOME / ".auth_cooldown"
COOLDOWN_HOURS = 25

# Cookie cache written by garmin_session_keepalive.py
COOKIE_CACHE = Path.home() / ".garmin-cookies.json"
# Legacy token file written by garmin_session_refresh.sh
LEGACY_TOKEN_FILE = PROJECT_ROOT / "garmin_tokens.json"
# Session status file written by keepalive script
STATUS_FILE = Path.home() / ".garmin-session-status.json"

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_DAILY = os.environ.get("SLACK_CHANNEL_DAILY", "")

# Browser-like headers for Cloudflare + Garmin API compatibility
BROWSER_HEADERS = {
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
    "Origin": "https://connect.garmin.com",
    "Referer": "https://connect.garmin.com/modern/",
}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AuthExpiredError(Exception):
    """Raised when all safe auth methods have failed."""
    pass


class RateLimitCooldownError(Exception):
    """Raised when we're still in a rate limit cooldown period."""
    pass


# ---------------------------------------------------------------------------
# Cooldown lock
# ---------------------------------------------------------------------------


def check_cooldown() -> tuple[bool, float]:
    """Check if we're in a rate limit cooldown period.

    Returns (is_locked, hours_remaining).
    """
    if not COOLDOWN_FILE.exists():
        return False, 0.0

    try:
        data = json.loads(COOLDOWN_FILE.read_text())
        ts = data.get("locked_at") or data.get("timestamp", "")
        locked_at = datetime.fromisoformat(ts)
        # Ensure timezone-aware
        if locked_at.tzinfo is None:
            locked_at = locked_at.replace(tzinfo=timezone.utc)
        elapsed = datetime.now(timezone.utc) - locked_at
        remaining = timedelta(hours=COOLDOWN_HOURS) - elapsed

        if remaining.total_seconds() > 0:
            return True, remaining.total_seconds() / 3600

        # Cooldown expired — remove lock file
        COOLDOWN_FILE.unlink(missing_ok=True)
        return False, 0.0

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        log.warning("Corrupted cooldown file, removing: %s", e)
        COOLDOWN_FILE.unlink(missing_ok=True)
        return False, 0.0


def check_cooldown_or_raise():
    """Raise RateLimitCooldownError if we're in cooldown."""
    locked, hours = check_cooldown()
    if locked:
        raise RateLimitCooldownError(
            f"Rate limit cooldown active. {hours:.1f} hours remaining. "
            f"Do NOT retry until cooldown expires."
        )


def record_cooldown(reason: str = "unknown"):
    """Record a rate limit event. All scripts must check this before auth."""
    COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
    }
    COOLDOWN_FILE.write_text(json.dumps(data, indent=2))
    expires = datetime.now(timezone.utc) + timedelta(hours=COOLDOWN_HOURS)
    log.warning("Rate limit cooldown set. Next safe attempt: %s",
                expires.strftime("%Y-%m-%d %H:%M UTC"))


def clear_cooldown():
    """Clear the cooldown (e.g., after confirmed successful auth)."""
    COOLDOWN_FILE.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Slack alerting
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
            json={
                "channel": SLACK_CHANNEL_DAILY,
                "text": message,
            },
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
# Auth Method 1: Cached cookies (from keepalive script)
# ---------------------------------------------------------------------------


def _try_cached_cookies() -> dict | None:
    """Load cookies from the cache file (written by session keepalive script)."""
    if not COOKIE_CACHE.exists():
        # Try legacy token file as fallback
        if LEGACY_TOKEN_FILE.exists():
            try:
                data = json.loads(LEGACY_TOKEN_FILE.read_text())
                cookies = data.get("cookies", {})
                if cookies and data.get("jwt_web"):
                    log.info("Auth: loaded cookies from legacy garmin_tokens.json")
                    return cookies
            except (json.JSONDecodeError, OSError):
                pass
        return None

    try:
        data = json.loads(COOKIE_CACHE.read_text())

        # Check freshness — cookies older than 6 hours are suspect
        if "timestamp" in data:
            age_hours = (time.time() - data["timestamp"]) / 3600
            if age_hours > 6:
                log.warning("Cached cookies are %.1f hours old — may be stale", age_hours)

        cookies = data.get("cookies", data)
        if not cookies or not isinstance(cookies, dict):
            return None

        log.info("Auth: loaded %d cached cookies", len(cookies))
        return cookies

    except (json.JSONDecodeError, OSError) as e:
        log.debug("Cookie cache load failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Auth Method 2: Live Safari cookie extraction
# ---------------------------------------------------------------------------


def _try_safari_cookies() -> dict | None:
    """Extract Garmin session cookies directly from Safari.

    Requires: pip install browser-cookie3
    Returns dict of cookies or None if unavailable.
    """
    try:
        import browser_cookie3
    except ImportError:
        log.debug("browser_cookie3 not installed, skipping live Safari extraction")
        return None

    try:
        cookie_jar = browser_cookie3.safari(domain_name=".garmin.com")
        cookies = {}
        for cookie in cookie_jar:
            if cookie.domain and "garmin" in cookie.domain:
                cookies[cookie.name] = cookie.value

        if not cookies:
            log.debug("No Garmin cookies found in Safari")
            return None

        # Check for essential session cookies
        essential = ["GARMIN-SSO-GUID", "GARMIN-SSO-CUST-GUID", "JWT_FGP", "SESSIONID"]
        has_session = any(k in cookies for k in essential)
        if not has_session:
            log.debug("Safari cookies found but no session cookies (%d total)", len(cookies))
            return None

        log.info("Auth: extracted %d cookies from Safari (live)", len(cookies))

        # Cache them for other scripts / next run
        _cache_cookies(cookies)
        return cookies

    except Exception as e:
        log.debug("Safari cookie extraction failed: %s", e)
        return None


def _cache_cookies(cookies: dict):
    """Save cookies to cache file for use by other scripts."""
    try:
        data = {
            "cookies": cookies,
            "timestamp": time.time(),
            "source": "safari_extraction",
        }
        COOKIE_CACHE.write_text(json.dumps(data, indent=2))
        log.debug("Cookies cached to %s", COOKIE_CACHE)
    except OSError as e:
        log.warning("Failed to cache cookies: %s", e)


# ---------------------------------------------------------------------------
# Auth Method 3: Saved garth OAuth tokens
# ---------------------------------------------------------------------------


def _try_garth_tokens():
    """Resume a garth session from saved OAuth tokens.

    These tokens auto-refresh for ~1 year. Does NOT call login().
    Returns a garth client or None.
    """
    try:
        import garth

        # Check both project-local and home directory for tokens
        for token_dir in [str(GARTH_TOKEN_DIR), str(GARTH_HOME)]:
            oauth_file = Path(token_dir) / "oauth2_token.json"
            if not oauth_file.exists():
                continue

            try:
                garth.resume(token_dir)
                garth.client.username  # verify tokens loaded
                log.info("Auth: garth.resume() succeeded from %s", token_dir)
                return garth.client
            except Exception as e:
                log.debug("garth.resume() from %s failed: %s", token_dir, e)
                continue

        log.info("Auth: no valid garth OAuth tokens found")
        return None

    except Exception as e:
        log.warning("Auth: garth token resume failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Session building + verification
# ---------------------------------------------------------------------------


def _build_cookie_session(cookies: dict) -> requests.Session:
    """Build a requests.Session with Garmin cookies and browser-like headers."""
    session = requests.Session()

    for name, value in cookies.items():
        session.cookies.set(name, value, domain=".garmin.com")

    session.headers.update(BROWSER_HEADERS)
    return session


def _verify_session(session: requests.Session) -> bool:
    """Verify a cookie-based session works by hitting a lightweight endpoint.

    Also detects 429 rate limits and sets cooldown automatically.
    """
    try:
        resp = session.get(
            "https://connect.garmin.com/userprofile-service/socialProfile",
            timeout=15,
        )
        if resp.status_code == 200:
            log.info("Auth: cookie session verified")
            return True
        elif resp.status_code == 429:
            log.error("Auth: RATE LIMITED (429) during session verification!")
            record_cooldown("429 on session verification")
            alert_slack(
                ":rotating_light: *Garmin 429 rate limit hit* during session verify. "
                "Cooldown set for 25 hours. Do NOT retry."
            )
            return False
        elif resp.status_code in (401, 403):
            log.warning("Auth: session expired or blocked (status %d)", resp.status_code)
            return False
        else:
            log.warning("Auth: session verification returned %d", resp.status_code)
            return False

    except Exception as e:
        log.warning("Auth: session verification failed: %s", e)
        return False


def _wrap_garminconnect(session=None, garth_client=None, method="unknown"):
    """Create a garminconnect.Garmin client from an existing session or garth client.

    NEVER calls login().
    """
    from garminconnect import Garmin

    client = Garmin()

    if garth_client:
        client.client = garth_client
        client.display_name = getattr(garth_client, "username", None) or method
        log.info("Garmin client created via %s", method)
        return client

    if session:
        # Inject cookie session into garth for garminconnect compatibility
        import garth
        for name in session.cookies.keys():
            garth.client.sess.cookies.set(
                name, session.cookies[name], domain=".garmin.com"
            )
        garth.client.sess.headers.update(BROWSER_HEADERS)
        client.client = garth.client
        client.display_name = method
        log.info("Garmin client created via %s", method)
        return client

    raise AuthExpiredError("Cannot create Garmin client without auth")


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------


def get_safe_client(require_garminconnect: bool = True):
    """Get an authenticated Garmin client using ONLY safe auth methods.

    Auth priority:
      1. Cached cookies (from keepalive script) — fastest, most reliable
      2. Live Safari cookie extraction — fallback
      3. Saved garth OAuth tokens — backup

    NEVER calls login(). If all methods fail, raises AuthExpiredError.

    Args:
        require_garminconnect: If True (default), returns a garminconnect.Garmin
            client. If False, returns a requests.Session with cookies set.

    Returns:
        Authenticated client (Garmin or requests.Session)

    Raises:
        AuthExpiredError: All safe auth methods failed
        RateLimitCooldownError: In rate limit cooldown
    """
    check_cooldown_or_raise()

    # Method 1: Cached cookies (fastest)
    cookies = _try_cached_cookies()
    if cookies:
        session = _build_cookie_session(cookies)
        if _verify_session(session):
            if require_garminconnect:
                return _wrap_garminconnect(session=session, method="cached_cookies")
            return session

    # Method 2: Live Safari cookie extraction
    cookies = _try_safari_cookies()
    if cookies:
        session = _build_cookie_session(cookies)
        if _verify_session(session):
            if require_garminconnect:
                return _wrap_garminconnect(session=session, method="safari_cookies")
            return session

    # Method 3: Saved garth tokens
    garth_client = _try_garth_tokens()
    if garth_client:
        if require_garminconnect:
            return _wrap_garminconnect(garth_client=garth_client, method="garth_tokens")
        return garth_client

    # All methods failed — alert and raise
    alert_slack(
        ":warning: *Garmin auth failed* — all methods exhausted.\n"
        "• Cached cookies: expired or missing\n"
        "• Safari cookies: not available\n"
        "• garth OAuth tokens: expired or missing\n"
        "\n*Action needed:* Log into Garmin Connect in Safari, "
        "then wait for keepalive to refresh cookies."
    )
    raise AuthExpiredError(
        "All Garmin auth methods failed.\n"
        "Options:\n"
        "  1. Log into connect.garmin.com in Safari (refreshes cookies)\n"
        "  2. Run garmin_browser_auth.py for new OAuth tokens\n"
        "Do NOT run any script with login() or credential-based auth."
    )


# Keep backward-compatible aliases
def get_garmin_client():
    """Backward-compatible wrapper. Prefer get_safe_client()."""
    return get_safe_client(require_garminconnect=True)


def save_tokens(client):
    """Save garth tokens after a successful session. Safe, no network."""
    import garth
    try:
        garth.save(str(GARTH_TOKEN_DIR))
        log.info("Tokens saved to %s", GARTH_TOKEN_DIR)
    except Exception as e:
        log.warning("Failed to save tokens: %s", e)


# ---------------------------------------------------------------------------
# CLI — auth status check
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    print("=== Garmin Auth Status Check ===\n")

    # Check cooldown
    locked, hours = check_cooldown()
    if locked:
        print(f"RATE LIMIT COOLDOWN ACTIVE — {hours:.1f} hours remaining")
        print("Do not attempt any Garmin auth until cooldown expires.")
        sys.exit(3)
    else:
        print("No rate limit cooldown active\n")

    # Check each auth method
    print("Checking auth methods:\n")

    cookies = _try_cached_cookies()
    if cookies:
        print(f"  [ok] Cached cookies: {len(cookies)} cookies found")
    else:
        print("  [--] Cached cookies: not available")

    cookies = _try_safari_cookies()
    if cookies:
        print(f"  [ok] Safari cookies: {len(cookies)} cookies extracted")
    else:
        print("  [--] Safari cookies: not available")

    garth_client = _try_garth_tokens()
    if garth_client:
        print("  [ok] Garth OAuth tokens: valid")
    else:
        print("  [--] Garth OAuth tokens: not available or expired")

    print()

    # Try full auth
    try:
        client = get_safe_client()
        print("Authentication successful!")
    except AuthExpiredError as e:
        print(f"All auth methods failed:\n{e}")
        sys.exit(2)
    except RateLimitCooldownError as e:
        print(f"{e}")
        sys.exit(3)

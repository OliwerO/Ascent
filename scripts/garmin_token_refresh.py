#!/usr/bin/env python3
"""Refresh Garmin tokens from Firefox SSO cookies.

Reads Firefox's SSO cookies (CASTGC, GARMIN-SSO, etc.) and uses them
to fetch a fresh JWT_WEB + CSRF from connect.garmin.com. No browser
interaction needed — Python requests handles the refresh silently.

Firefox just needs to be logged into Garmin Connect once and stay open
(so the CASTGC session cookie persists). Run every 90 min via launchd.

JWT_WEB expires every ~2 hours. SSO session cookies are essentially
permanent as long as Firefox stays open.
"""

import base64
import json
import logging
import re
import time
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("token_refresh")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = PROJECT_ROOT / ".garminconnect" / "garmin_tokens.json"
HOME_TOKEN_FILE = Path.home() / ".garminconnect" / "garmin_tokens.json"
STATUS_FILE = Path.home() / ".garmin-session-status.json"
COOKIE_CACHE = Path.home() / ".garmin-cookies.json"


def extract_firefox_cookies() -> dict | None:
    """Extract Garmin SSO cookies from Firefox (local file read, no network)."""
    try:
        import browser_cookie3
        jar = browser_cookie3.firefox(domain_name=".garmin.com")
        cookies = {c.name: c.value for c in jar if c.domain and "garmin" in c.domain}
        if cookies and ("GARMIN-SSO-CUST-GUID" in cookies or "session" in cookies):
            return cookies
        log.info("Firefox has %d Garmin cookies but no SSO session", len(cookies))
        return None
    except Exception as e:
        log.warning("Firefox cookie extraction failed: %s", e)
        return None


def fetch_fresh_jwt(cookies: dict) -> tuple[str | None, str | None, dict]:
    """Use SSO cookies to get a fresh JWT_WEB + CSRF from Garmin Connect.

    This is a normal page load — Garmin's server sees the SSO cookies
    and issues a fresh JWT. No login flow, no SSO endpoint, no rate limit risk.
    """
    try:
        import browser_cookie3
        jar = browser_cookie3.firefox(domain_name=".garmin.com")
        s = requests.Session()
        s.cookies = jar
        s.headers["User-Agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) "
            "Gecko/20100101 Firefox/128.0"
        )

        resp = s.get("https://connect.garmin.com/modern/", timeout=15)
        if resp.status_code != 200:
            log.warning("Page load returned %d", resp.status_code)
            return None, None, cookies

        # Extract fresh JWT from response cookies
        jwt_web = None
        all_cookies = {c.name: c.value for c in s.cookies if c.domain and "garmin" in c.domain}
        jwt_web = all_cookies.get("JWT_WEB")

        # Extract CSRF from page HTML (uses shared parser from garmin_auth)
        csrf = None
        try:
            from garmin_auth import extract_csrf_token
            csrf = extract_csrf_token(resp.text)
        except ImportError:
            m = re.search(r'csrf-token"\s+content="([^"]+)"', resp.text)
            if m:
                csrf = m.group(1)

        return jwt_web, csrf, all_cookies

    except Exception as e:
        log.warning("Fresh JWT fetch failed: %s", e)
        return None, None, cookies


def save_tokens(jwt_web: str, csrf: str, cookies: dict):
    """Save tokens to disk for garmin_auth.py and garmin_sync.py."""
    token_data = {"jwt_web": jwt_web, "csrf_token": csrf, "cookies": cookies}
    for path in [TOKEN_FILE, HOME_TOKEN_FILE]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(token_data, indent=2))

    COOKIE_CACHE.write_text(json.dumps({
        "cookies": cookies,
        "timestamp": time.time(),
        "source": "firefox_sso_refresh",
        "session_verified": True,
    }, indent=2))


def update_status(alive: bool, cookie_count: int, failures: int):
    """Update session status file."""
    STATUS_FILE.write_text(json.dumps({
        "last_check": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        "session_alive": alive,
        "cookie_count": cookie_count,
        "consecutive_failures": failures,
    }, indent=2))


def jwt_minutes_remaining() -> float:
    """Check how many minutes until the current saved JWT expires."""
    try:
        data = json.loads(HOME_TOKEN_FILE.read_text())
        jwt = data.get("jwt_web", "")
        if not jwt:
            return 0
        payload = jwt.split(".")[1] + "=="
        decoded = json.loads(base64.b64decode(payload))
        return (decoded["exp"] - time.time()) / 60
    except Exception:
        return 0


def main():
    remaining = jwt_minutes_remaining()
    log.info("Saved JWT has %.0f min remaining", remaining)

    # Step 1: Read SSO cookies from Firefox (local file, no network)
    cookies = extract_firefox_cookies()
    if not cookies:
        failures = 0
        if STATUS_FILE.exists():
            try:
                failures = json.loads(STATUS_FILE.read_text()).get("consecutive_failures", 0)
            except:
                pass
        update_status(False, 0, failures + 1)
        log.warning("No Firefox SSO cookies (failure #%d). Is Firefox logged into Garmin?", failures + 1)
        return

    # Step 2: Always fetch JWT + CSRF from Garmin Connect page
    # This uses Firefox's cookie jar (with SSO cookies) to load the page,
    # which gives us both a fresh JWT and the CSRF from the meta tag.
    jwt_web, csrf, all_cookies = fetch_fresh_jwt(cookies)

    # Fallback: if page fetch didn't return JWT, use Firefox's existing JWT
    if not jwt_web:
        jwt_web = cookies.get("JWT_WEB")
        if jwt_web:
            log.info("Page didn't return JWT, using Firefox's existing JWT")
            all_cookies = cookies

    if not jwt_web:
        update_status(False, len(cookies), 0)
        log.warning("No JWT available — SSO session may have expired")
        return

    if not csrf:
        log.warning("No CSRF from page — sync will fail with 403. Is Firefox logged in?")
        update_status(False, len(all_cookies), 0)
        return

    # Step 3: Save everything
    save_tokens(jwt_web, csrf, all_cookies)
    update_status(True, len(all_cookies), 0)

    try:
        payload = jwt_web.split(".")[1] + "=="
        decoded = json.loads(base64.b64decode(payload))
        remaining = (decoded["exp"] - time.time()) / 60
        log.info("Tokens refreshed: JWT valid for %.0f min, CSRF OK, %d cookies", remaining, len(all_cookies))
    except:
        log.info("Tokens refreshed: CSRF OK, %d cookies", len(all_cookies))


if __name__ == "__main__":
    main()

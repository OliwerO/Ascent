#!/usr/bin/env python3
"""Garmin session keeper — refreshes auth tokens using a persistent Playwright browser.

Runs periodically (every 4h via launchd) to keep the Garmin session alive.
Extracts fresh JWT + CSRF tokens and saves them for garmin_sync.py.

First run: opens a visible browser for manual login + MFA.
Subsequent runs: headless, uses saved session — no interaction needed.

Usage:
    python scripts/garmin_session_keeper.py           # normal (headless if session exists)
    python scripts/garmin_session_keeper.py --setup    # force visible browser for login
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = PROJECT_ROOT / "garmin_tokens.json"
BROWSER_PROFILE = PROJECT_ROOT / ".garmin-browser"
GARMIN_URL = "https://connect.garmin.com/modern/"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("garmin_session_keeper")


def extract_tokens(page, context) -> dict | None:
    """Extract JWT, CSRF, and cookies from a logged-in Garmin page."""
    # Get CSRF from meta tag
    csrf = None
    try:
        meta = page.query_selector('meta[name*="csrf" i], meta[content*="-"][name*="token" i]')
        if meta:
            csrf = meta.get_attribute("content")
    except Exception:
        pass

    if not csrf:
        try:
            content = page.content()
            match = re.search(r'<meta[^>]*csrf[^>]*content="([^"]+)"', content, re.IGNORECASE)
            if match:
                csrf = match.group(1)
        except Exception:
            pass

    # Get cookies
    cookies = context.cookies()
    cookie_dict = {}
    jwt_web = None
    for c in cookies:
        if "garmin" in c["domain"] or "connect" in c["domain"]:
            cookie_dict[c["name"]] = c["value"]
        if c["name"] == "JWT_WEB":
            jwt_web = c["value"]

    if not jwt_web or not csrf:
        return None

    return {
        "jwt_web": jwt_web,
        "csrf_token": csrf,
        "cookies": cookie_dict,
    }


def is_logged_in(page) -> bool:
    """Check if the current page shows a logged-in state."""
    url = page.url
    # If we're on the SSO login page, we're not logged in
    if "sso.garmin.com" in url:
        return False
    # If we're on connect.garmin.com with content, we're logged in
    if "connect.garmin.com" in url:
        # Check for the user avatar or navigation elements
        try:
            page.wait_for_selector('[class*="user"], [class*="avatar"], [class*="profile"]', timeout=5000)
            return True
        except Exception:
            # Check if page has the main app loaded
            return "Page Not Found" not in page.content() and len(page.content()) > 5000
    return False


def run_keeper(setup_mode: bool = False):
    """Main keeper logic."""
    profile_exists = BROWSER_PROFILE.exists() and any(BROWSER_PROFILE.iterdir())
    headless = not setup_mode and profile_exists

    if setup_mode:
        log.info("Setup mode: opening visible browser for login")
    elif not profile_exists:
        log.info("No browser profile found — opening visible browser for initial login")
        headless = False
    else:
        log.info("Refreshing Garmin session (headless)")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(BROWSER_PROFILE),
            headless=headless,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="en-US",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-first-run",
            ],
            ignore_default_args=["--enable-automation"],
        )

        # Apply stealth to avoid detection
        try:
            from playwright_stealth import stealth_sync
            for pg in context.pages:
                stealth_sync(pg)
        except ImportError:
            pass

        page = context.pages[0] if context.pages else context.new_page()
        try:
            from playwright_stealth import stealth_sync
            stealth_sync(page)
        except ImportError:
            pass

        log.info("Navigating to Garmin Connect...")
        try:
            page.goto(GARMIN_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            log.warning("Navigation timeout (may still be loading): %s", e)

        if not is_logged_in(page):
            if headless:
                log.error("Session expired — run with --setup to re-login")
                context.close()
                sys.exit(2)
            else:
                log.info("Please log in with your credentials and complete MFA...")
                log.info("Waiting for login to complete (timeout: 5 minutes)...")
                try:
                    page.wait_for_url("**/connect.garmin.com/**", timeout=300000)
                    # Give the page time to fully load after redirect
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass

                if not is_logged_in(page):
                    log.error("Login did not complete. Try again with --setup")
                    context.close()
                    sys.exit(1)

        log.info("Logged in — extracting tokens...")

        # Navigate to main page to get fresh CSRF
        try:
            page.goto(GARMIN_URL, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        tokens = extract_tokens(page, context)
        if tokens:
            TOKEN_FILE.write_text(json.dumps(tokens, indent=2))
            log.info("Tokens saved to %s", TOKEN_FILE)
            log.info("JWT: %s...", tokens["jwt_web"][:30])
            log.info("CSRF: %s", tokens["csrf_token"])
        else:
            log.error("Failed to extract tokens (JWT or CSRF missing)")
            context.close()
            sys.exit(1)

        context.close()
        log.info("Done")


def main():
    parser = argparse.ArgumentParser(description="Garmin session keeper")
    parser.add_argument("--setup", action="store_true", help="Force visible browser for login")
    args = parser.parse_args()
    run_keeper(setup_mode=args.setup)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""One-time interactive bootstrap for Garmin browser-session auth.

Opens a real Firefox window via Playwright, you log in manually (including
MFA if prompted), and the script saves Playwright's full storage_state to
~/.garminconnect/garmin_storage_state.json. The daily sync (garmin_auth.py
+ garmin_browser_session.py) loads this storage state into a *headless*
Firefox each run, inheriting the same cookie jar including JWT_FGP and
other partitioned cookies that no Python HTTP client can read.

This is the only way to authenticate with Garmin Connect since they
deployed JWT_FGP fingerprint-pair validation on connectapi.garmin.com.

Usage:
    cd ~/projects/ascent
    source venv/bin/activate
    python3 scripts/garmin_browser_bootstrap.py
    python3 scripts/garmin_browser_bootstrap.py --email other@gmail.com

Re-run when:
    - garmin_sync.py fails with AuthExpiredError
    - You see a "storage state expired" Slack alert
    - Garmin's session expires server-side (lifetime is currently unknown,
      we expect days-to-weeks based on JWT_WEB exp claim)
"""

import argparse
import base64
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

STORAGE_DIR = Path.home() / ".garminconnect"
STORAGE_PATH = STORAGE_DIR / "garmin_storage_state.json"
PROJECT_STORAGE_DIR = PROJECT_ROOT / ".garminconnect"
PROJECT_STORAGE_PATH = PROJECT_STORAGE_DIR / "garmin_storage_state.json"

# Garmin SSO URLs
SSO_BASE = "https://sso.garmin.com"
PORTAL_CLIENT_ID = "GarminConnect"
PORTAL_SERVICE_URL = "https://connect.garmin.com/app"

# ---------------------------------------------------------------------------
# Bot-detection avoidance (audit Phase 8 follow-up)
# ---------------------------------------------------------------------------
#
# A fixed-cadence headless refresh against the same SSO endpoint with the
# same user-agent is exactly the pattern Garmin's bot detection profiles.
# We mitigate two ways:
#
#   1. Time jitter: sleep a random 0–JITTER_MAX_S seconds at the start of
#      every headless run, BEFORE touching the network. launchd's
#      StartInterval has no native jitter; doing it in the script means
#      one tunable rather than two and works regardless of caller (launchd,
#      manual, future cron).
#
#   2. UA rotation: pick a UA from a small pool of plausible recent Firefox
#      builds on each run. Garmin's fingerprint cluster is (UA + IP +
#      cadence + cookie state) — varying any one of those makes the cluster
#      less coherent.
#
# Both can be disabled with --no-jitter (passes skip_jitter=True). Use for
# manual emergency refreshes when you don't want to wait up to 15 minutes.
# JITTER_MAX_S can be tuned via env var without a code change.

JITTER_MAX_S = int(os.environ.get("GARMIN_REFRESH_JITTER_MAX_S", "900"))

# Small pool of recent Firefox builds on macOS. Keep small (3-5) so the
# cluster doesn't widen so much that it looks artificial — real users
# update browsers slowly. Update this list when Firefox publishes new
# stable versions; stale UAs become flaggable on their own.
FIREFOX_UA_POOL = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.7; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.6; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:129.0) Gecko/20100101 Firefox/129.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:128.0) Gecko/20100101 Firefox/128.0",
]


def _decode_jwt_exp(jwt: str) -> datetime | None:
    """Decode the exp claim from a JWT (no signature verification)."""
    try:
        parts = jwt.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(int(exp), tz=timezone.utc)
    except Exception:
        return None
    return None


def _print_session_lifetime(storage_path: Path) -> None:
    """Decode JWT_WEB from storage_state and print its expiry."""
    try:
        data = json.loads(storage_path.read_text())
    except Exception as e:
        print(f"  (could not read storage state for lifetime check: {e})")
        return

    jwt_web = None
    for cookie in data.get("cookies", []):
        if cookie.get("name") == "JWT_WEB":
            jwt_web = cookie.get("value")
            break

    if not jwt_web:
        print("  WARNING: storage_state has no JWT_WEB cookie. Sync will fail.")
        return

    exp = _decode_jwt_exp(jwt_web)
    if exp:
        delta = exp - datetime.now(timezone.utc)
        days = delta.total_seconds() / 86400
        print(f"  JWT_WEB expires: {exp.isoformat()} ({days:.1f} days from now)")
    else:
        print("  JWT_WEB present but exp claim could not be decoded.")


def _save_storage_state(context, storage_path: Path = STORAGE_PATH) -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    PROJECT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(storage_path))
    # Mirror to the project dir under the same filename so either path resolves
    project_mirror = PROJECT_STORAGE_DIR / storage_path.name
    project_mirror.write_text(storage_path.read_text())
    print(f"Saved storage state to: {storage_path}")
    print(f"Saved storage state to: {project_mirror}")
    _print_session_lifetime(storage_path)

    # Clear any active cooldown — bootstrap success means we're fresh.
    for cf in [
        Path.home() / ".garth" / ".auth_cooldown",
        PROJECT_ROOT / ".garth" / ".auth_cooldown",
    ]:
        if cf.exists():
            try:
                cf.unlink()
                print(f"Cleared cooldown: {cf}")
            except OSError:
                pass


def bootstrap_headless(
    email: str,
    password: str,
    storage_path: Path = STORAGE_PATH,
    skip_jitter: bool = False,
) -> bool:
    """Headless re-login. Used by the launchd auto-refresh job.

    Returns True on success. Fails fast if MFA is required, the password is
    rejected, or anything unexpected happens — the user can then run the
    interactive `bootstrap()` manually.

    Bot-detection mitigation (see module docstring):
      - Sleeps a random 0..JITTER_MAX_S seconds before any network call
        (skip with skip_jitter=True for emergency manual refreshes).
      - Picks a random UA from FIREFOX_UA_POOL for the browser context.
    """
    from playwright.sync_api import sync_playwright

    try:
        from playwright_stealth import Stealth
        _stealth = Stealth()
    except Exception:
        _stealth = None

    # 1. Time jitter — BEFORE any network call so the actual SSO hit time
    #    is unpredictable from outside the host.
    if not skip_jitter and JITTER_MAX_S > 0:
        delay = random.randint(0, JITTER_MAX_S)
        print(f"[headless] jitter: sleeping {delay}s before refresh", flush=True)
        time.sleep(delay)

    # 2. UA rotation — picked once per run, used for the browser context.
    user_agent = random.choice(FIREFOX_UA_POOL)
    print(f"[headless] UA: {user_agent}", flush=True)

    login_url = (
        f"{SSO_BASE}/portal/sso/en-US/sign-in"
        f"?clientId={PORTAL_CLIENT_ID}"
        f"&service={PORTAL_SERVICE_URL}"
    )

    print(f"[headless] Refreshing Garmin session for {email}")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True, slow_mo=20)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            user_agent=user_agent,
        )
        page = context.new_page()
        if _stealth:
            try:
                _stealth.apply_stealth_sync(page)
            except Exception:
                pass

        try:
            # `domcontentloaded`, not `networkidle`: Garmin's SSO page keeps
            # background telemetry polling that prevents `networkidle` from
            # ever firing, hitting the 30s timeout. The login form is fully
            # interactive at DOMContentLoaded — we don't need to wait for all
            # background beacons to settle. (audit Phase 5/8 follow-up: this
            # is what broke the launchd auto-refresh chain on 2026-04-08.)
            page.goto(login_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"[headless] FAIL: navigate login page: {e}")
            browser.close()
            return False

        try:
            page.wait_for_selector(
                'input[name="username"], input[type="email"], #username',
                timeout=10000,
            ).fill(email)
            page.wait_for_selector(
                'input[name="password"], input[type="password"], #password',
                timeout=5000,
            ).fill(password)
            # Submit
            for sel in [
                'button[type="submit"]',
                'button#login-button-signin',
                'input[type="submit"]',
            ]:
                btn = page.query_selector(sel)
                if btn:
                    btn.click()
                    break
            else:
                page.keyboard.press("Enter")
        except Exception as e:
            print(f"[headless] FAIL: filling credentials: {e}")
            browser.close()
            return False

        # Wait for redirect to connect.garmin.com OR an MFA prompt
        deadline = time.time() + 45
        landed = False
        while time.time() < deadline:
            try:
                url = page.url
            except Exception:
                page.wait_for_timeout(500)
                continue
            if "connect.garmin.com" in url and "sso.garmin.com" not in url:
                landed = True
                break
            # MFA detection — query_selector can race in-flight navigations and
            # raise "Execution context was destroyed". Treat that as "not yet,
            # try again" rather than aborting the whole refresh.
            try:
                mfa = page.query_selector(
                    'input[name="code"], input[name="mfaCode"], #mfa-code'
                )
            except Exception:
                page.wait_for_timeout(500)
                continue
            if mfa:
                print("[headless] FAIL: MFA required — run interactive bootstrap manually.")
                browser.close()
                return False
            # Login error banner
            try:
                err = page.query_selector(".alert-danger, .login-error")
            except Exception:
                page.wait_for_timeout(500)
                continue
            if err:
                txt = (err.inner_text() or "").strip()[:120]
                print(f"[headless] FAIL: login error banner: {txt}")
                browser.close()
                return False
            page.wait_for_timeout(500)

        if not landed:
            print("[headless] FAIL: timed out waiting for connect.garmin.com")
            browser.close()
            return False

        # Trigger lazy session cookies
        for target in [
            "https://connect.garmin.com/modern/",
            "https://connect.garmin.com/modern/sleep",
        ]:
            try:
                page.goto(target, timeout=15000, wait_until="domcontentloaded")
                page.wait_for_timeout(1500)
            except Exception:
                pass

        try:
            _save_storage_state(context, storage_path=storage_path)
        finally:
            browser.close()
        return True


def bootstrap(email: str | None = None) -> None:
    from playwright.sync_api import sync_playwright

    # playwright_stealth hides anti-bot fingerprints (navigator.webdriver etc.)
    # Without it, Garmin's SSO page renders an "UNEXPECTED ERROR" banner.
    try:
        from playwright_stealth import Stealth
        _stealth = Stealth()
        _has_stealth = True
    except Exception as e:
        print(f"  WARNING: playwright_stealth unavailable ({e}); SSO may reject the page")
        _stealth = None
        _has_stealth = False

    login_url = (
        f"{SSO_BASE}/portal/sso/en-US/sign-in"
        f"?clientId={PORTAL_CLIENT_ID}"
        f"&service={PORTAL_SERVICE_URL}"
    )

    print("Garmin Browser Bootstrap")
    print("=" * 50)
    print(f"Email: {email or '(enter in browser)'}")
    print()
    print("A Firefox window will open to Garmin's login page.")
    print("Log in normally — including MFA if prompted.")
    print("The script auto-detects login and saves the session.")
    print()

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, slow_mo=50)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = context.new_page()

        if _has_stealth:
            try:
                _stealth.apply_stealth_sync(page)
            except Exception as e:
                print(f"  WARNING: stealth.apply_stealth_sync failed: {e}")

        print("Opening Garmin login page...")
        # Same fix as the headless path: avoid `networkidle`, Garmin's SSO
        # background polling never lets it fire.
        page.goto(login_url, wait_until="domcontentloaded")

        if email:
            try:
                el = page.wait_for_selector(
                    'input[name="username"], input[type="email"], #username',
                    timeout=5000,
                )
                if el:
                    el.fill(email)
                    print(f"Pre-filled email: {email}")
            except Exception:
                print("Could not pre-fill email — enter it manually.")

        print()
        print(">>> Log in to Garmin Connect in the browser window <<<")
        print(">>> Script auto-detects when you reach the dashboard <<<")
        print()

        max_wait = 600  # 10 minutes
        start = time.time()
        landed_at: float | None = None

        while time.time() - start < max_wait:
            try:
                current_url = page.url
            except Exception:
                break

            on_connect = (
                "connect.garmin.com" in current_url
                and "sso.garmin.com" not in current_url
            )

            if on_connect:
                if landed_at is None:
                    landed_at = time.time()
                    print("Login detected — landed on connect.garmin.com")
                    print("Letting page settle and triggering API calls...")
                    # Visit a few pages so any lazy session cookies get set
                    for target in [
                        "https://connect.garmin.com/modern/",
                        "https://connect.garmin.com/modern/sleep",
                        "https://connect.garmin.com/modern/activities",
                    ]:
                        try:
                            page.goto(target, timeout=15000, wait_until="domcontentloaded")
                            page.wait_for_timeout(1500)
                        except Exception as e:
                            print(f"  nav {target} failed: {e}")
                # Wait an extra few seconds after first landing for cookies to fully set
                if time.time() - landed_at >= 8:
                    break

            page.wait_for_timeout(500)
        else:
            print("Timed out waiting for login (10 minutes). Aborting.")
            browser.close()
            sys.exit(1)

        try:
            _save_storage_state(context)
        finally:
            browser.close()

    print()
    print("Done. Test the saved session with:")
    print("  python3 scripts/garmin_auth.py")
    print("Then run a sync with:")
    print("  python3 scripts/garmin_sync.py")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap Garmin browser session")
    parser.add_argument("--email", default=None, help="Pre-fill email in login form")
    parser.add_argument(
        "--headless", action="store_true",
        help="Headless re-login using GARMIN_EMAIL/GARMIN_PASSWORD from .env. "
             "Fails if MFA is required. Used by the launchd auto-refresh job.",
    )
    parser.add_argument(
        "--no-jitter", action="store_true",
        help="Skip the random 0..GARMIN_REFRESH_JITTER_MAX_S sleep at the "
             "start of headless refresh. Use for emergency manual runs when "
             "you need a fresh token immediately.",
    )
    args = parser.parse_args()

    email = args.email or os.environ.get("GARMIN_EMAIL")

    if args.headless:
        password = os.environ.get("GARMIN_PASSWORD")
        if not email or not password:
            print("[headless] FAIL: GARMIN_EMAIL/GARMIN_PASSWORD not set in .env")
            sys.exit(2)
        ok = bootstrap_headless(
            email, password,
            storage_path=STORAGE_PATH,
            skip_jitter=args.no_jitter,
        )
        sys.exit(0 if ok else 1)

    bootstrap(email)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Login to Garmin via WebKit (Safari engine) with stealth, extract OAuth tokens.

Uses Playwright WebKit which matches Safari's fingerprint, bypassing Cloudflare.
Opens a visible browser — log in manually if auto-fill doesn't work.
"""

import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

EMAIL = os.environ["GARMIN_EMAIL"]
PASSWORD = os.environ["GARMIN_PASSWORD"]
GARTH_TOKEN_DIR = PROJECT_ROOT / ".garth"


def run():
    with sync_playwright() as p:
        print("Launching Firefox...")
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Go directly to the new Garmin SSO portal
        print("Loading Garmin SSO...")
        page.goto("https://sso.garmin.com/portal/sso/en-US/sign-in?clientId=GarminConnect&service=https://connect.garmin.com/modern/")

        print("\n👤 Please log in manually in the browser window.")
        print("   Enter your email, password, and MFA code when prompted.")
        print("   The script will detect when login succeeds.\n")

        # Wait until we land on connect.garmin.com dashboard
        max_wait = 180  # 3 minutes
        start = time.time()
        logged_in = False
        while time.time() - start < max_wait:
            url = page.url
            if "connect.garmin.com/modern" in url and "sso" not in url.lower():
                # Verify it's actually the dashboard
                if page.title() and "Garmin" in page.title() and "Sign" not in page.title():
                    print(f"✅ Login successful! URL: {url}")
                    logged_in = True
                    break
            time.sleep(1)

        if not logged_in:
            print("⏰ Timeout. Please try again.")
            browser.close()
            return False

        # Give it a moment to settle
        time.sleep(2)

        # Now navigate to the SSO embed to trigger OAuth token generation
        print("\nExchanging session for OAuth tokens...")

        # Navigate to SSO embed — since we're logged in, it should auto-complete
        page.goto(
            "https://sso.garmin.com/sso/embed?"
            "id=gauth-widget&embedWidget=true"
            "&gauthHost=https://sso.garmin.com/sso"
        )
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        embed_html = page.content()
        title_match = re.search(r"<title>([^<]+)</title>", embed_html)
        title = title_match.group(1) if title_match else "unknown"
        print(f"SSO embed title: {title}")

        # Look for the response URL with ticket
        ticket_match = re.search(r"response_url\s*=\s*['\"]([^'\"]+)['\"]", embed_html)
        if not ticket_match:
            ticket_match = re.search(r"ticket=([A-Za-z0-9\-_]+)", embed_html)

        if ticket_match:
            ticket_url = ticket_match.group(1) if "http" in ticket_match.group(1) else None
            ticket = ticket_match.group(1) if not ticket_url else re.search(r"ticket=([^&]+)", ticket_url).group(1)
            print(f"Got ticket: {ticket[:30]}...")
        else:
            print("No ticket in embed page, trying signin redirect...")

            # Try the signin page — when logged in, it should auto-redirect with ticket
            page.goto(
                "https://sso.garmin.com/sso/signin?"
                "id=gauth-widget&embedWidget=true"
                "&gauthHost=https://sso.garmin.com/sso/embed"
                "&service=https://sso.garmin.com/sso/embed"
                "&source=https://sso.garmin.com/sso/embed"
                "&redirectAfterAccountLoginUrl=https://sso.garmin.com/sso/embed"
                "&redirectAfterAccountCreationUrl=https://sso.garmin.com/sso/embed"
            )
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            signin_html = page.content()
            title_match = re.search(r"<title>([^<]+)</title>", signin_html)
            title = title_match.group(1) if title_match else "unknown"
            print(f"Signin title: {title}")

        # Extract all cookies from the browser
        all_cookies = context.cookies()

        # Now use garth to complete the OAuth exchange with browser cookies
        import garth
        from garth.sso import get_title, _complete_login

        # Transfer ALL browser cookies to garth
        for cookie in all_cookies:
            garth.client.sess.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie.get("domain", ".garmin.com"),
                path=cookie.get("path", "/"),
            )

        # Also set proper headers
        garth.client.sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                          "Version/17.0 Safari/605.1.15",
        })

        # Try to get the SSO embed page via garth (should auto-succeed with session)
        try:
            resp = garth.client.get(
                "sso", "/sso/embed",
                params={
                    "id": "gauth-widget",
                    "embedWidget": "true",
                    "gauthHost": "https://sso.garmin.com/sso",
                },
            )
            title = get_title(resp.text)
            print(f"Garth SSO embed title: {title}")

            if title == "Success":
                garth.client.oauth1_token, garth.client.oauth2_token = _complete_login(garth.client)
                GARTH_TOKEN_DIR.mkdir(exist_ok=True)
                garth.save(str(GARTH_TOKEN_DIR))
                print(f"\n🎉 OAuth tokens saved to {GARTH_TOKEN_DIR}/")
                print(f"Username: {garth.client.username}")

                # Verify
                try:
                    profile = garth.client.connectapi("/userprofile-service/socialProfile")
                    print(f"Verified: {profile.get('displayName', 'OK')}")
                except:
                    pass

                browser.close()
                return True
            else:
                print(f"SSO embed didn't return Success, got: {title}")
                print("Trying alternative approach...")
        except Exception as e:
            print(f"Garth SSO failed: {e}")

        # Alternative: use signin page via garth
        try:
            SSO_EMBED = "https://sso.garmin.com/sso/embed"
            SIGNIN_PARAMS = {
                "id": "gauth-widget", "embedWidget": "true",
                "gauthHost": SSO_EMBED, "service": SSO_EMBED,
                "source": SSO_EMBED,
                "redirectAfterAccountLoginUrl": SSO_EMBED,
                "redirectAfterAccountCreationUrl": SSO_EMBED,
            }
            resp = garth.client.get("sso", "/sso/signin", params=SIGNIN_PARAMS, referrer=True)
            title = get_title(resp.text)
            print(f"Garth signin title: {title}")

            if title == "Success":
                garth.client.oauth1_token, garth.client.oauth2_token = _complete_login(garth.client)
                GARTH_TOKEN_DIR.mkdir(exist_ok=True)
                garth.save(str(GARTH_TOKEN_DIR))
                print(f"\n🎉 OAuth tokens saved to {GARTH_TOKEN_DIR}/")
                browser.close()
                return True
        except Exception as e:
            print(f"Signin also failed: {e}")

        # Last resort: save cookies for manual use
        GARTH_TOKEN_DIR.mkdir(exist_ok=True)
        with open(GARTH_TOKEN_DIR / "browser_cookies.json", "w") as f:
            json.dump(all_cookies, f, indent=2)
        print(f"\nCookies saved to {GARTH_TOKEN_DIR}/browser_cookies.json")

        browser.close()
        return False


if __name__ == "__main__":
    success = run()
    if success:
        print("\n✅ Done! garmin_sync.py will now work automatically.")
    else:
        print("\n❌ OAuth exchange failed, but cookies were saved.")
        raise SystemExit(1)

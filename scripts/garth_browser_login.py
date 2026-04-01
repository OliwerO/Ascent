#!/usr/bin/env python3
"""Bootstrap garth OAuth tokens via real browser login.

Bypasses API rate limits by using Playwright to automate a real
browser login (same as Safari). Extracts OAuth tokens after login
and saves them for garth/garmin_sync.py to reuse.

Usage:
    cd ~/projects/ascent && source venv/bin/activate
    python3 scripts/garth_browser_login.py

MFA: The browser will pause for you to enter the MFA code manually.
"""

import json
import os
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
        print("Launching browser...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                       "Version/17.0 Safari/605.1.15",
        )
        page = context.new_page()

        # Step 1: Go to Garmin SSO
        print("Loading Garmin SSO login page...")
        page.goto("https://sso.garmin.com/sso/signin?service=https://connect.garmin.com/modern/&gauthHost=https://sso.garmin.com/sso")
        page.wait_for_load_state("networkidle")

        # Step 2: Enter credentials
        print(f"Entering credentials for {EMAIL}...")
        # Handle iframe if present
        try:
            frame = page.frame_locator("#gauth-widget-frame-gauth-widget")
            email_field = frame.locator("#email")
            if email_field.count() > 0:
                email_field.fill(EMAIL)
                frame.locator("#password").fill(PASSWORD)
                frame.locator("#login-btn-signin").click()
            else:
                raise Exception("No iframe")
        except Exception:
            # Try direct page (no iframe)
            try:
                page.locator("input[name='email'], #email").fill(EMAIL)
                page.locator("input[name='password'], #password").fill(PASSWORD)
                page.locator("button[type='submit'], #login-btn-signin").click()
            except Exception as e:
                print(f"Could not find login form: {e}")
                print("Please log in manually in the browser window.")

        # Step 3: Wait for MFA or redirect
        print("\n⏳ Waiting for login to complete...")
        print("   If MFA is required, enter the code in the browser window.")
        print("   (Check your email for the verification code)\n")

        # Wait until we land on connect.garmin.com
        max_wait = 120  # 2 minutes for MFA
        start = time.time()
        while time.time() - start < max_wait:
            url = page.url
            if "connect.garmin.com" in url and "sso" not in url:
                print(f"✅ Login successful! Landed on: {url}")
                break
            time.sleep(1)
        else:
            print("⏰ Timeout waiting for login. Check the browser window.")
            browser.close()
            return False

        # Step 4: Extract cookies and tokens
        print("\nExtracting session data...")
        cookies = context.cookies()
        cookie_dict = {c["name"]: c["value"] for c in cookies}

        # Step 5: Try to get OAuth tokens via the SSO embed flow
        # Navigate to the SSO embed to trigger OAuth token generation
        print("Exchanging session for OAuth tokens...")

        # Use garth's SSO flow but with the browser's session
        import garth
        import requests

        # Transfer browser cookies to garth's session
        for cookie in cookies:
            garth.client.sess.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie.get("domain", ".garmin.com"),
                path=cookie.get("path", "/"),
            )

        # Try the OAuth exchange via SSO embed
        try:
            # Get the embed page (should work since we're authenticated)
            resp = garth.client.get(
                "sso",
                "/sso/embed",
                params={
                    "id": "gauth-widget",
                    "embedWidget": "true",
                    "gauthHost": "https://sso.garmin.com/sso",
                },
            )

            # Try to get a service ticket
            from garth.sso import get_csrf_token, get_title, _complete_login

            csrf_token = get_csrf_token(resp.text)

            # The embed page after authenticated login should have a ticket
            # Try the signin endpoint - it should auto-redirect since we're logged in
            garth.client.get(
                "sso",
                "/sso/signin",
                params={
                    "id": "gauth-widget",
                    "embedWidget": "true",
                    "gauthHost": "https://sso.garmin.com/sso/embed",
                    "service": "https://sso.garmin.com/sso/embed",
                    "source": "https://sso.garmin.com/sso/embed",
                    "redirectAfterAccountLoginUrl": "https://sso.garmin.com/sso/embed",
                    "redirectAfterAccountCreationUrl": "https://sso.garmin.com/sso/embed",
                },
                referrer=True,
            )

            title = get_title(garth.client.last_resp.text)
            if title == "Success":
                print("Got OAuth ticket from SSO!")
                garth.client.oauth1_token, garth.client.oauth2_token = _complete_login(garth.client)
            else:
                raise Exception(f"SSO title: {title}")

        except Exception as e:
            print(f"Direct OAuth exchange failed: {e}")
            print("Trying alternative: browser-based OAuth flow...")

            # Alternative: use the browser to hit the embed endpoint
            page.goto("https://sso.garmin.com/sso/embed?id=gauth-widget&embedWidget=true&gauthHost=https://sso.garmin.com/sso")
            page.wait_for_load_state("networkidle")
            embed_content = page.content()

            if "Success" in embed_content or "response_url" in embed_content:
                print("Browser got Success page, extracting ticket...")
                # Extract the ticket from the page
                import re
                ticket_match = re.search(r'ticket=([A-Za-z0-9\-]+)', embed_content)
                if ticket_match:
                    ticket = ticket_match.group(1)
                    print(f"Got ticket: {ticket[:20]}...")

            # Last resort: use the browser to complete the full OAuth flow
            # Navigate to the endpoint garth uses for token exchange
            page.goto("https://sso.garmin.com/sso/embed?id=gauth-widget&embedWidget=true&gauthHost=https://sso.garmin.com/sso")
            time.sleep(2)

            # Re-extract all cookies after the OAuth flow
            cookies = context.cookies()
            for cookie in cookies:
                garth.client.sess.cookies.set(
                    cookie["name"],
                    cookie["value"],
                    domain=cookie.get("domain", ".garmin.com"),
                    path=cookie.get("path", "/"),
                )

            # Final attempt: post to signin (should auto-succeed with session)
            try:
                SSO_EMBED = "https://sso.garmin.com/sso/embed"
                SIGNIN_PARAMS = {
                    "id": "gauth-widget",
                    "embedWidget": "true",
                    "gauthHost": SSO_EMBED,
                    "service": SSO_EMBED,
                    "source": SSO_EMBED,
                    "redirectAfterAccountLoginUrl": SSO_EMBED,
                    "redirectAfterAccountCreationUrl": SSO_EMBED,
                }

                garth.client.get("sso", "/sso/signin", params=SIGNIN_PARAMS, referrer=True)
                csrf = get_csrf_token(garth.client.last_resp.text)

                garth.client.post(
                    "sso",
                    "/sso/signin",
                    params=SIGNIN_PARAMS,
                    referrer=True,
                    data={
                        "username": EMAIL,
                        "password": PASSWORD,
                        "embed": "true",
                        "_csrf": csrf,
                    },
                )
                title = get_title(garth.client.last_resp.text)
                if title == "Success":
                    garth.client.oauth1_token, garth.client.oauth2_token = _complete_login(garth.client)
                    print("OAuth tokens obtained via form resubmit!")
                else:
                    raise Exception(f"Title: {title}")
            except Exception as e2:
                print(f"Form resubmit also failed: {e2}")
                print("\nFalling back to cookie-only session save...")
                # Save what we have as a fallback
                GARTH_TOKEN_DIR.mkdir(exist_ok=True)
                with open(GARTH_TOKEN_DIR / "cookies.json", "w") as f:
                    json.dump(cookies, f, indent=2)
                print(f"Cookies saved to {GARTH_TOKEN_DIR}/cookies.json")
                browser.close()
                return False

        # Step 6: Save garth tokens
        GARTH_TOKEN_DIR.mkdir(exist_ok=True)
        garth.save(str(GARTH_TOKEN_DIR))
        print(f"\n✅ OAuth tokens saved to {GARTH_TOKEN_DIR}/")
        print(f"Username: {garth.client.username}")
        print("Tokens are valid for ~1 year. garmin_sync.py will reuse them.")

        # Step 7: Quick verification
        try:
            profile = garth.client.connectapi("/userprofile-service/socialProfile")
            print(f"Verified: {profile.get('displayName', 'OK')}")
        except Exception as e:
            print(f"Verification call failed ({e}), but tokens may still be valid.")

        browser.close()
        return True


if __name__ == "__main__":
    success = run()
    if not success:
        print("\n❌ Could not obtain OAuth tokens.")
        print("The browser cookies were saved as fallback.")
        raise SystemExit(1)

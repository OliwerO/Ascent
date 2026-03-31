#!/usr/bin/env python3
"""Browser-based Garmin login to bypass API rate limits.

Opens a real browser window. You log in manually (email, password, MFA).
The script captures session tokens and saves them for garmin_sync.py.

Usage:
    python scripts/garmin_browser_login.py
"""

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = PROJECT_ROOT / "garmin_tokens.json"

GARMIN_SSO = "https://sso.garmin.com/sso/signin?service=https%3A%2F%2Fconnect.garmin.com%2Fmodern&webhost=https%3A%2F%2Fconnect.garmin.com%2Fmodern&source=https%3A%2F%2Fconnect.garmin.com%2Fmodern&redirectAfterAccountLoginUrl=https%3A%2F%2Fconnect.garmin.com%2Fmodern&redirectAfterAccountCreationUrl=https%3A%2F%2Fconnect.garmin.com%2Fmodern&gauthHost=https%3A%2F%2Fsso.garmin.com%2Fsso&id=gauth-widget&cssUrl=https%3A%2F%2Fconnect.garmin.com%2Fgauth-custom-v1.2-min.css&locale=en_US&generateExtraServiceTicket=true&generateTwoExtraServiceTickets=true"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("Opening Garmin login page...")
        print("Please log in with your credentials and complete MFA.")
        print("The script will capture tokens automatically.\n")

        page.goto(GARMIN_SSO)

        # Wait until redirected to connect.garmin.com (login complete)
        print("Waiting for login to complete...")
        try:
            page.wait_for_url("**/connect.garmin.com/**", timeout=300000)
        except Exception:
            print("Timeout or navigation issue. Checking if we're logged in...")

        # Navigate to JWT endpoint to get fresh token
        print("Fetching JWT token...")
        resp = page.goto("https://connect.garmin.com/modern/main/jwt")
        jwt_web = None
        if resp and resp.status == 200:
            try:
                body = resp.json()
                jwt_web = body.get("token")
                print(f"Got JWT token: {jwt_web[:40]}...")
            except Exception:
                print("Could not parse JWT response, trying cookies...")

        # Collect all cookies
        cookies = context.cookies()
        cookie_dict = {}
        for c in cookies:
            if "garmin" in c["domain"]:
                cookie_dict[c["name"]] = c["value"]

        # Look for CSRF token
        csrf_token = cookie_dict.get("__csrf_token") or cookie_dict.get("csrf_token")

        # If no JWT from endpoint, try cookie
        if not jwt_web:
            jwt_web = cookie_dict.get("GARMIN-SSO-GUID") or cookie_dict.get("JWT_FGP")

        if not jwt_web:
            print("\nWARNING: Could not find JWT token. Saving cookies anyway.")

        token_data = {
            "jwt_web": jwt_web,
            "csrf_token": csrf_token,
            "cookies": cookie_dict,
        }

        TOKEN_FILE.write_text(json.dumps(token_data, indent=2))
        print(f"\nTokens saved to {TOKEN_FILE}")

        # Verify with garminconnect library
        print("Verifying tokens with garminconnect library...")
        try:
            from garminconnect import Garmin
            client = Garmin()
            client.login(str(TOKEN_FILE))
            print(f"SUCCESS - Logged in as: {client.display_name}")
            # Re-save in library's canonical format
            client.client.dump(str(TOKEN_FILE))
            print(f"Tokens re-saved in library format to {TOKEN_FILE}")
        except Exception as e:
            print(f"Library verification failed: {e}")
            print("Raw tokens are saved. The sync script may still work.")

        browser.close()


if __name__ == "__main__":
    main()

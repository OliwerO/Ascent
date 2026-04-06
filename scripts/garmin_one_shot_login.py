#!/usr/bin/env python3
"""One-time Garmin login via native mobile SSO.

Run ONCE to generate long-lived tokens (~1 year with auto-refresh).
Uses the mobile API endpoint (/mobile/api/login) which bypasses
Cloudflare and has more generous rate limits than web SSO.

This is completely separate from the garth SSO endpoint that got 429'd.

Usage:
    cd ~/projects/ascent
    source venv/bin/activate
    python3 scripts/garmin_one_shot_login.py

If MFA is enabled, you'll be prompted to enter the code from your email.
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# Token storage paths
TOKEN_DIR = PROJECT_ROOT / ".garminconnect"
TOKEN_FILE = TOKEN_DIR / "garmin_tokens.json"

# Also store in home dir for keepalive/other scripts
HOME_TOKEN_DIR = Path.home() / ".garminconnect"
HOME_TOKEN_FILE = HOME_TOKEN_DIR / "garmin_tokens.json"


def prompt_mfa():
    """Prompt for MFA code — check your email."""
    print("\n" + "=" * 50)
    print("MFA REQUIRED — check your email for the code.")
    print("=" * 50)
    code = input("Enter MFA code: ").strip()
    if not code:
        print("No code entered. Aborting.")
        sys.exit(1)
    return code


def main():
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")

    if not email or not password:
        print("ERROR: GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env")
        sys.exit(1)

    print(f"Garmin One-Shot Login")
    print(f"Email: {email}")
    print(f"Endpoint: Mobile SSO (/mobile/api/login)")
    print(f"Token path: {TOKEN_FILE}")
    print()
    print("This uses the Android app login flow — different from the")
    print("web SSO endpoint that was rate-limited on Apr 1-2.")
    print()
    print("IF YOU GET 429: STOP IMMEDIATELY. Do NOT retry.")
    print("Each retry resets the 24-hour cooldown timer.")
    print()

    confirm = input("Proceed with login? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        sys.exit(0)

    from garminconnect import Garmin

    garmin = Garmin(
        email=email,
        password=password,
        prompt_mfa=prompt_mfa,
    )

    try:
        print("\nAttempting mobile SSO login...")
        garmin.login()  # Uses /mobile/api/login internally

        # Save tokens to both locations
        garmin.client.dump(str(TOKEN_FILE))
        garmin.client.dump(str(HOME_TOKEN_FILE))

        print(f"\nLogin successful!")
        print(f"Display name: {garmin.display_name}")
        print(f"Tokens saved to: {TOKEN_FILE}")
        print(f"Tokens saved to: {HOME_TOKEN_FILE}")

        # Verify tokens can be loaded back (no network call)
        from garminconnect.client import Client
        verify = Client()
        verify.load(str(TOKEN_FILE))
        assert verify.is_authenticated, "Token verification failed"
        print(f"Token verification: PASSED (jwt + csrf present)")

        # Clear any old cooldown files
        cooldown_files = [
            Path.home() / ".garth" / ".auth_cooldown",
            PROJECT_ROOT / ".garth" / ".auth_cooldown",
        ]
        for cf in cooldown_files:
            if cf.exists():
                cf.unlink()
                print(f"Cleared old cooldown: {cf}")

        # Clear stale session status
        status_file = Path.home() / ".garmin-session-status.json"
        if status_file.exists():
            import json
            status_file.write_text(json.dumps({
                "last_check": None,
                "session_alive": True,
                "cookie_count": 0,
                "consecutive_failures": 0,
                "note": "Reset after successful one-shot login",
            }, indent=2))
            print(f"Reset session status: {status_file}")

        print("\nDone. garmin_sync.py will use these tokens automatically.")
        print("Tokens auto-refresh for ~1 year. No manual login needed.")

    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "Too Many" in err_str:
            print(f"\nRATE LIMITED (429). Do NOT retry.")
            print("Wait at least 24 hours before trying again.")
            print("Each retry resets the cooldown timer.")

            # Set cooldown
            from garmin_auth import record_cooldown
            record_cooldown("429 during one-shot mobile SSO login")
        elif "MFA" in err_str:
            print(f"\nMFA error: {e}")
            print("Try again — the MFA code may have expired.")
        elif "password" in err_str.lower() or "username" in err_str.lower():
            print(f"\nCredential error: {e}")
            print("Check GARMIN_EMAIL and GARMIN_PASSWORD in .env")
            print("Do NOT retry more than once — wrong passwords trigger account lock.")
        else:
            print(f"\nLogin failed: {e}")
            print("Check the error above. Do NOT retry blindly.")
        sys.exit(1)


if __name__ == "__main__":
    main()

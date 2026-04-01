#!/usr/bin/env python3
"""One-time garth login to create persistent OAuth tokens.

Handles MFA (required — ECG feature made it permanent).
After success, tokens last ~1 year and garmin_sync.py resumes them automatically.

Usage:
    cd ~/projects/ascent && source venv/bin/activate
    python3 scripts/garth_login.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import garth

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

email = os.environ["GARMIN_EMAIL"]
password = os.environ["GARMIN_PASSWORD"]
token_dir = str(PROJECT_ROOT / ".garth")


def prompt_mfa():
    """Prompt for MFA code — check your email."""
    print("\n📧 MFA required. Check your email for the verification code.")
    return input("Enter MFA code: ").strip()


print(f"Logging in as {email}...")
print("(If you get 429, wait 1-2 hours and try again. Do NOT retry immediately.)\n")

try:
    garth.login(email, password, prompt_mfa=prompt_mfa)
    garth.save(token_dir)
    print(f"\n✅ Success! Tokens saved to {token_dir}")
    print(f"Username: {garth.client.username}")
    print("Tokens are valid for ~1 year. garmin_sync.py will reuse them automatically.")
except Exception as e:
    if "429" in str(e):
        print(f"\n⛔ Rate limited. Do NOT retry — each attempt resets the timer.")
        print("Wait at least 1-2 hours, then try again.")
    else:
        print(f"\nFailed: {e}")
    raise SystemExit(1)

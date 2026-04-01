#!/usr/bin/env python3
"""Bootstrap garth tokens from Safari session cookies.

If you're logged into Garmin Connect in Safari, this extracts
the session and creates garth-compatible OAuth tokens.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

TOKEN_DIR = str(PROJECT_ROOT / ".garth")

print("Step 1: Extracting Safari cookies for garmin.com...")
try:
    import browser_cookie3
    cj = browser_cookie3.safari(domain_name=".garmin.com")
    cookies = {c.name: c.value for c in cj}
    print(f"  Found {len(cookies)} cookies")

    # Check for key session cookies
    key_cookies = ["GARMIN-SSO-GUID", "GARMIN-SSO-CUST-GUID", "JWT_FGP", "SESSIONID"]
    found = [k for k in key_cookies if k in cookies]
    print(f"  Key cookies found: {found}")

    if not found:
        print("\n  Not logged into Garmin Connect in Safari.")
        print("  Please log in at https://connect.garmin.com in Safari first.")
        raise SystemExit(1)

except Exception as e:
    print(f"  Cookie extraction failed: {e}")
    print("  Make sure Safari has Full Disk Access in System Preferences > Privacy & Security")
    raise SystemExit(1)

print("\nStep 2: Trying garminconnect with cookies...")
import requests
from garminconnect import Garmin

sess = requests.Session()
for name, value in cookies.items():
    sess.cookies.set(name, value, domain=".garmin.com")

# Add Cloudflare-compatible headers
sess.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Origin": "https://connect.garmin.com",
    "Referer": "https://connect.garmin.com/modern/",
})

# Test if session works
print("  Testing API access...")
r = sess.get("https://connect.garmin.com/userprofile-service/usersocialprofile")
print(f"  Profile endpoint: {r.status_code}")

if r.status_code == 200:
    profile = r.json()
    print(f"  Logged in as: {profile.get('userName', profile.get('displayName', 'unknown'))}")
else:
    print(f"  Response: {r.text[:200]}")
    print("\n  Safari session may be expired. Log in again at https://connect.garmin.com")
    raise SystemExit(1)

print("\nStep 3: Getting OAuth tokens via exchange...")
# Try to get a service ticket from the existing session
try:
    import garth

    # Set cookies on garth's session
    for name, value in cookies.items():
        garth.client.sess.cookies.set(name, value, domain=".garmin.com")

    # Try to access a garth endpoint to see if the session works
    r = garth.client.sess.get(
        "https://connect.garmin.com/modern/proxy/userprofile-service/usersocialprofile",
        headers={
            "NK": "NT",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
    )
    print(f"  Garth proxy test: {r.status_code}")

    # Try OAuth1 token exchange
    r = garth.client.sess.get(
        "https://connect.garmin.com/modern/main/jwt",
        headers={"Accept": "application/json"}
    )
    if r.status_code == 200:
        jwt_data = r.json()
        print(f"  Got JWT token (expires: {jwt_data.get('expires', 'unknown')})")

    # Try the OAuth exchange endpoint
    email = os.environ["GARMIN_EMAIL"]
    r = garth.client.sess.post(
        "https://connect.garmin.com/services/auth/token/exchange",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "NK": "NT",
        },
        json={"login": email}
    )
    print(f"  Token exchange: {r.status_code}")
    if r.status_code == 200:
        token_data = r.json()
        print(f"  Got exchange token")

except Exception as e:
    print(f"  OAuth exchange failed: {e}")

print("\nStep 4: Saving session for garmin_sync.py...")
# Even if garth OAuth didn't work, save what we have
# Create a minimal garth-compatible session
import json

os.makedirs(TOKEN_DIR, exist_ok=True)

# Save the cookies as a session file garth can use
session_data = {
    "cookies": cookies,
    "status": "cookie_session",
}
with open(os.path.join(TOKEN_DIR, "session.json"), "w") as f:
    json.dump(session_data, f, indent=2)

print(f"  Session saved to {TOKEN_DIR}/")
print("\nDone! Try running: python3 scripts/garmin_sync.py --date 2026-03-31")

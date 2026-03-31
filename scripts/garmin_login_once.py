#!/usr/bin/env python3
"""One-time Garmin login with MFA support.

Run this once to authenticate and save tokens. After that,
garmin_sync.py will reuse the saved tokens automatically.

Usage:
    python scripts/garmin_login_once.py
"""

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

EMAIL = os.environ["GARMIN_EMAIL"]
PASSWORD = os.environ["GARMIN_PASSWORD"]
TOKEN_FILE = PROJECT_ROOT / "garmin_tokens.json"

SSO = "https://sso.garmin.com"
CONNECT = "https://connect.garmin.com"
CLIENT_ID = "GarminConnect"
SERVICE_URL = f"{CONNECT}/modern"

sess = requests.Session()
sess.headers = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TQ3A.230901.001) GarminConnect/4.74.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

print("Step 1: Loading sign-in page...")
r = sess.get(f"{SSO}/mobile/sso/en/sign-in", params={"clientId": CLIENT_ID})
print(f"  Status: {r.status_code}")

print("Step 2: Submitting credentials...")
r = sess.post(
    f"{SSO}/mobile/api/login",
    params={"clientId": CLIENT_ID, "locale": "en-US", "service": SERVICE_URL},
    json={"username": EMAIL, "password": PASSWORD, "rememberMe": False, "captchaToken": ""},
)

res = r.json()
resp_type = res.get("responseStatus", {}).get("type")
print(f"  Status: {r.status_code}, Type: {resp_type}")

if "error" in res and res["error"].get("status-code") == "429":
    print("\n429 Rate Limit - wait 10-15 minutes and try again.")
    raise SystemExit(1)

if resp_type == "INVALID_USERNAME_PASSWORD":
    print("\nInvalid credentials. Check .env file.")
    raise SystemExit(1)

if resp_type == "MFA_REQUIRED":
    mfa_method = res.get("customerMfaInfo", {}).get("mfaLastMethodUsed", "email")
    print(f"\nMFA required (method: {mfa_method}). Check your email for the code.")
    mfa_code = input("Enter MFA code: ").strip()

    r = sess.put(
        f"{SSO}/mobile/api/login/mfa/complete",
        params={"clientId": CLIENT_ID, "locale": "en-US", "service": SERVICE_URL},
        json={"verificationCode": mfa_code},
    )
    res = r.json()
    resp_type = res.get("responseStatus", {}).get("type")
    print(f"  MFA result: {r.status_code}, Type: {resp_type}")

    if resp_type != "SUCCESSFUL":
        print(f"\nMFA failed: {json.dumps(res)[:500]}")
        raise SystemExit(1)

ticket = res.get("serviceTicketId")
if not ticket:
    print(f"\nNo ticket in response: {json.dumps(res)[:500]}")
    raise SystemExit(1)

print("Step 3: Exchanging ticket for session...")
r = sess.get(f"{CONNECT}/modern", params={"ticket": ticket}, allow_redirects=True)
print(f"  Status: {r.status_code}")

# Extract JWT and CSRF from cookies/response
cookies = sess.cookies.get_dict()
jwt_web = cookies.get("GARMIN-SSO-GUID") or cookies.get("JWT_FGP")

# Try to get JWT from the newer endpoints
r = sess.get(f"{CONNECT}/modern/main/jwt", headers={"Accept": "application/json"})
if r.status_code == 200:
    try:
        jwt_data = r.json()
        jwt_web = jwt_data.get("token") or jwt_web
    except Exception:
        pass

# Now try to use the garminconnect library's Client to establish and save session
print("Step 4: Saving tokens via garminconnect library...")
from garminconnect import Garmin

client = Garmin(EMAIL, PASSWORD, prompt_mfa=lambda: mfa_code)
# Manually set the session cookies on the client
for name, value in cookies.items():
    client.client.cs.cookies.set(name, value, domain=".garmin.com", path="/")

# Try to dump whatever state we have
token_data = {
    "jwt_web": jwt_web,
    "csrf_token": cookies.get("__csrf_token") or cookies.get("csrf_token"),
    "cookies": cookies,
}
TOKEN_FILE.write_text(json.dumps(token_data))
print(f"\nTokens saved to {TOKEN_FILE}")

# Verify by trying to load and make an API call
print("\nStep 5: Verifying tokens work...")
try:
    client2 = Garmin()
    client2.login(str(TOKEN_FILE))
    print("Login from saved tokens: SUCCESS")
    # Save again with library's format for compatibility
    client2.client.dump(str(TOKEN_FILE))
    print(f"Tokens re-saved in library format to {TOKEN_FILE}")
except Exception as e:
    print(f"Token verification failed: {e}")
    print("The raw tokens are saved - you may need to re-run once more.")

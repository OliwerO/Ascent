#!/usr/bin/env python3
"""Authoritative Garmin auth status check.

This is the ONLY script Jarvis (or any other consumer) should use to answer
"is Garmin auth working?". It uses the Ascent Playwright stack
(`garmin_auth.get_safe_client`) — the same one every other Ascent script
uses — so its answer always matches reality. Do NOT consult the
`garmin-connect-mcp` server, `~/.garth/`, or any other auth store.

Usage:
    python3 scripts/garmin_status.py            # human output
    python3 scripts/garmin_status.py --json     # machine output (single line)

JSON shape:
    {
      "ok": bool,
      "display_name": str | null,
      "storage_path": str,
      "storage_age_hours": float | null,
      "jwt_web_expires_in_hours": float | null,
      "error": str | null,
      "hint": str | null
    }

Exit codes: 0 ok, 1 expired/missing, 2 cooldown, 3 unexpected error.
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("garmin_status")


STORAGE_PATH = Path.home() / ".garminconnect" / "garmin_storage_state.json"


def _decode_jwt_exp(jwt: str) -> datetime | None:
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


def _storage_facts() -> tuple[float | None, float | None]:
    if not STORAGE_PATH.exists():
        return None, None
    age_h = (datetime.now().timestamp() - STORAGE_PATH.stat().st_mtime) / 3600
    try:
        data = json.loads(STORAGE_PATH.read_text())
    except Exception:
        return age_h, None
    jwt = next(
        (c.get("value") for c in data.get("cookies", []) if c.get("name") == "JWT_WEB"),
        None,
    )
    if not jwt:
        return age_h, None
    exp = _decode_jwt_exp(jwt)
    if not exp:
        return age_h, None
    return age_h, (exp - datetime.now(timezone.utc)).total_seconds() / 3600


def check() -> dict:
    age_h, jwt_h = _storage_facts()
    payload: dict = {
        "ok": False,
        "display_name": None,
        "storage_path": str(STORAGE_PATH),
        "storage_age_hours": round(age_h, 2) if age_h is not None else None,
        "jwt_web_expires_in_hours": round(jwt_h, 2) if jwt_h is not None else None,
        "error": None,
        "hint": None,
    }

    if not STORAGE_PATH.exists():
        payload["error"] = "storage_state.json missing"
        payload["hint"] = (
            "Run: cd ~/projects/ascent && source venv/bin/activate && "
            "python3 scripts/garmin_browser_bootstrap.py"
        )
        return payload

    if jwt_h is not None and jwt_h < 0:
        payload["error"] = f"JWT_WEB expired {abs(jwt_h):.1f}h ago"
        payload["hint"] = (
            "Auto-refresh should run within the hour; if it doesn't, "
            "re-run garmin_browser_bootstrap.py manually."
        )
        return payload

    try:
        from garmin_auth import (
            get_safe_client,
            AuthExpiredError,
            RateLimitCooldownError,
        )
        client = get_safe_client(require_garminconnect=True)
        payload["ok"] = True
        payload["display_name"] = getattr(client, "display_name", None)
        return payload
    except RateLimitCooldownError as e:
        payload["error"] = f"rate-limit cooldown active: {e}"
        payload["hint"] = "Wait for cooldown to clear; do not retry."
        return payload
    except AuthExpiredError as e:
        payload["error"] = str(e).splitlines()[0]
        payload["hint"] = (
            "Run garmin_browser_bootstrap.py (or wait for the auto-refresh "
            "launchd job to run)."
        )
        return payload
    except Exception as e:
        payload["error"] = f"unexpected: {e}"
        return payload


def main() -> int:
    p = argparse.ArgumentParser(description="Garmin auth status")
    p.add_argument("--json", action="store_true", help="Single-line JSON on stdout")
    args = p.parse_args()

    result = check()

    if args.json:
        sys.stdout.write(json.dumps(result, default=str) + "\n")
    else:
        if result["ok"]:
            print(f"OK — authenticated as {result['display_name']}")
            if result["jwt_web_expires_in_hours"] is not None:
                print(f"JWT_WEB expires in {result['jwt_web_expires_in_hours']:.1f}h")
            if result["storage_age_hours"] is not None:
                print(f"Storage age: {result['storage_age_hours']:.1f}h")
        else:
            print(f"FAIL — {result['error']}")
            if result["hint"]:
                print(f"Hint: {result['hint']}")

    if result["ok"]:
        return 0
    if result["error"] and "cooldown" in result["error"]:
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())

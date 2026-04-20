#!/usr/bin/env python3
"""Watch for on-demand sync requests from the Ascent app.

Polls Supabase coaching_log for unacknowledged sync_request entries.
When found, runs garmin_sync.py for today's date and marks the request
as acknowledged.

Designed to run via launchd every 5 minutes, or as a long-running daemon.

Usage:
    python sync_watcher.py              # check once and exit
    python sync_watcher.py --daemon     # poll every 5 minutes
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", os.environ["SUPABASE_KEY"])
SYNC_SCRIPT = PROJECT_ROOT / "scripts" / "garmin_sync.py"
EGYM_SCRIPT = PROJECT_ROOT / "scripts" / "egym_sync.py"
PUSH_SCRIPT = PROJECT_ROOT / "scripts" / "workout_push.py"
COACH_SCRIPT = PROJECT_ROOT / "scripts" / "coach_evaluate.py"
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"

# Map request types to scripts
REQUEST_SCRIPTS = {
    "sync_request": SYNC_SCRIPT,
    "egym_sync_request": EGYM_SCRIPT,
    "workout_push_request": PUSH_SCRIPT,
    "coach_evaluation_request": COACH_SCRIPT,
}

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("sync_watcher")


def check_and_run():
    """Check for pending sync requests and run the appropriate script."""
    # Query for unacknowledged requests of any supported type
    type_filter = ",".join(REQUEST_SCRIPTS.keys())
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/coaching_log",
        headers=HEADERS,
        params={
            "type": f"in.({type_filter})",
            "acknowledged": "eq.false",
            "order": "created_at.asc",
            "limit": "10",
        },
        timeout=10,
    )
    resp.raise_for_status()
    requests_list = resp.json()

    if not requests_list:
        log.debug("No pending sync requests")
        return False

    any_success = False
    for req in requests_list:
        req_id = req["id"]
        req_type = req["type"]
        script = REQUEST_SCRIPTS.get(req_type)

        if not script:
            log.warning("Unknown request type: %s (id=%s)", req_type, req_id)
            continue

        log.info("%s found (id=%s), running %s...", req_type, req_id, script.name)

        python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
        cmd = [python, str(script)]

        # Pass extra arguments from data_context
        ctx = req.get("data_context") or {}
        if req_type == "workout_push_request":
            if ctx.get("date"):
                cmd.extend(["--date", ctx["date"]])
            if ctx.get("session"):
                cmd.extend(["--session", ctx["session"]])
        elif req_type == "coach_evaluation_request":
            if ctx.get("date"):
                cmd.extend(["--date", ctx["date"]])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(PROJECT_ROOT),
        )

        success = result.returncode == 0
        log.info(
            "%s %s (exit code %d)",
            script.name,
            "completed" if success else "failed",
            result.returncode,
        )
        if result.stdout:
            log.info("stdout: %s", result.stdout[-500:])
        if result.stderr and not success:
            log.error("stderr: %s", result.stderr[-500:])

        # Mark request as acknowledged
        ack_resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/coaching_log?id=eq.{req_id}",
            headers={**HEADERS, "Prefer": "return=minimal"},
            json={
                "acknowledged": True,
                "data_context": {
                    **(req.get("data_context") or {}),
                    "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "success": success,
                    "exit_code": result.returncode,
                },
            },
            timeout=10,
        )
        ack_resp.raise_for_status()
        log.info("Request %s acknowledged", req_id)

        if success:
            any_success = True

    return any_success


def main():
    parser = argparse.ArgumentParser(description="Watch for Garmin sync requests")
    parser.add_argument(
        "--daemon", action="store_true", help="Run continuously, polling every 5 min"
    )
    args = parser.parse_args()

    if args.daemon:
        log.info("Starting sync watcher daemon (poll interval: 30s)")
        while True:
            try:
                check_and_run()
            except Exception as e:
                log.error("Error: %s", e)
            time.sleep(30)
    else:
        try:
            check_and_run()
        except Exception as e:
            log.error("Error: %s", e)
            sys.exit(1)


if __name__ == "__main__":
    main()

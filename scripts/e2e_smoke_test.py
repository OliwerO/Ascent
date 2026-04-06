#!/usr/bin/env python3
"""E2E smoke test for the Ascent coaching pipeline.

Verifies full pipeline connectivity:
1. Data layer — critical tables/views have recent data
2. Script layer — dry-run key scripts
3. Build layer — React app builds
4. Auth layer — Garmin token status
5. Freshness — data is recent enough to be useful

Usage:
    python e2e_smoke_test.py           # run all checks, output JSON
    python e2e_smoke_test.py --quick   # skip slow checks (build, scripts)
    python e2e_smoke_test.py --slack   # post failures to Slack

Exit codes: 0 = all pass, 1 = failures detected
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", os.environ["SUPABASE_KEY"])
SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("e2e")


def supabase_get(table: str, params: dict | None = None) -> list:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    resp = requests.get(url, headers=SUPABASE_HEADERS, params=params or {}, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Check functions — each returns (pass: bool, detail: str)
# ---------------------------------------------------------------------------

def check_table_exists(table: str) -> tuple[bool, str]:
    """Check that a table/view exists and is queryable."""
    try:
        supabase_get(table, {"limit": "1"})
        return True, f"{table} OK"
    except Exception as e:
        return False, f"{table} FAILED: {e}"


def check_table_has_recent_data(table: str, date_col: str, max_age_days: int = 7) -> tuple[bool, str]:
    """Check that a table has data within max_age_days."""
    cutoff = (date.today() - timedelta(days=max_age_days)).isoformat()
    try:
        rows = supabase_get(table, {
            date_col: f"gte.{cutoff}",
            "select": date_col,
            "order": f"{date_col}.desc",
            "limit": "1",
        })
        if rows:
            return True, f"{table} — latest: {rows[0][date_col]}"
        return False, f"{table} — no data in last {max_age_days} days"
    except Exception as e:
        return False, f"{table} — {e}"


def check_view_returns_data(view: str) -> tuple[bool, str]:
    """Check that a view returns at least one row."""
    try:
        rows = supabase_get(view, {"limit": "3"})
        if rows:
            return True, f"{view} — {len(rows)} rows (sample)"
        return False, f"{view} — empty"
    except Exception as e:
        return False, f"{view} — {e}"


def check_script_dry_run(script: str, args: list[str] | None = None) -> tuple[bool, str]:
    """Run a script in dry-run mode and check exit code."""
    cmd = [
        str(PROJECT_ROOT / "venv" / "bin" / "python"),
        str(PROJECT_ROOT / "scripts" / script),
        *(args or []),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(PROJECT_ROOT))
        if result.returncode == 0:
            return True, f"{script} — exit 0"
        return False, f"{script} — exit {result.returncode}: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, f"{script} — timed out (30s)"
    except Exception as e:
        return False, f"{script} — {e}"


def check_react_build() -> tuple[bool, str]:
    """Verify React app builds without errors."""
    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            capture_output=True, text=True, timeout=60,
            cwd=str(PROJECT_ROOT / "web"),
        )
        if result.returncode == 0:
            return True, "React build — OK"
        # Extract first error line
        err_lines = [l for l in result.stderr.split("\n") if "error" in l.lower()]
        return False, f"React build — FAILED: {err_lines[0] if err_lines else result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, "React build — timed out (60s)"
    except Exception as e:
        return False, f"React build — {e}"


def check_garmin_auth() -> tuple[bool, str]:
    """Check if Garmin auth tokens exist and are recent."""
    garth_dir = Path.home() / ".garth"
    if not garth_dir.exists():
        return False, "Garmin auth — ~/.garth/ directory not found"
    token_files = list(garth_dir.glob("*"))
    if not token_files:
        return False, "Garmin auth — no token files in ~/.garth/"
    newest = max(f.stat().st_mtime for f in token_files)
    from datetime import datetime
    age_hours = (datetime.now().timestamp() - newest) / 3600
    if age_hours > 48:
        return False, f"Garmin auth — tokens are {age_hours:.0f}h old (may be expired)"
    return True, f"Garmin auth — tokens {age_hours:.0f}h old"


def check_pytest() -> tuple[bool, str]:
    """Run pytest and report results."""
    try:
        result = subprocess.run(
            [str(PROJECT_ROOT / "venv" / "bin" / "python"), "-m", "pytest", "tests/", "-q", "--tb=line"],
            capture_output=True, text=True, timeout=60, cwd=str(PROJECT_ROOT),
        )
        # Parse output for pass/fail counts
        last_line = result.stdout.strip().split("\n")[-1] if result.stdout.strip() else ""
        if result.returncode == 0:
            return True, f"pytest — {last_line}"
        return False, f"pytest — {last_line}"
    except Exception as e:
        return False, f"pytest — {e}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_all_checks(quick: bool = False) -> dict:
    """Run all checks and return a report."""
    checks = {}

    # 1. Data layer — tables exist
    log.info("Checking tables and views...")
    critical_tables = [
        "daily_metrics", "sleep", "hrv", "body_composition", "activities",
        "training_sessions", "training_sets", "exercise_progression",
        "coaching_log", "planned_workouts",
        "athlete_response_patterns", "coaching_decision_outcomes",
        "exercise_feedback", "weekly_reflections",
    ]
    for table in critical_tables:
        ok, detail = check_table_exists(table)
        checks[f"table_{table}"] = {"pass": ok, "detail": detail}

    # 2. Data freshness
    log.info("Checking data freshness...")
    freshness_checks = [
        ("daily_metrics", "date", 3),
        ("sleep", "date", 3),
        ("hrv", "date", 3),
        ("activities", "date", 14),
        ("coaching_log", "date", 7),
    ]
    for table, col, age in freshness_checks:
        ok, detail = check_table_has_recent_data(table, col, age)
        checks[f"fresh_{table}"] = {"pass": ok, "detail": detail}

    # 3. Views return data
    log.info("Checking views...")
    views = [
        "daily_summary",
        "daily_coaching_context",
        "weekly_coaching_summary",
        "mountain_gym_interference",
        "weekly_training_load",
        "progression_velocity",
        "recomp_tracking",
    ]
    for view in views:
        ok, detail = check_view_returns_data(view)
        checks[f"view_{view}"] = {"pass": ok, "detail": detail}

    if not quick:
        # 4. Script dry-runs
        log.info("Running script dry-runs...")
        scripts = [
            ("interference_analysis.py", ["--dry-run", "--lookback", "30"]),
            ("decision_retrospective.py", ["--dry-run", "--lookback", "14"]),
            ("recomp_analysis.py", ["--dry-run"]),
        ]
        for script, args in scripts:
            ok, detail = check_script_dry_run(script, args)
            checks[f"script_{script}"] = {"pass": ok, "detail": detail}

        # 5. React build
        log.info("Checking React build...")
        ok, detail = check_react_build()
        checks["react_build"] = {"pass": ok, "detail": detail}

        # 6. Unit tests
        log.info("Running unit tests...")
        ok, detail = check_pytest()
        checks["pytest"] = {"pass": ok, "detail": detail}

    # 7. Auth
    log.info("Checking Garmin auth...")
    ok, detail = check_garmin_auth()
    checks["garmin_auth"] = {"pass": ok, "detail": detail}

    return checks


def main():
    parser = argparse.ArgumentParser(description="Ascent E2E smoke test")
    parser.add_argument("--quick", action="store_true", help="Skip slow checks")
    parser.add_argument("--slack", action="store_true", help="Post failures to Slack")
    args = parser.parse_args()

    checks = run_all_checks(quick=args.quick)

    # Summary
    passed = sum(1 for c in checks.values() if c["pass"])
    failed = sum(1 for c in checks.values() if not c["pass"])
    total = len(checks)

    report = {
        "date": date.today().isoformat(),
        "summary": {"passed": passed, "failed": failed, "total": total},
        "checks": checks,
    }

    # Print report
    print(json.dumps(report, indent=2))

    # Log failures
    if failed:
        log.warning("--- FAILURES ---")
        for name, check in checks.items():
            if not check["pass"]:
                log.warning("  FAIL: %s — %s", name, check["detail"])

    # Post to Slack on failure (if requested)
    if args.slack and failed:
        slack_token = os.environ.get("SLACK_BOT_TOKEN")
        channel = os.environ.get("SLACK_CHANNEL_DAILY")
        if slack_token and channel:
            fail_lines = [f"• {name}: {c['detail']}" for name, c in checks.items() if not c["pass"]]
            text = f":warning: *Ascent E2E: {failed}/{total} checks failed*\n" + "\n".join(fail_lines[:10])
            requests.post("https://slack.com/api/chat.postMessage", headers={
                "Authorization": f"Bearer {slack_token}",
                "Content-Type": "application/json",
            }, json={"channel": channel, "text": text}, timeout=10)

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

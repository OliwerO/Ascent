#!/usr/bin/env python3
"""Reconcile planned_workouts against actual Garmin activities.

Walks back through recent planned_workouts rows and marks them as
completed or skipped based on whether a matching Garmin activity exists.
Uses coach_adjust.py as the single write path.

Runs at 07:00 via launchd, after garmin_sync (06:00) has pulled
yesterday's activities into Supabase.

Usage:
    python daily_reconcile.py                  # reconcile (default: last 7 days)
    python daily_reconcile.py --lookback 14    # reconcile last 14 days
    python daily_reconcile.py --dry-run        # show what would change
    python daily_reconcile.py --date 2026-04-08  # reconcile a specific date
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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", os.environ["SUPABASE_KEY"])
PYTHON = str(PROJECT_ROOT / "venv" / "bin" / "python3")
COACH_ADJUST = str(SCRIPTS_DIR / "coach_adjust.py")

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
log = logging.getLogger("daily_reconcile")

# ---------------------------------------------------------------------------
# Activity type → session type mapping
# ---------------------------------------------------------------------------

MOUNTAIN_TYPES = {
    "backcountry_skiing", "backcountry_snowboarding", "resort_snowboarding",
    "resort_skiing", "hiking", "mountaineering", "splitboarding",
    "ski_touring",
}

STRENGTH_TYPES = {"strength_training"}

CARDIO_TYPES = {"indoor_cardio", "running", "cycling", "walking", "treadmill_running"}


# ---------------------------------------------------------------------------
# Supabase queries
# ---------------------------------------------------------------------------


def supabase_get(table: str, params: dict) -> list:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_unreconciled_workouts(start_date: date, end_date: date) -> list:
    """Get planned_workouts that haven't been reconciled yet.

    A row is unreconciled if:
    - status is 'pending' or 'adjusted'
    - scheduled_date is in the past (before today)
    - scheduled_date is within the lookback window
    """
    rows = supabase_get("planned_workouts", {
        "select": "id,scheduled_date,session_name,session_type,status,updated_at,created_at",
        "scheduled_date": f"gte.{start_date.isoformat()}",
        "and": f"(scheduled_date.lte.{end_date.isoformat()},status.in.(pending,adjusted))",
        "order": "scheduled_date.asc",
    })
    return rows


def get_activities_for_date(target_date: date) -> list:
    """Get Garmin activities for a specific date."""
    return supabase_get("activities", {
        "date": f"eq.{target_date.isoformat()}",
        "select": "activity_type,activity_name,duration_seconds,elevation_gain",
    })


# ---------------------------------------------------------------------------
# Matching logic
# ---------------------------------------------------------------------------


def classify_activities(activities: list) -> dict:
    """Classify a date's activities into types."""
    result = {
        "has_strength": False,
        "has_mountain": False,
        "has_cardio": False,
        "mountain_types": [],
        "all_types": [],
    }
    for act in activities:
        atype = act.get("activity_type", "")
        result["all_types"].append(atype)
        if atype in STRENGTH_TYPES:
            result["has_strength"] = True
        elif atype in MOUNTAIN_TYPES:
            result["has_mountain"] = True
            result["mountain_types"].append(atype)
        elif atype in CARDIO_TYPES:
            result["has_cardio"] = True
    return result


def determine_action(session_type: str, activity_info: dict) -> tuple[str, str]:
    """Determine the reconciliation action for a planned workout.

    Returns (action, reason) or (None, None) if no action needed.
    """
    stype = session_type or ""

    if stype == "rest":
        # Rest days don't need reconciliation
        return None, None

    if stype == "strength":
        if activity_info["has_strength"]:
            return "mark_completed", "strength session recorded in Garmin (auto-reconciled)"
        else:
            return "mark_skipped", "no strength activity recorded (auto-reconciled)"

    if stype in ("mountain_tour", "mountain"):
        if activity_info["has_mountain"]:
            return "mark_completed", "mountain activity recorded in Garmin (auto-reconciled)"
        else:
            return "mark_skipped", "no mountain activity recorded (auto-reconciled)"

    if stype in ("cardio_touring", "cross_training", "cardio"):
        if activity_info["has_cardio"] or activity_info["has_mountain"]:
            return "mark_completed", "activity recorded in Garmin (auto-reconciled)"
        else:
            return "mark_skipped", "no matching activity recorded (auto-reconciled)"

    if stype == "mobility":
        # Mobility sessions are short and may not show on Garmin —
        # don't auto-skip them, only auto-complete if strength/activity is found
        if activity_info["has_strength"] or activity_info["has_cardio"]:
            return "mark_completed", "activity recorded (auto-reconciled)"
        # Leave pending — user might have done it without Garmin
        return None, None

    # Unknown session type — leave alone
    log.warning("Unknown session_type '%s', skipping reconciliation", stype)
    return None, None


# ---------------------------------------------------------------------------
# Execute reconciliation
# ---------------------------------------------------------------------------


def run_coach_adjust(target_date: str, action: str, reason: str,
                     dry_run: bool = False) -> dict:
    """Call coach_adjust.py for a single reconciliation action."""
    details = json.dumps({"reason": reason})
    cmd = [
        PYTHON, COACH_ADJUST,
        "--date", target_date,
        "--action", action,
        "--details", details,
        "--no-garmin",
        "--no-slack",
    ]
    if dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
        else:
            log.error("coach_adjust failed: %s", result.stderr.strip()[-200:])
            return {"ok": False, "error": result.stderr.strip()[-200:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def reconcile(lookback_days: int = 7, dry_run: bool = False,
              specific_date: str | None = None) -> dict:
    """Run the full reconciliation pass.

    Returns summary of actions taken.
    """
    today = date.today()
    yesterday = today - timedelta(days=1)

    if specific_date:
        start = date.fromisoformat(specific_date)
        end = start
    else:
        start = today - timedelta(days=lookback_days)
        end = yesterday  # don't reconcile today — session might still happen

    log.info("Reconciling planned_workouts from %s to %s%s",
             start, end, " (dry run)" if dry_run else "")

    # Get all unreconciled workouts in window
    workouts = get_unreconciled_workouts(start, end)
    log.info("Found %d unreconciled workout(s)", len(workouts))

    summary = {
        "checked": len(workouts),
        "completed": 0,
        "skipped": 0,
        "unchanged": 0,
        "errors": 0,
        "actions": [],
    }

    for workout in workouts:
        wdate = workout["scheduled_date"]
        sname = workout.get("session_name", "Unknown")
        stype = workout.get("session_type", "")

        # Get actual activities for this date
        activities = get_activities_for_date(date.fromisoformat(wdate))
        activity_info = classify_activities(activities)

        # Determine action
        action, reason = determine_action(stype, activity_info)

        if action is None:
            log.info("  %s: %s (%s) — no action needed", wdate, sname, stype)
            summary["unchanged"] += 1
            continue

        log.info("  %s: %s (%s) → %s", wdate, sname, stype, action)

        result = run_coach_adjust(wdate, action, reason, dry_run=dry_run)

        action_record = {
            "date": wdate,
            "session": sname,
            "action": action,
            "ok": result.get("ok", False),
        }

        if result.get("ok"):
            if action == "mark_completed":
                summary["completed"] += 1
            else:
                summary["skipped"] += 1
        else:
            summary["errors"] += 1
            action_record["error"] = result.get("error", "unknown")
            log.error("    FAILED: %s", result.get("error", "unknown"))

        summary["actions"].append(action_record)

    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Reconcile planned_workouts against Garmin activities"
    )
    parser.add_argument("--lookback", type=int, default=7,
                        help="Days to look back (default: 7)")
    parser.add_argument("--date", type=str, default=None,
                        help="Reconcile a specific date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without writing")
    args = parser.parse_args()

    summary = reconcile(
        lookback_days=args.lookback,
        dry_run=args.dry_run,
        specific_date=args.date,
    )

    log.info("=== Reconciliation complete ===")
    log.info("  Checked: %d", summary["checked"])
    log.info("  Completed: %d", summary["completed"])
    log.info("  Skipped: %d", summary["skipped"])
    log.info("  Unchanged: %d", summary["unchanged"])
    log.info("  Errors: %d", summary["errors"])

    # Output JSON summary for other scripts to consume
    print(json.dumps(summary))

    sys.exit(0 if summary["errors"] == 0 else 1)


if __name__ == "__main__":
    main()

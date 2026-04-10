#!/usr/bin/env python3
"""Reconcile planned_workouts (Supabase) against Garmin Connect schedule.

Detects:
  - orphan_db        : planned_workouts row has garmin_workout_id but no
                       matching scheduled instance on or near its scheduled_date.
  - orphan_garmin    : scheduled Garmin instance exists with no planned_workouts
                       row for that date.
  - date_drift       : scheduled instance exists for the row's garmin_workout_id
                       but its date != planned_workouts.scheduled_date.
  - duplicate_garmin : two or more scheduled instances on the same calendar date.
  - stale_template   : garmin_workout_id in DB no longer exists as a template
                       in the Garmin workout library.

Defaults to dry-run. With --apply:
  - duplicate_garmin : unschedule all but the newest instance per date.
  - orphan_garmin    : unschedule (only if --apply --delete-orphans is set —
                       double-gated because it touches Garmin state).
  - stale_template   : clear planned_workouts.garmin_workout_id in DB.

Never deletes planned_workouts rows. Never deletes Garmin workout templates.
Date drift and orphan_db require human review — flagged but never auto-fixed,
because the right correction depends on whether the DB or Garmin side is the
source of truth in the moment, and that needs the coach in the loop.

Output contract (mirrors scripts/coach_adjust.py):
  - JSON object on stdout
  - All logs on stderr
  - Exit code 0 on success (even if drift was found), 1 on hard failure

Usage:
  python3 scripts/reconcile_garmin.py                      # dry-run, today + 14d
  python3 scripts/reconcile_garmin.py --window 28          # wider window
  python3 scripts/reconcile_garmin.py --apply              # apply safe fixes
  python3 scripts/reconcile_garmin.py --apply --delete-orphans  # also unschedule orphan Garmin entries
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import traceback
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,
)
log = logging.getLogger("reconcile_garmin")


# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------


def fetch_planned(sb, start: date, end: date) -> list[dict]:
    """Return planned_workouts rows in [start, end] (inclusive)."""
    res = (
        sb.table("planned_workouts")
        .select("id,scheduled_date,session_name,session_type,status,garmin_workout_id")
        .gte("scheduled_date", start.isoformat())
        .lte("scheduled_date", end.isoformat())
        .order("scheduled_date")
        .execute()
    )
    return res.data or []


def clear_garmin_id(sb, row_id: int) -> None:
    sb.table("planned_workouts").update({"garmin_workout_id": None}).eq("id", row_id).execute()


# ---------------------------------------------------------------------------
# Garmin
# ---------------------------------------------------------------------------


def get_client():
    """Reuse the project's existing browser-session auth path."""
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from garmin_auth import get_safe_client  # type: ignore

    return get_safe_client(require_garminconnect=True)


def fetch_garmin_calendar(client, start: date, end: date) -> list[dict]:
    """Pull Garmin calendar entries in [start, end] and return scheduled-workout items.

    Garmin's calendar-service returns one month at a time (0-indexed month).
    We iterate every month that the window touches and collect items whose
    `itemType` indicates a scheduled workout. Each returned dict has at least:
        scheduled_workout_id, workout_id, date (ISO), title.
    """
    items: list[dict] = []
    seen_months: set[tuple[int, int]] = set()
    cursor = start.replace(day=1)
    while cursor <= end:
        key = (cursor.year, cursor.month)
        if key not in seen_months:
            seen_months.add(key)
            try:
                # Garmin calendar uses 0-indexed months
                payload = client.connectapi(
                    f"/calendar-service/year/{cursor.year}/month/{cursor.month - 1}"
                )
            except Exception as exc:
                log.warning("calendar fetch failed for %s-%02d: %s", cursor.year, cursor.month, exc)
                payload = None
            if isinstance(payload, dict):
                for item in payload.get("calendarItems", []) or []:
                    item_type = (item.get("itemType") or "").lower()
                    if "workout" not in item_type:
                        continue
                    iso = item.get("date") or item.get("startDate")
                    if not iso:
                        continue
                    try:
                        d = date.fromisoformat(iso[:10])
                    except ValueError:
                        continue
                    if d < start or d > end:
                        continue
                    items.append({
                        "scheduled_workout_id": item.get("id"),
                        "workout_id": item.get("workoutId"),
                        "date": d.isoformat(),
                        "title": item.get("title"),
                        "raw_item_type": item_type,
                    })
        # advance to next month
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)
    return items


def template_exists(client, workout_id: str) -> bool | None:
    """Return True if the workout template exists, False if not, None if unknown."""
    try:
        client.get_workout_by_id(workout_id)
        return True
    except Exception as exc:
        msg = str(exc).lower()
        if "404" in msg or "not found" in msg:
            return False
        log.warning("template_exists(%s) ambiguous: %s", workout_id, exc)
        return None


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------


def diff(planned: list[dict], scheduled: list[dict]) -> dict:
    """Build the findings dict from DB rows + Garmin scheduled items."""
    by_date_db: dict[str, list[dict]] = defaultdict(list)
    for row in planned:
        by_date_db[row["scheduled_date"]].append(row)

    by_date_garmin: dict[str, list[dict]] = defaultdict(list)
    for item in scheduled:
        by_date_garmin[item["date"]].append(item)

    by_workout_id_garmin: dict[str, list[dict]] = defaultdict(list)
    for item in scheduled:
        if item.get("workout_id"):
            by_workout_id_garmin[str(item["workout_id"])].append(item)

    findings = {
        "orphan_db": [],
        "orphan_garmin": [],
        "date_drift": [],
        "duplicate_garmin": [],
    }

    # orphan_db + date_drift
    for row in planned:
        wid = row.get("garmin_workout_id")
        if not wid:
            continue
        instances = by_workout_id_garmin.get(str(wid), [])
        if not instances:
            findings["orphan_db"].append({
                "planned_workout_id": row["id"],
                "scheduled_date": row["scheduled_date"],
                "garmin_workout_id": wid,
                "session_name": row.get("session_name"),
            })
            continue
        if not any(inst["date"] == row["scheduled_date"] for inst in instances):
            findings["date_drift"].append({
                "planned_workout_id": row["id"],
                "db_date": row["scheduled_date"],
                "garmin_workout_id": wid,
                "garmin_dates": sorted({i["date"] for i in instances}),
                "session_name": row.get("session_name"),
            })

    # orphan_garmin (scheduled but no DB row at all on that date)
    for d_iso, items in by_date_garmin.items():
        if d_iso not in by_date_db:
            for item in items:
                findings["orphan_garmin"].append({
                    "scheduled_workout_id": item["scheduled_workout_id"],
                    "workout_id": item["workout_id"],
                    "date": d_iso,
                    "title": item.get("title"),
                })

    # duplicate_garmin
    for d_iso, items in by_date_garmin.items():
        if len(items) >= 2:
            findings["duplicate_garmin"].append({
                "date": d_iso,
                "instances": [
                    {
                        "scheduled_workout_id": i["scheduled_workout_id"],
                        "workout_id": i["workout_id"],
                        "title": i.get("title"),
                    }
                    for i in items
                ],
            })

    return findings


# ---------------------------------------------------------------------------
# Apply (writes)
# ---------------------------------------------------------------------------


def apply_fixes(
    client,
    sb,
    findings: dict,
    stale_templates: list[dict],
    delete_orphans: bool,
) -> dict:
    actions = {"unscheduled": [], "db_cleared": [], "errors": []}

    # 1. duplicate_garmin: keep highest scheduled_workout_id (newest), unschedule the rest
    for dup in findings["duplicate_garmin"]:
        instances = sorted(
            dup["instances"], key=lambda i: i.get("scheduled_workout_id") or 0
        )
        keep = instances[-1]
        for older in instances[:-1]:
            sid = older.get("scheduled_workout_id")
            if not sid:
                continue
            try:
                client.unschedule_workout(sid)
                actions["unscheduled"].append({"scheduled_workout_id": sid, "reason": "duplicate", "date": dup["date"], "kept": keep.get("scheduled_workout_id")})
            except Exception as exc:
                actions["errors"].append({"op": "unschedule_duplicate", "scheduled_workout_id": sid, "error": str(exc)})

    # 2. orphan_garmin: only if explicitly opted in
    if delete_orphans:
        for orphan in findings["orphan_garmin"]:
            sid = orphan.get("scheduled_workout_id")
            if not sid:
                continue
            try:
                client.unschedule_workout(sid)
                actions["unscheduled"].append({"scheduled_workout_id": sid, "reason": "orphan", "date": orphan["date"]})
            except Exception as exc:
                actions["errors"].append({"op": "unschedule_orphan", "scheduled_workout_id": sid, "error": str(exc)})

    # 3. stale_template: clear DB pointer (template is gone, the ID is dead anyway)
    for stale in stale_templates:
        try:
            clear_garmin_id(sb, stale["planned_workout_id"])
            actions["db_cleared"].append(stale)
        except Exception as exc:
            actions["errors"].append({"op": "clear_garmin_id", "planned_workout_id": stale["planned_workout_id"], "error": str(exc)})

    return actions


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", type=int, default=14, help="Days forward from today (default 14).")
    parser.add_argument("--start", type=str, help="Override start date (YYYY-MM-DD). Default: today.")
    parser.add_argument("--apply", action="store_true", help="Apply safe fixes (duplicates, stale templates).")
    parser.add_argument("--delete-orphans", action="store_true", help="With --apply, also unschedule orphan Garmin entries. Double-gated.")
    parser.add_argument("--no-garmin", action="store_true", help="Skip Garmin calls; report DB-side findings only.")
    args = parser.parse_args()

    start = date.fromisoformat(args.start) if args.start else date.today()
    end = start + timedelta(days=args.window)

    result: dict[str, Any] = {
        "ok": False,
        "dry_run": not args.apply,
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "findings": {},
        "stale_templates": [],
        "actions": None,
        "warnings": [],
    }

    try:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        planned = fetch_planned(sb, start, end)
        log.info("loaded %d planned_workouts rows in window", len(planned))

        if args.no_garmin:
            result["warnings"].append("--no-garmin set; Garmin side not consulted")
            result["findings"] = {"orphan_db": [], "orphan_garmin": [], "date_drift": [], "duplicate_garmin": []}
            result["counts"] = {k: 0 for k in result["findings"]}
            result["ok"] = True
            print(json.dumps(result, indent=2))
            return 0

        client = get_client()
        scheduled = fetch_garmin_calendar(client, start, end)
        log.info("loaded %d scheduled Garmin items in window", len(scheduled))

        findings = diff(planned, scheduled)
        result["findings"] = findings

        # stale_templates: only check rows with garmin_workout_id; cap to 50 to avoid pagination
        stale: list[dict] = []
        checked = 0
        for row in planned:
            wid = row.get("garmin_workout_id")
            if not wid or checked >= 50:
                continue
            checked += 1
            exists = template_exists(client, wid)
            if exists is False:
                stale.append({
                    "planned_workout_id": row["id"],
                    "scheduled_date": row["scheduled_date"],
                    "garmin_workout_id": wid,
                    "session_name": row.get("session_name"),
                })
        result["stale_templates"] = stale

        result["counts"] = {
            "orphan_db": len(findings["orphan_db"]),
            "orphan_garmin": len(findings["orphan_garmin"]),
            "date_drift": len(findings["date_drift"]),
            "duplicate_garmin": len(findings["duplicate_garmin"]),
            "stale_templates": len(stale),
        }

        if args.apply:
            result["actions"] = apply_fixes(client, sb, findings, stale, args.delete_orphans)

        result["ok"] = True
        print(json.dumps(result, indent=2, default=str))
        return 0

    except Exception as exc:
        log.error("reconcile failed: %s", exc)
        log.error(traceback.format_exc())
        result["error"] = str(exc)
        print(json.dumps(result, indent=2, default=str))
        return 1


if __name__ == "__main__":
    sys.exit(main())

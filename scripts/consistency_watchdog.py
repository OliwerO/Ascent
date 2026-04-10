#!/usr/bin/env python3
"""Cross-channel consistency watchdog for today's training session.

Runs before the daily coaching cron and verifies that:
  1. The planned_workouts row for today exists and has a session
  2. If the row has a garmin_workout_id, a matching Garmin calendar entry
     exists on the same date
  3. No orphan Garmin entries exist for today with no DB row

Posts to #ascent-daily ONLY when disagreement is found. Silent on success.

Output contract (mirrors coach_adjust.py):
  - JSON object on stdout
  - All logs on stderr
  - Exit code 0 on success (even if drift found), 1 on hard failure

Usage:
  python3 scripts/consistency_watchdog.py              # check today
  python3 scripts/consistency_watchdog.py --date 2026-04-10  # check specific date
  python3 scripts/consistency_watchdog.py --no-garmin  # DB-side only
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path

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
log = logging.getLogger("consistency_watchdog")


def alert_slack(message: str) -> None:
    """Post to #ascent-daily. Never raises."""
    token = os.environ.get("SLACK_BOT_TOKEN", "")
    channel = os.environ.get("SLACK_CHANNEL_DAILY", "")
    if not token or not channel:
        log.warning("Slack not configured — alert not sent: %s", message)
        return
    try:
        import requests
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"channel": channel, "text": message},
            timeout=10,
        )
        data = resp.json()
        if not data.get("ok"):
            log.warning("Slack alert failed: %s", data.get("error"))
        else:
            log.info("Slack alert sent")
    except Exception as e:
        log.warning("Slack alert failed: %s", e)


def fetch_todays_planned(sb, check_date: date) -> list[dict]:
    res = (
        sb.table("planned_workouts")
        .select("id,scheduled_date,session_name,session_type,status,garmin_workout_id")
        .eq("scheduled_date", check_date.isoformat())
        .execute()
    )
    return res.data or []


def fetch_garmin_today(client, check_date: date) -> list[dict]:
    """Fetch Garmin calendar entries for check_date only."""
    # Reuse reconcile_garmin's calendar fetch for the single month
    items = []
    try:
        payload = client.connectapi(
            f"/calendar-service/year/{check_date.year}/month/{check_date.month - 1}"
        )
    except Exception as exc:
        log.warning("Garmin calendar fetch failed: %s", exc)
        return []

    if not isinstance(payload, dict):
        return []

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
        if d != check_date:
            continue
        items.append({
            "scheduled_workout_id": item.get("id"),
            "workout_id": item.get("workoutId"),
            "date": d.isoformat(),
            "title": item.get("title"),
        })
    return items


def check_consistency(check_date: date, no_garmin: bool = False) -> dict:
    """Run the consistency check. Returns result dict."""
    result = {
        "ok": False,
        "date": check_date.isoformat(),
        "issues": [],
        "planned_count": 0,
        "garmin_count": 0,
    }

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    planned = fetch_todays_planned(sb, check_date)
    result["planned_count"] = len(planned)

    # Check 1: any non-rest session for today?
    active = [p for p in planned if p["status"] not in ("completed", "skipped", "rest")]
    rest_days = [p for p in planned if p["status"] == "rest"]

    if not planned:
        result["issues"].append({
            "type": "no_planned_row",
            "detail": f"No planned_workouts row exists for {check_date}",
        })

    if no_garmin:
        result["ok"] = True
        return result

    # Get Garmin side
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from garmin_auth import get_safe_client
        client = get_safe_client(require_garminconnect=True)
    except Exception as exc:
        result["issues"].append({
            "type": "garmin_auth_failed",
            "detail": f"Cannot connect to Garmin: {exc}",
        })
        result["ok"] = True  # not a consistency failure, just auth down
        return result

    garmin_items = fetch_garmin_today(client, check_date)
    result["garmin_count"] = len(garmin_items)
    garmin_wids = {str(g["workout_id"]) for g in garmin_items if g.get("workout_id")}

    # Check 2: DB rows with garmin_workout_id should have a matching Garmin entry
    for p in active:
        wid = p.get("garmin_workout_id")
        if wid and str(wid) not in garmin_wids:
            result["issues"].append({
                "type": "db_not_on_garmin",
                "detail": (
                    f"{p['session_name']} (garmin_id={wid}) is in DB but "
                    f"not scheduled on Garmin for {check_date}"
                ),
                "planned_workout_id": p["id"],
            })

    # Check 3: DB rows without garmin_workout_id (not pushed yet)
    for p in active:
        if not p.get("garmin_workout_id"):
            result["issues"].append({
                "type": "not_pushed",
                "detail": f"{p['session_name']} has no garmin_workout_id — not on watch",
                "planned_workout_id": p["id"],
            })

    # Check 4: Garmin entries with no matching DB row
    db_wids = {str(p["garmin_workout_id"]) for p in planned if p.get("garmin_workout_id")}
    for g in garmin_items:
        gwid = str(g.get("workout_id", ""))
        if gwid and gwid not in db_wids:
            result["issues"].append({
                "type": "orphan_garmin",
                "detail": (
                    f"Garmin has '{g['title']}' (wid={gwid}) scheduled for "
                    f"{check_date} but no DB row references it"
                ),
            })

    result["ok"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=str, help="Check date (YYYY-MM-DD). Default: today.")
    parser.add_argument("--no-garmin", action="store_true", help="Skip Garmin calls.")
    parser.add_argument("--quiet", action="store_true", help="Suppress stdout JSON on clean runs.")
    args = parser.parse_args()

    check_date = date.fromisoformat(args.date) if args.date else date.today()

    try:
        result = check_consistency(check_date, no_garmin=args.no_garmin)
    except Exception as exc:
        log.error("Watchdog failed: %s", exc)
        result = {"ok": False, "date": check_date.isoformat(), "error": str(exc), "issues": []}

    issues = result.get("issues", [])

    if issues:
        lines = [f":warning: *Consistency watchdog — {check_date}*"]
        for issue in issues:
            lines.append(f"• `{issue['type']}`: {issue['detail']}")
        alert_slack("\n".join(lines))
        log.warning("%d issue(s) found for %s", len(issues), check_date)

    if not args.quiet or issues:
        print(json.dumps(result, indent=2, default=str))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())

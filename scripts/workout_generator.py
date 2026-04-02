#!/usr/bin/env python3
"""Generate and manage planned workouts in Supabase.

Populates the planned_workouts table from workout_push.py's SESSIONS definitions,
applies progressive overload via the progression engine, and marks completed sessions.

Usage:
    python workout_generator.py --populate          # seed full 8-week program
    python workout_generator.py --mark-completed    # match sessions to activities
    python workout_generator.py --dry-run --populate # preview without writes
"""

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
)
log = logging.getLogger("workout_generator")

# Import program definitions from workout_push.py
from workout_push import (
    SESSIONS, WARMUP_PROTOCOLS, BARBELL_COMPOUNDS,
    BLOCK_1_START, BLOCK_2_START, BLOCK_2_END, DELOAD_WEEKS,
    DAY_TO_SESSION, get_program_week, is_deload_week, calculate_weight,
)


# ---------------------------------------------------------------------------
# workout_definition builder
# ---------------------------------------------------------------------------


def build_workout_definition(
    session_key: str,
    block: int,
    week: int,
    sb=None,
) -> dict:
    """Build the workout_definition JSONB for a planned_workouts row.

    Returns the app-facing JSON structure (not Garmin JSON).
    """
    session = SESSIONS[session_key]

    # RPE range based on block
    rpe_range = [6, 7] if block == 1 else [7, 8]

    # Warm-up exercises
    warmup = []
    for wu_name, wu_reps, wu_duration in WARMUP_PROTOCOLS.get(session_key, []):
        warmup.append({
            "name": wu_name,
            "reps": wu_reps,
            "duration_s": wu_duration,
        })

    # Working exercises with progressive weights
    exercises = []
    for ex in session["exercises"]:
        weight, note = calculate_weight(
            ex["name"], ex["start_kg"], block, week, sb=sb,
            target_reps=ex["reps"], target_sets=ex["sets"],
        )

        # Deload: keep weight, halve sets
        num_sets = ex["sets"]
        if is_deload_week(week):
            num_sets = max(1, num_sets // 2)

        exercise_def = {
            "name": ex["name"],
            "sets": num_sets,
            "reps": ex["reps"],
            "weight_kg": weight,
            "rest_s": ex["rest_s"],
            "equipment": _get_equipment(ex["name"]),
            "note": ex.get("note") or note if note != "formula fallback" else None,
        }

        # Include duration/distance for special exercises
        if ex.get("duration_s"):
            exercise_def["duration_s"] = ex["duration_s"]
        if ex.get("distance_m"):
            exercise_def["distance_m"] = ex["distance_m"]

        exercises.append(exercise_def)

    return {
        "session_label": session_key,
        "session_name": session["name"],
        "estimated_duration_minutes": session["estimated_duration_minutes"],
        "rpe_range": rpe_range,
        "warmup": warmup,
        "exercises": exercises,
    }


def _get_equipment(exercise_name: str) -> str:
    """Determine equipment type from exercise name."""
    if exercise_name in BARBELL_COMPOUNDS:
        return "barbell"
    if exercise_name.startswith("KB "):
        return "kettlebell"
    if exercise_name.startswith("Dumbbell ") or exercise_name.startswith("DB "):
        return "dumbbell"
    if "Cable" in exercise_name:
        return "cable"
    if exercise_name in ("Chin-ups", "Dead Bugs", "Copenhagen Plank", "Pallof Walkouts"):
        return "bodyweight"
    if "Split Squat" in exercise_name:
        return "dumbbell"
    if "Lateral Raises" in exercise_name:
        return "dumbbell"
    if "Farmer Carry" in exercise_name:
        return "kettlebell"
    if "Trap Bar" in exercise_name:
        return "barbell"
    return "other"


# ---------------------------------------------------------------------------
# Populate full 8-week program
# ---------------------------------------------------------------------------


def get_week_monday(week_num: int) -> date:
    """Get the Monday of a given program week (1-8)."""
    # Week 1 starts April 1 (Tuesday), but the Monday of that week is March 31
    # However, BLOCK_1_START is April 1 (Wednesday in 2026)
    # Week boundaries: week 1 = Apr 1-6, week 2 = Apr 7-13, etc.
    week_start = BLOCK_1_START + timedelta(weeks=week_num - 1)
    # Go back to the Monday of that week
    days_since_monday = week_start.weekday()  # 0=Mon, 1=Tue, ...
    return week_start - timedelta(days=days_since_monday)


def get_gym_dates(week_num: int) -> list[tuple[date, str]]:
    """Get (date, session_key) pairs for gym days in a given week.

    Returns list of (date, session_key) for Mon/Wed/Fri.
    Week 1 is special: starts Wednesday (no Monday session).
    """
    monday = get_week_monday(week_num)
    gym_days = []

    for day_offset, session_key in [(0, "B"), (2, "A"), (4, "C")]:
        gym_date = monday + timedelta(days=day_offset)

        # Week 1 exception: program starts Apr 1 (Wednesday), skip Monday
        if week_num == 1 and gym_date < BLOCK_1_START:
            continue

        # Don't schedule past program end
        if gym_date > BLOCK_2_END:
            continue

        gym_days.append((gym_date, session_key))

    return gym_days


def populate_full_program(sb, dry_run: bool = False) -> int:
    """Generate all 8 weeks of planned_workouts rows.

    Returns count of rows written.
    """
    rows = []

    for week_num in range(1, 9):
        block = 1 if week_num <= 4 else 2
        gym_dates = get_gym_dates(week_num)

        for gym_date, session_key in gym_dates:
            workout_def = build_workout_definition(
                session_key, block, week_num, sb=sb,
            )

            block_name = f"Base Rebuild Block {block}"
            if is_deload_week(week_num):
                block_name += " (Deload)"

            row = {
                "training_block": block_name,
                "week_number": week_num,
                "session_name": workout_def["session_name"],
                "session_type": "strength",
                "scheduled_date": gym_date.isoformat(),
                "scheduled_time": "19:00",
                "estimated_duration_minutes": workout_def["estimated_duration_minutes"],
                "workout_definition": workout_def,
                "status": "planned",
            }
            rows.append(row)

    log.info("Generated %d planned workouts across 8 weeks", len(rows))

    if dry_run:
        for r in rows:
            ex_names = [e["name"] for e in r["workout_definition"]["exercises"]]
            log.info("[DRY RUN] Week %d | %s | %s | %s",
                     r["week_number"], r["scheduled_date"],
                     r["session_name"], ", ".join(ex_names))
        return len(rows)

    # Upsert to Supabase — use scheduled_date + session_name as conflict key
    # Since there's no unique constraint on these, delete existing first then insert
    existing = sb.table("planned_workouts").select("id,scheduled_date,session_name").execute()
    existing_map = {
        (r["scheduled_date"], r["session_name"]): r["id"]
        for r in (existing.data or [])
    }

    written = 0
    for row in rows:
        key = (row["scheduled_date"], row["session_name"])
        if key in existing_map:
            # Update existing row (preserve status if already completed/adjusted)
            existing_row = sb.table("planned_workouts").select("status").eq(
                "id", existing_map[key]
            ).execute()
            if existing_row.data and existing_row.data[0]["status"] in ("completed", "adjusted"):
                log.info("Skipping %s %s — already %s",
                         row["scheduled_date"], row["session_name"],
                         existing_row.data[0]["status"])
                continue
            sb.table("planned_workouts").update({
                "workout_definition": row["workout_definition"],
                "training_block": row["training_block"],
                "estimated_duration_minutes": row["estimated_duration_minutes"],
            }).eq("id", existing_map[key]).execute()
        else:
            sb.table("planned_workouts").insert(row).execute()

        written += 1
        log.info("Wrote: Week %d | %s | %s",
                 row["week_number"], row["scheduled_date"], row["session_name"])

    return written


# ---------------------------------------------------------------------------
# Mark completed sessions
# ---------------------------------------------------------------------------


def mark_completed_sessions(sb) -> int:
    """Match planned_workouts to actual training_sessions by date.

    Sets status='completed' for past dates with matching training activity.
    Sets status='skipped' for past dates without any activity.
    """
    today = date.today()

    # Get all non-completed planned workouts up to today
    planned = sb.table("planned_workouts").select(
        "id,scheduled_date,session_name,status"
    ).in_("status", ["planned", "adjusted"]).lte(
        "scheduled_date", today.isoformat()
    ).execute()

    if not planned.data:
        log.info("No pending planned workouts to check")
        return 0

    # Get all training sessions (strength activities) in the date range
    dates = [r["scheduled_date"] for r in planned.data]
    sessions = sb.table("training_sessions").select(
        "id,date,garmin_activity_id,name"
    ).in_("date", dates).execute()

    session_by_date = {}
    for s in (sessions.data or []):
        session_by_date[s["date"]] = s

    # Also check activities table for garmin_activity_id linkage
    activities = sb.table("activities").select(
        "date,garmin_activity_id,activity_type"
    ).in_("date", dates).eq("activity_type", "strength_training").execute()

    activity_by_date = {}
    for a in (activities.data or []):
        activity_by_date[a["date"]] = a

    updated = 0
    for pw in planned.data:
        pw_date = pw["scheduled_date"]
        session = session_by_date.get(pw_date)
        activity = activity_by_date.get(pw_date)

        if session or activity:
            update = {"status": "completed"}
            if activity and activity.get("garmin_activity_id"):
                update["actual_garmin_activity_id"] = activity["garmin_activity_id"]
            sb.table("planned_workouts").update(update).eq("id", pw["id"]).execute()
            log.info("Marked completed: %s %s", pw_date, pw["session_name"])
            updated += 1
        elif pw_date < today.isoformat():
            sb.table("planned_workouts").update(
                {"status": "skipped"}
            ).eq("id", pw["id"]).execute()
            log.info("Marked skipped: %s %s", pw_date, pw["session_name"])
            updated += 1

    return updated


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Generate and manage planned workouts")
    parser.add_argument("--populate", action="store_true",
                        help="Seed the full 8-week program into planned_workouts")
    parser.add_argument("--mark-completed", action="store_true",
                        help="Match planned workouts to actual training sessions")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without writing to Supabase")
    args = parser.parse_args()

    if not args.populate and not args.mark_completed:
        parser.print_help()
        sys.exit(1)

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    if args.populate:
        count = populate_full_program(sb, dry_run=args.dry_run)
        prefix = "[DRY RUN] " if args.dry_run else ""
        log.info("%sPopulate complete: %d workouts", prefix, count)

    if args.mark_completed and not args.dry_run:
        count = mark_completed_sessions(sb)
        log.info("Mark-completed: %d workouts updated", count)


if __name__ == "__main__":
    main()

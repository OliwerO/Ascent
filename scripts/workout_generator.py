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
import re
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
import mobility_workout


# ---------------------------------------------------------------------------
# Program-doc self-check
# ---------------------------------------------------------------------------
#
# Guards against the Tuesday-Protocol-A class of bug: silent drift between
# DAY_TO_SESSION (workout_push.py:88) and the human-authored weekly schedule
# in openclaw/coaching-program.md. Runs at module import so any code path
# that touches the generator (CLI, cron, ad-hoc) trips the assertion before
# it can write a wrong row.
#
# Parses the "Weekly Structure" markdown table and asserts that for every
# weekday with a Strength session, the letter (A/B/C) matches DAY_TO_SESSION.
# Days that are rest/mobility/mountain in the doc must be absent from the
# dict. Mismatches raise RuntimeError with a precise diff.

PROGRAM_DOC_PATH = PROJECT_ROOT / "openclaw" / "coaching-program.md"

_WEEKDAY_TO_INT = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6,
}


def _parse_program_weekly_structure(text: str) -> dict[int, str]:
    """Return {weekday_int: 'A'|'B'|'C'} parsed from the first Weekly Structure
    table in coaching-program.md. Only Strength rows are returned; rest /
    mobility / mountain rows are deliberately omitted."""
    expected: dict[int, str] = {}
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### Weekly Structure"):
            in_table = True
            continue
        if not in_table:
            continue
        if stripped.startswith("###") or stripped.startswith("## "):
            break  # next section
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells or cells[0] not in _WEEKDAY_TO_INT:
            continue
        weekday = _WEEKDAY_TO_INT[cells[0]]
        # Cell 1 is the session label, e.g. "**Strength B: Upper + Core**"
        label = cells[1] if len(cells) > 1 else ""
        if "Strength A" in label:
            expected[weekday] = "A"
        elif "Strength B" in label:
            expected[weekday] = "B"
        elif "Strength C" in label:
            expected[weekday] = "C"
        # Mobility / Rest / Mountain rows are intentionally not added
    return expected


def _validate_program_doc() -> None:
    if not PROGRAM_DOC_PATH.exists():
        raise RuntimeError(
            f"workout_generator self-check: coaching-program.md not found at "
            f"{PROGRAM_DOC_PATH}. Generator refuses to run blind."
        )
    text = PROGRAM_DOC_PATH.read_text(encoding="utf-8")
    expected = _parse_program_weekly_structure(text)
    if not expected:
        raise RuntimeError(
            "workout_generator self-check: parsed 0 strength rows from "
            "coaching-program.md Weekly Structure table. The table format "
            "may have changed. Refusing to generate against unknown structure."
        )
    actual = dict(DAY_TO_SESSION)
    if expected != actual:
        diff_lines = [
            "workout_generator self-check FAILED — DAY_TO_SESSION drifted from coaching-program.md",
            f"  expected (from coaching-program.md): {expected}",
            f"  actual   (from workout_push.py:88):  {actual}",
        ]
        for d in sorted(set(expected) | set(actual)):
            e = expected.get(d, "<absent>")
            a = actual.get(d, "<absent>")
            if e != a:
                weekday_name = [k for k, v in _WEEKDAY_TO_INT.items() if v == d][0]
                diff_lines.append(f"  {weekday_name}: doc={e}  code={a}")
        raise RuntimeError("\n".join(diff_lines))


_validate_program_doc()


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

        ex_note = ex.get("note") or note if note != "formula fallback" else None
        # Notes must never embed numeric kg values — Weight column is the single
        # source of truth. Stale snapshots in notes drift after re-generation.
        if ex_note and re.search(r"\d+(?:\.\d+)?\s*kg", ex_note):
            raise ValueError(
                f"Refusing to store note with embedded kg value for {ex['name']}: {ex_note!r}"
            )

        exercise_def = {
            "name": ex["name"],
            "sets": num_sets,
            "reps": ex["reps"],
            "weight_kg": weight,
            "rest_s": ex["rest_s"],
            "equipment": _get_equipment(ex["name"]),
            "note": ex_note,
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


def build_mobility_definition(protocol: str) -> dict:
    """Build the workout_definition JSONB for a mobility planned_workouts row.

    Mirrors `build_workout_definition` shape so the React training-plan card
    renders the same way as a strength session.
    """
    proto = protocol.upper()
    if proto not in ("A", "B", "C", "T"):
        raise ValueError(f"protocol must be A/B/C/T, got {protocol!r}")

    steps = mobility_workout.summarize_steps(proto)  # type: ignore[arg-type]

    exercises = []
    for s in steps:
        exercises.append({
            "name": s["name"],
            "sets": 1,
            "reps": s["reps"],
            "duration_s": s["duration_s"],
            "side": s["side"],
            "cue": s["cue"],
            "equipment": "bodyweight",
        })

    return {
        "session_label": f"mobility_{proto.lower()}",
        "session_name": f"Mobility (Protocol {proto})",
        "estimated_duration_minutes": mobility_workout.PROTOCOL_DURATIONS[proto],
        "rpe_range": [3, 5],
        "warmup": [],
        "exercises": exercises,
    }


def _get_equipment(exercise_name: str) -> str:
    """Determine equipment type from exercise name."""
    if exercise_name in BARBELL_COMPOUNDS:
        return "barbell"
    if exercise_name.startswith("Kettlebell ") or exercise_name.startswith("KB "):
        return "kettlebell"
    if exercise_name.startswith("Dumbbell ") or exercise_name.startswith("DB "):
        return "dumbbell"
    if "Cable" in exercise_name:
        return "cable"
    if exercise_name in ("Chin-Up", "Dead Bugs", "Copenhagen Plank", "Pallof Walkouts"):
        return "bodyweight"
    if "Split Squat" in exercise_name:
        return "dumbbell"
    if "Lateral Raise" in exercise_name:
        return "dumbbell"
    if "Farmer Carry" in exercise_name:
        return "kettlebell"
    if "Turkish Get-Up" in exercise_name:
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

    # ---- Mobility rows: every Tuesday gets Protocol A (Protocol C on deload)
    for week_num in range(1, 9):
        monday = get_week_monday(week_num)
        tuesday = monday + timedelta(days=1)
        if tuesday < BLOCK_1_START or tuesday > BLOCK_2_END:
            continue
        proto = "C" if is_deload_week(week_num) else "T"
        block = 1 if week_num <= 4 else 2
        block_name = f"Base Rebuild Block {block}"
        if is_deload_week(week_num):
            block_name += " (Deload)"
        mob_def = build_mobility_definition(proto)
        rows.append({
            "training_block": block_name,
            "week_number": week_num,
            "session_name": mob_def["session_name"],
            "session_type": "mobility",
            "scheduled_date": tuesday.isoformat(),
            "scheduled_time": "07:30",
            "estimated_duration_minutes": mob_def["estimated_duration_minutes"],
            "workout_definition": mob_def,
            "status": "planned",
        })

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
    """Mark past planned_workouts as skipped if no activity was recorded.

    Completion marking (status='completed') is owned by garmin_sync.py which
    has the actual Garmin activity ID.  This function only handles the
    'skipped' case: past-date rows still in planned/pushed/adjusted state
    with no matching training activity.
    """
    today = date.today()

    planned = sb.table("planned_workouts").select(
        "id,scheduled_date,session_name,status"
    ).in_("status", ["planned", "pushed", "adjusted"]).lte(
        "scheduled_date", today.isoformat()
    ).execute()

    if not planned.data:
        log.info("No pending planned workouts to check")
        return 0

    dates = [r["scheduled_date"] for r in planned.data]

    # Check both tables to avoid marking a completed session as skipped
    sessions = sb.table("training_sessions").select(
        "date"
    ).in_("date", dates).execute()
    session_dates = {s["date"] for s in (sessions.data or [])}

    activities = sb.table("activities").select(
        "date,activity_type"
    ).in_("date", dates).eq("activity_type", "strength_training").execute()
    activity_dates = {a["date"] for a in (activities.data or [])}

    has_activity = session_dates | activity_dates

    updated = 0
    for pw in planned.data:
        pw_date = pw["scheduled_date"]
        if pw_date < today.isoformat() and pw_date not in has_activity:
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

#!/usr/bin/env python3
"""Push structured workouts to Garmin Connect based on the current training program.

Reads coaching-context.md to determine the workout for a given day, queries
Supabase for previous weights, applies progressive overload rules, constructs
Garmin workout JSON, and uploads to Garmin Connect.

Usage:
    python workout_push.py --dry-run                    # preview next workout as JSON
    python workout_push.py --dry-run --session A        # preview Strength A
    python workout_push.py --dry-run --session B --date 2026-04-07  # Strength B for a date
    python workout_push.py --session A --date 2026-04-02            # upload Strength A
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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

COACHING_CONTEXT_PATH = PROJECT_ROOT / "openclaw" / "coaching-context.md"

TOKEN_STORE = PROJECT_ROOT / "garmin_tokens.json"  # legacy, kept for reference
GARTH_TOKEN_DIR = PROJECT_ROOT / ".garth"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("workout_push")

# ---------------------------------------------------------------------------
# Block / week determination
# ---------------------------------------------------------------------------

BLOCK_1_START = date(2026, 4, 1)   # Wednesday
BLOCK_1_END = date(2026, 4, 28)
BLOCK_2_START = date(2026, 4, 29)
BLOCK_2_END = date(2026, 5, 26)

DELOAD_WEEKS = {4, 8}  # Week 4 and Week 8 are deloads


def get_program_week(target_date: date) -> tuple[int, int]:
    """Return (block_number, week_number) for a given date.

    Block 1: Weeks 1-4 (Apr 1 - Apr 28)
    Block 2: Weeks 5-8 (Apr 29 - May 26)
    """
    if target_date < BLOCK_1_START:
        log.warning("Date %s is before Block 1 start. Defaulting to Block 1 Week 1.", target_date)
        return 1, 1
    if target_date > BLOCK_2_END:
        log.warning("Date %s is after Block 2 end. Defaulting to Block 2 Week 8.", target_date)
        return 2, 8

    days_from_start = (target_date - BLOCK_1_START).days
    week = (days_from_start // 7) + 1

    if week <= 4:
        return 1, week
    else:
        return 2, week


def is_deload_week(week: int) -> bool:
    return week in DELOAD_WEEKS


# ---------------------------------------------------------------------------
# Day → Session mapping
# ---------------------------------------------------------------------------

DAY_TO_SESSION = {
    0: "B",  # Monday
    2: "A",  # Wednesday
    4: "C",  # Friday
}


def get_session_for_date(target_date: date) -> str | None:
    """Return session letter (A/B/C) for a date, or None if not a gym day."""
    return DAY_TO_SESSION.get(target_date.weekday())


# ---------------------------------------------------------------------------
# Garmin exercise mapping
# ---------------------------------------------------------------------------

# Maps (category, exerciseName) for Garmin workout JSON
GARMIN_EXERCISE_MAP = {
    # Format: "exercise_name": ("GARMIN_CATEGORY", "GARMIN_EXERCISE_NAME")
    # Based on Garmin FIT SDK Profile v21.195.0 (see docs/knowledge-base/garmin-exercise-categories.md)
    # Where exact match doesn't exist, closest movement pattern is used with a note.

    # Strength A (Wednesday)
    "Barbell Back Squat":       ("SQUAT",          "BARBELL_BACK_SQUAT"),
    "Dumbbell Bench Press":     ("BENCH_PRESS",    "DUMBBELL_BENCH_PRESS"),
    "Barbell Row":              ("ROW",            "BARBELL_ROW"),
    "KB Swings":                ("HIP_RAISE",      "KETTLEBELL_SWING"),          # FIT SDK: HIP_RAISE category
    "KB Halo":                  ("WARM_UP",        "ARM_CIRCLES"),               # No exact match — use Arm Circles. Actual: KB Halo
    "KB Turkish Get-up":        ("CORE",           "TURKISH_GET_UP"),            # FIT SDK: CORE category

    # Strength B (Monday)
    "Overhead Press":           ("SHOULDER_PRESS",  "OVERHEAD_BARBELL_PRESS"),
    "DB Overhead Press":        ("SHOULDER_PRESS",  "DUMBBELL_SHOULDER_PRESS"),
    "Chin-ups":                 ("PULL_UP",         "CHIN_UP"),
    "Lat Pulldown":             ("PULL_UP",         "LAT_PULLDOWN"),
    "Dumbbell Incline Press":   ("BENCH_PRESS",     "INCLINE_DUMBBELL_BENCH_PRESS"),
    "Cable Row":                ("ROW",             "SEATED_CABLE_ROW"),
    "Dead Bugs":                ("HIP_STABILITY",   "DEAD_BUG"),                 # FIT SDK: HIP_STABILITY category
    "Copenhagen Plank":         ("PLANK",           "SIDE_PLANK"),               # No exact match — use Side Plank. Actual: Copenhagen Plank
    "Pallof Walkouts":          ("CORE",            "CABLE_CORE_PRESS"),         # FIT SDK: closest to Pallof press

    # Strength C (Friday)
    "Trap Bar Deadlift":        ("DEADLIFT",        "TRAP_BAR_DEADLIFT"),
    "KB Clean & Press":         ("OLYMPIC_LIFT",    "CLEAN_AND_PRESS"),          # FIT SDK: OLYMPIC_LIFT category
    "Single-Arm DB Row":        ("ROW",             "ONE_ARM_DUMBBELL_ROW"),
    "Bulgarian Split Squat":    ("LUNGE",           "DUMBBELL_BULGARIAN_SPLIT_SQUAT"),  # FIT SDK: LUNGE category
    "Lateral Raises":           ("LATERAL_RAISE",   "DUMBBELL_LATERAL_RAISE"),   # FIT SDK: LATERAL_RAISE category
    "KB Farmer Carry":          ("CARRY",           "FARMERS_WALK"),
}

# Garmin benchmark e1RMs (from user's Garmin Connect, as of Feb 2026)
# Used for benchmarkPercentage approach — Garmin calculates weight from these
GARMIN_BENCHMARKS = {
    "BARBELL_BACK_SQUAT": 133.3,
    "BARBELL_BENCH_PRESS": 102.9,
    "DUMBBELL_BENCH_PRESS": 33.8,      # per hand
    "BARBELL_ROW": 30.0,
    "OVERHEAD_BARBELL_PRESS": 66.7,
    "TRAP_BAR_DEADLIFT": 120.0,         # using barbell deadlift benchmark
    "DUMBBELL_LATERAL_RAISE": None,     # not set
    "CHIN_UP": None,                     # bodyweight
    "INCLINE_DUMBBELL_BENCH_PRESS": None,  # not set
    "SEATED_CABLE_ROW": None,            # not set
    "ONE_ARM_DUMBBELL_ROW": 80.0,        # per hand
    "DUMBBELL_BULGARIAN_SPLIT_SQUAT": None,  # not set
}

# Exercises where the Garmin name doesn't match the actual exercise
# These get a note in the description field
EXERCISE_NOTES = {
    "KB Halo":           "Actual exercise: Kettlebell Halo",
    "Copenhagen Plank":  "Actual exercise: Copenhagen Plank",
    "Pallof Walkouts":   "Actual exercise: Pallof Walkouts",
    "KB Clean & Press":  "Actual exercise: KB Clean & Press",
}

# Exercises that are barbell compounds (get +2.5kg/week progression)
BARBELL_COMPOUNDS = {
    "Barbell Back Squat",
    "Barbell Row",
    "Overhead Press",
    "Trap Bar Deadlift",
}

# Exercises that are DB/accessory (get +1kg/week progression)
DB_ACCESSORIES = {
    "Dumbbell Bench Press",
    "Dumbbell Incline Press",
    "DB Overhead Press",
    "Cable Row",
    "KB Swings",
    "KB Halo",
    "KB Turkish Get-up",
    "Chin-ups",
    "Lat Pulldown",
    "Dead Bugs",
    "Copenhagen Plank",
    "Pallof Walkouts",
    "KB Clean & Press",
    "Single-Arm DB Row",
    "Bulgarian Split Squat",
    "Lateral Raises",
    "KB Farmer Carry",
}

# ---------------------------------------------------------------------------
# Session definitions from coaching-context.md
# ---------------------------------------------------------------------------

# Each exercise: (name, sets, reps, rpe_low, rpe_high, rest_seconds, start_weight_kg)
# start_weight_kg is the Week 1 starting weight (conservative estimates)
# For bodyweight/timed exercises, weight may be None

SESSIONS = {
    # Starting weights calibrated from:
    # - Garmin benchmark e1RMs (as of Feb 2026)
    # - Last 3 strength sessions (Feb 11, 24, 25 2026)
    # - ~5 week detraining gap (Feb 25 → Apr 1): ~10% reduction applied
    # - RPE 6-7 target = ~55-65% of e1RM
    # - DB weights are PER HAND (Garmin benchmarks show single DB)
    #
    # Garmin benchmarks: Squat e1RM 133.3kg, Bench e1RM 102.9kg,
    # Deadlift e1RM 120kg, OHP e1RM 66.7kg, DB Bench 33.8kg/hand,
    # Barbell Row 30kg e1RM, DB Row 80kg/hand, DB Curl 32.7kg/hand
    "A": {
        "name": "Strength A: Full Body",
        "day": "Wednesday",
        "estimated_duration_minutes": 50,
        "exercises": [
            {"name": "Barbell Back Squat",   "sets": 3, "reps": 8,  "rpe_low": 6, "rpe_high": 7, "rest_s": 120, "start_kg": 70.0},
            {"name": "Dumbbell Bench Press",  "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 90,  "start_kg": 18.0},
            {"name": "Barbell Row",           "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 90,  "start_kg": 25.0},
            {"name": "KB Swings",             "sets": 3, "reps": 15, "rpe_low": 6, "rpe_high": 7, "rest_s": 60,  "start_kg": 24.0},
            {"name": "KB Halo",               "sets": 2, "reps": 10, "rpe_low": 5, "rpe_high": 6, "rest_s": 60,  "start_kg": 12.0},
            {"name": "KB Turkish Get-up",     "sets": 2, "reps": 3,  "rpe_low": 6, "rpe_high": 6, "rest_s": 90,  "start_kg": 12.0},
        ],
    },
    "B": {
        "name": "Strength B: Upper + Core",
        "day": "Monday",
        "estimated_duration_minutes": 40,
        "exercises": [
            {"name": "Overhead Press",        "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 90,  "start_kg": 35.0},
            {"name": "Chin-ups",              "sets": 3, "reps": 8,  "rpe_low": 6, "rpe_high": 7, "rest_s": 90,  "start_kg": None},
            {"name": "Dumbbell Incline Press", "sets": 2, "reps": 12, "rpe_low": 6, "rpe_high": 6, "rest_s": 60,  "start_kg": 14.0},
            {"name": "Cable Row",             "sets": 2, "reps": 12, "rpe_low": 6, "rpe_high": 6, "rest_s": 60,  "start_kg": 35.0},
            # Core circuit — 3 rounds, 30s between exercises
            {"name": "Dead Bugs",             "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 6, "rest_s": 30,  "start_kg": None},
            {"name": "Copenhagen Plank",      "sets": 3, "reps": 1,  "rpe_low": 6, "rpe_high": 6, "rest_s": 30,  "start_kg": None,
             "duration_s": 20, "note": "20s/side"},
            {"name": "Pallof Walkouts",       "sets": 3, "reps": 8,  "rpe_low": 6, "rpe_high": 6, "rest_s": 30,  "start_kg": None},
        ],
    },
    "C": {
        "name": "Strength C: Full Body Variant",
        "day": "Friday",
        "estimated_duration_minutes": 50,
        "exercises": [
            {"name": "Trap Bar Deadlift",     "sets": 3, "reps": 8,  "rpe_low": 6, "rpe_high": 7, "rest_s": 120, "start_kg": 65.0},
            {"name": "KB Clean & Press",      "sets": 3, "reps": 8,  "rpe_low": 6, "rpe_high": 7, "rest_s": 90,  "start_kg": 16.0},
            {"name": "Single-Arm DB Row",     "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 60,  "start_kg": 22.0},
            {"name": "Bulgarian Split Squat", "sets": 2, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 60,  "start_kg": 10.0},
            {"name": "Lateral Raises",        "sets": 2, "reps": 15, "rpe_low": 5, "rpe_high": 6, "rest_s": 60,  "start_kg": 6.0},
            {"name": "KB Farmer Carry",       "sets": 3, "reps": 1,  "rpe_low": 6, "rpe_high": 7, "rest_s": 60,  "start_kg": 24.0,
             "distance_m": 40, "note": "40m carry"},
        ],
    },
    # --- Consolidated 2x templates (used when 2+ mountain days in the week) ---
    "A2": {
        "name": "Consolidated A: Full Body Heavy",
        "day": "Wednesday",
        "estimated_duration_minutes": 55,
        "exercises": [
            {"name": "Barbell Back Squat",    "sets": 3, "reps": 8,  "rpe_low": 6, "rpe_high": 7, "rest_s": 120, "start_kg": 70.0},
            {"name": "Overhead Press",        "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 90,  "start_kg": 35.0},
            {"name": "Barbell Row",           "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 90,  "start_kg": 25.0},
            {"name": "KB Swings",             "sets": 3, "reps": 15, "rpe_low": 6, "rpe_high": 7, "rest_s": 60,  "start_kg": 24.0},
            {"name": "KB Halo",               "sets": 2, "reps": 10, "rpe_low": 5, "rpe_high": 6, "rest_s": 60,  "start_kg": 12.0},
            # Core circuit (3 rounds) — matches coaching-context.md consolidated A2
            {"name": "Dead Bugs",             "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 6, "rest_s": 30,  "start_kg": None},
            {"name": "Copenhagen Plank",      "sets": 3, "reps": 1,  "rpe_low": 6, "rpe_high": 6, "rest_s": 30,  "start_kg": None,
             "duration_s": 20, "note": "20s/side"},
            {"name": "Pallof Walkouts",       "sets": 3, "reps": 8,  "rpe_low": 6, "rpe_high": 6, "rest_s": 30,  "start_kg": None},
        ],
    },
    "B2": {
        "name": "Consolidated B: Full Body Functional",
        "day": "Friday",
        "estimated_duration_minutes": 55,
        "exercises": [
            {"name": "Trap Bar Deadlift",     "sets": 3, "reps": 8,  "rpe_low": 6, "rpe_high": 7, "rest_s": 120, "start_kg": 65.0},
            {"name": "KB Clean & Press",      "sets": 3, "reps": 8,  "rpe_low": 6, "rpe_high": 7, "rest_s": 90,  "start_kg": 16.0},
            {"name": "Chin-ups",              "sets": 3, "reps": 8,  "rpe_low": 6, "rpe_high": 7, "rest_s": 90,  "start_kg": None},
            {"name": "Bulgarian Split Squat", "sets": 2, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 60,  "start_kg": 10.0},
            {"name": "KB Turkish Get-up",     "sets": 2, "reps": 3,  "rpe_low": 6, "rpe_high": 6, "rest_s": 90,  "start_kg": 12.0},
            {"name": "KB Farmer Carry",       "sets": 3, "reps": 1,  "rpe_low": 6, "rpe_high": 7, "rest_s": 60,  "start_kg": 24.0,
             "distance_m": 40, "note": "40m carry"},
        ],
    },
}


# ---------------------------------------------------------------------------
# Progressive overload logic
# ---------------------------------------------------------------------------


def get_last_strength_session(sb, session_name_prefix: str) -> dict | None:
    """Query Supabase for the most recent completed strength session matching a name prefix.

    Looks in the activities table for strength_training activities with matching names,
    then checks raw_json for exercise/set data.

    Returns dict with exercise data or None.
    """
    try:
        result = sb.table("activities").select(
            "date,activity_name,raw_json,total_sets,total_reps"
        ).eq(
            "activity_type", "strength_training"
        ).like(
            "activity_name", f"%{session_name_prefix}%"
        ).order(
            "date", desc=True
        ).limit(1).execute()

        if result.data:
            return result.data[0]
    except Exception as exc:
        log.warning("Failed to query last strength session: %s", exc)
    return None


def calculate_weight(
    exercise_name: str,
    start_kg: float | None,
    block: int,
    week: int,
    last_session_data: dict | None,
) -> float | None:
    """Apply progressive overload rules to determine target weight.

    Block 1 (Weeks 1-3):
    - +2.5kg/week on barbell compounds
    - +1kg/week on DB/accessories
    - If RPE hit 8 before week 3, hold weight and add reps
    - Week 4: deload (same weight, 50% volume)

    Block 2 (Weeks 5-7):
    - Resume at Week 3 weights + 2.5kg
    - RPE 7-8 target
    - If RPE > 8, drop 5% for remaining sets
    - Week 8: deload
    """
    if start_kg is None:
        return None

    if week <= 3:
        # Block 1 progression: weeks 1-3 → 0, 1, 2 increments
        weeks_of_progression = week - 1
    elif week == 4:
        # Deload: same weight as week 3 (volume halved elsewhere)
        weeks_of_progression = 2
    elif week <= 7:
        # Block 2: resume at week 3 weight + one increment, then progress
        # Week 5=3, Week 6=4, Week 7=5 increments
        weeks_of_progression = week - 2
    else:
        # Week 8 deload: same weight as week 7
        weeks_of_progression = 5

    if exercise_name in BARBELL_COMPOUNDS:
        increment_per_week = 2.5
    elif exercise_name in DB_ACCESSORIES:
        increment_per_week = 1.0
    else:
        increment_per_week = 1.0

    target_kg = start_kg + (weeks_of_progression * increment_per_week)

    # Block 2 RPE check: if we had data showing RPE > 8, drop 5%
    # (This would use last_session_data in a full implementation)
    if block == 2 and last_session_data:
        # Placeholder for RPE-based adjustment
        # In practice, parse raw_json for RPE data from Garmin
        pass

    return round(target_kg, 1)


def calculate_sets(exercise: dict, week: int) -> int:
    """Return the number of sets, accounting for deload weeks."""
    base_sets = exercise["sets"]
    if is_deload_week(week):
        return max(1, base_sets // 2)  # 50% volume reduction
    return base_sets


# ---------------------------------------------------------------------------
# Garmin workout JSON construction
# ---------------------------------------------------------------------------

SPORT_TYPE = {
    "sportTypeId": 5,
    "sportTypeKey": "strength_training",
    "displayOrder": 5,
}

STEP_ORDER_COUNTER = 0


def make_step_order() -> int:
    global STEP_ORDER_COUNTER
    STEP_ORDER_COUNTER += 1
    return STEP_ORDER_COUNTER


def build_exercise_step(
    exercise_name: str,
    weight_kg: float | None,
    reps: int,
    step_order: int,
    duration_s: int | None = None,
    distance_m: int | None = None,
) -> dict:
    """Build a single Garmin ExecutableStepDTO for a working set.

    Weight is conveyed via benchmarkPercentage (if a Garmin benchmark exists)
    or via the description field (if not). Garmin's workout API does not
    reliably support direct weightValue on creation.
    """
    garmin_mapping = GARMIN_EXERCISE_MAP.get(exercise_name, ("OTHER", "OTHER"))
    category = garmin_mapping[0]
    garmin_exercise_name = garmin_mapping[1]

    # Build description: target weight + any exercise name note
    desc_parts = []
    if weight_kg is not None and weight_kg > 0:
        desc_parts.append(f"{weight_kg:.1f}kg")
    note = EXERCISE_NOTES.get(exercise_name)
    if note:
        desc_parts.append(note)
    description = " — ".join(desc_parts) if desc_parts else None

    step = {
        "type": "ExecutableStepDTO",
        "stepOrder": step_order,
        "stepType": {
            "stepTypeId": 3,
            "stepTypeKey": "interval",
            "displayOrder": 3,
        },
        "category": category,
        "exerciseName": garmin_exercise_name,
        "description": description,
    }

    # Set end condition based on exercise type
    if duration_s:
        step["endCondition"] = {
            "conditionTypeId": 2,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        }
        step["endConditionValue"] = float(duration_s)
    elif distance_m:
        step["endCondition"] = {
            "conditionTypeId": 3,
            "conditionTypeKey": "distance",
            "displayOrder": 3,
            "displayable": True,
        }
        step["endConditionValue"] = float(distance_m)
    else:
        step["endCondition"] = {
            "conditionTypeId": 10,
            "conditionTypeKey": "reps",
            "displayOrder": 10,
            "displayable": True,
        }
        step["endConditionValue"] = float(reps)

    # Weight: use benchmarkPercentage if a Garmin benchmark exists for this exercise
    benchmark_e1rm = GARMIN_BENCHMARKS.get(garmin_exercise_name)
    if weight_kg is not None and weight_kg > 0 and benchmark_e1rm:
        pct = round((weight_kg / benchmark_e1rm) * 100)
        pct = max(1, min(100, pct))  # clamp 1-100
        step["benchmarkPercentage"] = pct
        step["benchmarkKey"] = garmin_exercise_name

    return step


def build_rest_step(rest_seconds: int, step_order: int) -> dict:
    """Build a Garmin rest step."""
    return {
        "type": "ExecutableStepDTO",
        "stepOrder": step_order,
        "childStepId": None,
        "description": None,
        "stepType": {
            "stepTypeId": 5,
            "stepTypeKey": "rest",
            "displayOrder": 5,
        },
        "endCondition": {
            "conditionTypeId": 2,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        },
        "endConditionValue": float(rest_seconds),
        "preferredEndConditionUnit": None,
        "endConditionCompare": None,
        "targetType": {
            "workoutTargetTypeId": 1,
            "workoutTargetTypeKey": "no.target",
            "displayOrder": 1,
        },
        "targetValueOne": None,
        "targetValueTwo": None,
        "targetValueUnit": None,
        "zoneNumber": None,
        "secondaryTargetType": None,
        "secondaryTargetValueOne": None,
        "secondaryTargetValueTwo": None,
        "secondaryTargetValueUnit": None,
        "secondaryZoneNumber": None,
        "endConditionZone": None,
        "strokeType": {"strokeTypeId": 0, "strokeTypeKey": None, "displayOrder": 0},
        "equipmentType": {"equipmentTypeId": 0, "equipmentTypeKey": None, "displayOrder": 0},
        "category": None,
        "exerciseName": None,
        "workoutProvider": None,
        "providerExerciseSourceId": None,
        "weightValue": None,
        "weightUnit": None,
    }


def build_garmin_workout(
    session_key: str,
    block: int,
    week: int,
    target_date: date,
    sb=None,
    volume_reduction: float = 0.0,
    rpe_cap: int | None = None,
) -> dict:
    """Build the complete Garmin workout JSON for a session.

    Args:
        session_key: "A", "B", "C", "A2", or "B2"
        block: 1 or 2
        week: 1-8
        target_date: the date to schedule the workout
        sb: Supabase client (optional, for querying previous weights)
        volume_reduction: 0.0-1.0 fraction to reduce sets (e.g. 0.3 = drop 30%)
        rpe_cap: if set, clamp all RPE targets to this maximum
    """
    global STEP_ORDER_COUNTER
    STEP_ORDER_COUNTER = 0

    session = SESSIONS[session_key]
    exercises = session["exercises"]

    # Query last session data for progressive overload
    last_session = None
    if sb:
        last_session = get_last_strength_session(sb, session["name"].split(":")[0])

    # Build workout steps
    workout_steps = []

    for ex in exercises:
        num_sets = calculate_sets(ex, week)

        # Apply volume reduction (coaching agent can scale down on fatigued days)
        if volume_reduction > 0:
            num_sets = max(1, round(num_sets * (1 - volume_reduction)))

        weight = calculate_weight(
            ex["name"],
            ex["start_kg"],
            block,
            week,
            last_session,
        )

        for set_num in range(num_sets):
            # Working set
            step_order = make_step_order()
            step = build_exercise_step(
                exercise_name=ex["name"],
                weight_kg=weight,
                reps=ex["reps"],
                step_order=step_order,
                duration_s=ex.get("duration_s"),
                distance_m=ex.get("distance_m"),
            )
            workout_steps.append(step)

            # Rest period (skip after the last set of the last exercise)
            is_last_set = set_num == num_sets - 1
            is_last_exercise = ex is exercises[-1]
            if not (is_last_set and is_last_exercise):
                rest_order = make_step_order()
                rest = build_rest_step(ex["rest_s"], rest_order)
                workout_steps.append(rest)

    # Calculate estimated duration
    total_work_seconds = sum(
        calculate_sets(ex, week) * (ex.get("duration_s") or 5)  # ~5s per rep set
        + calculate_sets(ex, week) * ex["rest_s"]
        for ex in exercises
    )
    estimated_duration = max(
        total_work_seconds,
        session["estimated_duration_minutes"] * 60,
    )

    # Build workout name
    deload_tag = " (Deload)" if is_deload_week(week) else ""
    adj_tags = []
    if volume_reduction > 0:
        adj_tags.append(f"-{int(volume_reduction * 100)}% vol")
    if rpe_cap is not None:
        adj_tags.append(f"RPE≤{rpe_cap}")
    adj_suffix = f" [{', '.join(adj_tags)}]" if adj_tags else ""
    workout_name = f"Block {block} Wk{week} — {session['name']}{deload_tag}{adj_suffix}"

    rpe_display_low = min(exercises[0]["rpe_low"], rpe_cap) if rpe_cap else exercises[0]["rpe_low"]
    rpe_display_high = min(exercises[0]["rpe_high"], rpe_cap) if rpe_cap else exercises[0]["rpe_high"]

    workout = {
        "workoutName": workout_name,
        "description": (
            f"Ascent training program — Block {block}, Week {week}. "
            f"{'Deload week: same weight, 50% volume. ' if is_deload_week(week) else ''}"
            f"RPE target: {rpe_display_low}-{rpe_display_high}."
            f"{f' Volume reduced {int(volume_reduction * 100)}%.' if volume_reduction > 0 else ''}"
        ),
        "sportType": SPORT_TYPE,
        "estimatedDurationInSecs": estimated_duration,
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": SPORT_TYPE,
                "workoutSteps": workout_steps,
            }
        ],
    }

    return workout


# ---------------------------------------------------------------------------
# Weight summary for logging
# ---------------------------------------------------------------------------


def format_weight_summary(session_key: str, block: int, week: int) -> str:
    """Return a human-readable summary of target weights for logging."""
    session = SESSIONS[session_key]
    lines = [f"\n{session['name']} — Block {block}, Week {week}"]
    if is_deload_week(week):
        lines.append("  ** DELOAD WEEK — 50% volume, same weight **")
    lines.append("")

    for ex in session["exercises"]:
        num_sets = calculate_sets(ex, week)
        weight = calculate_weight(ex["name"], ex["start_kg"], block, week, None)

        if weight:
            weight_str = f"{weight}kg"
        elif ex.get("duration_s"):
            weight_str = f"{ex['duration_s']}s"
        elif ex.get("distance_m"):
            weight_str = f"{ex['distance_m']}m"
        else:
            weight_str = "BW"

        note = ex.get("note", "")
        note_str = f" ({note})" if note else ""
        reps_str = f"{ex['reps']}" if ex['reps'] > 1 else ""

        lines.append(
            f"  {ex['name']}: {num_sets}x{reps_str} @ {weight_str} "
            f"[RPE {ex['rpe_low']}-{ex['rpe_high']}, {ex['rest_s']}s rest]{note_str}"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Session exception handling
# ---------------------------------------------------------------------------


def check_session_exception(target_date: date) -> dict | None:
    """Read coaching-context.md and return exception info if one exists for target_date.

    Returns dict with keys: original_session, exception, reason, row_line_text
    or None if no exception for this date.
    """
    try:
        content = COACHING_CONTEXT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.warning("coaching-context.md not found at %s", COACHING_CONTEXT_PATH)
        return None

    date_str = target_date.isoformat()  # "2026-04-04"

    # Find lines in the Session Exceptions table matching this date
    for line in content.splitlines():
        # Match table rows: | date | original | exception | reason | status |
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        # split on | gives empty strings at start/end: ['', 'date', 'orig', 'exc', 'reason', 'status', '']
        cells = [c for c in cells if c]  # drop empties
        if len(cells) < 5:
            continue
        if cells[0] == date_str:
            return {
                "original_session": cells[1],
                "exception": cells[2],
                "reason": cells[3],
                "pushed_status": cells[4],
                "row_line_text": line,
            }

    return None


def parse_exception_exercises(exception_text: str) -> list[dict]:
    """Parse exception exercise text into structured exercise dicts.

    Example input:
        "Upper Body + Core (incline DB press 3×10, chest-supported row 3×10,
         landmine press 3×8/side, chin-ups 3×6-8, core circuit: ab wheel +
         bird dogs + suitcase carry)"

    Returns list of dicts with keys: name, sets, reps, mapped (bool).
    """
    exercises = []

    # Extract the parenthesised exercise list if present
    paren_match = re.search(r"\((.+)\)", exception_text, re.DOTALL)
    if paren_match:
        exercise_str = paren_match.group(1)
    else:
        # No parens — treat entire string after the label as exercise list
        # Strip leading label like "Upper Body + Core"
        exercise_str = exception_text

    # Split on commas, then on " + " for circuit-style lists
    parts = []
    for chunk in re.split(r",\s*", exercise_str):
        # Handle "core circuit: ab wheel + bird dogs + suitcase carry"
        if ":" in chunk:
            # "core circuit: ab wheel + bird dogs + ..."
            _, _, after_colon = chunk.partition(":")
            for sub in re.split(r"\s*\+\s*", after_colon.strip()):
                if sub.strip():
                    parts.append(sub.strip())
        elif " + " in chunk and not re.search(r"\d+[×x]\d+", chunk):
            # Only split on + if it's not part of an exercise with sets/reps
            for sub in re.split(r"\s*\+\s*", chunk):
                if sub.strip():
                    parts.append(sub.strip())
        else:
            parts.append(chunk.strip())

    for part in parts:
        if not part:
            continue

        # Try to parse "exercise_name SETSxREPS" or "exercise_name SETS×REPS"
        # Handles: "incline DB press 3×10", "chin-ups 3×6-8", "landmine press 3×8/side"
        match = re.match(
            r"^(.+?)\s+(\d+)\s*[×x]\s*(\d+)(?:\s*[-–]\s*\d+)?(?:/side)?$",
            part,
            re.IGNORECASE,
        )
        if match:
            name = match.group(1).strip()
            sets = int(match.group(2))
            reps = int(match.group(3))
        else:
            # No sets/reps found — default to 3x10 for strength, 3x1 for carries/holds
            name = part.strip()
            sets = 3
            reps = 10

        # Check if we have a Garmin mapping for this exercise (fuzzy match)
        mapped = _fuzzy_garmin_match(name) is not None

        exercises.append({
            "name": name,
            "sets": sets,
            "reps": reps,
            "mapped": mapped,
        })

    return exercises


def _fuzzy_garmin_match(exercise_name: str) -> tuple[str, str] | None:
    """Try to find a Garmin exercise mapping by fuzzy matching.

    Returns (category, garmin_exercise_name) or None.
    """
    name_lower = exercise_name.lower()

    # Direct match first
    if exercise_name in GARMIN_EXERCISE_MAP:
        return GARMIN_EXERCISE_MAP[exercise_name]

    # Keyword-based fallback mapping for common exception exercises
    FUZZY_MAP = {
        "incline db press":       ("BENCH_PRESS",     "INCLINE_DUMBBELL_BENCH_PRESS"),
        "incline dumbbell press": ("BENCH_PRESS",     "INCLINE_DUMBBELL_BENCH_PRESS"),
        "chest-supported row":    ("ROW",             "CHEST_SUPPORTED_DUMBBELL_ROW"),  # May not exist; fallback
        "chest supported row":    ("ROW",             "CHEST_SUPPORTED_DUMBBELL_ROW"),
        "landmine press":         ("SHOULDER_PRESS",  "SINGLE_ARM_LANDMINE_PRESS"),
        "chin-ups":               ("PULL_UP",         "CHIN_UP"),
        "chin ups":               ("PULL_UP",         "CHIN_UP"),
        "ab wheel":               ("CORE",            "AB_WHEEL_ROLLOUT"),
        "ab rollout":             ("CORE",            "AB_WHEEL_ROLLOUT"),
        "bird dogs":              ("HIP_STABILITY",   "BIRD_DOG"),
        "bird dog":               ("HIP_STABILITY",   "BIRD_DOG"),
        "suitcase carry":         ("CARRY",           "FARMERS_WALK"),  # Closest match
        "farmer carry":           ("CARRY",           "FARMERS_WALK"),
        "overhead press":         ("SHOULDER_PRESS",  "OVERHEAD_BARBELL_PRESS"),
        "db bench press":         ("BENCH_PRESS",     "DUMBBELL_BENCH_PRESS"),
        "dumbbell bench press":   ("BENCH_PRESS",     "DUMBBELL_BENCH_PRESS"),
        "barbell row":            ("ROW",             "BARBELL_ROW"),
        "cable row":              ("ROW",             "SEATED_CABLE_ROW"),
        "lateral raise":          ("LATERAL_RAISE",   "DUMBBELL_LATERAL_RAISE"),
        "lateral raises":         ("LATERAL_RAISE",   "DUMBBELL_LATERAL_RAISE"),
        "deadlift":               ("DEADLIFT",        "TRAP_BAR_DEADLIFT"),
        "squat":                  ("SQUAT",           "BARBELL_BACK_SQUAT"),
        "pull-ups":               ("PULL_UP",         "PULL_UP"),
        "pull ups":               ("PULL_UP",         "PULL_UP"),
    }

    for keyword, mapping in FUZZY_MAP.items():
        if keyword in name_lower:
            return mapping

    return None


def build_exception_workout(
    exception_info: dict,
    parsed_exercises: list[dict],
    block: int,
    week: int,
    target_date: date,
) -> dict:
    """Build a Garmin workout JSON from parsed exception exercises.

    Uses the same Garmin JSON structure as build_garmin_workout() but without
    progressive overload (exception workouts use whatever the coach prescribed).
    """
    global STEP_ORDER_COUNTER
    STEP_ORDER_COUNTER = 0

    workout_steps = []
    default_rest_s = 60

    for ex in parsed_exercises:
        garmin_mapping = _fuzzy_garmin_match(ex["name"]) or ("OTHER", "OTHER")
        category = garmin_mapping[0]
        garmin_exercise_name = garmin_mapping[1]

        for set_num in range(ex["sets"]):
            step_order = make_step_order()

            # Build description
            desc = ex["name"] if garmin_exercise_name == "OTHER" else None

            step = {
                "type": "ExecutableStepDTO",
                "stepOrder": step_order,
                "stepType": {
                    "stepTypeId": 3,
                    "stepTypeKey": "interval",
                    "displayOrder": 3,
                },
                "category": category,
                "exerciseName": garmin_exercise_name,
                "description": desc,
                "endCondition": {
                    "conditionTypeId": 10,
                    "conditionTypeKey": "reps",
                    "displayOrder": 10,
                    "displayable": True,
                },
                "endConditionValue": float(ex["reps"]),
            }
            workout_steps.append(step)

            # Rest between sets (skip after last set of last exercise)
            is_last_set = set_num == ex["sets"] - 1
            is_last_exercise = ex is parsed_exercises[-1]
            if not (is_last_set and is_last_exercise):
                rest_order = make_step_order()
                rest = build_rest_step(default_rest_s, rest_order)
                workout_steps.append(rest)

    # Extract label from exception text (before the parentheses)
    label_match = re.match(r"^([^(]+)", exception_info["exception"])
    label = label_match.group(1).strip() if label_match else "Exception Workout"

    deload_tag = " (Deload)" if is_deload_week(week) else ""
    workout_name = f"Block {block} Wk{week} — {label} (Exception){deload_tag}"

    workout = {
        "workoutName": workout_name,
        "description": (
            f"Session exception: {exception_info['reason'][:200]}. "
            f"Original: {exception_info['original_session']}."
        ),
        "sportType": SPORT_TYPE,
        "estimatedDurationInSecs": len(parsed_exercises) * 3 * 90,  # rough estimate
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": SPORT_TYPE,
                "workoutSteps": workout_steps,
            }
        ],
    }

    return workout


def update_exception_status(target_date: date) -> None:
    """Update the 'Pushed to Garmin' column from 'Pending' to 'Yes' in coaching-context.md."""
    try:
        content = COACHING_CONTEXT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.warning("Cannot update exception status: coaching-context.md not found")
        return

    date_str = target_date.isoformat()
    lines = content.splitlines()
    updated = False

    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        if date_str not in line:
            continue
        # Replace "Pending" with "Yes" in this row
        if "Pending" in line:
            lines[i] = line.replace("Pending", "Yes", 1)
            updated = True
            break

    if updated:
        COACHING_CONTEXT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        log.info("Updated exception status to 'Yes' for %s in coaching-context.md", date_str)
    else:
        log.warning("Could not find Pending exception for %s to update", date_str)


# ---------------------------------------------------------------------------
# Garmin client (imported pattern from garmin_sync.py)
# ---------------------------------------------------------------------------


def get_garmin_client():
    """Build a Garmin API client backed by garth's long-lived OAuth tokens.

    Uses garth for authentication (OAuth1 tokens last ~1 year, auto-refresh
    OAuth2 access tokens). Injects garth's Client into garminconnect's Garmin
    class so all API methods work with garth's auth.
    """
    import garth
    from garminconnect import Garmin

    garmin_email = os.environ.get("GARMIN_EMAIL", "")
    garmin_password = os.environ.get("GARMIN_PASSWORD", "")
    token_dir = str(GARTH_TOKEN_DIR)

    # Step 1: Try resuming saved OAuth tokens (~1 year lifetime)
    try:
        garth.resume(token_dir)
        garth.client.username
        log.info("Resumed garth session from saved OAuth tokens")
    except Exception as e:
        log.info("Garth token resume failed: %s", e)
        # Step 2: Fresh login
        log.info("Attempting garth credential login via SSO")
        garth.login(garmin_email, garmin_password)
        garth.save(token_dir)
        log.info("Garth login successful, tokens saved to %s", GARTH_TOKEN_DIR)

    # Build Garmin wrapper with garth's client injected
    client = Garmin()
    client.client = garth.client
    client.display_name = garth.client.username or garmin_email

    garth.save(token_dir)
    return client


# ---------------------------------------------------------------------------
# Garmin upload
# ---------------------------------------------------------------------------


def upload_workout(client, workout: dict) -> str | None:
    """Upload a workout to Garmin Connect. Returns workout ID or None."""
    try:
        response = client.upload_workout(workout)
        if response and isinstance(response, dict):
            workout_id = response.get("workoutId")
            log.info("Workout uploaded: ID %s", workout_id)
            return str(workout_id) if workout_id else None
        log.warning("Unexpected upload response: %s", response)
        return None
    except Exception as exc:
        log.error("Failed to upload workout: %s", exc)
        return None


def schedule_workout(client, workout_id: str, target_date: date) -> bool:
    """Schedule a workout on a specific date in Garmin Connect."""
    try:
        date_str = target_date.strftime("%Y-%m-%d")
        client.schedule_workout(workout_id, date_str)
        log.info("Workout %s scheduled for %s", workout_id, date_str)
        return True
    except Exception as exc:
        log.error("Failed to schedule workout %s: %s", workout_id, exc)
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Push structured workouts to Garmin Connect"
    )
    parser.add_argument(
        "--session",
        choices=["A", "B", "C", "A2", "B2"],
        help="Which workout session (A/B/C=standard, A2/B2=consolidated 2x template). "
             "Auto-detected from date if not specified.",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Target date (YYYY-MM-DD). Defaults to next gym day.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print workout JSON without uploading to Garmin.",
    )
    parser.add_argument(
        "--volume-reduction",
        type=float,
        default=0.0,
        help="Reduce volume by this fraction (0.0-1.0). E.g. 0.3 = drop 30%% of sets.",
    )
    parser.add_argument(
        "--rpe-cap",
        type=int,
        default=None,
        help="Cap all RPE targets at this value (e.g. 6).",
    )
    args = parser.parse_args()

    # Determine target date
    if args.date:
        target_date = date.fromisoformat(args.date)
    else:
        target_date = date.today()
        # If today is not a gym day, find next one
        if get_session_for_date(target_date) is None and args.session is None:
            for i in range(1, 8):
                candidate = target_date + timedelta(days=i)
                if get_session_for_date(candidate) is not None:
                    target_date = candidate
                    break

    # Determine session
    if args.session:
        session_key = args.session.upper()
    else:
        session_key = get_session_for_date(target_date)
        if session_key is None:
            log.error(
                "Date %s is not a gym day (Mon/Wed/Fri). "
                "Use --session to override or --date for a gym day.",
                target_date,
            )
            sys.exit(1)

    # Determine block and week
    block, week = get_program_week(target_date)
    log.info(
        "Target: %s (%s) — Session %s, Block %d, Week %d%s",
        target_date,
        target_date.strftime("%A"),
        session_key,
        block,
        week,
        " (DELOAD)" if is_deload_week(week) else "",
    )

    # Check for session exception before building workout
    exception_info = check_session_exception(target_date)
    is_exception = False

    if exception_info and exception_info["pushed_status"] != "Yes":
        log.info(
            "Session exception found for %s: %s → %s (reason: %s)",
            target_date,
            exception_info["original_session"],
            exception_info["exception"][:80],
            exception_info["reason"][:60],
        )
        parsed_exercises = parse_exception_exercises(exception_info["exception"])
        if parsed_exercises:
            is_exception = True
            workout = build_exception_workout(
                exception_info, parsed_exercises, block, week, target_date,
            )
            # Log parsed exercises
            log.info("Exception exercises:")
            for ex in parsed_exercises:
                mapped_str = "" if ex["mapped"] else " [unmapped → OTHER]"
                log.info("  %s: %dx%d%s", ex["name"], ex["sets"], ex["reps"], mapped_str)
        else:
            log.warning("Could not parse exception exercises, falling back to template")

    if not is_exception:
        # Normal template path
        # Connect to Supabase for previous weight data
        sb = None
        try:
            sb = create_client(SUPABASE_URL, SUPABASE_KEY)
            log.info("Connected to Supabase for progression data")
        except Exception as exc:
            log.warning("Could not connect to Supabase (progression will use defaults): %s", exc)

        # Build the workout
        workout = build_garmin_workout(
            session_key, block, week, target_date, sb,
            volume_reduction=args.volume_reduction,
            rpe_cap=args.rpe_cap,
        )

        # Log weight summary
        summary = format_weight_summary(session_key, block, week)
        log.info(summary)

    if args.dry_run:
        print("\n--- Garmin Workout JSON (dry run) ---")
        print(json.dumps(workout, indent=2))
        print("--- End ---\n")
        log.info("Dry run complete. No upload performed.")
        sys.exit(0)

    # Upload to Garmin
    log.info("Connecting to Garmin Connect...")
    client = get_garmin_client()

    workout_id = upload_workout(client, workout)
    if not workout_id:
        log.error("Workout upload failed.")
        sys.exit(1)

    # Schedule on target date
    if schedule_workout(client, workout_id, target_date):
        log.info("Done. Workout '%s' uploaded and scheduled for %s.", workout["workoutName"], target_date)
        # Update exception status if this was an exception workout
        if is_exception:
            update_exception_status(target_date)
    else:
        log.warning(
            "Workout uploaded (ID: %s) but scheduling failed. "
            "You may need to schedule it manually in Garmin Connect.",
            workout_id,
        )


if __name__ == "__main__":
    main()

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
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"]

COACHING_CONTEXT_PATH = PROJECT_ROOT / "openclaw" / "coaching-context.md"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("workout_push")

# ---------------------------------------------------------------------------
# Block / week determination — loaded from config/training_constants.json
# ---------------------------------------------------------------------------

_CONSTANTS_PATH = PROJECT_ROOT / "config" / "training_constants.json"
with open(_CONSTANTS_PATH) as _f:
    _CONSTANTS = json.load(_f)

_block_dates = _CONSTANTS["block_dates"]
BLOCK_1_START = date.fromisoformat(_block_dates["block_1_start"])
BLOCK_1_END = date.fromisoformat(_block_dates["block_1_end"])
BLOCK_2_START = date.fromisoformat(_block_dates["block_2_start"])
BLOCK_2_END = date.fromisoformat(_block_dates["block_2_end"])

DELOAD_WEEKS = set(_CONSTANTS["deload_weeks"])


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
    # Verified against connect.garmin.com/web-data/exercises/Exercises.json (2026-04-03)

    # Strength A (Wednesday)
    "Barbell Back Squat":       ("SQUAT",          "BARBELL_BACK_SQUAT"),
    "Dumbbell Bench Press":     ("BENCH_PRESS",    "DUMBBELL_BENCH_PRESS"),
    "Barbell Row":              ("ROW",            "BARBELL_ROW"),
    "Kettlebell Swing":         ("HIP_RAISE",      "KETTLEBELL_SWING"),
    "Kettlebell Halo":          ("WARM_UP",        "ARM_CIRCLES"),               # No exact match
    "Turkish Get-Up":           ("CORE",           "TURKISH_GET_UP"),

    # Strength B (Monday)
    "Overhead Press":           ("SHOULDER_PRESS",  "OVERHEAD_BARBELL_PRESS"),
    "DB Overhead Press":        ("SHOULDER_PRESS",  "DUMBBELL_SHOULDER_PRESS"),
    "DB/BB Overhead Press":     ("SHOULDER_PRESS",  "OVERHEAD_BARBELL_PRESS"),
    "Chin-Up":                  ("PULL_UP",         "CHIN_UP"),
    "Chin-ups":                 ("PULL_UP",         "CHIN_UP"),
    "DB Incline Press":         ("BENCH_PRESS",     "INCLINE_DUMBBELL_BENCH_PRESS"),
    "Lat Pulldown":             ("PULL_UP",         "LAT_PULLDOWN"),
    "Dumbbell Incline Press":   ("BENCH_PRESS",     "INCLINE_DUMBBELL_BENCH_PRESS"),
    "Cable Row":                ("ROW",             "SEATED_CABLE_ROW"),
    "Dead Bugs":                ("HIP_STABILITY",   "DEAD_BUG"),
    "Copenhagen Plank":         ("SUSPENSION",      "SIDE_PLANK"),               # No exact match
    "Pallof Walkouts":          ("CORE",            "CABLE_CORE_PRESS"),

    # Strength C (Friday)
    "Trap Bar Deadlift":        ("DEADLIFT",        "TRAP_BAR_DEADLIFT"),
    "KB Clean & Press":         ("SANDBAG",         "CLEAN_AND_PRESS"),
    "Single-Arm DB Row":        ("ROW",             "ONE_ARM_BENT_OVER_ROW"),
    "Bulgarian Split Squat":    ("LUNGE",           "DUMBBELL_BULGARIAN_SPLIT_SQUAT"),
    "Lateral Raise":            ("LATERAL_RAISE",   "DUMBBELL_LATERAL_RAISE"),
    "KB Farmer Carry":          ("CARRY",           "FARMERS_WALK"),

    # Exception / adjusted workout exercises
    "Incline DB Press":         ("BENCH_PRESS",     "INCLINE_DUMBBELL_BENCH_PRESS"),
    "Chest-Supported Row":      ("ROW",             "CHEST_SUPPORTED_DUMBBELL_ROW"),
    "Landmine Press":           ("SHOULDER_PRESS",  "SINGLE_ARM_DUMBBELL_SHOULDER_PRESS"),  # No exact match
    "Ab Wheel Rollout":         ("CORE",            "KNEELING_AB_WHEEL"),
    "Bird Dogs":                ("HIP_STABILITY",   "QUADRUPED_WITH_LEG_LIFT"),
    "Suitcase Carry":           ("CARRY",           "FARMERS_WALK"),

    # Home workout substitutes
    "Barbell Front Squat":      ("SQUAT",           "BARBELL_FRONT_SQUAT"),
    "DB Floor Press":           ("BENCH_PRESS",     "DUMBBELL_BENCH_PRESS"),
    "DB Swing":                 ("HIP_RAISE",       "KETTLEBELL_SWING"),          # Closest match
    "DB Halo":                  ("WARM_UP",         "ARM_CIRCLES"),               # No exact match
    "DB Turkish Get-Up":        ("CORE",            "TURKISH_GET_UP"),
    "Band-Assisted Inverted Row": ("ROW",           "INVERTED_ROW"),
    "Feet-Elevated Push-Up":    ("PUSH_UP",         "PUSH_UP"),
    "Band Row":                 ("ROW",             "BARBELL_ROW"),               # Closest match
    "Band Pallof Press":        ("CORE",            "CABLE_CORE_PRESS"),
    "Conventional Deadlift":    ("DEADLIFT",        "BARBELL_DEADLIFT"),
    "DB Clean & Press":         ("SANDBAG",         "CLEAN_AND_PRESS"),
    "DB Farmer Carry":          ("CARRY",           "FARMERS_WALK"),
    "Jump Rope":                ("CARDIO",          "JUMP_ROPE"),

    # Warm-up exercises (aligned with mobility_workout.EXERCISE_MAP)
    "Foam Roll T-Spine":        ("WARM_UP",         "FOAM_ROLLER"),
    "Ankle Mobilization":       ("WARM_UP",         "ANKLE_DORSIFLEXION_WITH_BAND"),
    "Goblet Squat Hold":        ("WARM_UP",         "GOBLET_SQUAT"),
    "World's Greatest Stretch": ("WARM_UP",         "WORLDS_GREATEST_STRETCH"),
    "Bodyweight Squat":         ("WARM_UP",         "BODY_WEIGHT_SQUAT"),
    "90/90 Hip Switch":         ("HIP_STABILITY",   "HIP_CIRCLES"),
    "Single-Leg RDL":           ("WARM_UP",         "SINGLE_LEG_DEADLIFT"),
    "Inchworm":                 ("WARM_UP",         "INCHWORM"),
    "Wall Slides":              ("WARM_UP",         "WALL_SLIDE"),
    "Band Pull-Aparts":        ("WARM_UP",          "BAND_PULL_APART"),
    "Thread the Needle":        ("WARM_UP",         "THORACIC_ROTATION"),
    "Half-Kneeling OH Press":   ("WARM_UP",         "HALF_KNEELING_OVERHEAD_PRESS"),
}

# Garmin benchmark e1RMs — loaded from config/training_constants.json
# Used for benchmarkPercentage approach — Garmin calculates weight from these
GARMIN_BENCHMARKS: dict[str, float | None] = _CONSTANTS["garmin_benchmarks"]

# Exercises where the Garmin name doesn't match the actual exercise
# These get a note in the description field
EXERCISE_NOTES = {
    "Kettlebell Halo":   "Actual exercise: Kettlebell Halo",
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
    "Kettlebell Swing",
    "Kettlebell Halo",
    "Turkish Get-Up",
    "Chin-Up",
    "Lat Pulldown",
    "Dead Bugs",
    "Copenhagen Plank",
    "Pallof Walkouts",
    "KB Clean & Press",
    "Single-Arm DB Row",
    "Bulgarian Split Squat",
    "Lateral Raise",
    "KB Farmer Carry",
}

# ---------------------------------------------------------------------------
# Home workout substitution system
# ---------------------------------------------------------------------------

# Equipment available at home — single-user, rarely changes
HOME_EQUIPMENT = {
    "barbell": {
        "bar_kg": 10.0,
        # All plates (including those normally on dumbbells)
        "plates_kg": [20, 20, 10, 10, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5,
                      1.25, 1.25, 1.25, 1.25, 1.25, 1.25, 1.25, 1.25,
                      2, 2],
        "max_load_kg": 100.0,
    },
    "dumbbell_adjustable": {
        "max_per_hand_kg": 12.5,
        "increments_kg": [1.25, 2.5],
    },
    "dumbbell_fixed": {
        "weights_kg": [20.0],
        "pairs": 1,
    },
    "bands": ["heavy", "medium", "light"],
    "gymnastic_rings": {"mounted": False},
    "jump_rope": True,
}

# Home workout substitution map — loaded from shared config
# Both this file and web/src/lib/homeWorkout.ts consume the same JSON
_HOME_CONFIG_PATH = PROJECT_ROOT / "config" / "home_substitutions.json"
with open(_HOME_CONFIG_PATH) as _f:
    _home_config = json.load(_f)

HOME_SUBSTITUTIONS: dict[str, dict] = _home_config["substitutions"]
HOME_COMPATIBLE = set(_home_config["home_compatible"])
_HOME_WEIGHT_CAPS: dict[str, float] = _home_config["weight_caps"]


def _apply_home_weight(
    exercise_name: str,
    gym_weight: float | None,
    equipment: str | None = None,
) -> float | None:
    """Apply home equipment weight constraints to an exercise."""
    if gym_weight is None:
        return None
    sub = HOME_SUBSTITUTIONS.get(exercise_name)
    if sub:
        strategy = sub["weight_strategy"]
        if strategy == "bodyweight":
            return None
        if strategy == "fixed":
            return sub["max_weight_kg"]
        if strategy == "cap_at":
            return min(gym_weight, sub["max_weight_kg"])
        return gym_weight  # "same"
    # Home-compatible: cap based on equipment type
    if equipment == "barbell":
        return min(gym_weight, _HOME_WEIGHT_CAPS["barbell"])
    if equipment == "dumbbell":
        return min(gym_weight, _HOME_WEIGHT_CAPS["dumbbell"])
    return gym_weight


def build_home_workout_definition(
    gym_definition: dict,
    include_jump_rope: bool = True,
) -> dict:
    """Convert a gym workout_definition to a home-equipment version.

    Pure function — no side effects. Returns a new dict.
    The original gym definition is stored under 'original_gym_definition'
    so the switch can be reversed.
    """
    from copy import deepcopy

    home = deepcopy(gym_definition)
    home["original_gym_definition"] = deepcopy(gym_definition)
    home["venue"] = "home"
    home["session_name"] = home.get("session_name", "") + " (Home)"

    # --- Substitute exercises ---
    substituted_count = 0
    for ex in home.get("exercises", []):
        name = ex.get("name", "")
        equipment = ex.get("equipment")
        sub = HOME_SUBSTITUTIONS.get(name)
        if sub:
            ex["name"] = sub["name"]
            ex["equipment"] = sub["equipment"]
            ex["weight_kg"] = _apply_home_weight(name, ex.get("weight_kg"), equipment)
            ex["note"] = sub["note"]
            substituted_count += 1
        elif name in HOME_COMPATIBLE:
            # Keep exercise but cap weight to home limits
            ex["weight_kg"] = _apply_home_weight(name, ex.get("weight_kg"), equipment)
        # Exercises not in either map are kept as-is (bodyweight core etc.)

    # --- Jump rope warm-up ---
    if include_jump_rope:
        warmup = home.get("warmup", [])
        warmup.insert(0, {"name": "Jump Rope", "reps": None, "duration_s": 180})
        home["warmup"] = warmup

    return home


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
            {"name": "Kettlebell Swing",             "sets": 3, "reps": 15, "rpe_low": 6, "rpe_high": 7, "rest_s": 60,  "start_kg": 24.0},
            {"name": "Kettlebell Halo",               "sets": 2, "reps": 10, "rpe_low": 5, "rpe_high": 6, "rest_s": 60,  "start_kg": 12.0},
            {"name": "Turkish Get-Up",     "sets": 2, "reps": 3,  "rpe_low": 6, "rpe_high": 6, "rest_s": 90,  "start_kg": 12.0},
        ],
    },
    "B": {
        "name": "Strength B: Upper + Core",
        "day": "Monday",
        "estimated_duration_minutes": 40,
        "exercises": [
            {"name": "Overhead Press",        "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 90,  "start_kg": 35.0},
            {"name": "Chin-Up",              "sets": 3, "reps": 8,  "rpe_low": 6, "rpe_high": 7, "rest_s": 90,  "start_kg": None},
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
            {"name": "Lateral Raise",        "sets": 2, "reps": 15, "rpe_low": 5, "rpe_high": 6, "rest_s": 60,  "start_kg": 6.0},
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
            {"name": "Kettlebell Swing",             "sets": 3, "reps": 15, "rpe_low": 6, "rpe_high": 7, "rest_s": 60,  "start_kg": 24.0},
            {"name": "Kettlebell Halo",               "sets": 2, "reps": 10, "rpe_low": 5, "rpe_high": 6, "rest_s": 60,  "start_kg": 12.0},
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
            {"name": "Chin-Up",              "sets": 3, "reps": 8,  "rpe_low": 6, "rpe_high": 7, "rest_s": 90,  "start_kg": None},
            {"name": "Bulgarian Split Squat", "sets": 2, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 60,  "start_kg": 10.0},
            {"name": "Turkish Get-Up",     "sets": 2, "reps": 3,  "rpe_low": 6, "rpe_high": 6, "rest_s": 90,  "start_kg": 12.0},
            {"name": "KB Farmer Carry",       "sets": 3, "reps": 1,  "rpe_low": 6, "rpe_high": 7, "rest_s": 60,  "start_kg": 24.0,
             "distance_m": 40, "note": "40m carry"},
        ],
    },
}


def load_sessions_from_db(sb, block_number: int = 1) -> dict | None:
    """Load session definitions from program_sessions table (canonical source).

    Returns a dict in the same format as SESSIONS, or None if DB is unavailable.
    Only loads strength sessions (A, B, C, A2, B2).
    """
    try:
        result = sb.table("program_sessions").select(
            "session_key, name, estimated_duration_minutes, exercises"
        ).eq("block_id", block_number).execute()
        if not result.data:
            return None

        sessions = {}
        # Map session_key to day (matches DAY_TO_SESSION)
        key_to_day = {"A": "Wednesday", "B": "Monday", "C": "Friday",
                      "A2": "Wednesday", "B2": "Friday"}

        for row in result.data:
            key = row["session_key"]
            if key not in key_to_day:
                continue  # Skip mobility, rest, etc.

            exercises = []
            for ex in row["exercises"]:
                exercises.append({
                    "name": ex["name"],
                    "sets": ex.get("sets", 0),
                    "reps": ex.get("reps", 0),
                    "rpe_low": ex.get("rpe_low", 6),
                    "rpe_high": ex.get("rpe_high", 7),
                    "rest_s": ex.get("rest_s", 60),
                    "start_kg": ex.get("start_kg"),
                    **({"duration_s": ex["duration_s"]} if "duration_s" in ex else {}),
                    **({"distance_m": ex["distance_m"]} if "distance_m" in ex else {}),
                    **({"note": ex["notes"]} if "notes" in ex else {}),
                })

            sessions[key] = {
                "name": row["name"],
                "day": key_to_day[key],
                "estimated_duration_minutes": row["estimated_duration_minutes"] or 50,
                "exercises": exercises,
            }

        if sessions:
            log.info("Loaded %d session templates from DB (block %d)", len(sessions), block_number)
            return sessions
        return None
    except Exception as exc:
        log.warning("Could not load sessions from DB, using hardcoded: %s", exc)
        return None


def get_sessions(sb=None, block_number: int = 1) -> dict:
    """Get session definitions.

    NOTE 2026-04-08: DB program_sessions is intentionally NOT consulted here.
    The DB had drifted from the canonical static `SESSIONS` dict (different
    exercise names, different start_kg values), causing workout_push to
    disagree with workout_generator (which uses SESSIONS). Since the React
    app reads `planned_workouts` written from SESSIONS, the static dict is
    the source of truth for now. Re-enable the DB path only after the
    program_sessions table is rebuilt from SESSIONS and a cross-check test
    asserts they stay in sync.
    """
    return SESSIONS


# ---------------------------------------------------------------------------
# Progressive overload logic
# ---------------------------------------------------------------------------


def calculate_weight(
    exercise_name: str,
    start_kg: float | None,
    block: int,
    week: int,
    sb=None,
    target_reps: int = 8,
    target_sets: int = 3,
) -> tuple[float | None, str]:
    """Apply smart progressive overload based on actual performance data.

    Uses progression_engine to query training_sets for last actual weights
    and apply double progression logic. Falls back to formula if no data.

    Returns (weight_kg, progression_note).
    """
    if start_kg is None:
        return None, "bodyweight"

    # Try data-driven progression via the engine
    if sb:
        try:
            from progression_engine import calculate_next_weight, record_progression

            result = calculate_next_weight(
                sb, exercise_name,
                target_reps=target_reps,
                target_sets=target_sets,
                current_week=week,
                start_kg=start_kg,
            )

            # Record the decision to exercise_progression table
            from datetime import date
            record_progression(sb, exercise_name, date.today().isoformat(), result,
                               planned_rpe=7.0 if block == 1 else 8.0)

            w = result.weight_kg
            if exercise_name in BARBELL_COMPOUNDS:
                w = round_to_plates(w)
            return round(w, 2), result.note

        except Exception as exc:
            log.warning("Progression engine failed for %s, using formula fallback: %s",
                        exercise_name, exc)

    # Formula fallback (no Supabase or engine failure)
    if week <= 3:
        weeks_of_progression = week - 1
    elif week == 4:
        weeks_of_progression = 2
    elif week <= 7:
        weeks_of_progression = week - 2
    else:
        weeks_of_progression = 5

    if exercise_name in BARBELL_COMPOUNDS:
        increment_per_week = 2.5
    else:
        increment_per_week = 1.0

    target_kg = start_kg + (weeks_of_progression * increment_per_week)
    if exercise_name in BARBELL_COMPOUNDS:
        target_kg = round_to_plates(target_kg)
    return round(target_kg, 2), "formula fallback"


BARBELL_BAR_KG = 20.0  # standard Olympic bar
SMALLEST_PLATE_PAIR_KG = 2.5  # 1.25 kg per side, smallest pair commonly stocked


def round_to_plates(weight_kg: float, bar_kg: float = BARBELL_BAR_KG,
                    pair_kg: float = SMALLEST_PLATE_PAIR_KG) -> float:
    """Round a target weight to the nearest achievable barbell load.

    Assumes a standard bar plus pairs of plates of size `pair_kg`. Anything
    below the bar weight is rounded UP to the bar (you can't load less than
    the bar itself). Above the bar, the load above the bar is rounded to the
    nearest multiple of `pair_kg`.

    Examples (bar=20, pair=2.5):
        47.5 → 47.5   (20 + 11×2.5 = 47.5; valid as-is)
        46.3 → 47.5   (20 + 10.625 → round to 11 pairs)
        18.0 → 20.0   (below bar)
    """
    if weight_kg < bar_kg:
        return bar_kg
    over_bar = weight_kg - bar_kg
    rounded_over = round(over_bar / pair_kg) * pair_kg
    return round(bar_kg + rounded_over, 2)


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


def build_warmup_step(
    exercise_name: str,
    reps: int | None = None,
    duration_s: int | None = None,
    step_order: int = 0,
) -> dict:
    """Build a Garmin warmup step as an interval (stepTypeId: 3).

    Uses stepTypeId 3 ("interval") instead of 1 ("warmup") because Garmin
    watches collapse multiple warmup-type steps into a single hidden phase.
    Interval steps render individually on the watch, matching the behavior
    of standalone mobility workouts (mobility_workout.py).
    """
    # Safe fallback: ARM_CIRCLES is a known-valid Garmin warmup exerciseName
    # used elsewhere in GARMIN_EXERCISE_MAP for unmappable items. "OTHER"
    # triggers Garmin API "Invalid category" 400.
    garmin_mapping = GARMIN_EXERCISE_MAP.get(exercise_name, ("WARM_UP", "ARM_CIRCLES"))
    category = garmin_mapping[0]
    garmin_exercise_name = garmin_mapping[1]

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
        "description": exercise_name,
    }

    if duration_s:
        step["endCondition"] = {
            "conditionTypeId": 2,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        }
        step["endConditionValue"] = float(duration_s)
    elif reps:
        step["endCondition"] = {
            "conditionTypeId": 10,
            "conditionTypeKey": "reps",
            "displayOrder": 10,
            "displayable": True,
        }
        step["endConditionValue"] = float(reps)

    return step


# Toggle: prepend Protocol B (Domain 9 §9.6) mobility steps before the
# session-specific warm-up. Set False to revert to the legacy warm-up only.
MOBILITY_PREPEND = True  # uses build_warmup_step + GARMIN_EXERCISE_MAP fallback (validated)

# Warm-up protocols per session type (from Domain 9: Mobility, Protocol B)
WARMUP_PROTOCOLS = {
    # B1 — Squat day (ankle, hip, thoracic focus)
    "A": [
        ("Foam Roll T-Spine", None, 120),        # 2 min segmental extension
        ("Ankle Mobilization", 10, None),         # 10 reps each side (shown as 10)
        ("Goblet Squat Hold", None, 15),          # 15s hold at bottom, prying
        ("World's Greatest Stretch", 6, None),    # 3 reps each side
        ("Bodyweight Squat", 5, None),            # 5 reps with 3s pause
    ],
    # B2 — Hinge day (hamstring, hip, posterior chain focus)
    "C": [
        ("Foam Roll T-Spine", None, 60),          # 1 min foam roll
        ("90/90 Hip Switch", 10, None),            # 5 transitions each direction
        ("Single-Leg RDL", 6, None),               # 6 reps each side, BW
        ("Inchworm", 5, None),                     # 5 reps inchworm to downdog
        ("World's Greatest Stretch", 6, None),     # 3 each side
    ],
    # B3 — Upper body day (thoracic, shoulder, scapular focus)
    "B": [
        ("Foam Roll T-Spine", None, 120),         # 2 min T-spine + lats
        ("Wall Slides", 8, None),                  # 8 reps
        ("Band Pull-Aparts", 10, None),            # 10 reps
        ("Thread the Needle", 8, None),            # 8 reps each side
    ],
}
# Consolidated sessions use the same warm-ups
WARMUP_PROTOCOLS["A2"] = WARMUP_PROTOCOLS["A"]
WARMUP_PROTOCOLS["B2"] = WARMUP_PROTOCOLS["C"]


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

    # Weight: set directly via weightValue (benchmarkPercentage causes 400 errors)
    if weight_kg is not None and weight_kg > 0:
        step["weightValue"] = weight_kg
        step["weightUnit"] = {"unitId": 8, "unitKey": "kilogram", "factor": 1000.0}

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


def build_repeat_group(num_iterations: int, child_steps: list[dict],
                       step_order: int) -> dict:
    """Wrap a list of child steps in a Garmin RepeatGroupDTO.

    Garmin's strength workout schema lets you say "do these N child steps M
    times" instead of inlining N×M ExecutableStepDTOs. The watch then renders
    "Set 1/3", "Set 2/3" instead of N independent exercises.
    """
    return {
        "type": "RepeatGroupDTO",
        "stepOrder": step_order,
        "stepType": {
            "stepTypeId": 6,
            "stepTypeKey": "repeat",
            "displayOrder": 6,
        },
        "numberOfIterations": num_iterations,
        "smartRepeat": False,
        "endCondition": {
            "conditionTypeId": 7,
            "conditionTypeKey": "iterations",
            "displayOrder": 7,
            "displayable": False,
        },
        "endConditionValue": float(num_iterations),
        "workoutSteps": child_steps,
        "skipLastRestStep": False,
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

    sessions = get_sessions(sb, block)
    session = sessions[session_key]
    exercises = session["exercises"]

    # Build workout steps — start with warm-up protocol
    workout_steps = []

    # Optionally prepend Protocol B mobility steps for this session's target.
    # We re-use build_warmup_step (and its validated GARMIN_EXERCISE_MAP) so
    # any unknown exercise falls back to ('WARM_UP','ARM_CIRCLES') instead of
    # crashing the entire upload with "Invalid category".
    if MOBILITY_PREPEND:
        try:
            import mobility_workout  # local import keeps test-time cycles minimal
            mob_target = session_key.rstrip("2")  # 'A2'/'B2' → 'A'/'B'
            if mob_target in mobility_workout.PROTOCOL_B_BY_TARGET:
                for wu_name, wu_reps, wu_duration in mobility_workout.protocol_b_warmup_tuples(mob_target):
                    workout_steps.append(
                        build_warmup_step(
                            exercise_name=wu_name,
                            reps=wu_reps,
                            duration_s=wu_duration,
                            step_order=make_step_order(),
                        )
                    )
        except Exception as exc:
            log.warning("mobility prepend skipped: %s", exc)

    warmup_exercises = WARMUP_PROTOCOLS.get(session_key, [])
    for wu_name, wu_reps, wu_duration in warmup_exercises:
        wu_step = build_warmup_step(
            exercise_name=wu_name,
            reps=wu_reps,
            duration_s=wu_duration,
            step_order=make_step_order(),
        )
        workout_steps.append(wu_step)

    progression_notes = []  # Collect progression decisions for summary

    for ex in exercises:
        num_sets = calculate_sets(ex, week)

        # Apply volume reduction (coaching agent can scale down on fatigued days)
        if volume_reduction > 0:
            num_sets = max(1, round(num_sets * (1 - volume_reduction)))

        weight, prog_note = calculate_weight(
            ex["name"],
            ex["start_kg"],
            block,
            week,
            sb=sb,
            target_reps=ex["reps"],
            target_sets=ex["sets"],
        )
        progression_notes.append((ex["name"], weight, prog_note))

        # Build ONE working set + ONE rest step as the child template, then
        # wrap them in a RepeatGroupDTO with numberOfIterations = num_sets.
        # The watch will render "Set 1/N", "Set 2/N" etc. instead of
        # showing the same exercise N times in a flat list.
        group_order = make_step_order()
        child_set = build_exercise_step(
            exercise_name=ex["name"],
            weight_kg=weight,
            reps=ex["reps"],
            step_order=make_step_order(),
            duration_s=ex.get("duration_s"),
            distance_m=ex.get("distance_m"),
        )
        children = [child_set]
        is_last_exercise = ex is exercises[-1]
        # Include a rest step inside the group so it repeats with each set,
        # except for the very last exercise (where the final rest is dead time).
        if not is_last_exercise:
            children.append(build_rest_step(ex["rest_s"], make_step_order()))
        elif num_sets > 1:
            # For the last exercise, we still want a rest BETWEEN its sets,
            # but not AFTER the final set. Garmin's smartRepeat=False with a
            # rest child will rest after every iteration including the last,
            # so we accept one trailing rest on the last exercise as a known
            # cosmetic blemish in exchange for proper grouping.
            children.append(build_rest_step(ex["rest_s"], make_step_order()))
        workout_steps.append(build_repeat_group(num_sets, children, group_order))

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
    workout_name = f"{session['name']}{deload_tag} | Block {block} Wk{week}{adj_suffix}"

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
        "_progression_notes": progression_notes,
    }

    return workout


# ---------------------------------------------------------------------------
# Weight summary for logging
# ---------------------------------------------------------------------------


def format_weight_summary(session_key: str, block: int, week: int,
                          progression_notes: list | None = None, sb=None) -> str:
    """Return a human-readable summary of target weights for logging."""
    sessions = get_sessions(sb, block)
    session = sessions[session_key]
    lines = [f"\n{session['name']} — Block {block}, Week {week}"]
    if is_deload_week(week):
        lines.append("  ** DELOAD WEEK — 50% volume, same weight **")
    lines.append("")

    # Build a lookup from progression notes if available
    prog_lookup = {}
    if progression_notes:
        for name, weight, note in progression_notes:
            prog_lookup[name] = (weight, note)

    for ex in session["exercises"]:
        num_sets = calculate_sets(ex, week)

        # Use progression data if available, otherwise compute
        if ex["name"] in prog_lookup:
            weight, prog_note = prog_lookup[ex["name"]]
        else:
            weight, prog_note = calculate_weight(
                ex["name"], ex["start_kg"], block, week, sb=sb,
                target_reps=ex["reps"], target_sets=ex["sets"],
            )

        if weight:
            weight_str = f"{weight}kg"
        elif ex.get("duration_s"):
            weight_str = f"{ex['duration_s']}s"
        elif ex.get("distance_m"):
            weight_str = f"{ex['distance_m']}m"
        else:
            weight_str = "BW"

        reps_str = f"{ex['reps']}" if ex['reps'] > 1 else ""
        prog_str = f" [{prog_note}]" if prog_note and prog_note != "formula fallback" else ""

        lines.append(
            f"  {ex['name']}: {num_sets}x{reps_str} @ {weight_str}"
            f" [RPE {ex['rpe_low']}-{ex['rpe_high']}]{prog_str}"
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
        num_sets = ex["sets"]
        rest_s = ex.get("rest_s") or default_rest_s
        weight_kg = ex.get("weight_kg")
        duration_s = ex.get("duration_s")
        distance_m = ex.get("distance_m")

        # Build ONE working set as the child template, then wrap in
        # RepeatGroupDTO — same pattern as build_garmin_workout().
        group_order = make_step_order()
        child_set = build_exercise_step(
            exercise_name=ex["name"],
            weight_kg=weight_kg,
            reps=ex["reps"],
            step_order=make_step_order(),
            duration_s=duration_s,
            distance_m=distance_m,
        )
        children = [child_set]
        is_last_exercise = ex is parsed_exercises[-1]
        # Include rest inside the group so it repeats with each set
        if not is_last_exercise:
            children.append(build_rest_step(rest_s, make_step_order()))
        elif num_sets > 1:
            children.append(build_rest_step(rest_s, make_step_order()))
        workout_steps.append(build_repeat_group(num_sets, children, group_order))

    # Extract label from exception text (before the parentheses)
    label_match = re.match(r"^([^(]+)", exception_info["exception"])
    label = label_match.group(1).strip() if label_match else "Exception Workout"

    deload_tag = " (Deload)" if is_deload_week(week) else ""
    workout_name = f"{exception_info['original_session']}{deload_tag} (Adjusted) | Block {block} Wk{week}"

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
    """Build a Garmin API client using the browser-session auth path.

    Delegates to garmin_auth.get_safe_client() which loads a saved
    Playwright storage_state into a headless Firefox, captures a runtime
    CSRF token from the SPA, and monkey-patches Client._run_request to
    route all API calls through an in-page fetch on connect.garmin.com/gc-api.
    NEVER calls login() or hits SSO. See project_garmin_browser_auth.md.
    """
    from garmin_auth import get_safe_client
    return get_safe_client(require_garminconnect=True)


# ---------------------------------------------------------------------------
# planned_workouts back-link (single owner of garmin_workout_id writes)
# ---------------------------------------------------------------------------


def link_garmin_workout_id(
    workout_id: str,
    target_date: date,
    *,
    sb=None,
    planned_id: int | None = None,
) -> bool:
    """Link a Garmin workout ID to the planned_workouts row.

    This is the SINGLE authoritative writer of garmin_workout_id to
    planned_workouts.  All scripts that push workouts to Garmin must call
    this function instead of writing directly.

    Args:
        workout_id: Garmin workout ID returned by upload_workout().
        target_date: The scheduled date of the workout.
        sb: Optional Supabase client (created if not provided).
        planned_id: If known, update by row ID instead of date lookup.

    Returns True if a row was linked, False otherwise.
    """
    try:
        link_sb = sb if sb else create_client(SUPABASE_URL, SUPABASE_KEY)
        if planned_id:
            result = link_sb.table("planned_workouts").update({
                "garmin_workout_id": workout_id,
                "status": "pushed",
            }).eq("id", planned_id).in_(
                "status", ["planned", "adjusted", "pushed"]
            ).execute()
        else:
            date_str = target_date.isoformat()
            result = link_sb.table("planned_workouts").update({
                "garmin_workout_id": workout_id,
                "status": "pushed",
            }).eq("scheduled_date", date_str).in_(
                "status", ["planned", "adjusted", "pushed"]
            ).execute()
        if result.data:
            log.info("Linked garmin_workout_id=%s to planned_workout (date=%s)", workout_id, target_date)
            return True
        log.info("No matching planned_workout found for %s to link", target_date)
        return False
    except Exception as exc:
        log.warning("Failed to link workout ID to planned_workouts: %s", exc)
        return False


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

        # Log weight summary with progression decisions
        prog_notes = workout.pop("_progression_notes", None)
        summary = format_weight_summary(session_key, block, week,
                                        progression_notes=prog_notes, sb=sb)
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

    link_garmin_workout_id(workout_id, target_date, sb=sb)


if __name__ == "__main__":
    main()

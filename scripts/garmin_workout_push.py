#!/usr/bin/env python3
"""Push structured workouts to Garmin Connect.

Reads workout definitions (JSON) and uploads them to Garmin Connect
so they appear on the watch with pre-filled target weights and reps.

BLOCKED: Requires Garmin Auth Spike completion to determine:
  - Whether JSON API or FIT file upload works for workouts
  - Whether target weights can be pre-filled per set
  - Whether custom exercise names are supported
  See: spikes/garmin-auth-spike.md

Usage:
    python garmin_workout_push.py workout.json           # push single workout
    python garmin_workout_push.py --planned-id 42        # push from planned_workouts table
    python garmin_workout_push.py --week 2026-04-06      # push all workouts for a week
"""

import argparse
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from garmin_auth import (
    get_safe_client, save_tokens, alert_slack,
    AuthExpiredError, RateLimitCooldownError,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("garmin_workout_push")

# ---------------------------------------------------------------------------
# Workout definition format (internal JSON)
# ---------------------------------------------------------------------------
#
# Strength:
# {
#   "type": "strength",
#   "name": "Week 12 — Upper Body A",
#   "scheduled_date": "2026-04-06",
#   "estimated_duration_minutes": 75,
#   "exercises": [
#     {
#       "name": "Bench Press",
#       "garmin_exercise_id": "BENCH_PRESS",
#       "sets": 4,
#       "reps": 6,
#       "target_weight_kg": 87.5,
#       "target_rpe": 8,
#       "rest_seconds": 180
#     }
#   ]
# }
#
# Cardio (touring):
# {
#   "type": "cardio_touring",
#   "name": "Week 12 — Endurance Hike",
#   "scheduled_date": "2026-04-08",
#   "target_duration_minutes": 180,
#   "target_elevation_gain_m": 1200,
#   "hr_zones": [
#     { "zone": 2, "percentage": 70 },
#     { "zone": 3, "percentage": 25 },
#     { "zone": 4, "percentage": 5 }
#   ]
# }

# ---------------------------------------------------------------------------
# Exercise mapping (Ascent name → Garmin exercise key)
# Will be populated after Garmin spike determines custom exercise support
# ---------------------------------------------------------------------------

EXERCISE_MAP = {
    "Bench Press": "BENCH_PRESS",
    "Incline Bench Press": "INCLINE_DUMBBELL_BENCH_PRESS",
    "Squat": "BARBELL_SQUAT",
    "Deadlift": "BARBELL_DEADLIFT",
    "Overhead Press": "OVERHEAD_PRESS",
    "Barbell Row": "BENT_OVER_ROW",
    "Pull-up": "PULL_UP",
    "Lat Pulldown": "LAT_PULLDOWN",
    "Dumbbell Curl": "DUMBBELL_CURL",
    "Tricep Pushdown": "TRICEPS_PUSHDOWN",
    "Leg Press": "LEG_PRESS",
    "Romanian Deadlift": "ROMANIAN_DEADLIFT",
    "Bulgarian Split Squat": "SINGLE_LEG_SQUAT",
    "Face Pull": "FACE_PULL",
    "Lateral Raise": "LATERAL_RAISE",
}


def get_garmin_exercise_id(exercise_name: str) -> str:
    """Map an Ascent exercise name to a Garmin exercise ID."""
    mapped = EXERCISE_MAP.get(exercise_name)
    if mapped:
        return mapped
    # Fallback: uppercase with underscores (may not match Garmin's library)
    log.warning("No Garmin mapping for '%s' — using generated key", exercise_name)
    return exercise_name.upper().replace(" ", "_")


# ---------------------------------------------------------------------------
# Garmin push methods (to be implemented after spike)
# ---------------------------------------------------------------------------


def push_workout_json(client, workout_def: dict) -> dict | None:
    """Push workout via Garmin Connect JSON API.

    TODO: Implement after Garmin Auth Spike determines if JSON API works.
    See spikes/garmin-auth-spike.md "Alternative Write Test" section.

    Returns: {"workoutId": str, "scheduled": bool} or None on failure.
    """
    raise NotImplementedError(
        "Blocked on Garmin Auth Spike — JSON workout push not yet validated. "
        "Run the spike tests first: spikes/garmin-auth-spike.md"
    )


def push_workout_fit(client, workout_def: dict) -> dict | None:
    """Push workout via FIT file upload (fallback).

    TODO: Implement after Garmin Auth Spike determines if FIT upload works.
    See spikes/garmin-auth-spike.md "Option C" section.

    Returns: {"workoutId": str, "scheduled": bool} or None on failure.
    """
    raise NotImplementedError(
        "Blocked on Garmin Auth Spike — FIT file upload not yet validated. "
        "Run the spike tests first: spikes/garmin-auth-spike.md"
    )


def update_planned_workout_record(sb, planned_id: int, garmin_workout_id: str):
    """Update the planned_workouts table with the Garmin workout ID after push.

    Delegates to workout_push.link_garmin_workout_id — the single authoritative
    writer of garmin_workout_id to planned_workouts.
    """
    from workout_push import link_garmin_workout_id  # noqa: F811
    # planned_id path doesn't need a real date — pass a sentinel; the function
    # uses the id-based branch when planned_id is provided.
    link_garmin_workout_id(garmin_workout_id, date.today(), sb=sb, planned_id=planned_id)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Push workouts to Garmin Connect")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("workout_file", nargs="?", help="Path to workout JSON file")
    group.add_argument("--planned-id", type=int, help="Push from planned_workouts table by ID")
    group.add_argument("--week", type=str, help="Push all planned workouts for week starting YYYY-MM-DD")
    args = parser.parse_args()

    log.error(
        "garmin_workout_push.py is not yet implemented. "
        "Blocked on Garmin Auth Spike (spikes/garmin-auth-spike.md). "
        "Run the spike on Mac with real Garmin credentials first."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()

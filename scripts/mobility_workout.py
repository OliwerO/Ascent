#!/usr/bin/env python3
"""Build and upload Protocol A daily mobility workout to Garmin Connect.

Creates a 12-minute yoga-type workout with timed stretches from Domain 9.
This is a one-time upload — the same workout is reused daily.

Usage:
    python mobility_workout.py              # build and upload
    python mobility_workout.py --dry-run    # print JSON without uploading
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("mobility_workout")

# ---------------------------------------------------------------------------
# Garmin exercise mapping for mobility/stretch exercises
# ---------------------------------------------------------------------------

EXERCISE_MAP = {
    "Cat-Cow":                  ("WARM_UP",       "CAT_CAMEL"),
    "Ankle Mobilization":       ("WARM_UP",       "ANKLE_DORSIFLEXION_WITH_BAND"),
    "Hip Flexor Stretch":       ("WARM_UP",       "ELBOW_TO_FOOT_LUNGE"),
    "90/90 Hip Stretch":        ("HIP_STABILITY", "HIP_CIRCLES"),
    "Thoracic Rotation":        ("WARM_UP",       "THORACIC_ROTATION"),
    "Figure-4 Stretch":         ("HIP_STABILITY", "SUPINE_HIP_INTERNAL_ROTATION"),
}

# ---------------------------------------------------------------------------
# Protocol A: Daily Maintenance (12 min)
# From Domain 9, §9.6
# Format: (name, description, side, reps_or_none, duration_s_or_none)
# ---------------------------------------------------------------------------

PROTOCOL_A = [
    # 1. Cat-Cow: 60s (~8-10 cycles)
    ("Cat-Cow", "Spinal segmental wake-up", None, None, 60),

    # 2. Half-kneeling wall ankle mobilization: 2x30s each side
    ("Ankle Mobilization", "Knee over 2nd-3rd toe, heel planted", "R", None, 30),
    ("Ankle Mobilization", "Knee over 2nd-3rd toe, heel planted", "L", None, 30),
    ("Ankle Mobilization", "Set 2", "R", None, 30),
    ("Ankle Mobilization", "Set 2", "L", None, 30),

    # 3. Half-kneeling hip flexor stretch + PPT: 2x30s each side
    ("Hip Flexor Stretch", "Squeeze glute, tuck pelvis, reach arm overhead", "R", None, 30),
    ("Hip Flexor Stretch", "Squeeze glute, tuck pelvis, reach arm overhead", "L", None, 30),
    ("Hip Flexor Stretch", "Set 2", "R", None, 30),
    ("Hip Flexor Stretch", "Set 2", "L", None, 30),

    # 4. 90/90 hip stretch: 45s each side
    ("90/90 Hip Stretch", "Sit tall, lean forward with straight spine", "R", None, 45),
    ("90/90 Hip Stretch", "Sit tall, lean forward with straight spine", "L", None, 45),

    # 5. Side-lying open book (thoracic rotation): 5 reps each side with 5s hold
    ("Thoracic Rotation", "5 reps + 5s end-range hold", "R", 5, None),
    ("Thoracic Rotation", "5 reps + 5s end-range hold", "L", 5, None),

    # 6. Supine figure-4 stretch: 30s each side
    ("Figure-4 Stretch", "Ankle over opposite knee, pull toward chest", "R", None, 30),
    ("Figure-4 Stretch", "Ankle over opposite knee, pull toward chest", "L", None, 30),
]


# ---------------------------------------------------------------------------
# Workout builder
# ---------------------------------------------------------------------------

YOGA_SPORT_TYPE = {
    "sportTypeId": 6,
    "sportTypeKey": "yoga",
    "displayOrder": 6,
}


def build_step(name: str, description: str, side: str | None,
               reps: int | None, duration_s: int | None, step_order: int) -> dict:
    """Build a single timed or rep-based yoga step."""
    mapping = EXERCISE_MAP.get(name, ("WARM_UP", "OTHER"))

    # Build description with side indicator
    desc_parts = [name]
    if side:
        desc_parts[0] = f"{name} ({side})"
    if description:
        desc_parts.append(description)
    desc = " — ".join(desc_parts)

    step = {
        "type": "ExecutableStepDTO",
        "stepOrder": step_order,
        "stepType": {
            "stepTypeId": 3,
            "stepTypeKey": "interval",
            "displayOrder": 3,
        },
        "category": mapping[0],
        "exerciseName": mapping[1],
        "description": desc,
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


def build_protocol_a_workout() -> dict:
    """Build the complete Garmin workout JSON for Protocol A daily mobility."""
    steps = []
    for i, (name, desc, side, reps, dur) in enumerate(PROTOCOL_A, 1):
        steps.append(build_step(name, desc, side, reps, dur, step_order=i))

    workout = {
        "sportType": YOGA_SPORT_TYPE,
        "workoutName": "Protocol A: Daily Mobility (12 min)",
        "description": (
            "Domain 9 daily maintenance. Targets ankle DF, hip flexors, "
            "thoracic rotation, hip ER. Non-negotiable minimum."
        ),
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": YOGA_SPORT_TYPE,
                "workoutSteps": steps,
            }
        ],
    }
    return workout


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Upload Protocol A mobility workout to Garmin")
    parser.add_argument("--dry-run", action="store_true", help="Print JSON without uploading")
    args = parser.parse_args()

    workout = build_protocol_a_workout()

    if args.dry_run:
        print(json.dumps(workout, indent=2))
        log.info("Dry run — workout NOT uploaded")
        return

    # Upload to Garmin
    try:
        from garmin_auth import get_safe_client, AuthExpiredError, RateLimitCooldownError
        client = get_safe_client(require_garminconnect=True)
    except Exception as e:
        log.error("Garmin auth failed: %s", e)
        log.info("Workout JSON (save for later upload):")
        print(json.dumps(workout, indent=2))
        sys.exit(1)

    try:
        result = client.upload_workout(workout)
        workout_id = result.get("workoutId") if isinstance(result, dict) else None
        log.info("Uploaded! Workout ID: %s", workout_id)
        log.info("Find it in Garmin Connect → Training → Workouts → Protocol A: Daily Mobility")
    except Exception as e:
        log.error("Upload failed: %s", e)
        log.info("Workout JSON (save for manual upload):")
        print(json.dumps(workout, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate weekly workouts from coaching plan + last week's performance data.

Reads coaching-context.md (Opus-authored plan) and last week's Garmin data
from Supabase, applies progressive overload rules, and outputs workout
definitions for garmin_workout_push.py.

BLOCKED: Requires Phase 6 (first Opus planning session) to produce
coaching-context.md with training block structure, exercise selection,
and progression rules.

Usage:
    python workout_generator.py                    # generate next week
    python workout_generator.py --week 2026-04-06  # generate specific week
    python workout_generator.py --dry-run          # preview without writing to DB
"""

import argparse
import json
import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("workout_generator")

# ---------------------------------------------------------------------------
# Progressive overload rules (defaults, overridden by coaching-context.md)
# ---------------------------------------------------------------------------

DEFAULT_PROGRESSION_RULES = {
    "compound_strength": {
        "weight_increment_kg": 2.5,
        "rep_range": [4, 6],
        "target_rpe": 8,
        "rpe_threshold_hold": 9.5,
        "rpe_threshold_reduce": 10,
    },
    "isolation": {
        "weight_increment_kg": 1.25,
        "rep_range": [8, 12],
        "target_rpe": 7,
        "rpe_threshold_hold": 9,
        "rpe_threshold_reduce": 10,
    },
    "deload": {
        "volume_multiplier": 0.6,
        "intensity_multiplier": 0.9,
    },
}

# ---------------------------------------------------------------------------
# Plan parsing (reads coaching-context.md)
# ---------------------------------------------------------------------------


def load_coaching_context(path: str | None = None) -> dict:
    """Parse coaching-context.md into structured plan data.

    TODO: Implement markdown parsing after Phase 6 produces the plan.
    Expected sections in coaching-context.md:
      - Current training block (mesocycle name, week number)
      - Weekly structure (sessions × days)
      - Exercise selection per session template
      - Progression rules per exercise category
      - Deload rules (frequency, modifiers)
      - Cardio periodization phase

    Returns: dict with keys: block, week, sessions, progression_rules, deload_rules
    """
    raise NotImplementedError(
        "Blocked on Phase 6 — coaching-context.md does not yet contain "
        "structured training plan data. Run first Opus planning session."
    )


# ---------------------------------------------------------------------------
# Performance data retrieval
# ---------------------------------------------------------------------------


def get_last_week_performance(sb, exercise_name: str) -> dict | None:
    """Get last week's actual performance for an exercise from Supabase.

    Queries exercise_progression and training_sets tables.

    Returns: {
        "weight_kg": float,
        "sets_completed": int,
        "reps_per_set": [int],
        "avg_rpe": float,
        "all_sets_completed": bool,
    } or None if no data.
    """
    # TODO: Implement Supabase query
    return None


def get_unplanned_activities(sb, week_start: date, week_end: date) -> list:
    """Find activities that don't match any planned_workouts entry.

    Used to detect resort snowboarding and other unplanned sessions
    that should factor into weekly training load.

    Returns: list of activity dicts with estimated training load.
    """
    # TODO: Implement — query activities LEFT JOIN planned_workouts
    # WHERE planned_workouts.id IS NULL
    # AND activity_type IN ('snowboarding', 'resort_skiing', ...)
    return []


def get_readiness_context(sb, week_start: date, week_end: date) -> dict:
    """Get weekly readiness averages from daily_metrics, sleep, hrv.

    Returns: {
        "avg_hrv": float,
        "hrv_trend": "stable" | "declining" | "improving",
        "avg_body_battery": float,
        "avg_sleep_score": float,
        "readiness_flag": "good" | "moderate" | "poor",
    }
    """
    # TODO: Implement Supabase queries
    return {"readiness_flag": "good"}


# ---------------------------------------------------------------------------
# Progressive overload engine
# ---------------------------------------------------------------------------


def apply_progression(
    exercise: dict,
    last_performance: dict | None,
    rules: dict,
    is_deload_week: bool,
) -> dict:
    """Apply progressive overload logic to determine next week's targets.

    Logic (from training-expansion-brief.md):
      IF all sets completed AND avg_rpe <= target_rpe:
        → APPLY progression (+weight or +rep or +set per rule)
      ELIF avg_rpe > target_rpe + 1:
        → HOLD or REDUCE
      ELIF missed_sets > 0:
        → HOLD, flag for review
      IF deload_week:
        → APPLY deload modifiers

    Returns: updated exercise dict with new target weight/reps/sets.
    """
    if is_deload_week:
        deload = rules.get("deload", DEFAULT_PROGRESSION_RULES["deload"])
        return {
            **exercise,
            "target_weight_kg": round(exercise["target_weight_kg"] * deload["intensity_multiplier"], 1),
            "sets": max(2, int(exercise["sets"] * deload["volume_multiplier"])),
            "progression_applied": "deload",
        }

    if last_performance is None:
        return {**exercise, "progression_applied": "hold"}

    category_rules = rules.get(
        exercise.get("category", "compound_strength"),
        DEFAULT_PROGRESSION_RULES["compound_strength"],
    )
    target_rpe = category_rules["target_rpe"]

    if last_performance["all_sets_completed"] and last_performance["avg_rpe"] <= target_rpe:
        increment = category_rules["weight_increment_kg"]
        return {
            **exercise,
            "target_weight_kg": exercise["target_weight_kg"] + increment,
            "progression_applied": "weight_increase",
            "progression_amount": increment,
        }
    elif last_performance["avg_rpe"] > category_rules.get("rpe_threshold_hold", 9.5):
        return {
            **exercise,
            "target_weight_kg": exercise["target_weight_kg"] - category_rules["weight_increment_kg"],
            "progression_applied": "reduce",
        }
    else:
        return {**exercise, "progression_applied": "hold"}


# ---------------------------------------------------------------------------
# Workout generation
# ---------------------------------------------------------------------------


def generate_week(
    plan: dict,
    week_start: date,
    sb=None,
    dry_run: bool = False,
) -> list[dict]:
    """Generate all workout definitions for a given week.

    Returns: list of workout definition dicts ready for garmin_workout_push.py
    """
    # TODO: Implement after Phase 6
    # 1. Determine current block + week from plan
    # 2. For each session in weekly structure:
    #    a. Get exercise list from session template
    #    b. For each exercise, get last performance + apply progression
    #    c. Factor in unplanned activities
    #    d. Check readiness context for adjustments
    # 3. Build workout definition JSONs
    # 4. Write to planned_workouts + exercise_progression tables
    # 5. Return definitions for garmin_workout_push.py
    raise NotImplementedError(
        "Blocked on Phase 6 — no structured training plan in coaching-context.md yet."
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Generate weekly workouts")
    parser.add_argument(
        "--week", type=str,
        help="Week start date (Monday, YYYY-MM-DD). Default: next Monday.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview generated workouts without writing to DB or pushing to Garmin",
    )
    args = parser.parse_args()

    log.error(
        "workout_generator.py is not yet implemented. "
        "Blocked on Phase 6 (first Opus planning session). "
        "coaching-context.md needs structured training block data."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Smart lift progression engine for Ascent.

Determines the next workout weight for each exercise based on actual
performance data from training_sets. Uses double progression (hit target
reps → increase weight) with plate-aware rounding and stall detection.

Usage:
    from progression_engine import calculate_next_weight, ProgressionResult

    result = calculate_next_weight(sb, "Barbell Back Squat", target_reps=8, target_sets=3, current_week=2)
    # result.weight_kg = 72.5
    # result.applied = "weight_increase"
    # result.note = "+2.5kg — all sets hit 8+ reps last session"
"""

import logging
from dataclasses import dataclass

log = logging.getLogger("progression")

# ---------------------------------------------------------------------------
# Equipment config — plate-aware increments
# ---------------------------------------------------------------------------

# Valid kettlebell weights (standard competition KBs)
KB_WEIGHTS = [4, 6, 8, 10, 12, 14, 16, 20, 24, 28, 32, 36, 40, 44, 48]

# Equipment type → minimum weight increment
PLATE_INCREMENTS = {
    "barbell": 5.0,     # 2.5kg plates × 2 sides (smallest available)
    "dumbbell": 2.5,    # DB pairs go in 2.5kg steps
    "kettlebell": 4.0,  # snapped to KB_WEIGHTS
    "cable": 2.5,       # cable stack steps (gym-dependent)
    "machine": 2.5,
    "bodyweight": 0,
}

# Exercises that use barbell plates (for the 2-sides rule)
# Equipment type is fetched from DB, but this is the fallback
# Name aliases: workout_push.py names → DB names
NAME_ALIASES = {
    "KB Swings": "Kettlebell Swing",
    "KB Halo": "Kettlebell Halo",
    "KB Turkish Get-up": "Turkish Get-Up",
    "KB Clean & Press": "KB Clean & Press",
    "KB Farmer Carry": "KB Farmer Carry",
    "Dumbbell Incline Press": "Incline Dumbbell Press",
    "Single-Arm DB Row": "Single-Arm DB Row",
    "Cable Row": "Seated Cable Row",
}


def resolve_exercise_name(name: str) -> str:
    """Resolve an exercise name alias to its canonical DB name."""
    return NAME_ALIASES.get(name, name)


EQUIPMENT_FALLBACK = {
    "Barbell Back Squat": "barbell",
    "Barbell Front Squat": "barbell",
    "Conventional Deadlift": "barbell",
    "Trap Bar Deadlift": "barbell",
    "Romanian Deadlift": "barbell",
    "Barbell Bench Press": "barbell",
    "Overhead Press": "barbell",
    "Barbell Row": "barbell",
    "Dumbbell Bench Press": "dumbbell",
    "Dumbbell Incline Press": "dumbbell",
    "Single-Arm DB Row": "dumbbell",
    "Lateral Raise": "dumbbell",
    "Bulgarian Split Squat": "dumbbell",
    "Kettlebell Swing": "kettlebell",
    "Kettlebell Halo": "kettlebell",
    "Turkish Get-Up": "kettlebell",
    "KB Clean & Press": "kettlebell",
    "KB Farmer Carry": "kettlebell",
    "Cable Row": "cable",
    "Seated Cable Row": "cable",
    "Pull-Up": "bodyweight",
    "Chin-Up": "bodyweight",
}


# ---------------------------------------------------------------------------
# Plate-aware rounding
# ---------------------------------------------------------------------------


def round_to_plate(weight_kg: float, equipment: str) -> float:
    """Round weight to the nearest valid increment for the equipment type."""
    if equipment == "kettlebell":
        # Snap to nearest standard KB weight
        return min(KB_WEIGHTS, key=lambda w: abs(w - weight_kg))

    if equipment == "bodyweight":
        return 0.0

    increment = PLATE_INCREMENTS.get(equipment, 2.5)
    if increment == 0:
        return weight_kg

    # Round to nearest increment
    return round(weight_kg / increment) * increment


def next_plate_up(weight_kg: float, equipment: str) -> float:
    """Return the next weight up from current, respecting plate increments."""
    if equipment == "kettlebell":
        for w in KB_WEIGHTS:
            if w > weight_kg:
                return w
        return weight_kg  # already at max KB

    if equipment == "bodyweight":
        return 0.0

    increment = PLATE_INCREMENTS.get(equipment, 2.5)
    return round_to_plate(weight_kg + increment, equipment)


# ---------------------------------------------------------------------------
# Progression result
# ---------------------------------------------------------------------------


@dataclass
class ProgressionResult:
    weight_kg: float
    reps: int
    sets: int
    applied: str   # "weight_increase", "hold", "rep_increase", "deload_reset", "deload_week", "first_session"
    note: str
    amount: float = 0.0  # kg change from last session


# ---------------------------------------------------------------------------
# Core query
# ---------------------------------------------------------------------------


def get_exercise_history(sb, exercise_name: str, limit: int = 30) -> list[dict]:
    """Query training_sets for recent working sets of an exercise.

    Returns list of {weight_kg, reps, rpe, set_number, date} ordered by
    date desc, set_number asc.
    """
    # Resolve name aliases (e.g., "KB Swings" → "Kettlebell Swing")
    db_name = resolve_exercise_name(exercise_name)

    try:
        # Get exercise ID first
        ex = sb.table("exercises").select("id").eq("name", db_name).limit(1).execute()
        if not ex.data:
            return []
        ex_id = ex.data[0]["id"]

        # Get recent working sets
        sets = sb.table("training_sets").select(
            "weight_kg, reps, rpe, set_number, session_id"
        ).eq(
            "exercise_id", ex_id
        ).eq(
            "set_type", "working"
        ).order(
            "id", desc=True
        ).limit(limit).execute()

        if not sets.data:
            return []

        # Get session dates
        session_ids = list(set(s["session_id"] for s in sets.data))
        sessions = sb.table("training_sessions").select(
            "id, date"
        ).in_("id", session_ids).execute()
        session_dates = {s["id"]: s["date"] for s in sessions.data}

        # Merge and sort
        for s in sets.data:
            s["date"] = session_dates.get(s["session_id"])

        # Sort by date desc, then set_number asc
        sets.data.sort(key=lambda s: (-_date_ord(s.get("date", "")), s["set_number"]))
        return sets.data

    except Exception as e:
        log.warning("Failed to query exercise history for %s: %s", exercise_name, e)
        return []


def _date_ord(ds: str) -> int:
    """Convert date string to ordinal for sorting."""
    try:
        from datetime import date
        return date.fromisoformat(ds).toordinal()
    except (ValueError, TypeError):
        return 0


def get_equipment_type(sb, exercise_name: str) -> str:
    """Get equipment type for an exercise from DB, with fallback."""
    if exercise_name in EQUIPMENT_FALLBACK:
        return EQUIPMENT_FALLBACK[exercise_name]

    db_name = resolve_exercise_name(exercise_name)
    if db_name in EQUIPMENT_FALLBACK:
        return EQUIPMENT_FALLBACK[db_name]

    try:
        result = sb.table("exercises").select("equipment").eq(
            "name", db_name
        ).limit(1).execute()
        if result.data and result.data[0].get("equipment"):
            return result.data[0]["equipment"]
    except Exception:
        pass

    return "barbell"  # conservative default


# ---------------------------------------------------------------------------
# Progression algorithm
# ---------------------------------------------------------------------------


def calculate_next_weight(
    sb,
    exercise_name: str,
    target_reps: int,
    target_sets: int,
    current_week: int,
    start_kg: float | None = None,
) -> ProgressionResult:
    """Determine the next workout weight based on actual performance.

    Args:
        sb: Supabase client
        exercise_name: Canonical exercise name
        target_reps: Target reps per set
        target_sets: Target number of sets
        current_week: Current program week (1-8)
        start_kg: Fallback starting weight if no history exists

    Returns:
        ProgressionResult with weight, reps, sets, and progression decision
    """
    equipment = get_equipment_type(sb, exercise_name)

    # Bodyweight exercises don't have weight progression
    if equipment == "bodyweight" or start_kg is None:
        return ProgressionResult(
            weight_kg=0 if start_kg is None else start_kg,
            reps=target_reps,
            sets=target_sets,
            applied="bodyweight",
            note="bodyweight exercise",
        )

    # Deload weeks: same weight, reduced volume (volume handled by caller)
    is_deload = current_week in (4, 8)

    # Query actual performance history
    history = get_exercise_history(sb, exercise_name, limit=30)

    if not history:
        # No history — use starting weight
        weight = round_to_plate(start_kg, equipment)
        return ProgressionResult(
            weight_kg=weight,
            reps=target_reps,
            sets=target_sets,
            applied="first_session",
            note=f"first session — starting at {weight}kg",
        )

    # Group by session date
    sessions = _group_by_session(history)
    last_session = sessions[0]
    last_date = last_session["date"]
    last_sets = last_session["sets"]

    # Extract last session metrics
    last_weight = max(s["weight_kg"] for s in last_sets if s["weight_kg"])
    last_reps_list = [s["reps"] for s in last_sets]
    last_rpe_max = max((s.get("rpe") or 0) for s in last_sets)
    has_rpe = any(s.get("rpe") for s in last_sets)

    # Check for mixed weights (e.g., KB exercises ramping up)
    all_same_weight = len(set(s["weight_kg"] for s in last_sets if s["weight_kg"])) == 1

    if is_deload:
        return ProgressionResult(
            weight_kg=last_weight,
            reps=target_reps,
            sets=target_sets,
            applied="deload_week",
            note=f"deload week — holding at {last_weight}kg, 50% volume",
        )

    # Double progression check
    all_hit_target = all(r >= target_reps for r in last_reps_list)

    # For mixed-weight sets (KB ramping), require all sets at max weight
    if not all_same_weight:
        sets_at_max = [s for s in last_sets if s["weight_kg"] == last_weight]
        all_at_max_hit = (
            len(sets_at_max) >= target_sets
            and all(s["reps"] >= target_reps for s in sets_at_max)
        )
        if not all_at_max_hit:
            return ProgressionResult(
                weight_kg=last_weight,
                reps=target_reps,
                sets=target_sets,
                applied="hold",
                note=f"not all sets at {last_weight}kg yet — keep building",
            )
        all_hit_target = True  # all sets at max weight hit target

    # Check stall history
    stall_weeks = _count_stall_weeks(sessions, last_weight)

    if stall_weeks >= 3:
        # Stall protocol: drop 10%, increase reps to 12, rebuild
        drop_weight = round_to_plate(last_weight * 0.90, equipment)
        return ProgressionResult(
            weight_kg=drop_weight,
            reps=12,
            sets=target_sets,
            applied="deload_reset",
            amount=drop_weight - last_weight,
            note=f"stalled {stall_weeks} sessions at {last_weight}kg — dropping to {drop_weight}kg × 12",
        )

    if stall_weeks == 2 and not all_hit_target:
        return ProgressionResult(
            weight_kg=last_weight,
            reps=target_reps,
            sets=target_sets,
            applied="hold",
            note=f"stall watch — 2 sessions at {last_weight}kg without hitting all reps",
        )

    if all_hit_target and (not has_rpe or last_rpe_max < 9):
        # Ready to increase
        new_weight = next_plate_up(last_weight, equipment)
        increase = new_weight - last_weight

        # 10% cap — only for heavier lifts where the increment is a choice.
        # With 5kg barbell plates, anything under 50kg inherently exceeds 10%.
        # Only apply when the increment could reasonably be smaller.
        if last_weight >= 50 and increase / last_weight > 0.10:
            return ProgressionResult(
                weight_kg=last_weight,
                reps=target_reps,
                sets=target_sets,
                applied="hold",
                note=f"increment {increase}kg would exceed 10% cap — holding at {last_weight}kg",
            )

        return ProgressionResult(
            weight_kg=new_weight,
            reps=target_reps,
            sets=target_sets,
            applied="weight_increase",
            amount=increase,
            note=f"+{increase}kg — all sets hit {target_reps}+ reps at {last_weight}kg",
        )

    if all_hit_target and has_rpe and last_rpe_max >= 9:
        # Hit reps but grinding
        return ProgressionResult(
            weight_kg=last_weight,
            reps=target_reps,
            sets=target_sets,
            applied="hold",
            note=f"hit reps but RPE {last_rpe_max} — holding at {last_weight}kg until it feels easier",
        )

    # Didn't hit all target reps — hold weight, work on reps
    missed = [r for r in last_reps_list if r < target_reps]
    return ProgressionResult(
        weight_kg=last_weight,
        reps=target_reps,
        sets=target_sets,
        applied="rep_increase",
        note=f"not all sets at {target_reps} reps yet (got {last_reps_list}) — holding at {last_weight}kg",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _group_by_session(history: list[dict]) -> list[dict]:
    """Group flat set records into sessions by date."""
    from collections import OrderedDict
    sessions = OrderedDict()
    for row in history:
        d = row.get("date", "unknown")
        if d not in sessions:
            sessions[d] = {"date": d, "sets": []}
        sessions[d]["sets"].append(row)
    return list(sessions.values())


def _count_stall_weeks(sessions: list[dict], current_weight: float) -> int:
    """Count how many consecutive recent sessions used the same max weight."""
    count = 0
    for session in sessions:
        max_w = max((s["weight_kg"] for s in session["sets"] if s.get("weight_kg")), default=0)
        if abs(max_w - current_weight) < 0.1:
            count += 1
        else:
            break
    return count


# ---------------------------------------------------------------------------
# Record progression decision
# ---------------------------------------------------------------------------


def record_progression(sb, exercise_name: str, target_date: str, result: ProgressionResult,
                       planned_rpe: float | None = None):
    """Write progression decision to exercise_progression table."""
    try:
        sb.table("exercise_progression").upsert({
            "exercise_name": exercise_name,
            "date": target_date,
            "planned_sets": result.sets,
            "planned_reps": result.reps,
            "planned_weight_kg": result.weight_kg,
            "planned_rpe": planned_rpe,
            "progression_applied": result.applied,
            "progression_amount": result.amount,
        }, on_conflict="exercise_name,date").execute()
    except Exception as e:
        log.warning("Failed to record progression for %s: %s", exercise_name, e)


# ---------------------------------------------------------------------------
# CLI — test progression for an exercise
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    import sys
    from pathlib import Path
    from dotenv import load_dotenv
    from supabase import create_client

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    load_dotenv(PROJECT_ROOT / ".env")

    sb = create_client(os.environ["SUPABASE_URL"],
                       os.environ.get("SUPABASE_SERVICE_KEY", os.environ["SUPABASE_KEY"]))

    exercise = sys.argv[1] if len(sys.argv) > 1 else "Barbell Back Squat"
    week = int(sys.argv[2]) if len(sys.argv) > 2 else 2

    print(f"\n=== Progression for {exercise} (Week {week}) ===\n")

    result = calculate_next_weight(sb, exercise, target_reps=8, target_sets=3, current_week=week, start_kg=70)
    print(f"  Weight: {result.weight_kg}kg")
    print(f"  Reps:   {result.reps}")
    print(f"  Sets:   {result.sets}")
    print(f"  Action: {result.applied}")
    print(f"  Note:   {result.note}")
    if result.amount:
        print(f"  Change: {result.amount:+.1f}kg")

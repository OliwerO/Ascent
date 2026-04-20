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

import json
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("progression")

# ---------------------------------------------------------------------------
# Equipment config — loaded from config/training_constants.json
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONSTANTS_PATH = _PROJECT_ROOT / "config" / "training_constants.json"
with open(_CONSTANTS_PATH) as _f:
    _CONSTANTS = json.load(_f)

# Valid kettlebell weights (standard competition KBs)
KB_WEIGHTS: list[int] = _CONSTANTS["kb_weights"]

# Equipment type → minimum weight increment
PLATE_INCREMENTS: dict[str, float] = {
    k: float(v) for k, v in _CONSTANTS["plate_increments"].items()
}

def resolve_exercise_name(name: str) -> str:
    """Return the exercise name as-is (names are now canonical DB names)."""
    return name


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
    applied: str   # "weight_increase", "accelerated_increase", "hold", "rep_increase",
                    #  "deload_reset", "deload_week", "add_set", "rpe_reduction", "first_session"
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
    # Names are now canonical DB names (no alias resolution needed)
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
    target_rpe: float | None = None,
) -> ProgressionResult:
    """Determine the next workout weight based on actual performance.

    Args:
        sb: Supabase client
        exercise_name: Canonical exercise name
        target_reps: Target reps per set
        target_sets: Target number of sets
        current_week: Current program week (1-8)
        start_kg: Fallback starting weight if no history exists
        target_rpe: Target RPE for this exercise (for overshoot detection)

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

    # Deload weeks: same weight, reduced volume (volume handled by caller).
    # This check runs BEFORE stall detection — deload weeks always return
    # last_weight unchanged. KB Halo oscillation (12→14→12kg) is caused by
    # stall_reset on non-deload weeks, not a deload bug. The add_set
    # intermediate step (Item 7) addresses this oscillation pattern.
    # Skip planned deload if previous week was a natural deload (heavy mountain, minimal gym)
    is_deload = current_week in (4, 8) and not _check_natural_deload(sb, current_week)

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
            note="first session",
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
            note="deload week — 50% volume",
        )

    # Check exercise feedback — hold weight if rated "heavy" 2+ consecutive sessions
    heavy_streak = _count_heavy_streak(sb, exercise_name)
    if heavy_streak >= 2 and all(r >= target_reps for r in last_reps_list):
        return ProgressionResult(
            weight_kg=last_weight,
            reps=target_reps,
            sets=target_sets,
            applied="hold",
            note=f"rated 'heavy' {heavy_streak} sessions in a row — holding until it feels easier",
        )

    # Acceleration gate: light feel OR low avg sRPE → 2× standard increment
    # KB §1.1: when all sets hit target reps with ease, accelerate progression
    all_hit_target_early = all(r >= target_reps for r in last_reps_list)
    if all_hit_target_early and all_same_weight:
        should_accelerate = False
        accel_reason = ""

        light_streak = _count_light_streak(sb, exercise_name)
        srpe_for_accel = _get_session_rpe_modifier(sb, exercise_name)

        if light_streak >= 3 and (srpe_for_accel is None or srpe_for_accel == 0):
            should_accelerate = True
            accel_reason = f"light feel {light_streak} sessions + low sRPE"

        if not should_accelerate:
            avg_srpe = _get_avg_srpe(sb, exercise_name, sessions=2)
            if avg_srpe is not None and avg_srpe <= 6.5:
                should_accelerate = True
                accel_reason = f"avg sRPE {avg_srpe:.1f} over 2 sessions"

        if should_accelerate and (not has_rpe or last_rpe_max < 9):
            new_weight = _accelerated_increase(last_weight, equipment)
            increase = new_weight - last_weight
            # Skip the per-exercise 10% cap for acceleration: the triggers
            # (3+ light sessions OR avg sRPE ≤ 6.5) are conservative enough
            # that a larger jump is warranted. The weekly volume cap (Phase 3)
            # provides the aggregate safety net.
            if increase > 0:
                return ProgressionResult(
                    weight_kg=new_weight,
                    reps=target_reps,
                    sets=target_sets,
                    applied="accelerated_increase",
                    amount=increase,
                    note=f"{accel_reason} — accelerated +{increase:.1f}kg",
                )

    # Session-level sRPE check — hold if the whole session felt brutal,
    # even when per-set RPE and per-exercise feel are fine
    srpe_mod = _get_session_rpe_modifier(sb, exercise_name)
    if srpe_mod is not None and srpe_mod >= 1.0 and all(r >= target_reps for r in last_reps_list):
        # sRPE >= 9: hold weight regardless — session was a grinder
        return ProgressionResult(
            weight_kg=last_weight,
            reps=target_reps,
            sets=target_sets,
            applied="hold",
            note=f"session RPE >= 9 — holding at {last_weight}kg until sessions feel easier",
        )

    if srpe_mod is not None and srpe_mod >= 0.5 and all(r >= target_reps for r in last_reps_list):
        # sRPE 8 with recent weight increase: be conservative
        sessions_at_wt = _count_sessions_at_weight(sessions, last_weight)
        if sessions_at_wt <= 2:
            return ProgressionResult(
                weight_kg=last_weight,
                reps=target_reps,
                sets=target_sets,
                applied="hold",
                note=f"session RPE 8 with recent weight increase — consolidating at {last_weight}kg",
            )

    # Wellness check: poor wellness → mild conservatism (same as sRPE 8)
    # KB: subjective wellness overrides wearables (Saw et al. 2016)
    wellness_mod = _get_wellness_modifier(sb)
    if wellness_mod is not None and wellness_mod >= 0.5 and all(r >= target_reps for r in last_reps_list):
        sessions_at_wt = _count_sessions_at_weight(sessions, last_weight)
        if sessions_at_wt <= 2:
            return ProgressionResult(
                weight_kg=last_weight,
                reps=target_reps,
                sets=target_sets,
                applied="hold",
                note=f"low wellness score — consolidating at {last_weight}kg",
            )

    # RPE overshoot: actual RPE consistently >1 above target for 2+ weeks → reduce weight
    # KB §1.3: reduce loads 2.5-5% to address fatigue accumulation
    if target_rpe is not None:
        if _check_rpe_overshoot(sb, exercise_name, target_rpe, weeks=2):
            drop_weight = round_to_plate(last_weight * 0.95, equipment)
            reduction = drop_weight - last_weight
            return ProgressionResult(
                weight_kg=drop_weight,
                reps=target_reps,
                sets=target_sets,
                applied="rpe_reduction",
                amount=reduction,
                note=f"RPE consistently >{target_rpe + 1:.0f} for 2+ weeks — reducing {abs(reduction):.1f}kg",
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
                note="not all sets at top weight yet — keep building",
            )
        all_hit_target = True  # all sets at max weight hit target

    # Check stall history
    stall_weeks = _count_stall_weeks(sessions, last_weight)

    if stall_weeks >= 3:
        # KB §1.1: try +1 set for 3-4 weeks before deload_reset
        if not _was_add_set_tried(sb, exercise_name, weeks=4):
            return ProgressionResult(
                weight_kg=last_weight,
                reps=target_reps,
                sets=target_sets + 1,
                applied="add_set",
                amount=0,
                note=f"stalled {stall_weeks} sessions — adding 1 set to break plateau",
            )
        # add_set already tried and still stalled → deload_reset
        drop_weight = round_to_plate(last_weight * 0.90, equipment)
        return ProgressionResult(
            weight_kg=drop_weight,
            reps=12,
            sets=target_sets,
            applied="deload_reset",
            amount=drop_weight - last_weight,
            note=f"stalled {stall_weeks} sessions (add_set tried) — dropping weight, rebuild at 12 reps",
        )

    if stall_weeks == 2 and not all_hit_target:
        return ProgressionResult(
            weight_kg=last_weight,
            reps=target_reps,
            sets=target_sets,
            applied="hold",
            note="stall watch — 2 sessions without hitting all reps",
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
                note="next jump would exceed 10% cap — holding",
            )

        # Per-muscle-group weekly volume cap: block if any primary mover
        # would exceed 10% week-over-week increase
        if _check_muscle_group_volume_cap(
            sb, exercise_name, new_weight, last_weight, target_sets, target_reps
        ):
            return ProgressionResult(
                weight_kg=last_weight,
                reps=target_reps,
                sets=target_sets,
                applied="hold",
                note="weekly muscle group volume cap — increase would exceed 10% WoW growth",
            )

        return ProgressionResult(
            weight_kg=new_weight,
            reps=target_reps,
            sets=target_sets,
            applied="weight_increase",
            amount=increase,
            note=f"weight up — all sets hit {target_reps}+ reps last session",
        )

    if all_hit_target and has_rpe and last_rpe_max >= 9:
        # Hit reps but grinding
        return ProgressionResult(
            weight_kg=last_weight,
            reps=target_reps,
            sets=target_sets,
            applied="hold",
            note=f"hit reps but RPE {last_rpe_max} — holding until it feels easier",
        )

    # Didn't hit all target reps — hold weight, work on reps
    missed = [r for r in last_reps_list if r < target_reps]
    return ProgressionResult(
        weight_kg=last_weight,
        reps=target_reps,
        sets=target_sets,
        applied="rep_increase",
        note=f"not all sets at {target_reps} reps yet (got {last_reps_list}) — holding weight",
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


def _count_heavy_streak(sb, exercise_name: str) -> int:
    """Count consecutive recent sessions where exercise was rated 'heavy'."""
    try:
        result = sb.table("exercise_feedback").select(
            "session_date, feel"
        ).eq(
            "exercise_name", exercise_name
        ).order(
            "session_date", desc=True
        ).limit(5).execute()

        if not result.data:
            return 0

        streak = 0
        for row in result.data:
            if row["feel"] == "heavy":
                streak += 1
            else:
                break
        return streak
    except Exception:
        return 0


def _count_light_streak(sb, exercise_name: str) -> int:
    """Count consecutive recent sessions where exercise was rated 'light'."""
    try:
        result = sb.table("exercise_feedback").select(
            "session_date, feel"
        ).eq(
            "exercise_name", exercise_name
        ).order(
            "session_date", desc=True
        ).limit(5).execute()

        if not result.data:
            return 0

        streak = 0
        for row in result.data:
            if row["feel"] == "light":
                streak += 1
            else:
                break
        return streak
    except Exception:
        return 0


def _accelerated_increase(weight_kg: float, equipment: str) -> float:
    """Return weight with 2x normal increment (for acceleration triggers).

    Used when light-feel or low-RPE signals indicate the athlete is ready
    for faster progression than the standard minimum increment.
    """
    if equipment == "kettlebell":
        # Skip one KB weight (e.g., 16 → 24 instead of 16 → 20)
        first_up = next_plate_up(weight_kg, equipment)
        return next_plate_up(first_up, equipment)

    # For barbell/dumbbell: double the plate increment
    increment = PLATE_INCREMENTS.get(equipment, 2.5)
    return round_to_plate(weight_kg + 2 * increment, equipment)


def _get_avg_srpe(sb, exercise_name: str, sessions: int = 2) -> float | None:
    """Get average session RPE over last N sessions containing this exercise.

    Returns None if fewer than `sessions` data points with sRPE exist.
    """
    try:
        db_name = resolve_exercise_name(exercise_name)

        ex = sb.table("exercises").select("id").eq("name", db_name).limit(1).execute()
        if not ex.data:
            return None
        ex_id = ex.data[0]["id"]

        # Get recent distinct session_ids for this exercise
        recent_sets = sb.table("training_sets").select(
            "session_id"
        ).eq("exercise_id", ex_id).order("id", desc=True).limit(sessions * 3).execute()

        if not recent_sets.data:
            return None

        # Deduplicate session IDs preserving order
        seen = set()
        session_ids = []
        for s in recent_sets.data:
            sid = s["session_id"]
            if sid not in seen:
                seen.add(sid)
                session_ids.append(sid)
            if len(session_ids) >= sessions:
                break

        if len(session_ids) < sessions:
            return None

        # Get sRPE for each session
        sessions_data = sb.table("training_sessions").select(
            "id, srpe"
        ).in_("id", session_ids).execute()

        srpe_values = [s["srpe"] for s in (sessions_data.data or []) if s.get("srpe") is not None]

        if len(srpe_values) < sessions:
            return None

        return sum(srpe_values) / len(srpe_values)
    except Exception:
        return None


def _check_rpe_overshoot(sb, exercise_name: str, target_rpe: float, weeks: int = 2) -> bool:
    """Check if actual RPE consistently exceeds target by >1 for N+ weeks.

    KB §1.3: "IF RPE consistently overshoots target by >1 RPE for ≥2 weeks
    → flag as potential fatigue accumulation; reduce loads 2.5-5%."

    Requires exercise_progression.actual_rpe to be populated (via backfill_actuals).
    Returns True if overshoot detected.
    """
    try:
        from datetime import date, timedelta
        cutoff = (date.today() - timedelta(weeks=weeks)).isoformat()

        result = sb.table("exercise_progression").select(
            "actual_rpe, planned_rpe"
        ).eq(
            "exercise_name", exercise_name
        ).gte(
            "date", cutoff
        ).order("date", desc=True).limit(weeks * 2).execute()

        if not result.data:
            return False

        # Filter for rows with actual RPE data
        rows_with_rpe = [r for r in result.data if r.get("actual_rpe") is not None]

        if len(rows_with_rpe) < weeks:
            return False

        # Check if the most recent entries all overshoot by >1
        for row in rows_with_rpe[:weeks]:
            if row["actual_rpe"] <= target_rpe + 1.0:
                return False

        return True
    except Exception:
        return False


def _get_session_rpe_modifier(sb, exercise_name: str) -> float | None:
    """Check the most recent session sRPE for a session containing this exercise.

    Returns a modifier indicating how conservative to be:
      None  — no session RPE data
      0     — sRPE <= 7, no effect
      0.5   — sRPE 8, mild conservatism (hold on recent weight increases)
      1.0   — sRPE >= 9, strong conservatism (always hold)
    """
    try:
        db_name = resolve_exercise_name(exercise_name)

        # Find the most recent session containing this exercise
        ex = sb.table("exercises").select("id").eq("name", db_name).limit(1).execute()
        if not ex.data:
            return None
        ex_id = ex.data[0]["id"]

        # Get the most recent session_id for this exercise
        recent_set = sb.table("training_sets").select(
            "session_id"
        ).eq("exercise_id", ex_id).order("id", desc=True).limit(1).execute()

        if not recent_set.data:
            return None

        session_id = recent_set.data[0]["session_id"]

        # Get the session's sRPE
        session = sb.table("training_sessions").select(
            "srpe"
        ).eq("id", session_id).limit(1).execute()

        if not session.data or session.data[0].get("srpe") is None:
            return None

        srpe = session.data[0]["srpe"]
        if srpe >= 9:
            return 1.0
        elif srpe == 8:
            return 0.5
        else:
            return 0
    except Exception:
        return None


def _count_sessions_at_weight(sessions: list[dict], weight: float) -> int:
    """Count how many of the most recent sessions used this weight."""
    count = 0
    for session in sessions:
        max_w = max((s["weight_kg"] for s in session["sets"] if s.get("weight_kg")), default=0)
        if abs(max_w - weight) < 0.1:
            count += 1
        else:
            break
    return count


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


def _was_add_set_tried(sb, exercise_name: str, weeks: int = 4) -> bool:
    """Check if 'add_set' was applied for this exercise in the last N weeks.

    KB §1.1: try +1 set for 3-4 weeks before deload_reset.
    """
    try:
        from datetime import date, timedelta
        cutoff = (date.today() - timedelta(weeks=weeks)).isoformat()

        result = sb.table("exercise_progression").select(
            "id"
        ).eq(
            "exercise_name", exercise_name
        ).eq(
            "progression_applied", "add_set"
        ).gte(
            "date", cutoff
        ).limit(1).execute()

        return bool(result.data)
    except Exception:
        return False


def _get_wellness_modifier(sb) -> float | None:
    """Check today's/yesterday's subjective wellness for conservatism signal.

    KB: subjective wellness overrides wearables (Saw et al. 2016).

    Returns:
        None — no wellness data
        0    — wellness OK (composite >= 2.5)
        0.5  — poor wellness (composite < 2.5), treat like sRPE 8
    """
    try:
        result = sb.table("subjective_wellness").select(
            "composite_score"
        ).order("date", desc=True).limit(1).execute()

        if not result.data or result.data[0].get("composite_score") is None:
            return None

        composite = result.data[0]["composite_score"]
        if composite < 2.5:
            return 0.5
        return 0
    except Exception:
        return None


def _check_natural_deload(sb, current_week: int) -> bool:
    """Check if previous week had enough mountain activity to serve as natural deload.

    KB §5: weeks with 3+ mountain days and 1 gym session function as partial deloads.
    Returns True if the athlete already deloaded naturally.
    """
    try:
        result = sb.table("weekly_training_load").select(
            "mountain_days, gym_sessions"
        ).order("week_start", desc=True).limit(2).execute()

        if not result.data or len(result.data) < 2:
            return False

        # Second row is previous week (first is current)
        prev_week = result.data[1]
        mountain_days = prev_week.get("mountain_days") or 0
        gym_sessions = prev_week.get("gym_sessions") or 0

        return mountain_days >= 3 and gym_sessions <= 1
    except Exception:
        return False


def _check_muscle_group_volume_cap(
    sb,
    exercise_name: str,
    proposed_weight: float,
    current_weight: float,
    target_sets: int,
    target_reps: int,
) -> bool:
    """Check if proposed weight increase would exceed 10% WoW volume for any primary mover.

    Per-exercise gate: only checks this exercise's muscle groups.
    A full-body session evaluates each exercise independently.

    Returns True if the increase should be blocked.
    """
    try:
        # Get muscle groups for this exercise
        ex = sb.table("exercises").select(
            "muscle_groups"
        ).eq("name", exercise_name).limit(1).execute()

        if not ex.data or not ex.data[0].get("muscle_groups"):
            return False

        muscle_groups = ex.data[0]["muscle_groups"]
        if isinstance(muscle_groups, str):
            import json
            muscle_groups = json.loads(muscle_groups)

        if not muscle_groups:
            return False

        # Get current and previous week volumes
        weeks = sb.table("weekly_training_load").select(
            "total_gym_volume_kg"
        ).order("week_start", desc=True).limit(2).execute()

        if not weeks.data or len(weeks.data) < 2:
            return False

        prev_vol = weeks.data[1].get("total_gym_volume_kg") or 0
        if prev_vol == 0:
            return False

        curr_vol = weeks.data[0].get("total_gym_volume_kg") or 0

        # Calculate the volume delta from this exercise's weight increase
        volume_delta = (proposed_weight - current_weight) * target_sets * target_reps
        projected_vol = curr_vol + volume_delta

        # Check if projected exceeds 10% over previous
        if projected_vol / prev_vol > 1.10:
            return True

        return False
    except Exception:
        return False


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
# Actual performance backfill
# ---------------------------------------------------------------------------


def backfill_actuals(sb, session_date: str) -> int:
    """Backfill exercise_progression.actual_* from training_sets for a given date.

    Called after garmin_sync writes training_sets. Updates existing
    exercise_progression rows (planned side must already exist from
    record_progression) with actual performance data.

    Args:
        sb: Supabase client
        session_date: ISO date string (e.g. "2026-04-01")

    Returns:
        Number of exercise_progression rows updated
    """
    try:
        # Find training session(s) for this date
        sessions = sb.table("training_sessions").select(
            "id"
        ).eq("date", session_date).execute()

        if not sessions.data:
            return 0

        session_ids = [s["id"] for s in sessions.data]

        # Get all working sets for these sessions
        sets = sb.table("training_sets").select(
            "exercise_id, weight_kg, reps, rpe, set_type"
        ).in_("session_id", session_ids).eq("set_type", "working").execute()

        if not sets.data:
            return 0

        # Get exercise names for the exercise IDs
        exercise_ids = list(set(s["exercise_id"] for s in sets.data if s.get("exercise_id")))
        if not exercise_ids:
            return 0

        exercises = sb.table("exercises").select(
            "id, name"
        ).in_("id", exercise_ids).execute()

        id_to_name = {e["id"]: e["name"] for e in (exercises.data or [])}

        # Group sets by exercise name
        from collections import defaultdict
        by_exercise: dict[str, list[dict]] = defaultdict(list)
        for s in sets.data:
            name = id_to_name.get(s.get("exercise_id"))
            if name:
                by_exercise[name].append(s)

        # Update exercise_progression rows
        updated = 0
        for exercise_name, exercise_sets in by_exercise.items():
            actual_sets = len(exercise_sets)
            actual_reps = [s["reps"] for s in exercise_sets if s.get("reps") is not None]
            weights = [s["weight_kg"] for s in exercise_sets if s.get("weight_kg")]
            rpes = [s["rpe"] for s in exercise_sets if s.get("rpe") is not None]

            actual_weight = max(weights) if weights else None
            actual_rpe = round(sum(rpes) / len(rpes), 1) if rpes else None

            # Only update rows that already exist (planned side written by record_progression)
            existing = sb.table("exercise_progression").select("id").eq(
                "exercise_name", exercise_name
            ).eq("date", session_date).limit(1).execute()

            if not existing.data:
                continue

            sb.table("exercise_progression").update({
                "actual_sets": actual_sets,
                "actual_reps_per_set": actual_reps,
                "actual_weight_kg": actual_weight,
                "actual_rpe": actual_rpe,
            }).eq("exercise_name", exercise_name).eq("date", session_date).execute()

            updated += 1
            log.info("Backfilled actuals for %s on %s: %d sets, %s reps, %skg, RPE %s",
                     exercise_name, session_date, actual_sets, actual_reps,
                     actual_weight, actual_rpe)

        return updated

    except Exception as e:
        log.warning("Failed to backfill actuals for %s: %s", session_date, e)
        return 0


# ---------------------------------------------------------------------------
# Missing weight data detection (Gap 10)
# ---------------------------------------------------------------------------


def check_missing_weight_data(sb, lookback_days: int = 14) -> list[dict]:
    """Detect recent training sessions where exercises have missing weight data.

    When Garmin doesn't record weight_kg for working sets (e.g., TGU firmware
    limitation), the engine silently skips them. This function flags those
    sessions so the coaching context can surface "incomplete session data."

    Returns:
        List of dicts with: date, exercise_name, total_sets, sets_missing_weight
    """
    from datetime import date, timedelta

    cutoff = (date.today() - timedelta(days=lookback_days)).isoformat()
    try:
        # Get recent training sessions
        sessions = sb.table("training_sessions").select(
            "id, date"
        ).gte("date", cutoff).execute()

        if not sessions.data:
            return []

        session_ids = [s["id"] for s in sessions.data]
        session_dates = {s["id"]: s["date"] for s in sessions.data}

        # Get all working sets for these sessions
        sets_result = sb.table("training_sets").select(
            "session_id, weight_kg, exercises(name)"
        ).in_("session_id", session_ids).eq(
            "set_type", "working"
        ).execute()

        if not sets_result.data:
            return []

        # Group by session + exercise, check for missing weights
        from collections import defaultdict
        exercise_sets: dict[tuple[int, str], dict] = defaultdict(
            lambda: {"total": 0, "missing": 0}
        )

        for s in sets_result.data:
            ex_name = s.get("exercises", {}).get("name") if s.get("exercises") else None
            if not ex_name:
                continue
            key = (s["session_id"], ex_name)
            exercise_sets[key]["total"] += 1
            if s.get("weight_kg") is None:
                exercise_sets[key]["missing"] += 1

        alerts = []
        for (session_id, exercise_name), counts in exercise_sets.items():
            if counts["missing"] > 0:
                alerts.append({
                    "date": session_dates.get(session_id, "unknown"),
                    "exercise_name": exercise_name,
                    "total_sets": counts["total"],
                    "sets_missing_weight": counts["missing"],
                })

        return sorted(alerts, key=lambda a: a["date"], reverse=True)

    except Exception as e:
        log.warning("Failed to check missing weight data: %s", e)
        return []


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

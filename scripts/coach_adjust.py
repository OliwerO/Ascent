#!/usr/bin/env python3
"""Single write-path for health-coach session adjustments.

Replaces the 4 scattered curl/file/script invocations the health-coach skill
used to do inline (and silently no-op'd because of a `date` vs `scheduled_date`
column-name bug) with a deterministic Python wrapper that:

  1. Validates the action and details up front
  2. Mutates planned_workouts via the supabase Python client
  3. Re-pushes to Garmin via workout_push.py imports (when applicable)
  4. Appends to coaching-context.md Session Exceptions table
  5. Inserts a coaching_log row with type='adjustment'
  6. Posts to Slack
  7. Prints a single JSON object to stdout summarising what landed

The skill calls this once and gates its user-facing reply on the JSON `ok`
field. Logs go to stderr; only the JSON goes to stdout.

See: project_coach_write_path_broken.md, project_automation_audit_followup.md
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import traceback
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from supabase import create_client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"]
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL_DAILY = os.environ.get("SLACK_CHANNEL_DAILY", "C0AQ1KHMBGS")
SLACK_CHANNEL_TRAINING = os.environ.get("SLACK_CHANNEL_TRAINING", "C0AQ1KJAKM0")

COACHING_CONTEXT_PATH = PROJECT_ROOT / "openclaw" / "coaching-context.md"

VALID_SESSION_TYPES = {
    "strength",
    "cardio_touring",
    "mobility",
    "rest",
    "mountain_tour",
    "cross_training",
}

# Mirrors B4's assertion in workout_generator.py — never let a numeric kg
# value back into a note string via the new write path.
KG_IN_NOTE_RE = re.compile(r"\d+(?:\.\d+)?\s*kg", re.IGNORECASE)

ACTIONS = {
    "swap_exercise",
    "lighten_session",
    "replace_session",
    "reschedule_session",
    "mark_rest",
    "mark_mountain_day",
    "mark_skipped",
    "mark_completed",
    "mark_mobility",
    # No-op log path: the cron decided to train as planned. Writes a
    # coaching_log row only — no planned_workouts mutation, no Garmin push.
    # Closes the traceability hole where train-as-planned days left no audit
    # trail. See sql/021_coaching_log_traceability.sql + audit Phase 7.
    "mark_train_as_planned",
    # Home ↔ gym switching. Converts a planned gym session to a home-equipment
    # version (or back) using the substitution map in workout_push.py.
    "switch_to_home",
    "switch_to_gym",
}

# Maps an action to the typed decision_type stored in coaching_log.
DECISION_TYPE_BY_ACTION = {
    "swap_exercise":         "adjust",
    "lighten_session":       "adjust",
    "replace_session":       "adjust",
    "reschedule_session":    "adjust",
    "mark_rest":             "rest",
    "mark_mountain_day":     "mountain_day",
    "mark_mobility":         "mobility",
    "mark_skipped":          "skipped",
    "mark_completed":        "completed",
    "mark_train_as_planned": "train_as_planned",
    "switch_to_home":        "adjust",
    "switch_to_gym":         "adjust",
}

# Actions that require us to re-push a workout to Garmin afterwards.
GARMIN_REPUSH_ACTIONS = {"swap_exercise", "lighten_session", "replace_session", "switch_to_home", "switch_to_gym"}
# Actions that push a mobility workout via mobility_workout.py instead of workout_push.py.
GARMIN_MOBILITY_ACTIONS = {"mark_mobility"}

# Actions that should drop any existing Garmin scheduled workout (no replacement).
GARMIN_CLEAR_ACTIONS = {"mark_rest", "mark_mountain_day", "mark_skipped"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,  # keep stdout clean for the JSON contract
)
log = logging.getLogger("coach_adjust")


# ---------------------------------------------------------------------------
# Step result helpers
# ---------------------------------------------------------------------------


class StepResult(dict):
    """Per-step result; serialised into the final JSON."""

    @classmethod
    def ok(cls, **extra: Any) -> "StepResult":
        return cls(status="ok", **extra)

    @classmethod
    def fail(cls, error: str, **extra: Any) -> "StepResult":
        return cls(status="fail", error=error, **extra)

    @classmethod
    def skipped(cls, reason: str, **extra: Any) -> "StepResult":
        return cls(status="skipped", reason=reason, **extra)


def is_terminal_ok(steps: dict[str, StepResult]) -> bool:
    """ok iff every step is 'ok' or 'skipped' (no 'fail')."""
    return all(s.get("status") in ("ok", "skipped") for s in steps.values())


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class ValidationError(Exception):
    pass


def _require_keys(details: dict, keys: list[str], action: str) -> None:
    missing = [k for k in keys if k not in details]
    if missing:
        raise ValidationError(
            f"action '{action}' requires details keys {missing} (got: {sorted(details.keys())})"
        )


def _assert_no_kg_in_notes(workout_def: dict) -> None:
    """B4 mirror: refuse to write workout_definitions whose exercise notes
    embed numeric kg values. The Weight column is the source of truth.
    """
    for ex in workout_def.get("exercises", []) or []:
        note = ex.get("note") or ""
        if KG_IN_NOTE_RE.search(note):
            raise ValidationError(
                f"exercise '{ex.get('name')}' note contains a kg value "
                f"({note!r}); notes must not duplicate weight"
            )


def validate_action(action: str, details: dict) -> None:
    if action not in ACTIONS:
        raise ValidationError(f"unknown action {action!r}; valid: {sorted(ACTIONS)}")

    if action == "swap_exercise":
        _require_keys(details, ["old", "new", "reason"], action)
    elif action == "lighten_session":
        if "volume_reduction" not in details and "rpe_cap" not in details:
            raise ValidationError(
                "lighten_session requires at least one of "
                "'volume_reduction' or 'rpe_cap'"
            )
        _require_keys(details, ["reason"], action)
        vr = details.get("volume_reduction")
        if vr is not None and not (0.0 <= float(vr) < 1.0):
            raise ValidationError("volume_reduction must be in [0.0, 1.0)")
    elif action == "replace_session":
        _require_keys(details, ["session_name", "workout_definition", "reason"], action)
        if not isinstance(details["workout_definition"], dict):
            raise ValidationError("workout_definition must be a JSON object")
        _assert_no_kg_in_notes(details["workout_definition"])
    elif action == "reschedule_session":
        _require_keys(details, ["to_date", "reason"], action)
        try:
            date.fromisoformat(details["to_date"])
        except (TypeError, ValueError):
            raise ValidationError("to_date must be ISO YYYY-MM-DD")
    elif action == "mark_rest":
        _require_keys(details, ["reason"], action)
    elif action == "mark_mountain_day":
        _require_keys(details, ["reason"], action)
    elif action == "mark_skipped":
        _require_keys(details, ["reason"], action)
    elif action == "mark_completed":
        pass  # all keys optional
    elif action == "mark_mobility":
        _require_keys(details, ["reason"], action)
        proto = details.get("protocol", "A")
        if proto not in ("A", "B", "C"):
            raise ValidationError("mark_mobility protocol must be A/B/C")
    elif action == "mark_train_as_planned":
        _require_keys(details, ["reason"], action)
        # `inputs` (JSONB), `rule` (TEXT), `kb_refs` (TEXT[]) are optional but
        # strongly encouraged — they're the whole point of this action.
    elif action == "switch_to_home":
        _require_keys(details, ["reason"], action)
    elif action == "switch_to_gym":
        _require_keys(details, ["reason"], action)

    # Optional traceability fields are accepted on every action and stored
    # on the coaching_log row. Validate shape if present.
    if "kb_refs" in details and not isinstance(details["kb_refs"], list):
        raise ValidationError("kb_refs must be a JSON array of strings")
    if "inputs" in details and not isinstance(details["inputs"], dict):
        raise ValidationError("inputs must be a JSON object")
    if "rule" in details and not isinstance(details["rule"], str):
        raise ValidationError("rule must be a string")


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------


def get_sb():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_row(sb, target_date: date) -> dict | None:
    res = (
        sb.table("planned_workouts")
        .select("*")
        .eq("scheduled_date", target_date.isoformat())
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]
    return None


def patch_row(sb, row_id: int, patch: dict) -> dict:
    res = (
        sb.table("planned_workouts")
        .update(patch)
        .eq("id", row_id)
        .execute()
    )
    if not res.data:
        raise RuntimeError(f"PATCH planned_workouts id={row_id} returned no data")
    return res.data[0]


def insert_row(sb, row: dict) -> dict:
    res = sb.table("planned_workouts").insert(row).execute()
    if not res.data:
        raise RuntimeError("INSERT planned_workouts returned no data")
    return res.data[0]


# ---------------------------------------------------------------------------
# Action → row patch
# ---------------------------------------------------------------------------


def _diff(before: dict | None, after: dict) -> dict:
    """Return only the keys that changed (or are new)."""
    if before is None:
        return {k: {"before": None, "after": v} for k, v in after.items()}
    out = {}
    for k, v in after.items():
        if before.get(k) != v:
            out[k] = {"before": before.get(k), "after": v}
    return out


def apply_action_to_row(
    action: str,
    details: dict,
    row: dict | None,
    target_date: date,
) -> tuple[dict, str]:
    """Compute the patched/new row dict + a human-readable summary line.

    Does NOT touch the database. Pure transformation.
    """
    if row is None and action not in {"mark_rest", "mark_mountain_day", "replace_session", "mark_mobility"}:
        raise ValidationError(
            f"no planned_workouts row exists for {target_date.isoformat()}; "
            f"only mark_rest, mark_mountain_day, replace_session can create one"
        )

    if action == "swap_exercise":
        new_row = deepcopy(row)
        wd = new_row.get("workout_definition") or {}
        exercises = wd.get("exercises") or []
        old_name = details["old"]
        replaced = False
        for i, ex in enumerate(exercises):
            if ex.get("name", "").lower() == old_name.lower():
                # Drop the old exercise's progression note — it described the
                # OLD exercise's history and is meaningless on the replacement.
                replacement = {**ex, "name": details["new"], "note": None}
                for k in ("sets", "reps", "weight_kg", "rest_s", "equipment"):
                    if k in details:
                        replacement[k] = details[k]
                exercises[i] = replacement
                replaced = True
                break
        if not replaced:
            raise ValidationError(
                f"exercise {old_name!r} not found in workout_definition.exercises"
            )
        wd["exercises"] = exercises
        # NOTE: _assert_no_kg_in_notes is intentionally NOT called here.
        # The other (unswapped) exercises legitimately carry kg-bearing
        # progression notes from workout_generator.py / progression_engine.py
        # ("+5kg — all sets hit 8+ reps at 70kg") and the React TrainingPlanView
        # displays them. The assertion's intent is output-validation on content
        # the wrapper *writes*; it is still enforced in replace_session where
        # the caller supplies fresh content. If you ever change swap_exercise
        # to write into ex["note"], call _assert_no_kg_in_notes again here.
        new_row["workout_definition"] = wd
        new_row["status"] = "adjusted"
        new_row["adjustment_reason"] = details["reason"]
        return new_row, f"Swapped {old_name} → {details['new']}"

    if action == "lighten_session":
        new_row = deepcopy(row)
        wd = new_row.get("workout_definition") or {}
        exercises = wd.get("exercises") or []
        vr = float(details.get("volume_reduction") or 0.0)
        rpe_cap = details.get("rpe_cap")
        for ex in exercises:
            if vr > 0 and ex.get("sets"):
                # Drop sets proportionally, minimum 1.
                new_sets = max(1, round(ex["sets"] * (1.0 - vr)))
                ex["sets"] = new_sets
        if rpe_cap is not None:
            rng = wd.get("rpe_range") or [rpe_cap, rpe_cap]
            wd["rpe_range"] = [min(rng[0], rpe_cap), min(rng[1], rpe_cap)]
        wd["exercises"] = exercises
        # NOTE: _assert_no_kg_in_notes is intentionally NOT called here.
        # lighten_session does not modify ex["note"]; it only changes sets and
        # rpe_range. Existing kg-bearing progression notes describe the planned
        # weight (which lighten_session does not change) and remain factually
        # accurate after RPE/volume capping. The React TrainingPlanView displays
        # them. The assertion's intent is output-validation on content the
        # wrapper *writes*; it is still enforced in replace_session where the
        # caller supplies fresh content. If you ever change lighten_session to
        # write into ex["note"], call _assert_no_kg_in_notes again here.
        new_row["workout_definition"] = wd
        new_row["status"] = "adjusted"
        new_row["adjustment_reason"] = details["reason"]
        bits = []
        if vr > 0:
            bits.append(f"volume -{int(vr*100)}%")
        if rpe_cap is not None:
            bits.append(f"RPE cap {rpe_cap}")
        return new_row, f"Lightened session ({', '.join(bits)})"

    if action == "replace_session":
        new_wd = details["workout_definition"]
        if row is None:
            new_row = {
                "training_block": details.get("training_block", "unscheduled"),
                "week_number": details.get("week_number", 0),
                "session_name": details["session_name"],
                "session_type": details.get("session_type", "strength"),
                "scheduled_date": target_date.isoformat(),
                "estimated_duration_minutes": new_wd.get("estimated_duration_minutes"),
                "workout_definition": new_wd,
                "status": "adjusted",
                "adjustment_reason": details["reason"],
            }
        else:
            new_row = deepcopy(row)
            new_row["session_name"] = details["session_name"]
            if "session_type" in details:
                new_row["session_type"] = details["session_type"]
            new_row["workout_definition"] = new_wd
            new_row["estimated_duration_minutes"] = new_wd.get(
                "estimated_duration_minutes", new_row.get("estimated_duration_minutes")
            )
            new_row["status"] = "adjusted"
            new_row["adjustment_reason"] = details["reason"]
        if new_row.get("session_type") not in VALID_SESSION_TYPES:
            raise ValidationError(
                f"session_type {new_row.get('session_type')!r} not in {sorted(VALID_SESSION_TYPES)}"
            )
        return new_row, f"Replaced session with {details['session_name']}"

    if action == "reschedule_session":
        # This action is special-cased in run_action — touches two rows.
        # Returning the source-row patch here; the target-row write happens
        # in the orchestrator.
        new_row = deepcopy(row)
        new_row["status"] = details.get("source_disposition", "skipped")
        new_row["adjustment_reason"] = (
            f"rescheduled to {details['to_date']}: {details['reason']}"
        )
        return new_row, f"Rescheduled {target_date.isoformat()} → {details['to_date']}"

    if action == "mark_rest":
        if row is None:
            new_row = {
                "training_block": "unscheduled",
                "week_number": 0,
                "session_name": "Rest",
                "session_type": "rest",
                "scheduled_date": target_date.isoformat(),
                "workout_definition": {"session_label": "rest"},
                "status": "adjusted",
                "adjustment_reason": details["reason"],
            }
        else:
            new_row = deepcopy(row)
            new_row["session_name"] = "Rest"
            new_row["session_type"] = "rest"
            new_row["workout_definition"] = {"session_label": "rest"}
            new_row["status"] = "adjusted"
            new_row["adjustment_reason"] = details["reason"]
        return new_row, "Marked as rest day"

    if action == "mark_mountain_day":
        wd = {
            "session_label": "mountain_tour",
            "expected_duration_h": details.get("expected_duration_h"),
            "expected_elevation_m": details.get("expected_elevation_m"),
            "activity": details.get("activity"),
        }
        if row is None:
            new_row = {
                "training_block": "unscheduled",
                "week_number": 0,
                "session_name": details.get("activity") or "Mountain Day",
                "session_type": "mountain_tour",
                "scheduled_date": target_date.isoformat(),
                "workout_definition": wd,
                "status": "adjusted",
                "adjustment_reason": details["reason"],
            }
        else:
            new_row = deepcopy(row)
            new_row["session_name"] = details.get("activity") or "Mountain Day"
            new_row["session_type"] = "mountain_tour"
            new_row["workout_definition"] = wd
            new_row["status"] = "adjusted"
            new_row["adjustment_reason"] = details["reason"]
        return new_row, "Marked as mountain day"

    if action == "mark_skipped":
        new_row = deepcopy(row)
        new_row["status"] = "skipped"
        new_row["adjustment_reason"] = details["reason"]
        return new_row, "Marked as skipped"

    if action == "mark_mobility":
        from workout_generator import build_mobility_definition
        proto = details.get("protocol", "A")
        wd = build_mobility_definition(proto)
        session_name = f"Mobility (Protocol {proto})"
        if row is None:
            new_row = {
                "training_block": "unscheduled",
                "week_number": 0,
                "session_name": session_name,
                "session_type": "mobility",
                "scheduled_date": target_date.isoformat(),
                "estimated_duration_minutes": wd.get("estimated_duration_minutes"),
                "workout_definition": wd,
                "status": "adjusted",
                "adjustment_reason": details["reason"],
            }
        else:
            new_row = deepcopy(row)
            new_row["session_name"] = session_name
            new_row["session_type"] = "mobility"
            new_row["workout_definition"] = wd
            new_row["estimated_duration_minutes"] = wd.get("estimated_duration_minutes")
            new_row["status"] = "adjusted"
            new_row["adjustment_reason"] = details["reason"]
        return new_row, f"Marked as mobility (Protocol {proto})"

    if action == "mark_completed":
        new_row = deepcopy(row)
        new_row["status"] = "completed"
        if "compliance_score" in details:
            new_row["compliance_score"] = details["compliance_score"]
        if "reason" in details:
            new_row["adjustment_reason"] = details["reason"]
        return new_row, "Marked as completed"

    if action == "switch_to_home":
        from workout_push import build_home_workout_definition
        wd = row.get("workout_definition") or {}
        if wd.get("venue") == "home":
            raise ValidationError("session is already a home workout")
        home_wd = build_home_workout_definition(wd)
        new_row = deepcopy(row)
        new_row["workout_definition"] = home_wd
        new_row["status"] = "adjusted"
        new_row["adjustment_reason"] = f"Switched to home: {details['reason']}"
        return new_row, "Switched to home workout"

    if action == "switch_to_gym":
        wd = row.get("workout_definition") or {}
        original = wd.get("original_gym_definition")
        if not original:
            raise ValidationError(
                "no original gym definition found — cannot switch back"
            )
        new_row = deepcopy(row)
        new_row["workout_definition"] = original
        new_row["status"] = "adjusted"
        new_row["adjustment_reason"] = f"Switched back to gym: {details['reason']}"
        return new_row, "Switched back to gym workout"

    raise ValidationError(f"unhandled action {action}")  # pragma: no cover


# Columns we PATCH (everything else is identity / server-managed)
PATCHABLE_COLUMNS = {
    "session_name",
    "session_type",
    "workout_definition",
    "status",
    "adjustment_reason",
    "estimated_duration_minutes",
    "compliance_score",
    "garmin_workout_id",
}


def row_patch_diff(before: dict, after: dict) -> dict:
    """Subset of `after` containing only patchable, changed fields."""
    return {
        k: after[k]
        for k in PATCHABLE_COLUMNS
        if k in after and after.get(k) != before.get(k)
    }


# ---------------------------------------------------------------------------
# Side-effect runners
# ---------------------------------------------------------------------------


def run_garmin_repush(
    new_row: dict,
    target_date: date,
    sb,
) -> StepResult:
    """Re-build a Garmin workout from the (patched) workout_definition and
    upload + schedule it. Reuses workout_push.py for the heavy lifting.
    """
    try:
        # Lazy import — avoids paying the Playwright cost on dry-run / mark_rest
        from workout_push import (
            build_exception_workout,
            get_garmin_client,
            schedule_workout,
            upload_workout,
            get_program_week,
        )
    except Exception as exc:
        return StepResult.fail(f"import workout_push failed: {exc}")

    wd = new_row.get("workout_definition") or {}
    raw_exercises = wd.get("exercises") or []
    if not raw_exercises:
        return StepResult.skipped("no exercises in workout_definition")

    parsed = []
    for ex in raw_exercises:
        parsed.append({
            "name": ex.get("name", "Unknown"),
            "sets": int(ex.get("sets") or 1),
            "reps": int(ex.get("reps") or 1),
            "weight_kg": ex.get("weight_kg"),
            "rest_s": int(ex.get("rest_s") or 60),
            "duration_s": ex.get("duration_s"),
            "distance_m": ex.get("distance_m"),
            "mapped": False,  # build_exception_workout uses fuzzy match
        })

    block, week = get_program_week(target_date)
    fake_exception_info = {
        "exception": new_row.get("session_name", "Adjusted Session"),
        "original_session": new_row.get("session_name", "Adjusted Session"),
        "reason": new_row.get("adjustment_reason") or "coach adjustment",
        "pushed_status": "Pending",
    }

    try:
        workout = build_exception_workout(
            fake_exception_info, parsed, block, week, target_date,
        )
    except Exception as exc:
        return StepResult.fail(f"build_exception_workout failed: {exc}")

    try:
        client = get_garmin_client()
    except Exception as exc:
        return StepResult.fail(f"garmin auth failed: {exc}")

    workout_id = upload_workout(client, workout)
    if not workout_id:
        return StepResult.fail("upload_workout returned no id")

    if not schedule_workout(client, workout_id, target_date):
        return StepResult.fail(
            f"scheduled upload but schedule_workout failed (workout_id={workout_id})",
            workout_id=workout_id,
        )

    # Link new garmin_workout_id back to the row
    try:
        patch_row(sb, new_row["id"], {"garmin_workout_id": workout_id, "status": "pushed"})
    except Exception as exc:
        log.warning("failed to write garmin_workout_id back to row: %s", exc)

    return StepResult.ok(workout_id=workout_id)


def run_mobility_push(
    new_row: dict,
    target_date: date,
    details: dict,
    sb,
) -> StepResult:
    """Shell out to mobility_workout.py to upload + schedule a mobility session."""
    import subprocess
    proto = details.get("protocol", "A")
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "mobility_workout.py"),
        "--protocol", proto,
        "--date", target_date.isoformat(),
        "--push",
        "--json-out",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except Exception as exc:
        return StepResult.fail(f"mobility_workout.py spawn failed: {exc}")
    if proc.returncode != 0 and not proc.stdout.strip():
        return StepResult.fail(f"mobility_workout.py exit {proc.returncode}: {proc.stderr[-400:]}")
    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:
        return StepResult.fail(f"mobility_workout.py json parse failed: {exc}")
    if not payload.get("ok"):
        return StepResult.fail(payload.get("error") or "mobility push failed")
    wid = payload.get("garmin_workout_id")
    if wid and new_row.get("id"):
        try:
            patch_row(sb, new_row["id"], {"garmin_workout_id": wid})
        except Exception as exc:
            log.warning("failed to write garmin_workout_id back: %s", exc)
    return StepResult.ok(workout_id=wid, scheduled=payload.get("scheduled"))


def run_garmin_clear(new_row: dict, target_date: date) -> StepResult:
    """For mark_rest / mark_mountain_day / mark_skipped: any previously
    scheduled Garmin workout is now stale. We don't have a clean delete
    helper, so log a warning and surface it in the JSON. The user can
    delete manually from the watch.
    """
    existing = (new_row or {}).get("garmin_workout_id")
    if not existing:
        return StepResult.skipped("no existing garmin workout to clear")
    return StepResult.skipped(
        f"existing garmin workout {existing} for {target_date.isoformat()} "
        f"left in place (manual delete required)",
        stale_workout_id=existing,
    )


def run_coaching_context_append(
    target_date: date,
    action: str,
    summary: str,
    reason: str,
) -> StepResult:
    """Append a row to the Session Exceptions table in coaching-context.md."""
    try:
        content = COACHING_CONTEXT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return StepResult.fail(f"coaching-context.md not found at {COACHING_CONTEXT_PATH}")

    new_line = (
        f"| {target_date.isoformat()} | {action} | {summary} | {reason[:200]} | Pending |"
    )

    lines = content.splitlines()
    inserted = False
    for i, line in enumerate(lines):
        if line.strip().startswith("## Session Exceptions"):
            # Find the end of the table block (first blank line after the header row)
            j = i + 1
            while j < len(lines) and not (lines[j].strip() == "" and j > i + 3):
                j += 1
            lines.insert(j, new_line)
            inserted = True
            break

    if not inserted:
        # No Session Exceptions section yet — append one at the end
        lines.append("")
        lines.append("## Session Exceptions")
        lines.append("")
        lines.append("| Date | Action | Summary | Reason | Pushed |")
        lines.append("|------|--------|---------|--------|--------|")
        lines.append(new_line)

    try:
        COACHING_CONTEXT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as exc:
        return StepResult.fail(f"write coaching-context.md failed: {exc}")

    return StepResult.ok(row_added=new_line)


def run_coaching_log_insert(
    sb,
    target_date: date,
    action: str,
    details: dict,
    steps_so_far: dict,
    summary: str,
) -> StepResult:
    log_type = "train_as_planned" if action == "mark_train_as_planned" else "adjustment"
    row = {
        "date": target_date.isoformat(),
        "type": log_type,
        "channel": "coach_adjust",
        "message": summary,
        "data_context": {
            "action": action,
            "details": details,
            "steps": steps_so_far,
        },
    }
    # Phase 7 traceability columns (sql/021_coaching_log_traceability.sql).
    # Only include them if the caller supplied any of the optional fields OR
    # the action is mark_train_as_planned (where the columns are the whole
    # point). This keeps existing call sites working even before the migration
    # has been applied to prod — if any of decision_type/rule/kb_refs/inputs
    # show up here, the migration MUST be applied first.
    has_traceability = (
        action == "mark_train_as_planned"
        or "rule" in details
        or "kb_refs" in details
        or "inputs" in details
    )
    if has_traceability:
        row["decision_type"] = DECISION_TYPE_BY_ACTION.get(action, "adjust")
        row["rule"] = details.get("rule")
        row["kb_refs"] = details.get("kb_refs")
        row["inputs"] = details.get("inputs")
    try:
        res = sb.table("coaching_log").insert(row).execute()
        if not res.data:
            return StepResult.fail("coaching_log insert returned no data")
        return StepResult.ok(id=res.data[0].get("id"))
    except Exception as exc:
        return StepResult.fail(f"coaching_log insert failed: {exc}")


def run_slack_post(message: str, channel: str) -> StepResult:
    if not SLACK_BOT_TOKEN:
        return StepResult.skipped("SLACK_BOT_TOKEN not set")
    if not channel:
        return StepResult.skipped("no slack channel configured")
    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"channel": channel, "text": message},
            timeout=15,
        )
        data = resp.json()
        if not data.get("ok"):
            return StepResult.fail(f"slack api: {data.get('error', 'unknown')}")
        return StepResult.ok(ts=data.get("ts"), channel=channel)
    except Exception as exc:
        return StepResult.fail(f"slack post failed: {exc}")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def build_user_message(
    action: str,
    summary: str,
    steps: dict,
) -> str:
    """Generate the human-readable message the skill should paste to Slack.

    Disambiguation rule (audit Phase 8): if the DB write succeeded but the
    Garmin push failed, the message must explicitly say so — otherwise the
    athlete cannot tell whether to re-run the adjustment (which would
    double-write the DB) or just delete the stale Garmin workout manually.
    """
    parts = [summary + "."]
    garmin = steps.get("garmin_push") or {}
    pw = steps.get("planned_workouts") or {}
    db_landed = pw.get("status") == "ok"
    if garmin.get("status") == "fail":
        if db_landed:
            parts.append(
                f"⚠️ Database IS updated but Garmin push failed: {garmin.get('error')}. "
                f"Do NOT re-run this adjustment (would double-write the DB) — "
                f"delete the stale workout from the watch manually if needed."
            )
        else:
            parts.append(f"Garmin push failed: {garmin.get('error')}.")
    elif garmin.get("status") == "skipped" and "stale_workout_id" in garmin:
        parts.append(
            f"Stale workout still on watch — delete manually."
        )
    if not is_terminal_ok(steps):
        failures = [
            f"{name}: {res.get('error', 'unknown')}"
            for name, res in steps.items()
            if res.get("status") == "fail"
        ]
        parts.append(f"Partial failure → {'; '.join(failures)}")
    return " ".join(parts)


def run_action(args) -> dict:
    target_date = date.fromisoformat(args.date)
    try:
        details = json.loads(args.details)
        if not isinstance(details, dict):
            raise ValueError("details must be a JSON object")
    except (ValueError, json.JSONDecodeError) as exc:
        return {
            "date": args.date,
            "action": args.action,
            "ok": False,
            "exit_code": 2,
            "steps": {"validate": StepResult.fail(f"invalid --details JSON: {exc}")},
            "user_message": f"Couldn't parse --details: {exc}",
        }

    steps: dict[str, StepResult] = {}

    # Step 1: validate
    try:
        validate_action(args.action, details)
        steps["validate"] = StepResult.ok()
    except ValidationError as exc:
        return {
            "date": args.date,
            "action": args.action,
            "ok": False,
            "exit_code": 2,
            "steps": {"validate": StepResult.fail(str(exc))},
            "user_message": f"Invalid request: {exc}",
        }

    sb = get_sb()

    # Fast path: mark_train_as_planned writes ONLY a coaching_log row.
    # No planned_workouts mutation, no Garmin push, no coaching-context.md
    # append, no Slack post (the cron's daily card is the user-facing surface
    # for train-as-planned days). Closes the traceability hole where the
    # health-coach-daily cron's no-adjust branch left no audit row at all.
    if args.action == "mark_train_as_planned":
        steps["planned_workouts"] = StepResult.skipped("no-op: train as planned")
        steps["garmin_push"] = StepResult.skipped("no-op: train as planned")
        steps["coaching_context"] = StepResult.skipped("no-op: train as planned")
        if args.dry_run:
            steps["coaching_log"] = StepResult.skipped(
                "dry-run",
                would_insert={
                    "date": args.date,
                    "type": "train_as_planned",
                    "decision_type": "train_as_planned",
                    "rule": details.get("rule"),
                    "kb_refs": details.get("kb_refs"),
                    "inputs": details.get("inputs"),
                    "message": details.get("reason", ""),
                },
            )
        else:
            steps["coaching_log"] = run_coaching_log_insert(
                sb, target_date, args.action, details, dict(steps),
                details.get("reason", "train as planned"),
            )
        steps["slack"] = StepResult.skipped("no-op: train as planned (daily card is the surface)")
        ok = is_terminal_ok(steps)
        return {
            "date": args.date,
            "action": args.action,
            "ok": ok,
            "exit_code": 0 if ok else 1,
            "steps": steps,
            "user_message": details.get("reason", "train as planned (logged)"),
        }

    # Step 2: load existing row + compute patch
    try:
        existing = fetch_row(sb, target_date)
        new_row, summary = apply_action_to_row(args.action, details, existing, target_date)
    except ValidationError as exc:
        steps["planned_workouts"] = StepResult.fail(str(exc))
        return {
            "date": args.date,
            "action": args.action,
            "ok": False,
            "exit_code": 2,
            "steps": steps,
            "user_message": f"Couldn't apply action: {exc}",
        }
    except Exception as exc:
        log.error("apply_action_to_row failed: %s\n%s", exc, traceback.format_exc())
        steps["planned_workouts"] = StepResult.fail(f"apply action failed: {exc}")
        return {
            "date": args.date,
            "action": args.action,
            "ok": False,
            "exit_code": 2,
            "steps": steps,
            "user_message": f"Internal error applying action: {exc}",
        }

    # Step 3: planned_workouts write
    if args.dry_run:
        steps["planned_workouts"] = StepResult.skipped(
            "dry-run",
            would_diff=row_patch_diff(existing or {}, new_row),
            would_insert=existing is None,
        )
    else:
        try:
            if existing is None:
                # mark_rest / mark_mountain_day / replace_session can create rows
                created = insert_row(sb, new_row)
                new_row["id"] = created["id"]
                steps["planned_workouts"] = StepResult.ok(
                    row_id=created["id"],
                    inserted=True,
                    diff=row_patch_diff({}, new_row),
                )
            else:
                patch = row_patch_diff(existing, new_row)
                if not patch:
                    steps["planned_workouts"] = StepResult.skipped("no-op (row already matches)")
                else:
                    updated = patch_row(sb, existing["id"], patch)
                    new_row["id"] = updated["id"]
                    steps["planned_workouts"] = StepResult.ok(
                        row_id=updated["id"],
                        inserted=False,
                        diff=patch,
                    )
        except Exception as exc:
            log.error("planned_workouts write failed: %s\n%s", exc, traceback.format_exc())
            steps["planned_workouts"] = StepResult.fail(f"supabase write failed: {exc}")
            return {
                "date": args.date,
                "action": args.action,
                "ok": False,
                "exit_code": 2,
                "steps": steps,
                "user_message": f"Database write failed: {exc}",
            }

    # Special case: reschedule_session writes a SECOND row at to_date
    if args.action == "reschedule_session" and not args.dry_run:
        try:
            to_date = date.fromisoformat(details["to_date"])
            target_existing = fetch_row(sb, to_date)
            # Build the destination row from the original (pre-patch) workout
            dest_def = (existing or {}).get("workout_definition")
            dest_row = {
                "training_block": (existing or {}).get("training_block", "unscheduled"),
                "week_number": (existing or {}).get("week_number", 0),
                "session_name": (existing or {}).get("session_name", "Rescheduled"),
                "session_type": (existing or {}).get("session_type", "strength"),
                "scheduled_date": to_date.isoformat(),
                "estimated_duration_minutes": (existing or {}).get("estimated_duration_minutes"),
                "workout_definition": dest_def,
                "status": "adjusted",
                "adjustment_reason": f"rescheduled from {target_date.isoformat()}: {details['reason']}",
            }
            if target_existing:
                dest_patch = row_patch_diff(target_existing, dest_row)
                patch_row(sb, target_existing["id"], dest_patch)
                steps["reschedule_target"] = StepResult.ok(
                    row_id=target_existing["id"], updated=True, diff=dest_patch,
                )
            else:
                created = insert_row(sb, dest_row)
                steps["reschedule_target"] = StepResult.ok(
                    row_id=created["id"], inserted=True,
                )
        except Exception as exc:
            steps["reschedule_target"] = StepResult.fail(f"reschedule target write failed: {exc}")

    # Step 4: Garmin (re-push or clear)
    if args.dry_run:
        steps["garmin_push"] = StepResult.skipped("dry-run")
    elif args.no_garmin:
        steps["garmin_push"] = StepResult.skipped("--no-garmin")
    elif args.action in GARMIN_REPUSH_ACTIONS:
        steps["garmin_push"] = run_garmin_repush(new_row, target_date, sb)
    elif args.action in GARMIN_MOBILITY_ACTIONS:
        steps["garmin_push"] = run_mobility_push(new_row, target_date, details, sb)
    elif args.action in GARMIN_CLEAR_ACTIONS:
        steps["garmin_push"] = run_garmin_clear(existing, target_date)
    else:
        steps["garmin_push"] = StepResult.skipped(f"action {args.action} does not push")

    # Step 5: coaching-context.md append
    if args.dry_run:
        steps["coaching_context"] = StepResult.skipped("dry-run")
    else:
        steps["coaching_context"] = run_coaching_context_append(
            target_date, args.action, summary, details.get("reason", ""),
        )

    # Step 6: coaching_log
    if args.dry_run:
        steps["coaching_log"] = StepResult.skipped("dry-run")
    else:
        steps["coaching_log"] = run_coaching_log_insert(
            sb, target_date, args.action, details, dict(steps), summary,
        )

    # Step 7: Slack
    user_message = build_user_message(args.action, summary, steps)
    if args.dry_run:
        steps["slack"] = StepResult.skipped("dry-run")
    elif args.no_slack:
        steps["slack"] = StepResult.skipped("--no-slack")
    else:
        steps["slack"] = run_slack_post(user_message, SLACK_CHANNEL_TRAINING)

    ok = is_terminal_ok(steps)
    pw_status = steps.get("planned_workouts", {}).get("status")
    if not ok and pw_status == "fail":
        exit_code = 2
    elif not ok:
        exit_code = 1  # planned_workouts landed but something downstream failed
    else:
        exit_code = 0

    return {
        "date": args.date,
        "action": args.action,
        "ok": ok,
        "exit_code": exit_code,
        "steps": steps,
        "user_message": user_message,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Single write-path for health-coach session adjustments.",
    )
    parser.add_argument("--date", required=True, help="Target date (YYYY-MM-DD)")
    parser.add_argument(
        "--action", required=True, choices=sorted(ACTIONS),
        help="Adjustment action to apply",
    )
    parser.add_argument(
        "--details", required=True,
        help="Action-specific details as a JSON object string",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate and compute the diff but write nothing",
    )
    parser.add_argument(
        "--no-garmin", action="store_true",
        help="Skip Garmin push step (useful when auth is broken)",
    )
    parser.add_argument(
        "--no-slack", action="store_true",
        help="Skip Slack post step",
    )
    args = parser.parse_args()

    try:
        result = run_action(args)
    except Exception as exc:
        log.error("unexpected failure: %s\n%s", exc, traceback.format_exc())
        result = {
            "date": args.date,
            "action": args.action,
            "ok": False,
            "exit_code": 2,
            "steps": {"_unhandled": StepResult.fail(str(exc))},
            "user_message": f"Unexpected error: {exc}",
        }

    print(json.dumps(result, indent=2, default=str))
    sys.exit(result.get("exit_code", 1))


if __name__ == "__main__":
    main()

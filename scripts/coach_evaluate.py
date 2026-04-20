#!/usr/bin/env python3
"""On-demand coaching evaluation triggered from the Ascent app.

Reads daily_coaching_context + planned_workouts, applies the deterministic
decision matrix from SKILL.md, and writes through coach_adjust.py.

This handles the ~80% of days where the decision is straightforward:
  - All green → train as planned
  - HRV LOW → rest
  - Hard overrides (BB<30, TR<40, wellness<2.5) → rest
  - Mountain interference → lighten
  - Unbalanced + short sleep → rest

The daily CCD agent (09:43) still runs for nuanced reasoning, injury
accommodation, and KB-informed adjustments. This script provides a quick
programmatic evaluation when the athlete wants a decision outside that window.

Usage:
    python coach_evaluate.py                    # evaluate today
    python coach_evaluate.py --date 2026-04-16  # specific date
    python coach_evaluate.py --dry-run          # preview without writing
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", os.environ["SUPABASE_KEY"])
VENV_PYTHON = str(PROJECT_ROOT / "venv" / "bin" / "python")
COACH_ADJUST = str(PROJECT_ROOT / "scripts" / "coach_adjust.py")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("coach_evaluate")


def get_coaching_context(sb) -> dict | None:
    """Fetch the single-row daily_coaching_context view."""
    res = sb.table("daily_coaching_context").select("*").limit(1).execute()
    return res.data[0] if res.data else None


def get_planned_workout(sb, target_date: str) -> dict | None:
    """Fetch today's planned workout."""
    res = (
        sb.table("planned_workouts")
        .select("*")
        .eq("scheduled_date", target_date)
        .execute()
    )
    return res.data[0] if res.data else None


def get_wellness(sb, target_date: str) -> dict | None:
    """Fetch today's subjective wellness if submitted."""
    res = (
        sb.table("subjective_wellness")
        .select("composite_score")
        .eq("date", target_date)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def evaluate(ctx: dict, planned: dict | None, wellness: dict | None) -> dict:
    """Apply the SKILL.md decision matrix. Returns action + details for coach_adjust.py."""

    hrv_status = (ctx.get("hrv_status") or "").upper()
    sleep_hours = ctx.get("sleep_hours")
    bb_high = ctx.get("body_battery_highest")
    tr_score = ctx.get("training_readiness_score")
    hard_override = ctx.get("hard_override")
    mountain_3d = ctx.get("mountain_days_3d") or 0
    elevation_3d = ctx.get("elevation_3d") or 0
    last_srpe = ctx.get("last_srpe")
    is_deload = ctx.get("is_deload_week") or False
    wellness_score = wellness.get("composite_score") if wellness else None
    is_fallback = ctx.get("is_fallback_data") or False

    inputs = {
        "hrv_status": hrv_status or None,
        "sleep_hours": sleep_hours,
        "body_battery_highest": bb_high,
        "training_readiness_score": tr_score,
        "mountain_days_3d": mountain_3d,
        "last_srpe": last_srpe,
        "hard_override": hard_override,
        "wellness_composite": wellness_score,
        "is_fallback_data": is_fallback,
        "channel": "app_trigger",
    }

    # No planned workout → nothing to decide
    if not planned:
        return {
            "action": None,
            "reason": "No planned workout for today.",
            "rule": None,
            "inputs": inputs,
        }

    session_type = planned.get("session_type", "")
    if session_type == "rest":
        return {
            "action": "mark_train_as_planned",
            "reason": "Rest day as planned.",
            "rule": "R-TAP",
            "kb_refs": ["recovery-baseline"],
            "inputs": inputs,
        }

    # === Hard overrides (SKILL.md: always apply) ===
    if wellness_score is not None and wellness_score < 2.5:
        return {
            "action": "mark_rest",
            "reason": f"Wellness score {wellness_score:.1f}/5 — below 2.5 threshold. Rest recommended.",
            "rule": "recovery.wellness_low.rest",
            "kb_refs": ["domain-1.1", "wellness-override"],
            "inputs": inputs,
        }

    if bb_high is not None and bb_high < 30:
        return {
            "action": "mark_rest",
            "reason": f"Body Battery {bb_high} — below 30 hard override. Rest recommended.",
            "rule": "recovery.bb_low.rest",
            "kb_refs": ["domain-1.1"],
            "inputs": inputs,
        }

    if tr_score is not None and tr_score < 40:
        return {
            "action": "mark_rest",
            "reason": f"Training Readiness {tr_score} — below 40 hard override. Rest recommended.",
            "rule": "recovery.tr_low.rest",
            "kb_refs": ["domain-1.1"],
            "inputs": inputs,
        }

    # Multi-signal convergence (3+ degraded = force rest)
    degraded_count = 0
    if hrv_status == "LOW":
        degraded_count += 1
    if sleep_hours is not None and sleep_hours < 6:
        degraded_count += 1
    if bb_high is not None and bb_high < 50:
        degraded_count += 1
    if tr_score is not None and tr_score < 50:
        degraded_count += 1
    if wellness_score is not None and wellness_score < 3:
        degraded_count += 1

    if degraded_count >= 3:
        return {
            "action": "mark_rest",
            "reason": f"{degraded_count} recovery signals degraded — multi-signal convergence. Rest recommended.",
            "rule": "recovery.multi_signal.rest",
            "kb_refs": ["domain-1.1", "rule-13"],
            "inputs": inputs,
        }

    # === Decision matrix (HRV status × sleep) ===

    if hrv_status == "LOW":
        return {
            "action": "mark_rest",
            "reason": f"HRV status LOW — rest or mobility only.",
            "rule": "recovery.hrv_low.rest",
            "kb_refs": ["domain-1.1"],
            "inputs": inputs,
        }

    if hrv_status == "UNBALANCED" and sleep_hours is not None and sleep_hours < 6:
        return {
            "action": "mark_rest",
            "reason": f"HRV unbalanced + sleep {sleep_hours:.1f}h (<6h) — rest recommended.",
            "rule": "recovery.unbalanced_sleep_short.rest",
            "kb_refs": ["domain-1.1"],
            "inputs": inputs,
        }

    if hrv_status == "UNBALANCED":
        return {
            "action": "lighten_session",
            "reason": f"HRV unbalanced — train but cap RPE at 6.",
            "rule": "recovery.unbalanced.lighten",
            "kb_refs": ["domain-1.1"],
            "inputs": inputs,
            "extra_details": {"rpe_cap": 6},
        }

    if sleep_hours is not None and sleep_hours < 6:
        return {
            "action": "lighten_session",
            "reason": f"Sleep {sleep_hours:.1f}h (<6h) — reduce volume 30%, cap RPE at 6.",
            "rule": "recovery.sleep_short.lighten",
            "kb_refs": ["domain-1.1"],
            "inputs": inputs,
            "extra_details": {"volume_reduction": 0.3, "rpe_cap": 6},
        }

    # Mountain interference: weekend mountain + Monday gym → cap RPE
    if mountain_3d > 0 and elevation_3d > 800:
        return {
            "action": "lighten_session",
            "reason": f"Mountain activity in past 3 days ({elevation_3d}m elevation) — cap RPE at 6.",
            "rule": "mountain.recent_load.lighten",
            "kb_refs": ["domain-1.1", "rule-17"],
            "inputs": inputs,
            "extra_details": {"rpe_cap": 6},
        }

    # All green
    reasons = []
    if bb_high is not None:
        reasons.append(f"BB {bb_high}")
    if sleep_hours is not None:
        reasons.append(f"{sleep_hours:.1f}h sleep")
    if tr_score is not None:
        reasons.append(f"TR {tr_score}")
    if mountain_3d == 0:
        reasons.append("no mountain load")
    reason_str = ", ".join(reasons) + " — all signals clear to train as planned."

    return {
        "action": "mark_train_as_planned",
        "reason": reason_str,
        "rule": "all_green.train_as_planned",
        "kb_refs": ["domain-1.1"],
        "inputs": inputs,
    }


def run_coach_adjust(target_date: str, decision: dict, dry_run: bool = False) -> dict:
    """Call coach_adjust.py with the decision."""
    action = decision["action"]
    if action is None:
        return {"ok": True, "action": None, "message": decision["reason"]}

    details = {
        "reason": decision["reason"],
        "rule": decision.get("rule"),
        "kb_refs": decision.get("kb_refs", []),
        "inputs": decision.get("inputs", {}),
    }
    # Merge extra details (volume_reduction, rpe_cap, etc.)
    if "extra_details" in decision:
        details.update(decision["extra_details"])

    cmd = [
        VENV_PYTHON, COACH_ADJUST,
        "--date", target_date,
        "--action", action,
        "--details", json.dumps(details),
        "--no-slack",
    ]
    if dry_run:
        cmd.append("--dry-run")

    log.info("Running: %s %s", action, target_date)
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=120, cwd=str(PROJECT_ROOT)
    )

    try:
        output = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        output = {
            "ok": result.returncode == 0,
            "stdout": result.stdout[-500:] if result.stdout else "",
            "stderr": result.stderr[-500:] if result.stderr else "",
        }

    output["action"] = action
    output["decision_reason"] = decision["reason"]
    output["decision_rule"] = decision.get("rule")
    return output


def main():
    parser = argparse.ArgumentParser(description="On-demand coaching evaluation")
    parser.add_argument("--date", help="Target date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    target_date = args.date or date.today().isoformat()
    log.info("Evaluating coaching for %s", target_date)

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    ctx = get_coaching_context(sb)
    if not ctx:
        result = {"ok": False, "error": "Could not read daily_coaching_context"}
        print(json.dumps(result))
        sys.exit(1)

    planned = get_planned_workout(sb, target_date)
    wellness = get_wellness(sb, target_date)

    decision = evaluate(ctx, planned, wellness)
    log.info("Decision: %s — %s", decision.get("action"), decision.get("reason"))

    if decision["action"] is None:
        result = {"ok": True, "action": None, "message": decision["reason"]}
        print(json.dumps(result))
        return

    result = run_coach_adjust(target_date, decision, dry_run=args.dry_run)
    print(json.dumps(result))

    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()

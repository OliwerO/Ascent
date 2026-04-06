#!/usr/bin/env python3
"""Coaching decision retrospective — evaluates past decisions against outcomes.

Looks at each coaching decision (train/rest/adjust) and checks what happened:
- Did the athlete complete the session? At what volume/RPE?
- Did recovery metrics improve or degrade after rest decisions?
- Are exercises progressing at the expected rate?

Writes findings to coaching_decision_outcomes and updates
athlete_response_patterns with recovery_response patterns.

Usage:
    python decision_retrospective.py                  # evaluate last 14 days
    python decision_retrospective.py --lookback 30    # evaluate last 30 days
    python decision_retrospective.py --dry-run        # print findings, don't write
    python decision_retrospective.py --velocity-only  # only progression velocity

Called by:
    - Weekly review cron (Sunday 20:00)
    - Importable: from decision_retrospective import evaluate_recent_decisions
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", os.environ["SUPABASE_KEY"])

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("retrospective")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DecisionOutcome:
    """Evaluated outcome of a coaching decision."""
    coaching_log_id: int
    decision_date: str
    decision_type: str
    recovery_signals: dict
    next_session_performance: dict | None
    recovery_trajectory: dict | None
    outcome_quality: str  # 'good', 'neutral', 'poor'
    assessment_notes: str


@dataclass
class ProgressionSummary:
    """Summary of progression velocity for an exercise."""
    exercise_name: str
    planned_weight_kg: float
    start_weight_kg: float | None
    total_gain_kg: float
    weeks_tracked: int
    kg_per_week: float | None
    sessions_at_weight: int
    status: str  # 'on_track', 'behind', 'stalled', 'deloading'
    current_e1rm: float | None


# ---------------------------------------------------------------------------
# Supabase helpers (same pattern as interference_analysis.py)
# ---------------------------------------------------------------------------

def supabase_get(table: str, params: dict | None = None) -> list:
    """GET from Supabase REST API."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    resp = requests.get(url, headers=SUPABASE_HEADERS, params=params or {}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def supabase_upsert(table: str, data: dict) -> bool:
    """Upsert a row into Supabase. Returns True on success."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {**SUPABASE_HEADERS, "Prefer": "resolution=merge-duplicates,return=minimal"}
    resp = requests.post(url, headers=headers, json=data, timeout=15)
    if resp.status_code in (200, 201, 204):
        return True
    log.error("Upsert failed (%s): %s %s", table, resp.status_code, resp.text)
    return False


# ---------------------------------------------------------------------------
# Decision evaluation
# ---------------------------------------------------------------------------

def _classify_decision_type(log_entry: dict) -> str | None:
    """Extract the decision type from a coaching_log entry."""
    entry_type = log_entry.get("type", "")
    ctx = log_entry.get("data_context") or {}

    if entry_type in ("daily_plan", "daily_session"):
        decision = ctx.get("decision") or ctx.get("recovery_action") or ""
        if "rest" in decision.lower():
            return "rest_override"
        if "reduce" in decision.lower() or ctx.get("exception_type") == "reduce":
            return "volume_reduction"
        if "moderate" in decision.lower():
            return "train_moderate"
        if "planned" in decision.lower():
            return "train_as_planned"
        # Default: if a session_key exists, it was a training decision
        if ctx.get("session_key"):
            return "train_moderate" if ctx.get("recovery_rpe") else "train_as_planned"
        return None

    if entry_type == "adjustment":
        return "volume_reduction"

    if entry_type == "schedule_change":
        return "schedule_change"

    return None


def _extract_recovery_signals(ctx: dict) -> dict:
    """Pull recovery signals from coaching_log data_context."""
    return {
        k: ctx.get(k)
        for k in [
            "hrv_avg", "hrv_weekly_avg", "hrv_status",
            "sleep_hours", "body_battery_highest", "body_battery_lowest",
            "training_readiness_score", "mountain_days_3d",
            "recovery_action", "is_fallback_data",
        ]
        if ctx.get(k) is not None
    }


def _get_next_gym_session(decision_date: str) -> dict | None:
    """Find the next gym training_session after a decision date."""
    rows = supabase_get("training_sessions", {
        "date": f"gt.{decision_date}",
        "order": "date.asc",
        "limit": "1",
    })
    return rows[0] if rows else None


def _get_recovery_trajectory(decision_date: str) -> dict | None:
    """Get HRV/sleep metrics for 24-48h after a decision."""
    d = date.fromisoformat(decision_date)
    d1 = (d + timedelta(days=1)).isoformat()
    d2 = (d + timedelta(days=2)).isoformat()

    rows = supabase_get("daily_summary", {
        "date": f"in.({d1},{d2})",
        "select": "date,hrv_avg,hrv_status,sleep_score,total_sleep_seconds,body_battery_highest,resting_hr",
        "order": "date.asc",
    })

    if not rows:
        return None

    # Also get the decision-day metrics for comparison
    baseline_rows = supabase_get("daily_summary", {
        "date": f"eq.{decision_date}",
        "select": "hrv_avg,sleep_score,total_sleep_seconds,body_battery_highest,resting_hr",
    })
    baseline = baseline_rows[0] if baseline_rows else {}

    trajectory = {
        "baseline": {k: baseline.get(k) for k in ["hrv_avg", "sleep_score", "body_battery_highest", "resting_hr"]},
        "days_after": [],
    }
    for r in rows:
        trajectory["days_after"].append({
            "date": r["date"],
            "hrv_avg": r.get("hrv_avg"),
            "sleep_score": r.get("sleep_score"),
            "body_battery_highest": r.get("body_battery_highest"),
            "resting_hr": r.get("resting_hr"),
        })

    return trajectory


def _assess_train_decision(next_session: dict | None, recovery: dict | None, signals: dict) -> tuple[str, str]:
    """Assess quality of a 'train' decision (as planned or moderate)."""
    notes = []

    if not next_session:
        return "neutral", "No subsequent gym session found to evaluate."

    volume = next_session.get("total_volume_kg")
    srpe = next_session.get("srpe")
    rating = next_session.get("rating")

    # Session completed = baseline good
    notes.append(f"Session completed: {next_session.get('name', '?')}")

    # Check if recovery degraded after training
    if recovery and recovery.get("days_after"):
        baseline_hrv = (recovery.get("baseline") or {}).get("hrv_avg")
        after_hrv_values = [d.get("hrv_avg") for d in recovery["days_after"] if d.get("hrv_avg")]

        if baseline_hrv and after_hrv_values:
            avg_after = mean(after_hrv_values)
            hrv_delta = avg_after - baseline_hrv
            if hrv_delta < -15:
                notes.append(f"HRV dropped significantly: {baseline_hrv:.0f} → {avg_after:.0f}")
                return "poor", " ".join(notes)
            elif hrv_delta > 5:
                notes.append(f"HRV improved: {baseline_hrv:.0f} → {avg_after:.0f}")

    # sRPE check — if they reported high RPE on a "moderate" day, the call was borderline
    if srpe is not None and srpe >= 9:
        notes.append(f"sRPE was {srpe} — session felt very hard")
        return "neutral", " ".join(notes)

    if srpe is not None and srpe <= 7:
        notes.append(f"sRPE {srpe} — well within target range")

    return "good", " ".join(notes)


def _assess_rest_decision(recovery: dict | None, signals: dict) -> tuple[str, str]:
    """Assess quality of a rest/skip decision."""
    notes = ["Rest day taken."]

    if not recovery or not recovery.get("days_after"):
        return "neutral", "No follow-up recovery data to evaluate rest decision."

    baseline = recovery.get("baseline") or {}
    after_days = recovery["days_after"]

    baseline_hrv = baseline.get("hrv_avg")
    baseline_sleep = baseline.get("sleep_score")
    baseline_bb = baseline.get("body_battery_highest")

    improvements = 0
    degradations = 0

    for day in after_days:
        if baseline_hrv and day.get("hrv_avg"):
            delta = day["hrv_avg"] - baseline_hrv
            if delta > 5:
                improvements += 1
            elif delta < -10:
                degradations += 1

        if baseline_sleep and day.get("sleep_score"):
            delta = day["sleep_score"] - baseline_sleep
            if delta > 5:
                improvements += 1
            elif delta < -10:
                degradations += 1

        if baseline_bb and day.get("body_battery_highest"):
            delta = day["body_battery_highest"] - baseline_bb
            if delta > 10:
                improvements += 1
            elif delta < -15:
                degradations += 1

    if improvements >= 2:
        notes.append("Recovery metrics improved in 24-48h — rest was the right call.")
        return "good", " ".join(notes)
    elif degradations >= 2:
        notes.append("Recovery continued degrading despite rest — may indicate deeper fatigue or illness.")
        return "neutral", " ".join(notes)
    else:
        notes.append("Recovery metrics stable after rest.")
        return "neutral", " ".join(notes)


def _assess_reduction_decision(next_session: dict | None, recovery: dict | None, signals: dict) -> tuple[str, str]:
    """Assess quality of a volume reduction decision."""
    notes = ["Volume reduction applied."]

    if not next_session:
        return "neutral", "No subsequent session to evaluate reduction impact."

    srpe = next_session.get("srpe")

    # A good reduction = next session completed at moderate RPE + recovery stable
    if srpe is not None and srpe <= 7:
        notes.append(f"Next session sRPE {srpe} — reduced load was appropriate.")
        quality = "good"
    elif srpe is not None and srpe >= 9:
        notes.append(f"Next session sRPE {srpe} — may not have reduced enough.")
        quality = "neutral"
    else:
        quality = "neutral"

    if recovery and recovery.get("days_after"):
        baseline_hrv = (recovery.get("baseline") or {}).get("hrv_avg")
        after_hrvs = [d.get("hrv_avg") for d in recovery["days_after"] if d.get("hrv_avg")]
        if baseline_hrv and after_hrvs:
            avg_after = mean(after_hrvs)
            if avg_after >= baseline_hrv - 5:
                notes.append("Recovery maintained.")
                if quality != "good":
                    quality = "good"

    return quality, " ".join(notes)


def evaluate_recent_decisions(lookback_days: int = 14) -> list[DecisionOutcome]:
    """Evaluate coaching decisions from the last N days."""
    cutoff = (date.today() - timedelta(days=lookback_days)).isoformat()

    entries = supabase_get("coaching_log", {
        "date": f"gte.{cutoff}",
        "type": "in.(daily_plan,daily_session,adjustment,schedule_change)",
        "order": "date.asc",
        "select": "id,date,type,message,data_context",
    })

    if not entries:
        log.info("No coaching decisions found in the last %d days.", lookback_days)
        return []

    # Check which decisions already have outcomes (avoid re-evaluation)
    existing = supabase_get("coaching_decision_outcomes", {
        "decision_date": f"gte.{cutoff}",
        "select": "coaching_log_id",
    })
    existing_ids = {r["coaching_log_id"] for r in existing}

    outcomes: list[DecisionOutcome] = []

    for entry in entries:
        if entry["id"] in existing_ids:
            continue

        decision_type = _classify_decision_type(entry)
        if not decision_type:
            continue

        ctx = entry.get("data_context") or {}
        signals = _extract_recovery_signals(ctx)

        # Need at least 48h to have passed for meaningful evaluation
        decision_date = entry["date"]
        if date.fromisoformat(decision_date) > date.today() - timedelta(days=2):
            continue

        # Gather outcome data
        next_session = _get_next_gym_session(decision_date)
        recovery = _get_recovery_trajectory(decision_date)

        # Assess based on decision type
        if decision_type == "rest_override":
            quality, notes = _assess_rest_decision(recovery, signals)
        elif decision_type == "volume_reduction":
            quality, notes = _assess_reduction_decision(next_session, recovery, signals)
        elif decision_type in ("train_as_planned", "train_moderate"):
            quality, notes = _assess_train_decision(next_session, recovery, signals)
        elif decision_type == "schedule_change":
            # Schedule changes are informational — assess based on whether
            # the rescheduled session was completed
            if next_session:
                quality, notes = "good", f"Rescheduled session completed: {next_session.get('name', '?')}"
            else:
                quality, notes = "neutral", "Rescheduled session not yet completed."
        else:
            continue

        # Build next_session_performance summary
        next_perf = None
        if next_session:
            next_perf = {
                "date": next_session.get("date"),
                "name": next_session.get("name"),
                "total_volume_kg": next_session.get("total_volume_kg"),
                "total_sets": next_session.get("total_sets"),
                "srpe": next_session.get("srpe"),
                "rating": next_session.get("rating"),
            }

        outcomes.append(DecisionOutcome(
            coaching_log_id=entry["id"],
            decision_date=decision_date,
            decision_type=decision_type,
            recovery_signals=signals,
            next_session_performance=next_perf,
            recovery_trajectory=recovery,
            outcome_quality=quality,
            assessment_notes=notes,
        ))

    return outcomes


# ---------------------------------------------------------------------------
# Progression velocity
# ---------------------------------------------------------------------------

def get_progression_velocity() -> list[ProgressionSummary]:
    """Query the progression_velocity view for current state."""
    try:
        rows = supabase_get("progression_velocity", {
            "select": "*",
            "order": "progression_status.asc,exercise_name.asc",
        })
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            log.warning("progression_velocity view not found — migration not deployed?")
            return []
        raise

    summaries = []
    for r in rows:
        summaries.append(ProgressionSummary(
            exercise_name=r["exercise_name"],
            planned_weight_kg=r.get("planned_weight_kg", 0),
            start_weight_kg=r.get("start_weight_kg"),
            total_gain_kg=r.get("total_weight_gain_kg", 0) or 0,
            weeks_tracked=r.get("weeks_tracked", 0) or 0,
            kg_per_week=r.get("kg_per_week"),
            sessions_at_weight=r.get("sessions_at_current_weight", 1),
            status=r.get("progression_status", "on_track"),
            current_e1rm=r.get("current_e1rm"),
        ))
    return summaries


# ---------------------------------------------------------------------------
# Pattern updates → athlete_response_patterns
# ---------------------------------------------------------------------------

def _confidence_level(n: int) -> str:
    if n >= 15:
        return "high"
    elif n >= 5:
        return "medium"
    return "low"


def compute_decision_patterns(outcomes: list[DecisionOutcome]) -> list[dict]:
    """Aggregate decision outcomes into learnable patterns."""
    patterns = []

    # Group by decision type
    by_type: dict[str, list[DecisionOutcome]] = {}
    for o in outcomes:
        by_type.setdefault(o.decision_type, []).append(o)

    for dtype, group in by_type.items():
        if len(group) < 2:
            continue

        good = [o for o in group if o.outcome_quality == "good"]
        poor = [o for o in group if o.outcome_quality == "poor"]
        total = len(group)
        good_pct = round(len(good) / total * 100)

        patterns.append({
            "pattern_type": "recovery_response",
            "pattern_key": f"decision_{dtype}_success_rate",
            "observation": (
                f"'{dtype}' decisions: {good_pct}% led to good outcomes "
                f"({len(good)}/{total}). "
                + (f"{len(poor)} had poor outcomes." if poor else "No poor outcomes.")
            ),
            "confidence": _confidence_level(total),
            "sample_size": total,
            "effect_size": round(len(good) / max(total, 1), 2),
            "data_summary": {
                "decision_type": dtype,
                "total": total,
                "good": len(good),
                "neutral": len([o for o in group if o.outcome_quality == "neutral"]),
                "poor": len(poor),
                "good_pct": good_pct,
            },
            "first_observed": min(o.decision_date for o in group),
            "last_updated": date.today().isoformat(),
        })

    # Special pattern: rest decisions when HRV was low
    rest_decisions = by_type.get("rest_override", [])
    hrv_low_rest = [o for o in rest_decisions
                    if (o.recovery_signals.get("hrv_status") or "").upper() == "LOW"]
    if hrv_low_rest:
        good_after_rest = [o for o in hrv_low_rest if o.outcome_quality == "good"]
        n = len(hrv_low_rest)
        patterns.append({
            "pattern_type": "recovery_response",
            "pattern_key": "rest_after_hrv_low",
            "observation": (
                f"Rest on HRV LOW days → good outcome {len(good_after_rest)}/{n} times "
                f"({round(len(good_after_rest)/max(n,1)*100)}% success rate)."
            ),
            "confidence": _confidence_level(n),
            "sample_size": n,
            "effect_size": round(len(good_after_rest) / max(n, 1), 2),
            "data_summary": {
                "total_hrv_low_rest": n,
                "good_outcomes": len(good_after_rest),
            },
            "first_observed": min(o.decision_date for o in hrv_low_rest),
            "last_updated": date.today().isoformat(),
        })

    return patterns


# ---------------------------------------------------------------------------
# Write results
# ---------------------------------------------------------------------------

def write_outcomes(outcomes: list[DecisionOutcome], dry_run: bool = False) -> int:
    """Write decision outcomes to Supabase. Returns count written."""
    written = 0
    for o in outcomes:
        data = {
            "coaching_log_id": o.coaching_log_id,
            "decision_date": o.decision_date,
            "decision_type": o.decision_type,
            "recovery_signals": o.recovery_signals,
            "next_session_performance": o.next_session_performance,
            "recovery_trajectory": o.recovery_trajectory,
            "outcome_quality": o.outcome_quality,
            "assessment_notes": o.assessment_notes,
        }
        if dry_run:
            log.info("[DRY RUN] Would write outcome: %s on %s → %s (%s)",
                     o.decision_type, o.decision_date, o.outcome_quality, o.assessment_notes)
        else:
            if supabase_upsert("coaching_decision_outcomes", data):
                written += 1
    return written


def write_patterns(patterns: list[dict], dry_run: bool = False) -> int:
    """Write patterns to athlete_response_patterns. Returns count written."""
    written = 0
    for p in patterns:
        if dry_run:
            log.info("[DRY RUN] Would write pattern: %s — %s (%s confidence, n=%d)",
                     p["pattern_key"], p["observation"], p["confidence"], p["sample_size"])
        else:
            if supabase_upsert("athlete_response_patterns", p):
                written += 1
    return written


# ---------------------------------------------------------------------------
# Summary generation (for weekly review Slack post)
# ---------------------------------------------------------------------------

def generate_retrospective_summary(
    outcomes: list[DecisionOutcome],
    velocity: list[ProgressionSummary],
) -> str:
    """Generate a natural language summary for the weekly review."""
    lines = []

    # Decision quality
    if outcomes:
        good = sum(1 for o in outcomes if o.outcome_quality == "good")
        neutral = sum(1 for o in outcomes if o.outcome_quality == "neutral")
        poor = sum(1 for o in outcomes if o.outcome_quality == "poor")
        total = len(outcomes)
        lines.append(f"**Decision Quality:** {good} good, {neutral} neutral, {poor} poor out of {total} decisions evaluated.")

        # Highlight any poor decisions
        for o in outcomes:
            if o.outcome_quality == "poor":
                lines.append(f"  ⚠️ {o.decision_type} on {o.decision_date}: {o.assessment_notes}")
    else:
        lines.append("**Decision Quality:** No decisions old enough to evaluate yet.")

    # Progression velocity
    if velocity:
        stalled = [v for v in velocity if v.status == "stalled"]
        behind = [v for v in velocity if v.status == "behind"]
        on_track = [v for v in velocity if v.status == "on_track"]

        lines.append(f"\n**Progression:** {len(on_track)} on track, {len(behind)} behind, {len(stalled)} stalled.")

        if stalled:
            names = ", ".join(v.exercise_name for v in stalled[:3])
            lines.append(f"  🔴 Stalled: {names}")

        if behind:
            names = ", ".join(f"{v.exercise_name} ({v.sessions_at_weight} sessions at {v.planned_weight_kg}kg)" for v in behind[:3])
            lines.append(f"  🟡 Watch: {names}")

        # Show gains for exercises with meaningful progress
        gainers = [v for v in velocity if v.total_gain_kg > 0 and v.weeks_tracked >= 2]
        if gainers:
            best = sorted(gainers, key=lambda v: v.total_gain_kg, reverse=True)[:3]
            for v in best:
                lines.append(f"  📈 {v.exercise_name}: {v.start_weight_kg}kg → {v.planned_weight_kg}kg (+{v.total_gain_kg}kg in {v.weeks_tracked}w)")
    else:
        lines.append("\n**Progression:** No progression data yet.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Coaching decision retrospective")
    parser.add_argument("--lookback", type=int, default=14, help="Days to look back (default: 14)")
    parser.add_argument("--dry-run", action="store_true", help="Print findings, don't write to DB")
    parser.add_argument("--velocity-only", action="store_true", help="Only run progression velocity")
    args = parser.parse_args()

    if not args.velocity_only:
        log.info("Evaluating coaching decisions from the last %d days...", args.lookback)
        outcomes = evaluate_recent_decisions(args.lookback)
        log.info("Found %d decisions to evaluate.", len(outcomes))

        if outcomes:
            written = write_outcomes(outcomes, dry_run=args.dry_run)
            log.info("Wrote %d decision outcomes.", written)

            patterns = compute_decision_patterns(outcomes)
            if patterns:
                pw = write_patterns(patterns, dry_run=args.dry_run)
                log.info("Wrote %d decision patterns.", pw)
    else:
        outcomes = []

    log.info("Computing progression velocity...")
    velocity = get_progression_velocity()
    log.info("Tracked %d exercises.", len(velocity))

    for v in velocity:
        status_icon = {"stalled": "🔴", "behind": "🟡", "on_track": "🟢", "deloading": "⏸️"}.get(v.status, "?")
        log.info("  %s %s: %skg (%s, %d sessions at weight)",
                 status_icon, v.exercise_name, v.planned_weight_kg, v.status, v.sessions_at_weight)

    # Generate summary
    summary = generate_retrospective_summary(outcomes, velocity)
    print("\n" + summary)

    # Progression velocity patterns
    stalled = [v for v in velocity if v.status == "stalled"]
    if len(stalled) >= 3:
        log.warning("⚠️  3+ exercises stalled — flagging for Opus review")
        if not args.dry_run:
            supabase_upsert("athlete_response_patterns", {
                "pattern_type": "progression_velocity",
                "pattern_key": "multi_exercise_stall",
                "observation": f"{len(stalled)} exercises stalled simultaneously: {', '.join(v.exercise_name for v in stalled[:5])}. Consider program redesign.",
                "confidence": "high",
                "sample_size": len(stalled),
                "effect_size": None,
                "data_summary": {
                    "stalled_exercises": [{"name": v.exercise_name, "weight": v.planned_weight_kg, "sessions": v.sessions_at_weight} for v in stalled],
                },
                "first_observed": date.today().isoformat(),
                "last_updated": date.today().isoformat(),
            })


if __name__ == "__main__":
    main()

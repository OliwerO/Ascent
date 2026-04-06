#!/usr/bin/env python3
"""Body recomposition trajectory analysis.

Queries the recomp_tracking view and generates a summary of weight,
body fat, and lean mass trends. Used in monthly sections of the
weekly review.

Usage:
    python recomp_analysis.py              # 90-day analysis
    python recomp_analysis.py --days 30    # 30-day window
    python recomp_analysis.py --dry-run    # print only

Called by:
    - Weekly review cron (monthly cadence)
    - Importable: from recomp_analysis import compute_recomp_trajectory
"""

import argparse
import logging
import os
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

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
log = logging.getLogger("recomp")


@dataclass
class RecompSummary:
    """Summary of body recomposition trajectory."""
    period_days: int
    start_weight: float | None
    end_weight: float | None
    weight_change: float | None
    rate_per_week: float | None
    start_bf: float | None
    end_bf: float | None
    bf_change: float | None
    start_lean: float | None
    end_lean: float | None
    lean_change: float | None
    phase: str  # 'recomp', 'cutting', 'gaining', 'maintaining', 'insufficient_data'
    data_points: int


def supabase_get(table: str, params: dict | None = None) -> list:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    resp = requests.get(url, headers=SUPABASE_HEADERS, params=params or {}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def compute_recomp_trajectory(days: int = 90) -> RecompSummary:
    """Compute body recomposition trajectory from the recomp_tracking view."""
    cutoff = (date.today() - timedelta(days=days)).isoformat()

    try:
        rows = supabase_get("recomp_tracking", {
            "date": f"gte.{cutoff}",
            "smoothed_weight_kg": "not.is.null",
            "select": "date,smoothed_weight_kg,body_fat_pct,estimated_lean_mass_kg,weight_rate_per_week,phase_classification",
            "order": "date.asc",
        })
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            log.warning("recomp_tracking view not found — migration not deployed?")
            return RecompSummary(
                period_days=days, start_weight=None, end_weight=None,
                weight_change=None, rate_per_week=None, start_bf=None,
                end_bf=None, bf_change=None, start_lean=None, end_lean=None,
                lean_change=None, phase="insufficient_data", data_points=0,
            )
        raise

    if len(rows) < 7:
        return RecompSummary(
            period_days=days, start_weight=None, end_weight=None,
            weight_change=None, rate_per_week=None, start_bf=None,
            end_bf=None, bf_change=None, start_lean=None, end_lean=None,
            lean_change=None, phase="insufficient_data", data_points=len(rows),
        )

    first = rows[0]
    last = rows[-1]

    start_w = first.get("smoothed_weight_kg")
    end_w = last.get("smoothed_weight_kg")
    start_bf = first.get("body_fat_pct")
    end_bf = last.get("body_fat_pct")
    start_lean = first.get("estimated_lean_mass_kg")
    end_lean = last.get("estimated_lean_mass_kg")

    # Determine dominant phase from last 7 days
    recent = rows[-7:]
    phases = [r.get("phase_classification") for r in recent if r.get("phase_classification")]
    if phases:
        from collections import Counter
        phase = Counter(phases).most_common(1)[0][0]
    else:
        phase = "insufficient_data"

    return RecompSummary(
        period_days=days,
        start_weight=start_w,
        end_weight=end_w,
        weight_change=round(end_w - start_w, 2) if start_w and end_w else None,
        rate_per_week=last.get("weight_rate_per_week"),
        start_bf=start_bf,
        end_bf=end_bf,
        bf_change=round(end_bf - start_bf, 1) if start_bf and end_bf else None,
        start_lean=start_lean,
        end_lean=end_lean,
        lean_change=round(end_lean - start_lean, 2) if start_lean and end_lean else None,
        phase=phase,
        data_points=len(rows),
    )


def generate_recomp_summary(s: RecompSummary) -> str:
    """Natural language summary for weekly review."""
    if s.phase == "insufficient_data":
        return f"**Body Composition:** Insufficient data ({s.data_points} points in {s.period_days} days)."

    lines = [f"**Body Composition** ({s.period_days}d window, {s.data_points} data points):"]

    if s.start_weight and s.end_weight and s.weight_change is not None:
        direction = "up" if s.weight_change > 0 else "down" if s.weight_change < 0 else "flat"
        lines.append(f"  Weight: {s.start_weight}kg → {s.end_weight}kg ({s.weight_change:+.1f}kg, {direction})")
        if s.rate_per_week is not None:
            lines.append(f"  Rate: {s.rate_per_week:+.2f} kg/week")

    if s.start_bf and s.end_bf and s.bf_change is not None:
        lines.append(f"  Body fat: {s.start_bf}% → {s.end_bf}% ({s.bf_change:+.1f}%)")

    if s.start_lean and s.end_lean and s.lean_change is not None:
        lines.append(f"  Est. lean mass: {s.start_lean}kg → {s.end_lean}kg ({s.lean_change:+.1f}kg)")

    phase_labels = {
        "recomp": "Recomposition (weight up, BF% down)",
        "cutting": "Cutting (weight down)",
        "gaining": "Gaining (weight up)",
        "maintaining": "Maintaining (stable)",
    }
    lines.append(f"  Phase: {phase_labels.get(s.phase, s.phase)}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Body recomposition analysis")
    parser.add_argument("--days", type=int, default=90, help="Analysis window in days")
    parser.add_argument("--dry-run", action="store_true", help="Print only")
    args = parser.parse_args()

    log.info("Computing recomp trajectory (%d days)...", args.days)
    summary = compute_recomp_trajectory(args.days)
    print("\n" + generate_recomp_summary(summary))


if __name__ == "__main__":
    main()

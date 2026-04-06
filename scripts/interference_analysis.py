#!/usr/bin/env python3
"""Mountain-gym interference analysis + cumulative load tracking.

Analyzes how mountain activity affects subsequent gym performance,
detects training load spikes, and writes learned patterns to the
athlete_response_patterns table for the coaching agent to use.

Usage:
    python interference_analysis.py                     # full analysis, update patterns
    python interference_analysis.py --dry-run            # print findings, don't write
    python interference_analysis.py --lookback 60        # analyze last 60 days (default: 90)
    python interference_analysis.py --load-only          # only check load spikes (fast)

Called by:
    - Weekly review cron (Sunday 20:00)
    - Importable as library: from interference_analysis import analyze_interference
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean, median, stdev

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
# Use service key for writes, fall back to anon key for reads
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
log = logging.getLogger("interference")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class InterferencePattern:
    """A learned pattern about mountain-gym interference."""
    pattern_key: str
    observation: str
    confidence: str  # 'low', 'medium', 'high'
    sample_size: int
    effect_size: float | None
    data_summary: dict


@dataclass
class LoadSpike:
    """A detected training load spike."""
    week_start: str
    metric: str  # 'elevation', 'gym_volume', 'srpe_load', 'duration'
    current_value: float
    avg_4w: float
    spike_pct: float  # % above average


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------

def supabase_get(table: str, params: dict | None = None) -> list:
    """GET from Supabase REST API."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    resp = requests.get(url, headers=SUPABASE_HEADERS, params=params or {}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def supabase_upsert(table: str, data: dict, on_conflict: str = "") -> bool:
    """Upsert a row into Supabase. Returns True on success."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {**SUPABASE_HEADERS, "Prefer": "resolution=merge-duplicates,return=minimal"}
    if on_conflict:
        headers["Prefer"] = f"resolution=merge-duplicates,return=minimal"
    resp = requests.post(url, headers=headers, json=data, timeout=15)
    if resp.status_code in (200, 201, 204):
        return True
    log.error("Upsert failed: %s %s", resp.status_code, resp.text)
    return False


# ---------------------------------------------------------------------------
# Mountain-gym interference analysis
# ---------------------------------------------------------------------------

def fetch_interference_data(lookback_days: int = 90) -> list[dict]:
    """Fetch mountain_gym_interference view data."""
    cutoff = (date.today() - timedelta(days=lookback_days)).isoformat()
    return supabase_get("mountain_gym_interference", {
        "gym_date": f"gte.{cutoff}",
        "select": "*",
        "order": "gym_date.desc",
    })


def _confidence_level(n: int) -> str:
    """Map sample size to confidence level."""
    if n >= 15:
        return "high"
    elif n >= 5:
        return "medium"
    return "low"


def _cohens_d(group_a: list[float], group_b: list[float]) -> float | None:
    """Compute Cohen's d between two groups. Returns None if insufficient data."""
    if len(group_a) < 2 or len(group_b) < 2:
        return None
    mean_a, mean_b = mean(group_a), mean(group_b)
    sd_a, sd_b = stdev(group_a), stdev(group_b)
    pooled_sd = ((sd_a ** 2 + sd_b ** 2) / 2) ** 0.5
    if pooled_sd == 0:
        return None
    return round((mean_a - mean_b) / pooled_sd, 2)


def analyze_interference(lookback_days: int = 90) -> list[InterferencePattern]:
    """Analyze mountain-gym interference patterns from historical data.

    Compares gym session performance when preceded by mountain activity
    vs no mountain activity in the 72h window. Breaks down by mountain
    load category (none, light, moderate, heavy).

    Returns a list of InterferencePattern objects to be written to the DB.
    """
    rows = fetch_interference_data(lookback_days)
    if not rows:
        log.info("No interference data found for the last %d days.", lookback_days)
        return []

    patterns: list[InterferencePattern] = []

    # --- Pattern 1: Overall mountain impact on gym volume ---
    # Split sessions by mountain_load_category
    no_mountain = [r for r in rows if r["mountain_load_category"] == "none"]
    with_mountain = [r for r in rows if r["mountain_load_category"] != "none"]

    if no_mountain and with_mountain:
        no_vols = [r["total_volume_kg"] for r in no_mountain if r.get("total_volume_kg")]
        mt_vols = [r["total_volume_kg"] for r in with_mountain if r.get("total_volume_kg")]

        if no_vols and mt_vols:
            avg_no = mean(no_vols)
            avg_mt = mean(mt_vols)
            delta_pct = round((avg_mt - avg_no) / avg_no * 100, 1) if avg_no > 0 else 0
            d = _cohens_d(mt_vols, no_vols)
            n = len(mt_vols)

            patterns.append(InterferencePattern(
                pattern_key="mountain_any_volume_impact",
                observation=(
                    f"Gym volume {'drops' if delta_pct < 0 else 'increases'} "
                    f"{abs(delta_pct)}% after mountain days vs rest days "
                    f"(avg {round(avg_mt)}kg vs {round(avg_no)}kg)."
                ),
                confidence=_confidence_level(n),
                sample_size=n,
                effect_size=d,
                data_summary={
                    "avg_volume_after_mountain": round(avg_mt, 1),
                    "avg_volume_no_mountain": round(avg_no, 1),
                    "delta_pct": delta_pct,
                    "sessions_with_mountain": len(mt_vols),
                    "sessions_without": len(no_vols),
                },
            ))

    # --- Pattern 2: Heavy mountain day impact specifically ---
    heavy = [r for r in rows if r["mountain_load_category"] == "heavy"]
    if heavy and no_mountain:
        heavy_vols = [r["total_volume_kg"] for r in heavy if r.get("total_volume_kg")]
        no_vols = [r["total_volume_kg"] for r in no_mountain if r.get("total_volume_kg")]

        if heavy_vols and no_vols:
            avg_heavy = mean(heavy_vols)
            avg_no = mean(no_vols)
            delta_pct = round((avg_heavy - avg_no) / avg_no * 100, 1) if avg_no > 0 else 0
            d = _cohens_d(heavy_vols, no_vols)
            n = len(heavy_vols)

            patterns.append(InterferencePattern(
                pattern_key="heavy_mountain_volume_impact",
                observation=(
                    f"After heavy mountain days (≥2000m or ≥5h), gym volume "
                    f"{'drops' if delta_pct < 0 else 'increases'} {abs(delta_pct)}% "
                    f"(avg {round(avg_heavy)}kg vs {round(avg_no)}kg baseline)."
                ),
                confidence=_confidence_level(n),
                sample_size=n,
                effect_size=d,
                data_summary={
                    "avg_volume_heavy": round(avg_heavy, 1),
                    "avg_volume_baseline": round(avg_no, 1),
                    "delta_pct": delta_pct,
                    "heavy_sessions": n,
                },
            ))

    # --- Pattern 3: Elevation threshold impact ---
    # Compare sessions after >1500m elevation vs <500m
    high_elev = [r for r in rows if (r.get("mountain_elevation_72h") or 0) >= 1500]
    low_elev = [r for r in rows if (r.get("mountain_elevation_72h") or 0) < 500]

    if high_elev and low_elev:
        high_vols = [r["total_volume_kg"] for r in high_elev if r.get("total_volume_kg")]
        low_vols = [r["total_volume_kg"] for r in low_elev if r.get("total_volume_kg")]

        if high_vols and low_vols:
            avg_high = mean(high_vols)
            avg_low = mean(low_vols)
            delta_pct = round((avg_high - avg_low) / avg_low * 100, 1) if avg_low > 0 else 0
            d = _cohens_d(high_vols, low_vols)
            n = len(high_vols)

            patterns.append(InterferencePattern(
                pattern_key="elevation_gt_1500m",
                observation=(
                    f"After >1500m elevation in 72h, gym volume "
                    f"{'drops' if delta_pct < 0 else 'stays stable at'} {abs(delta_pct)}% "
                    f"vs low-elevation weeks."
                ),
                confidence=_confidence_level(n),
                sample_size=n,
                effect_size=d,
                data_summary={
                    "avg_volume_high_elev": round(avg_high, 1),
                    "avg_volume_low_elev": round(avg_low, 1),
                    "delta_pct": delta_pct,
                    "high_elev_sessions": n,
                    "low_elev_sessions": len(low_vols),
                },
            ))

    # --- Pattern 4: sRPE impact (how hard sessions feel after mountain days) ---
    if no_mountain and with_mountain:
        no_rpes = [r["srpe"] for r in no_mountain if r.get("srpe") is not None]
        mt_rpes = [r["srpe"] for r in with_mountain if r.get("srpe") is not None]

        if no_rpes and mt_rpes:
            avg_no_rpe = mean(no_rpes)
            avg_mt_rpe = mean(mt_rpes)
            delta = round(avg_mt_rpe - avg_no_rpe, 1)
            d = _cohens_d(mt_rpes, no_rpes)
            n = len(mt_rpes)

            patterns.append(InterferencePattern(
                pattern_key="mountain_rpe_impact",
                observation=(
                    f"Sessions feel {abs(delta)} points {'harder' if delta > 0 else 'easier'} "
                    f"(sRPE) after mountain days (avg {round(avg_mt_rpe, 1)} vs "
                    f"{round(avg_no_rpe, 1)})."
                ),
                confidence=_confidence_level(n),
                sample_size=n,
                effect_size=d,
                data_summary={
                    "avg_srpe_after_mountain": round(avg_mt_rpe, 1),
                    "avg_srpe_no_mountain": round(avg_no_rpe, 1),
                    "delta": delta,
                },
            ))

    # --- Pattern 5: Resort skiing impact (eccentric quad load) ---
    resort = [r for r in rows if (r.get("resort_days_72h") or 0) > 0]
    no_resort = [r for r in rows if (r.get("resort_days_72h") or 0) == 0 and r["mountain_load_category"] == "none"]

    if resort and no_resort:
        resort_vols = [r["total_volume_kg"] for r in resort if r.get("total_volume_kg")]
        base_vols = [r["total_volume_kg"] for r in no_resort if r.get("total_volume_kg")]

        if resort_vols and base_vols:
            avg_resort = mean(resort_vols)
            avg_base = mean(base_vols)
            delta_pct = round((avg_resort - avg_base) / avg_base * 100, 1) if avg_base > 0 else 0
            n = len(resort_vols)

            patterns.append(InterferencePattern(
                pattern_key="resort_skiing_impact",
                observation=(
                    f"After resort skiing, gym volume "
                    f"{'drops' if delta_pct < 0 else 'holds at'} {abs(delta_pct)}% "
                    f"(eccentric quad load from turns affects lower body work)."
                ),
                confidence=_confidence_level(n),
                sample_size=n,
                effect_size=_cohens_d(resort_vols, base_vols),
                data_summary={
                    "avg_volume_after_resort": round(avg_resort, 1),
                    "avg_volume_baseline": round(avg_base, 1),
                    "delta_pct": delta_pct,
                    "resort_sessions": n,
                },
            ))

    log.info("Generated %d interference patterns from %d gym sessions.", len(patterns), len(rows))
    return patterns


# ---------------------------------------------------------------------------
# Load spike detection
# ---------------------------------------------------------------------------

def detect_load_spikes() -> list[LoadSpike]:
    """Check the current week for training load spikes (>15% above 4-week avg).

    Queries the weekly_training_load view for the current week and
    returns any detected spikes.
    """
    current_week_start = date.today() - timedelta(days=date.today().weekday())
    rows = supabase_get("weekly_training_load", {
        "week_start": f"eq.{current_week_start.isoformat()}",
        "select": "*",
        "limit": "1",
    })

    if not rows:
        log.info("No load data for current week yet.")
        return []

    row = rows[0]
    spikes: list[LoadSpike] = []

    spike_checks = [
        ("elevation", "total_elevation_m", "avg_elevation_4w", "elevation_spike"),
        ("gym_volume", "total_gym_volume_kg", "avg_gym_volume_4w", "gym_volume_spike"),
        ("srpe_load", "total_srpe_load", "avg_srpe_load_4w", "srpe_load_spike"),
        ("duration", "total_hours", "avg_hours_4w", "duration_spike"),
    ]

    for metric, current_col, avg_col, flag_col in spike_checks:
        if row.get(flag_col):
            current_val = row.get(current_col, 0) or 0
            avg_val = row.get(avg_col, 0) or 0
            pct = round((current_val - avg_val) / avg_val * 100, 1) if avg_val > 0 else 0
            spikes.append(LoadSpike(
                week_start=row["week_start"],
                metric=metric,
                current_value=current_val,
                avg_4w=round(avg_val, 1),
                spike_pct=pct,
            ))

    if spikes:
        log.warning("Detected %d load spike(s) this week: %s",
                     len(spikes), ", ".join(s.metric for s in spikes))
    else:
        log.info("No load spikes this week.")

    return spikes


# ---------------------------------------------------------------------------
# Pattern persistence
# ---------------------------------------------------------------------------

def update_response_patterns(patterns: list[InterferencePattern], dry_run: bool = False) -> int:
    """Write interference patterns to athlete_response_patterns table.

    Uses upsert on (pattern_type, pattern_key) to update existing patterns
    with new data as more samples accumulate.

    Returns number of patterns written.
    """
    written = 0
    for p in patterns:
        row = {
            "pattern_type": "mountain_interference",
            "pattern_key": p.pattern_key,
            "observation": p.observation,
            "confidence": p.confidence,
            "sample_size": p.sample_size,
            "effect_size": p.effect_size,
            "data_summary": p.data_summary,
            "last_updated": date.today().isoformat(),
        }

        if dry_run:
            log.info("DRY RUN — would write pattern: %s (%s, n=%d)",
                     p.pattern_key, p.confidence, p.sample_size)
            written += 1
        else:
            if supabase_upsert("athlete_response_patterns", row):
                log.info("Updated pattern: %s (%s, n=%d)",
                         p.pattern_key, p.confidence, p.sample_size)
                written += 1

    return written


# ---------------------------------------------------------------------------
# Summary generation (for weekly review)
# ---------------------------------------------------------------------------

def generate_interference_summary(
    patterns: list[InterferencePattern],
    spikes: list[LoadSpike],
) -> str:
    """Generate a natural language summary for the coaching agent's weekly review.

    Returns a Slack-formatted string.
    """
    lines: list[str] = []

    # Interference patterns
    high_conf = [p for p in patterns if p.confidence in ("medium", "high")]
    if high_conf:
        lines.append("*Mountain-Gym Interference Patterns:*")
        for p in high_conf:
            conf_emoji = "🟢" if p.confidence == "high" else "🟡"
            lines.append(f"  {conf_emoji} {p.observation} (n={p.sample_size})")
    elif patterns:
        lines.append("*Mountain-Gym Interference:* Still building patterns (all low confidence).")
    else:
        lines.append("*Mountain-Gym Interference:* No data yet.")

    # Load spikes
    if spikes:
        lines.append("")
        lines.append("*⚠️ Load Spikes This Week:*")
        for s in spikes:
            lines.append(
                f"  {s.metric}: {s.current_value} vs {s.avg_4w} avg (+{s.spike_pct}%)"
            )
    else:
        lines.append("*Training Load:* Within normal range.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience for coaching agent queries
# ---------------------------------------------------------------------------

def get_mountain_context_for_today() -> dict | None:
    """Quick check: mountain load in last 72h + relevant learned patterns.

    Used by the coaching agent for daily decisions.
    Returns a dict with mountain load info and any applicable patterns,
    or None if no mountain activity.
    """
    today = date.today()
    cutoff = (today - timedelta(days=3)).isoformat()

    # Recent mountain activity
    activities = supabase_get("activities", {
        "date": f"gte.{cutoff}",
        "activity_type": "in.(backcountry_skiing,backcountry_snowboarding,hiking,mountaineering,splitboarding,resort_skiing,resort_snowboarding)",
        "select": "date,activity_type,elevation_gain,duration_seconds,calories",
        "order": "date.desc",
    })

    if not activities:
        return None

    total_elevation = sum(
        a.get("elevation_gain", 0) or 0
        for a in activities
        if a.get("activity_type") not in ("resort_skiing", "resort_snowboarding")
    )
    total_hours = round(sum(a.get("duration_seconds", 0) or 0 for a in activities) / 3600, 1)
    mountain_days = len(set(a["date"] for a in activities))
    has_resort = any(a.get("activity_type") in ("resort_skiing", "resort_snowboarding") for a in activities)

    # Categorize
    if total_elevation >= 2000 or total_hours >= 5:
        load_category = "heavy"
    elif total_elevation >= 1000 or total_hours >= 3:
        load_category = "moderate"
    else:
        load_category = "light"

    # Fetch relevant learned patterns (table may not exist yet)
    try:
        patterns = supabase_get("athlete_response_patterns", {
            "pattern_type": "eq.mountain_interference",
            "confidence": "in.(medium,high)",
            "select": "pattern_key,observation,confidence,sample_size,effect_size",
        })
    except Exception:
        patterns = []

    return {
        "mountain_days_72h": mountain_days,
        "total_elevation_72h": total_elevation,
        "total_hours_72h": total_hours,
        "load_category": load_category,
        "has_resort": has_resort,
        "activities": [
            {
                "date": a["date"],
                "type": a["activity_type"],
                "elevation": a.get("elevation_gain", 0),
                "hours": round((a.get("duration_seconds", 0) or 0) / 3600, 1),
            }
            for a in activities
        ],
        "learned_patterns": patterns,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Mountain-gym interference analysis")
    parser.add_argument("--dry-run", action="store_true", help="Print findings, don't write to DB")
    parser.add_argument("--lookback", type=int, default=90, help="Lookback period in days (default: 90)")
    parser.add_argument("--load-only", action="store_true", help="Only check load spikes (fast)")
    args = parser.parse_args()

    # Load spikes
    spikes = detect_load_spikes()

    if args.load_only:
        if spikes:
            for s in spikes:
                print(f"⚠️  {s.metric} spike: {s.current_value} vs {s.avg_4w} avg (+{s.spike_pct}%)")
        else:
            print("No load spikes this week.")
        return

    # Full interference analysis
    patterns = analyze_interference(lookback_days=args.lookback)

    if not patterns:
        log.info("No interference patterns found. Need more gym sessions with preceding mountain days.")
        return

    # Print summary
    summary = generate_interference_summary(patterns, spikes)
    print("\n" + summary + "\n")

    # Write patterns
    if args.dry_run:
        log.info("DRY RUN — not writing to database.")
        for p in patterns:
            print(f"  [{p.confidence}] {p.pattern_key}: {p.observation}")
    else:
        written = update_response_patterns(patterns)
        log.info("Wrote %d patterns to athlete_response_patterns.", written)

    # Print mountain context for today
    ctx = get_mountain_context_for_today()
    if ctx:
        print(f"\nToday's mountain context: {ctx['load_category']} load "
              f"({ctx['total_elevation_72h']}m, {ctx['total_hours_72h']}h in last 72h)")
        if ctx["learned_patterns"]:
            for p in ctx["learned_patterns"]:
                print(f"  → {p['observation']}")


if __name__ == "__main__":
    main()

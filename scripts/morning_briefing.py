#!/usr/bin/env python3
"""Morning health briefing → Slack.

Queries Supabase for today's health data and posts a formatted briefing to Slack.

Usage:
    python morning_briefing.py                    # post today's briefing
    python morning_briefing.py --dry-run           # print without posting
    python morning_briefing.py --date 2026-03-30   # briefing for specific date
"""

import argparse
import json
import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL_DAILY", "")

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
log = logging.getLogger("morning_briefing")

# ---------------------------------------------------------------------------
# Supabase queries
# ---------------------------------------------------------------------------


def supabase_get(table: str, params: dict) -> list:
    """GET from Supabase REST API. Returns list of rows."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    resp = requests.get(url, headers=SUPABASE_HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_data_freshness(target_date: date) -> float | None:
    """Return the age in hours of the most recent daily_metrics sync.

    Checks synced_at for target_date (or the most recent row before it).
    Returns None if no data exists.
    """
    rows = supabase_get("daily_metrics", {
        "select": "synced_at",
        "date": f"lte.{target_date.isoformat()}",
        "order": "date.desc",
        "limit": "1",
    })
    if not rows or not rows[0].get("synced_at"):
        return None
    from datetime import datetime, timezone
    synced = rows[0]["synced_at"]
    synced_dt = datetime.fromisoformat(synced.replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - synced_dt).total_seconds() / 3600
    return round(age, 1)


def fetch_daily_summary(target_date: date) -> dict | None:
    """Fetch daily_summary view for a given date."""
    rows = supabase_get("daily_summary", {
        "date": f"eq.{target_date.isoformat()}",
        "select": "*",
    })
    return rows[0] if rows else None


def fetch_daily_summary_range(start: date, end: date) -> list:
    """Fetch daily_summary for a date range (inclusive)."""
    url = f"{SUPABASE_URL}/rest/v1/daily_summary"
    params = {
        "select": "*",
        "order": "date.desc",
        "and": f"(date.gte.{start.isoformat()},date.lte.{end.isoformat()})",
    }
    resp = requests.get(url, headers=SUPABASE_HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_activities(target_date: date) -> list:
    """Fetch activities for a given date."""
    return supabase_get("activities", {
        "date": f"eq.{target_date.isoformat()}",
        "select": "activity_type,activity_name,duration_seconds,calories,elevation_gain,avg_hr,distance_meters",
        "order": "start_time.asc",
    })


def fetch_resting_hr_7d(end_date: date) -> float | None:
    """Calculate 7-day average resting HR ending on end_date."""
    start = end_date - timedelta(days=6)
    rows = fetch_daily_summary_range(start, end_date)
    hrs = [r["resting_hr"] for r in rows if r.get("resting_hr")]
    return round(sum(hrs) / len(hrs), 1) if hrs else None


def fetch_wellness(target_date: date) -> dict | None:
    """Fetch today's subjective wellness check-in."""
    rows = supabase_get("subjective_wellness", {
        "date": f"eq.{target_date.isoformat()}",
        "select": "sleep_quality,energy,muscle_soreness,motivation,stress,composite_score",
    })
    return rows[0] if rows else None


def fetch_progression_alerts() -> dict | None:
    """Fetch progression velocity data and return stalled/behind/top exercises."""
    try:
        rows = supabase_get("progression_velocity", {
            "select": "exercise_name,planned_weight_kg,progression_status,kg_per_week,sessions_at_current_weight",
            "order": "progression_status.asc,kg_per_week.desc",
        })
        if not rows:
            return None

        stalled = [r for r in rows if r.get("progression_status") == "stalled"]
        behind = [r for r in rows if r.get("progression_status") == "behind"]
        on_track = [r for r in rows
                    if r.get("progression_status") == "on_track" and r.get("kg_per_week")]
        top_gainer = max(on_track, key=lambda r: r["kg_per_week"]) if on_track else None

        if not stalled and not behind and not top_gainer:
            return None

        return {"stalled": stalled, "behind": behind, "top_gainer": top_gainer}
    except Exception as e:
        log.warning("Failed to fetch progression alerts: %s", e)
        return None


def fetch_stall_warnings() -> list:
    """Fetch exercises at risk of stalling (moderate+ risk)."""
    try:
        rows = supabase_get("stall_early_warning", {
            "select": "exercise_name,planned_weight_kg,sessions_at_current_weight,stall_risk,avg_recent_srpe,sleep_7d_avg",
            "stall_risk": "neq.low",
        })
        return rows
    except Exception as e:
        log.warning("Failed to fetch stall warnings: %s", e)
        return []


def fetch_mountain_patterns() -> list:
    """Fetch learned mountain interference patterns (medium/high confidence)."""
    try:
        rows = supabase_get("athlete_response_patterns", {
            "select": "observation,confidence,pattern_key",
            "pattern_type": "eq.mountain_interference",
            "or": "(confidence.eq.medium,confidence.eq.high)",
        })
        return rows
    except Exception as e:
        log.warning("Failed to fetch mountain patterns: %s", e)
        return []


def fetch_recent_prs(since_date: date) -> list:
    """Fetch exercise PRs set since the given date."""
    try:
        rows = supabase_get("exercise_prs", {
            "select": "exercise_id,pr_type,value,date",
            "date": f"gte.{since_date.isoformat()}",
            "pr_type": "eq.e1rm",
            "order": "date.desc",
        })
        if not rows:
            return []
        # Look up exercise names
        exercise_ids = list({r["exercise_id"] for r in rows})
        exercises = {}
        for eid in exercise_ids:
            ex = supabase_get("exercises", {
                "select": "id,name",
                "id": f"eq.{eid}",
                "limit": "1",
            })
            if ex:
                exercises[eid] = ex[0]["name"]
        for r in rows:
            r["exercise_name"] = exercises.get(r["exercise_id"], f"Exercise #{r['exercise_id']}")
        return rows
    except Exception as e:
        log.warning("Failed to fetch PRs: %s", e)
        return []


def is_gym_day(target_date: date) -> bool:
    """Check if there's a planned workout today."""
    try:
        rows = supabase_get("planned_workouts", {
            "select": "id",
            "scheduled_date": f"eq.{target_date.isoformat()}",
            "limit": "1",
        })
        return bool(rows)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _hrs_mins(seconds: int | None) -> str:
    if not seconds:
        return "N/A"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"


def _mins(seconds: int | None) -> str:
    if not seconds:
        return "N/A"
    return f"{seconds // 60}m"


def _hrv_emoji(hrv_avg: float | None, hrv_status: str | None) -> str:
    """Color emoji based on HRV status from Garmin."""
    if not hrv_status:
        if hrv_avg and hrv_avg >= 60:
            return ":large_green_circle:"
        elif hrv_avg and hrv_avg >= 40:
            return ":large_yellow_circle:"
        return ":red_circle:"
    status = hrv_status.upper()
    if "BALANCED" in status:
        return ":large_green_circle:"
    elif "LOW" in status:
        return ":red_circle:"
    elif "UNBALANCED" in status:
        return ":large_yellow_circle:"
    return ":white_circle:"


def _readiness_emoji(score: float | None) -> str:
    if score is None:
        return ":white_circle:"
    if score > 60:
        return ":large_green_circle:"
    elif score >= 40:
        return ":large_yellow_circle:"
    return ":red_circle:"


def _readiness_label(score: float | None) -> str:
    if score is None:
        return "N/A"
    return f"{int(score)}"


def _recommendation(readiness: float | None, hrv_avg: float | None,
                    sleep_score: int | None, wellness_composite: float | None,
                    data_is_stale: bool = False) -> str:
    """One-line training recommendation based on recovery signals."""
    # Wellness self-report is the highest-trust signal (never gated on data freshness)
    if wellness_composite is not None and wellness_composite < 2.5:
        return ":zzz: Rest day recommended. Self-reported wellness is low — listen to your body."

    scores = []
    # When data is stale, exclude device-only metrics (readiness, BB) from scoring
    # but keep HRV/sleep which may still be directionally useful
    if readiness is not None and not data_is_stale:
        scores.append(("readiness", readiness))
    if hrv_avg is not None:
        scores.append(("hrv", hrv_avg))
    if sleep_score is not None:
        scores.append(("sleep", sleep_score))
    if wellness_composite is not None:
        scores.append(("wellness", wellness_composite))

    if not scores:
        if data_is_stale:
            return ":white_circle: Data is stale — check how you feel before deciding."
        return "Insufficient data for recommendation."

    # Simple scoring: count how many signals are in green/yellow/red
    green = 0
    red = 0
    for name, val in scores:
        if name == "readiness":
            if val > 60:
                green += 1
            elif val < 40:
                red += 1
        elif name == "hrv":
            if val >= 55:
                green += 1
            elif val < 40:
                red += 1
        elif name == "sleep":
            if val >= 75:
                green += 1
            elif val < 50:
                red += 1
        elif name == "wellness":
            if val >= 4.0:
                green += 1
            elif val < 2.5:
                red += 1

    if red >= 2:
        return ":zzz: Rest day or very light movement. Multiple recovery signals are low."
    elif red >= 1:
        return ":walking: Moderate session — keep intensity in check. One recovery signal flagged."
    elif green >= 2:
        return ":fire: Green light for a hard session. Recovery looks solid."
    else:
        return ":person_running: Moderate training is fine. Recovery is acceptable."


def _format_activity(act: dict) -> str:
    """Format a single activity line."""
    name = act.get("activity_name") or act.get("activity_type", "Activity")
    parts = [f"*{name}*"]

    dur = act.get("duration_seconds")
    if dur:
        parts.append(_mins(dur))

    dist = act.get("distance_meters")
    if dist and dist > 0:
        km = dist / 1000
        parts.append(f"{km:.1f} km")

    elev = act.get("elevation_gain")
    if elev and elev > 0:
        parts.append(f"+{int(elev)}m elev")

    cal = act.get("calories")
    if cal:
        parts.append(f"{cal} kcal")

    return " | ".join(parts)


# ---------------------------------------------------------------------------
# Build Slack message
# ---------------------------------------------------------------------------


def build_message(target_date: date) -> dict:
    """Build Slack Block Kit message payload."""
    yesterday = target_date - timedelta(days=1)

    # Fetch data
    today_summary = fetch_daily_summary(target_date)
    yesterday_summary = fetch_daily_summary(yesterday)
    yesterday_activities = fetch_activities(yesterday)
    resting_hr_7d = fetch_resting_hr_7d(target_date)
    wellness = fetch_wellness(target_date)
    data_age_hours = fetch_data_freshness(target_date)

    # Use today's summary for current recovery state; fall back to yesterday
    summary = today_summary or yesterday_summary
    if not summary:
        return _error_message(target_date, "No health data found.")

    data_is_stale = data_age_hours is not None and data_age_hours > 12

    # Extract fields
    hrv_avg = summary.get("hrv_avg")
    hrv_weekly = summary.get("hrv_weekly_avg")
    hrv_status = summary.get("hrv_status")
    sleep_score = summary.get("sleep_score")
    sleep_seconds = summary.get("total_sleep_seconds")
    deep_seconds = summary.get("deep_sleep_seconds")
    rem_seconds = summary.get("rem_sleep_seconds")
    readiness = summary.get("training_readiness_score")
    bb_high = summary.get("body_battery_highest")
    bb_low = summary.get("body_battery_lowest")
    resting_hr = summary.get("resting_hr")
    steps = summary.get("total_steps")

    # Build blocks
    blocks = []

    # Header
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": f"Morning Briefing — {target_date.strftime('%A, %b %d')}"}
    })

    # Stale-data warning (if sync is >12h old)
    if data_is_stale:
        age_str = f"{data_age_hours:.0f}h" if data_age_hours < 48 else f"{data_age_hours / 24:.1f}d"
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text":
                f":warning: *Data may be stale* — last sync was {age_str} ago. "
                "Hard overrides (Training Readiness, Body Battery) are suppressed until fresh data arrives."}
        })

    # Recovery Triad
    triad_lines = []
    triad_lines.append(
        f"{_hrv_emoji(hrv_avg, hrv_status)} *HRV:* {int(hrv_avg) if hrv_avg else 'N/A'} ms"
        + (f"  (7d avg: {int(hrv_weekly)})" if hrv_weekly else "")
    )
    triad_lines.append(
        f":crescent_moon: *Sleep:* {_hrs_mins(sleep_seconds)}"
        + (f"  |  Score: {sleep_score}/100" if sleep_score else "")
        + (f"  |  Deep: {_mins(deep_seconds)}" if deep_seconds else "")
        + (f"  |  REM: {_mins(rem_seconds)}" if rem_seconds else "")
    )
    triad_lines.append(
        f"{_readiness_emoji(readiness)} *Training Readiness:* {_readiness_label(readiness)}"
    )

    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*Recovery Triad*\n" + "\n".join(triad_lines)}
    })

    blocks.append({"type": "divider"})

    # Body Battery + Resting HR
    vitals_lines = []
    if bb_high is not None or bb_low is not None:
        vitals_lines.append(
            f":battery: *Body Battery:* {bb_high or '?'} high / {bb_low or '?'} low"
        )
    hr_text = f":heartbeat: *Resting HR:* {resting_hr or 'N/A'} bpm"
    if resting_hr and resting_hr_7d:
        diff = resting_hr - resting_hr_7d
        arrow = ":arrow_up:" if diff > 0 else ":arrow_down:" if diff < 0 else ":left_right_arrow:"
        hr_text += f"  ({arrow} {abs(diff):.0f} vs 7d avg {resting_hr_7d:.0f})"
    vitals_lines.append(hr_text)

    if steps:
        vitals_lines.append(f":footprints: *Steps:* {steps:,}")

    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": "\n".join(vitals_lines)}
    })

    # Yesterday's Activities
    if yesterday_activities:
        blocks.append({"type": "divider"})
        act_lines = [_format_activity(a) for a in yesterday_activities]
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Yesterday's Activities*\n" + "\n".join(act_lines),
            }
        })

    # Personal Records (set yesterday)
    recent_prs = fetch_recent_prs(yesterday)
    if recent_prs:
        pr_lines = []
        for pr in recent_prs:
            pr_lines.append(
                f":trophy: *{pr['exercise_name']}* — new e1RM: {pr['value']}kg"
            )
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*New PRs*\n" + "\n".join(pr_lines)}
        })

    blocks.append({"type": "divider"})

    # Wellness check-in (if submitted today)
    wellness_composite = None
    if wellness:
        wellness_composite = wellness.get("composite_score")
        w_labels = {
            "sleep_quality": "Sleep", "energy": "Energy",
            "muscle_soreness": "Soreness", "motivation": "Motivation",
            "stress": "Stress"
        }
        w_parts = [f"{lbl}: {wellness.get(k, '?')}/5"
                   for k, lbl in w_labels.items() if wellness.get(k) is not None]
        if w_parts:
            w_emoji = ":large_green_circle:" if wellness_composite and wellness_composite >= 4 else \
                      ":red_circle:" if wellness_composite and wellness_composite < 2.5 else \
                      ":large_yellow_circle:"
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text":
                    f"{w_emoji} *Wellness Check-in:* {wellness_composite:.1f}/5\n"
                    + " | ".join(w_parts)}
            })

    # RPE follow-up: check if yesterday has a training session with no sRPE
    yesterday_sessions = supabase_get("training_sessions", {
        "date": f"eq.{yesterday.isoformat()}",
        "select": "id,name,srpe",
        "limit": "1",
    })
    if yesterday_sessions and yesterday_sessions[0].get("srpe") is None:
        session_name = yesterday_sessions[0].get("name") or "yesterday's session"
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text":
                f":memo: *RPE missing* — {session_name} has no RPE logged. "
                "Open the app or reply with a number (1-10)."}
        })

    blocks.append({"type": "divider"})

    # Recommendation
    rec = _recommendation(readiness, hrv_avg, sleep_score, wellness_composite,
                          data_is_stale=data_is_stale)
    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": rec}
    })

    # Gym-day sections: progression alerts, stall warnings, mountain context
    if is_gym_day(target_date):
        _add_gym_day_sections(blocks, target_date)

    return {"blocks": blocks}


def _add_gym_day_sections(blocks: list, target_date: date) -> None:
    """Add progression alerts, stall warnings, and mountain context on gym days."""
    sections_added = False

    # Stall early warnings (highest priority)
    stall_warnings = fetch_stall_warnings()
    high_risk = [w for w in stall_warnings if w.get("stall_risk") == "high"]
    if high_risk:
        lines = []
        for w in high_risk:
            name = w["exercise_name"]
            weight = w.get("planned_weight_kg", "?")
            sessions = w.get("sessions_at_current_weight", "?")
            lines.append(
                f":warning: *{name}* at {weight}kg for {sessions} sessions "
                "— RPE climbing, sleep declining. Consider holding this week."
            )
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*Stall Watch*\n" + "\n".join(lines)}
        })
        sections_added = True

    # Progression alerts
    alerts = fetch_progression_alerts()
    if alerts:
        alert_lines = []
        for ex in alerts.get("stalled", []):
            alert_lines.append(
                f":red_circle: *{ex['exercise_name']}* — stalled at "
                f"{ex.get('planned_weight_kg', '?')}kg "
                f"({ex.get('sessions_at_current_weight', '?')} sessions)"
            )
        for ex in alerts.get("behind", []):
            alert_lines.append(
                f":large_yellow_circle: *{ex['exercise_name']}* — behind at "
                f"{ex.get('planned_weight_kg', '?')}kg"
            )
        top = alerts.get("top_gainer")
        if top:
            alert_lines.append(
                f":chart_with_upwards_trend: *{top['exercise_name']}* — "
                f"+{top.get('kg_per_week', '?')}kg/week"
            )
        if alert_lines:
            if not sections_added:
                blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Progression*\n" + "\n".join(alert_lines)}
            })
            sections_added = True

    # Mountain impact context (if mountain activity in last 3 days)
    try:
        mountain = supabase_get("daily_coaching_context", {
            "select": "mountain_days_3d,elevation_3d",
        })
        mountain_active = (
            mountain and mountain[0].get("mountain_days_3d")
            and mountain[0]["mountain_days_3d"] > 0
        )
    except Exception:
        mountain_active = False

    if mountain_active:
        patterns = fetch_mountain_patterns()
        if patterns:
            pattern_lines = [f"_{p['observation']}_" for p in patterns[:2]]
            if not sections_added:
                blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":mountain: *Mountain Impact (from your data)*\n"
                    + "\n".join(pattern_lines),
                }
            })


def _error_message(target_date: date, error: str) -> dict:
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":warning: *Morning Briefing ({target_date.isoformat()}):* {error}",
                }
            }
        ]
    }


# ---------------------------------------------------------------------------
# Slack posting
# ---------------------------------------------------------------------------


def post_to_slack(message: dict, channel: str) -> None:
    """Post a Block Kit message to Slack."""
    if not channel:
        log.error("SLACK_CHANNEL_DAILY not set. Use --dry-run or set the env var.")
        sys.exit(1)

    payload = {
        "channel": channel,
        "blocks": message["blocks"],
        "text": "Morning health briefing",  # fallback for notifications
    }
    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )
    data = resp.json()
    if not data.get("ok"):
        log.error("Slack API error: %s", data.get("error", "unknown"))
        sys.exit(1)
    log.info("Posted to Slack channel %s (ts: %s)", channel, data.get("ts"))


def print_dry_run(message: dict) -> None:
    """Pretty-print the message for dry-run mode."""
    for block in message.get("blocks", []):
        btype = block.get("type")
        if btype == "header":
            print(f"\n{'=' * 50}")
            print(f"  {block['text']['text']}")
            print(f"{'=' * 50}")
        elif btype == "section":
            text = block.get("text", {}).get("text", "")
            # Strip Slack mrkdwn bold markers for terminal readability
            print(text)
        elif btype == "divider":
            print("-" * 40)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Post morning health briefing to Slack")
    parser.add_argument("--date", type=str, help="Briefing date (YYYY-MM-DD), default: today")
    parser.add_argument("--dry-run", action="store_true", help="Print message instead of posting")
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else date.today()
    log.info("Generating briefing for %s", target.isoformat())

    message = build_message(target)

    if args.dry_run:
        print_dry_run(message)
        # Also dump raw JSON for debugging
        print("--- Raw Block Kit JSON ---")
        print(json.dumps(message, indent=2))
    else:
        post_to_slack(message, SLACK_CHANNEL)


if __name__ == "__main__":
    main()

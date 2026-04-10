#!/usr/bin/env python3
"""Weekly narrative summary + insight delivery → Slack.

Generates a progress snapshot covering the past week's training, recovery,
and body composition, then adds 1-2 personal insights from the athlete's
own data. Posts to #ascent-training.

Designed to run Sunday 20:00 after weekly_analysis_runner.py completes.

Usage:
    python weekly_summary.py              # post this week's summary
    python weekly_summary.py --dry-run    # print without posting
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"]
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL_TRAINING", os.environ.get("SLACK_CHANNEL_DAILY", ""))

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("weekly_summary")


def supabase_get(table: str, params: dict) -> list:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------


def get_week_range(ref_date: date) -> tuple[date, date]:
    """Return (Monday, Sunday) of the week containing ref_date."""
    monday = ref_date - timedelta(days=ref_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def fetch_gym_sessions(start: date, end: date) -> list:
    return supabase_get("planned_workouts", {
        "select": "session_name,status,scheduled_date",
        "and": f"(scheduled_date.gte.{start},scheduled_date.lte.{end})",
        "session_type": "neq.rest",
        "order": "scheduled_date.asc",
    })


def fetch_activities(start: date, end: date) -> list:
    return supabase_get("activities", {
        "select": "activity_type,activity_name,duration_seconds,elevation_gain,calories,date",
        "and": f"(date.gte.{start},date.lte.{end})",
        "order": "date.asc",
    })


def fetch_sleep_avg(start: date, end: date) -> dict:
    rows = supabase_get("sleep", {
        "select": "total_sleep_seconds,overall_score",
        "and": f"(date.gte.{start},date.lte.{end})",
    })
    if not rows:
        return {"avg_hours": None, "avg_score": None, "nights_below_6h": 0}
    total = [r["total_sleep_seconds"] for r in rows if r.get("total_sleep_seconds")]
    scores = [r["overall_score"] for r in rows if r.get("overall_score")]
    below_6 = sum(1 for s in total if s < 21600)
    return {
        "avg_hours": round(sum(total) / len(total) / 3600, 1) if total else None,
        "avg_score": round(sum(scores) / len(scores), 0) if scores else None,
        "nights_below_6h": below_6,
    }


def fetch_body_comp_trend(end: date) -> dict:
    rows = supabase_get("body_composition", {
        "select": "weight_kg,date",
        "and": f"(date.gte.{(end - timedelta(days=13))},date.lte.{end})",
        "order": "date.asc",
    })
    if not rows or not any(r.get("weight_kg") for r in rows):
        return {"current_kg": None, "trend_kg_per_week": None}
    valid = [r for r in rows if r.get("weight_kg")]
    current = valid[-1]["weight_kg"]
    if len(valid) >= 3:
        first_avg = sum(r["weight_kg"] for r in valid[:3]) / 3
        last_avg = sum(r["weight_kg"] for r in valid[-3:]) / 3
        days = (date.fromisoformat(valid[-1]["date"]) - date.fromisoformat(valid[0]["date"])).days
        trend = (last_avg - first_avg) / max(days / 7, 0.5)
        return {"current_kg": round(current, 1), "trend_kg_per_week": round(trend, 2)}
    return {"current_kg": round(current, 1), "trend_kg_per_week": None}


def fetch_progression_summary() -> list:
    """Get progression velocity for all tracked exercises."""
    try:
        return supabase_get("progression_velocity", {
            "select": "exercise_name,planned_weight_kg,progression_status,kg_per_week,current_e1rm,sessions_at_current_weight",
            "order": "kg_per_week.desc.nullslast",
        })
    except Exception:
        return []


def fetch_prs_this_week(start: date, end: date) -> list:
    try:
        return supabase_get("exercise_prs", {
            "select": "exercise_id,value,date",
            "pr_type": "eq.e1rm",
            "and": f"(date.gte.{start},date.lte.{end})",
        })
    except Exception:
        return []


def fetch_weekly_reflection(start: date) -> dict | None:
    try:
        rows = supabase_get("weekly_reflections", {
            "select": "*",
            "week_start": f"eq.{start.isoformat()}",
            "limit": "1",
        })
        return rows[0] if rows else None
    except Exception:
        return None


def fetch_decision_quality(start: date, end: date) -> dict:
    """Get coaching decision quality stats from this week."""
    try:
        rows = supabase_get("coaching_decision_outcomes", {
            "select": "outcome_quality",
            "and": f"(decision_date.gte.{start},decision_date.lte.{end})",
        })
        if not rows:
            return {"total": 0}
        total = len(rows)
        good = sum(1 for r in rows if r.get("outcome_quality") == "good")
        poor = sum(1 for r in rows if r.get("outcome_quality") == "poor")
        return {"total": total, "good": good, "poor": poor, "good_pct": round(good / total * 100)}
    except Exception:
        return {"total": 0}


# ---------------------------------------------------------------------------
# Insight engine
# ---------------------------------------------------------------------------


def generate_insights(start: date, end: date) -> list[str]:
    """Generate 1-2 personal insights from the athlete's own data."""
    insights = []

    # Insight 1: Sleep-performance correlation
    try:
        corr = supabase_get("sleep_performance_correlation", {
            "select": "*",
            "limit": "3",
        })
        if corr:
            good_sleep = next((c for c in corr if c.get("sleep_bucket") == "good"), None)
            poor_sleep = next((c for c in corr if c.get("sleep_bucket") == "poor"), None)
            if good_sleep and poor_sleep:
                good_vol = good_sleep.get("avg_volume")
                poor_vol = poor_sleep.get("avg_volume")
                if good_vol and poor_vol and good_vol > 0 and poor_vol > 0:
                    pct_diff = round((good_vol - poor_vol) / poor_vol * 100, 0)
                    if abs(pct_diff) >= 5:
                        insights.append(
                            f"Your gym volume is {abs(pct_diff):.0f}% "
                            f"{'higher' if pct_diff > 0 else 'lower'} after 7.5h+ "
                            f"sleep nights vs <6.5h nights "
                            f"(n={good_sleep.get('session_count', '?')}+"
                            f"{poor_sleep.get('session_count', '?')} sessions)."
                        )
    except Exception as e:
        log.debug("Sleep insight failed: %s", e)

    # Insight 2: Mountain interference patterns
    try:
        patterns = supabase_get("athlete_response_patterns", {
            "select": "observation,confidence,sample_size",
            "pattern_type": "eq.mountain_interference",
            "confidence": "in.(medium,high)",
            "limit": "2",
        })
        for p in patterns:
            if p.get("sample_size", 0) >= 5:
                insights.append(p["observation"])
                break  # only one mountain insight per week
    except Exception as e:
        log.debug("Mountain insight failed: %s", e)

    # Insight 3: Progression velocity standout
    try:
        prog = fetch_progression_summary()
        gainers = [p for p in prog if (p.get("kg_per_week") or 0) > 0]
        stallers = [p for p in prog if p.get("progression_status") == "stalled"]
        if gainers and stallers:
            best = gainers[0]
            worst = stallers[0]
            insights.append(
                f"{best['exercise_name']} is your fastest gainer at "
                f"+{best['kg_per_week']}kg/week. Meanwhile, "
                f"{worst['exercise_name']} has been at "
                f"{worst['planned_weight_kg']}kg for "
                f"{worst.get('sessions_at_current_weight', '?')} sessions."
            )
    except Exception as e:
        log.debug("Progression insight failed: %s", e)

    return insights[:2]  # max 2 insights per week


# ---------------------------------------------------------------------------
# Education drip
# ---------------------------------------------------------------------------

EDUCATION_DRIPS = [
    {
        "trigger": "poor_sleep_good_session",
        "message": (
            "Despite short sleep, your session went well. Single bad nights "
            "rarely hurt maximal strength — it's accumulated sleep debt that "
            "degrades performance (Craven 2022)."
        ),
    },
    {
        "trigger": "deload_week",
        "message": (
            "Deload weeks feel like you're slacking. You're not — fatigue "
            "dissipates in 7-11 days while fitness persists for 30+ days. "
            "The bounce typically shows up next week."
        ),
    },
    {
        "trigger": "mountain_then_poor_gym",
        "message": (
            "Lower body volume dropped after the mountain day. Eccentric "
            "loading from descents takes 48-72h to clear — this is why "
            "Monday is upper body only."
        ),
    },
]


# ---------------------------------------------------------------------------
# Build summary
# ---------------------------------------------------------------------------


def build_summary(ref_date: date) -> dict:
    """Build the weekly narrative summary as Slack Block Kit."""
    start, end = get_week_range(ref_date)
    week_num = (start - date(2026, 3, 30)).days // 7 + 1  # relative to program start

    # Fetch all data
    gym_sessions = fetch_gym_sessions(start, end)
    activities = fetch_activities(start, end)
    sleep = fetch_sleep_avg(start, end)
    body = fetch_body_comp_trend(end)
    progression = fetch_progression_summary()
    prs = fetch_prs_this_week(start, end)
    reflection = fetch_weekly_reflection(start)
    decisions = fetch_decision_quality(start, end)
    insights = generate_insights(start, end)

    # Calculate stats
    completed = [s for s in gym_sessions if s.get("status") == "completed"]
    total_planned = [s for s in gym_sessions if s.get("status") != "rest"]
    mountain_acts = [a for a in activities if a.get("activity_type") in (
        "backcountry_skiing", "backcountry_snowboarding", "hiking",
        "mountaineering", "splitboarding", "resort_skiing",
    )]
    total_elevation = sum(a.get("elevation_gain", 0) or 0 for a in mountain_acts)
    total_duration_h = sum(a.get("duration_seconds", 0) or 0 for a in activities) / 3600

    # Build blocks
    blocks = []

    # Header
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text",
                 "text": f"Week {week_num} Summary — {start.strftime('%b %d')} to {end.strftime('%b %d')}"}
    })

    # Training overview
    gym_line = f"Gym: {len(completed)}/{len(total_planned)} sessions completed"
    mountain_line = (
        f"Mountain: {len(mountain_acts)} session{'s' if len(mountain_acts) != 1 else ''}"
        + (f", {int(total_elevation)}m elevation" if total_elevation else "")
    )
    duration_line = f"Total active time: {total_duration_h:.1f}h"

    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text":
            f"*Training*\n{gym_line}\n{mountain_line}\n{duration_line}"}
    })

    # Recovery
    sleep_line = f"Sleep: {sleep['avg_hours'] or '?'}h avg"
    if sleep["nights_below_6h"]:
        sleep_line += f" ({sleep['nights_below_6h']} nights <6h)"
    if sleep["avg_score"]:
        sleep_line += f" | Score: {int(sleep['avg_score'])}/100"
    body_line = ""
    if body["current_kg"]:
        body_line = f"Weight: {body['current_kg']}kg"
        if body["trend_kg_per_week"] is not None:
            direction = "+" if body["trend_kg_per_week"] > 0 else ""
            body_line += f" ({direction}{body['trend_kg_per_week']}kg/week trend)"

    recovery_text = f"*Recovery*\n{sleep_line}"
    if body_line:
        recovery_text += f"\n{body_line}"

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": recovery_text}
    })

    # Progression
    if progression:
        blocks.append({"type": "divider"})
        prog_lines = []
        gainers = [p for p in progression if (p.get("kg_per_week") or 0) > 0][:3]
        stalled = [p for p in progression if p.get("progression_status") == "stalled"]
        for p in gainers:
            prog_lines.append(
                f":chart_with_upwards_trend: *{p['exercise_name']}* "
                f"+{p['kg_per_week']}kg/wk → e1RM {p.get('current_e1rm', '?')}kg"
            )
        for p in stalled:
            prog_lines.append(
                f":red_circle: *{p['exercise_name']}* stalled at "
                f"{p.get('planned_weight_kg', '?')}kg "
                f"({p.get('sessions_at_current_weight', '?')} sessions)"
            )
        if prog_lines:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Progression*\n" + "\n".join(prog_lines)}
            })

    # PRs
    if prs:
        pr_text = " | ".join(f":trophy: e1RM PR" for _ in prs)
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Personal Records:* {len(prs)} new e1RM PR{'s' if len(prs) > 1 else ''} this week"}
        })

    # Decision quality
    if decisions["total"] > 0:
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text":
                f"*Coaching Decisions:* {decisions['total']} evaluated — "
                f"{decisions.get('good_pct', 0)}% good outcomes"}
        })

    # Reflection (if submitted)
    if reflection:
        blocks.append({"type": "divider"})
        ref_parts = []
        if reflection.get("energy_trend"):
            ref_parts.append(f"Energy: {reflection['energy_trend']}")
        if reflection.get("training_satisfaction"):
            ref_parts.append(f"Satisfaction: {reflection['training_satisfaction']}/5")
        if reflection.get("top_highlight"):
            ref_parts.append(f"Highlight: _{reflection['top_highlight']}_")
        if reflection.get("next_week_focus"):
            ref_parts.append(f"Focus: _{reflection['next_week_focus']}_")
        if ref_parts:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text":
                    "*Your Reflection*\n" + "\n".join(ref_parts)}
            })

    # Insights
    if insights:
        blocks.append({"type": "divider"})
        insight_text = "*Insights from your data*\n"
        for i, insight in enumerate(insights):
            insight_text += f"_{insight}_\n"
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": insight_text.strip()}
        })

    return {"blocks": blocks}


# ---------------------------------------------------------------------------
# Post
# ---------------------------------------------------------------------------


def post_to_slack(message: dict) -> None:
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL:
        log.error("Slack not configured")
        sys.exit(1)
    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "channel": SLACK_CHANNEL,
            "blocks": message["blocks"],
            "text": "Weekly training summary",
        },
        timeout=15,
    )
    data = resp.json()
    if not data.get("ok"):
        log.error("Slack error: %s", data.get("error"))
        sys.exit(1)
    log.info("Posted weekly summary to Slack")


def print_dry_run(message: dict) -> None:
    for block in message.get("blocks", []):
        btype = block.get("type")
        if btype == "header":
            print(f"\n{'=' * 50}")
            print(f"  {block['text']['text']}")
            print(f"{'=' * 50}")
        elif btype == "section":
            print(block.get("text", {}).get("text", ""))
        elif btype == "divider":
            print("-" * 40)
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--date", type=str, help="Reference date (default: today)")
    args = parser.parse_args()

    ref = date.fromisoformat(args.date) if args.date else date.today()
    log.info("Generating weekly summary for week of %s", ref)

    message = build_summary(ref)

    if args.dry_run:
        print_dry_run(message)
        print("--- Raw JSON ---")
        print(json.dumps(message, indent=2))
    else:
        post_to_slack(message)


if __name__ == "__main__":
    main()

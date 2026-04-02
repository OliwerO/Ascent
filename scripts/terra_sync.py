#!/usr/bin/env python3
"""Terra API → Supabase sync script.

Replaces garmin_sync.py for all READ operations. Uses Terra's official
Garmin Health API integration — no auth headaches, no rate limits,
no cookie management.

Usage:
    python terra_sync.py                          # sync yesterday + today
    python terra_sync.py --date 2026-04-01        # sync specific date
    python terra_sync.py --range 2026-04-01 2026-04-07  # sync date range

Env vars required: TERRA_API_KEY, TERRA_DEV_ID, TERRA_USER_ID,
                   SUPABASE_URL, SUPABASE_KEY
"""

import argparse
import json
import logging
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from supabase import create_client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

TERRA_API_KEY = os.environ.get("TERRA_API_KEY", "")
TERRA_DEV_ID = os.environ.get("TERRA_DEV_ID", "")
TERRA_USER_ID = os.environ.get("TERRA_USER_ID", "")
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

TERRA_BASE = "https://api.tryterra.co/v2"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("terra_sync")


# ---------------------------------------------------------------------------
# Slack alerting (reuse from garmin_auth)
# ---------------------------------------------------------------------------

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_DAILY = os.environ.get("SLACK_CHANNEL_DAILY", "")


def alert_slack(message: str):
    """Post an alert to #ascent-daily. Best-effort, never raises."""
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_DAILY:
        log.warning("Slack not configured — alert not sent: %s", message)
        return
    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"channel": SLACK_CHANNEL_DAILY, "text": message},
            timeout=10,
        )
        data = resp.json()
        if not data.get("ok"):
            log.warning("Slack alert failed: %s", data.get("error"))
    except Exception as e:
        log.warning("Slack alert failed: %s", e)


# ---------------------------------------------------------------------------
# Terra API client
# ---------------------------------------------------------------------------


def terra_get(endpoint: str, start_date: str, end_date: str | None = None,
              with_samples: bool = False) -> list[dict] | None:
    """Fetch data from Terra REST API. Returns the data array or None."""
    params = {
        "user_id": TERRA_USER_ID,
        "start_date": start_date,
        "to_webhook": "false",
    }
    if end_date:
        params["end_date"] = end_date
    if with_samples:
        params["with_samples"] = "true"

    try:
        resp = requests.get(
            f"{TERRA_BASE}/{endpoint}",
            headers={
                "dev-id": TERRA_DEV_ID,
                "x-api-key": TERRA_API_KEY,
            },
            params=params,
            timeout=30,
        )

        if resp.status_code == 429:
            log.error("Terra rate limit hit (429)")
            return None
        if resp.status_code != 200:
            log.warning("Terra %s returned %d: %s", endpoint, resp.status_code,
                        resp.text[:200])
            return None

        body = resp.json()
        resp_type = body.get("type", "")
        if resp_type in ("NoDataReturned", "RequestProcessing"):
            log.info("Terra %s: %s", endpoint, resp_type)
            return []

        return body.get("data", [])

    except Exception as e:
        log.error("Terra %s request failed: %s", endpoint, e)
        return None


def safe_json(obj):
    """Ensure obj is JSON-serialisable."""
    if obj is None:
        return None
    return json.loads(json.dumps(obj, default=str))


# ---------------------------------------------------------------------------
# Sync functions — one per Supabase table
# ---------------------------------------------------------------------------


def sync_daily_metrics(sb, d: date) -> bool:
    """Sync daily metrics from Terra Daily endpoint."""
    ds = d.isoformat()
    data = terra_get("daily", ds, ds, with_samples=True)
    if data is None:
        return False
    if not data:
        log.info("No daily data from Terra for %s", ds)
        return False

    entry = data[0]  # Take first daily entry for the date
    hr = entry.get("heart_rate_data", {}).get("summary", {})
    stress = entry.get("stress_data", {})
    calories = entry.get("calories_data", {})
    distance = entry.get("distance_data", {})
    oxygen = entry.get("oxygen_data", {})
    scores = entry.get("scores", {})

    # Body battery from stress_data samples
    bb_samples = stress.get("body_battery_samples", [])
    bb_values = [s.get("level") for s in bb_samples if s.get("level") is not None]
    bb_highest = max(bb_values) if bb_values else None
    bb_lowest = min(bb_values) if bb_values else None

    def to_int(v):
        return int(v) if v is not None else None

    row = {
        "date": ds,
        "total_steps": to_int(distance.get("summary", {}).get("steps")),
        "total_distance_meters": distance.get("summary", {}).get("distance_meters"),
        "active_calories": to_int(calories.get("net_activity_calories")),
        "total_calories": to_int(calories.get("total_burned_calories")),
        "floors_ascended": to_int(distance.get("summary", {}).get("floors_climbed")),
        "floors_descended": None,  # Not available via Terra
        "intensity_minutes": None,  # Garmin-specific metric
        "moderate_intensity_minutes": None,
        "vigorous_intensity_minutes": None,
        "resting_hr": to_int(hr.get("resting_hr_bpm")),
        "min_hr": to_int(hr.get("min_hr_bpm")),
        "max_hr": to_int(hr.get("max_hr_bpm")),
        "avg_hr": to_int(hr.get("avg_hr_bpm")),
        "avg_stress_level": to_int(stress.get("avg_stress_level")),
        "max_stress_level": to_int(stress.get("max_stress_level")),
        "rest_stress_duration": to_int(stress.get("rest_stress_duration_seconds")),
        "activity_stress_duration": to_int(stress.get("activity_stress_duration_seconds")),
        "body_battery_highest": to_int(bb_highest),
        "body_battery_lowest": to_int(bb_lowest),
        "body_battery_charged": None,  # Requires delta calc from samples
        "body_battery_drained": None,
        "training_readiness_score": scores.get("recovery"),
        "training_load": None,  # Garmin-specific
        "vo2max": None,  # Comes from activity endpoint
        "spo2_avg": oxygen.get("avg_saturation_percentage") if oxygen else None,
        "respiration_avg": None,  # Nested in detailed samples
        "raw_json": safe_json(entry),
    }
    sb.table("daily_metrics").upsert(row, on_conflict="date").execute()
    log.info("daily_metrics upserted for %s", ds)
    return True


def sync_sleep(sb, d: date) -> bool:
    """Sync sleep data from Terra Sleep endpoint."""
    ds = d.isoformat()
    data = terra_get("sleep", ds, ds, with_samples=True)
    if data is None:
        return False
    if not data:
        log.info("No sleep data from Terra for %s", ds)
        return False

    entry = data[0]
    meta = entry.get("metadata", {})
    durations = entry.get("sleep_durations_data", {})
    asleep = durations.get("asleep", {})
    scores_data = entry.get("scores", {})

    row = {
        "date": ds,
        "sleep_start": meta.get("start_time"),
        "sleep_end": meta.get("end_time"),
        "total_sleep_seconds": to_int_val(asleep.get("duration_asleep_state_seconds")),
        "deep_sleep_seconds": to_int_val(asleep.get("duration_deep_sleep_state_seconds")),
        "light_sleep_seconds": to_int_val(asleep.get("duration_light_sleep_state_seconds")),
        "rem_sleep_seconds": to_int_val(asleep.get("duration_REM_sleep_state_seconds")),
        "awake_seconds": to_int_val(
            durations.get("awake", {}).get("duration_awake_state_seconds")
        ),
        "overall_score": to_int_val(scores_data.get("sleep_score")),
        "quality_score": None,  # Garmin-specific sub-score
        "duration_score": None,
        "rem_percentage_score": None,
        "restlessness_score": None,
        "stress_score": None,
        "revitalization_score": None,
        "raw_json": safe_json(entry),
    }
    sb.table("sleep").upsert(row, on_conflict="date").execute()
    log.info("sleep upserted for %s", ds)
    return True


def sync_hrv(sb, d: date) -> bool:
    """Sync HRV data from Terra Sleep + Daily endpoints.

    Terra embeds HRV in heart_rate_data.summary (avg_hrv_rmssd, avg_hrv_sdnn).
    We pull from the Sleep endpoint for last_night_avg (more accurate overnight HRV).
    """
    ds = d.isoformat()

    # Get overnight HRV from sleep
    sleep_data = terra_get("sleep", ds, ds, with_samples=True)
    # Get daily HRV for weekly context
    daily_data = terra_get("daily", ds, ds)

    last_night_avg = None
    if sleep_data:
        hr_summary = sleep_data[0].get("heart_rate_data", {}).get("summary", {})
        last_night_avg = hr_summary.get("avg_hrv_rmssd")

    weekly_avg = None
    if daily_data:
        hr_summary = daily_data[0].get("heart_rate_data", {}).get("summary", {})
        weekly_avg = hr_summary.get("avg_hrv_rmssd")

    if last_night_avg is None and weekly_avg is None:
        log.info("No HRV data from Terra for %s", ds)
        return False

    row = {
        "date": ds,
        "weekly_avg": weekly_avg,
        "last_night_avg": last_night_avg,
        "last_night_5min_high": None,  # Not available via Terra
        "baseline_low_upper": None,  # Garmin-specific baseline
        "baseline_balanced_low": None,
        "baseline_balanced_upper": None,
        "status": None,  # Garmin-specific HRV status label
        "readings": None,  # Would need with_samples detailed data
        "raw_json": safe_json({
            "sleep_hrv": sleep_data[0] if sleep_data else None,
            "daily_hrv": daily_data[0] if daily_data else None,
        }),
    }
    sb.table("hrv").upsert(row, on_conflict="date").execute()
    log.info("hrv upserted for %s", ds)
    return True


def sync_body_composition(sb, d: date) -> bool:
    """Sync body composition from Terra Body endpoint."""
    ds = d.isoformat()
    data = terra_get("body", ds, ds)
    if data is None:
        return False
    if not data:
        log.info("No body data from Terra for %s", ds)
        return False

    entry = data[0]
    measurements = entry.get("measurements_data", {}).get("measurements", [])
    if not measurements:
        log.info("No body measurements from Terra for %s", ds)
        return False

    m = measurements[0]
    weight_kg = m.get("weight_kg")
    if weight_kg is None:
        return False

    row = {
        "date": ds,
        "weight_grams": int(weight_kg * 1000) if weight_kg else None,
        "bmi": m.get("BMI"),
        "body_fat_pct": m.get("bodyfat_percentage"),
        "body_water_pct": m.get("water_percentage"),
        "bone_mass_grams": m.get("bone_mass_g"),
        "muscle_mass_grams": m.get("muscle_mass_g"),
        "visceral_fat_rating": None,  # Not in Terra normalized schema
        "metabolic_age": m.get("estimated_fitness_age"),
        "lean_body_mass_grams": m.get("lean_mass_g"),
        "source": "terra",
        "raw_json": safe_json(entry),
    }
    sb.table("body_composition").upsert(row, on_conflict="date,source").execute()
    log.info("body_composition upserted for %s", ds)
    return True


def sync_heart_rate_series(sb, d: date) -> bool:
    """Sync heart rate time series from Terra Daily endpoint."""
    ds = d.isoformat()
    data = terra_get("daily", ds, ds, with_samples=True)
    if data is None:
        return False
    if not data:
        log.info("No HR series from Terra for %s", ds)
        return False

    entry = data[0]
    hr_data = entry.get("heart_rate_data", {})
    detailed = hr_data.get("detailed", {})
    summary = hr_data.get("summary", {})

    # Terra detailed HR: list of {timestamp, bpm}
    readings = detailed.get("hr_samples", [])

    row = {
        "date": ds,
        "readings": safe_json(readings) if readings else None,
        "resting_hr": to_int_val(summary.get("resting_hr_bpm")),
    }
    sb.table("heart_rate_series").upsert(row, on_conflict="date").execute()
    log.info("heart_rate_series upserted for %s", ds)
    return True


def sync_stress_series(sb, d: date) -> bool:
    """Sync stress time series from Terra Daily endpoint."""
    ds = d.isoformat()
    data = terra_get("daily", ds, ds, with_samples=True)
    if data is None:
        return False
    if not data:
        log.info("No stress series from Terra for %s", ds)
        return False

    entry = data[0]
    stress = entry.get("stress_data", {})
    readings = stress.get("samples", [])

    row = {
        "date": ds,
        "readings": safe_json(readings) if readings else None,
    }
    sb.table("stress_series").upsert(row, on_conflict="date").execute()
    log.info("stress_series upserted for %s", ds)
    return True


def sync_activities(sb, d: date) -> bool:
    """Sync activities from Terra Activity endpoint."""
    ds = d.isoformat()
    data = terra_get("activity", ds, ds, with_samples=True)
    if data is None:
        return False
    if not data:
        log.info("No activities from Terra for %s", ds)
        return True  # No activities is not an error

    count = 0
    for act in data:
        meta = act.get("metadata", {})
        hr = act.get("heart_rate_data", {}).get("summary", {})
        calories = act.get("calories_data", {})
        dist = act.get("distance_data", {}).get("summary", {})
        movement = act.get("movement_data", {})

        # Terra uses summary_id as unique identifier
        summary_id = meta.get("summary_id", "")
        if not summary_id:
            continue

        start_time = meta.get("start_time", "")
        act_date = start_time[:10] if start_time else ds

        row = {
            "garmin_activity_id": summary_id,
            "date": act_date,
            "activity_type": _map_terra_activity_type(meta.get("type")),
            "activity_name": meta.get("name"),
            "start_time": start_time,
            "duration_seconds": to_int_val(
                _duration_seconds(meta.get("start_time"), meta.get("end_time"))
            ),
            "distance_meters": dist.get("distance_meters"),
            "calories": to_int_val(calories.get("total_burned_calories")),
            "avg_hr": to_int_val(hr.get("avg_hr_bpm")),
            "max_hr": to_int_val(hr.get("max_hr_bpm")),
            "avg_speed": movement.get("avg_speed_meters_per_second") if movement else None,
            "max_speed": movement.get("max_speed_meters_per_second") if movement else None,
            "elevation_gain": dist.get("elevation", {}).get("gain_actual_meters")
                if isinstance(dist.get("elevation"), dict) else None,
            "elevation_loss": dist.get("elevation", {}).get("loss_actual_meters")
                if isinstance(dist.get("elevation"), dict) else None,
            "training_effect_aerobic": None,  # Garmin-specific
            "training_effect_anaerobic": None,
            "vo2max": None,  # Not in Terra activity response
            "total_sets": None,
            "total_reps": None,
            "hr_zones": safe_json(hr.get("hr_zone_data")) if hr.get("hr_zone_data") else None,
            "raw_json": safe_json(act),
        }
        sb.table("activities").upsert(row, on_conflict="garmin_activity_id").execute()
        count += 1

    log.info("activities: %d upserted for %s", count, ds)
    return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def to_int_val(v):
    """Convert to int if not None."""
    return int(v) if v is not None else None


def _duration_seconds(start: str | None, end: str | None) -> int | None:
    """Calculate duration in seconds between two ISO8601 timestamps."""
    if not start or not end:
        return None
    try:
        s = datetime.fromisoformat(start.replace("Z", "+00:00"))
        e = datetime.fromisoformat(end.replace("Z", "+00:00"))
        return int((e - s).total_seconds())
    except (ValueError, TypeError):
        return None


# Terra activity type codes → human-readable names
# See: https://docs.tryterra.co/reference/activity-types
TERRA_ACTIVITY_TYPES = {
    0: "unknown",
    1: "running",
    2: "cycling",
    3: "swimming",
    4: "walking",
    5: "strength_training",
    6: "yoga",
    7: "hiking",
    8: "skiing",
    9: "snowboarding",
    10: "rowing",
    12: "cross_country_skiing",
    13: "elliptical",
    14: "stair_climbing",
    16: "other",
    24: "mountaineering",
    52: "ski_touring",
    56: "indoor_cycling",
    62: "pilates",
    79: "functional_training",
    82: "trail_running",
    83: "indoor_running",
}


def _map_terra_activity_type(type_code: int | None) -> str:
    """Map Terra's numeric activity type to a readable string."""
    if type_code is None:
        return "unknown"
    return TERRA_ACTIVITY_TYPES.get(type_code, f"type_{type_code}")


# ---------------------------------------------------------------------------
# Sync orchestrator
# ---------------------------------------------------------------------------

SYNC_FUNCTIONS = [
    ("daily_metrics", sync_daily_metrics),
    ("sleep", sync_sleep),
    ("hrv", sync_hrv),
    ("body_composition", sync_body_composition),
    ("heart_rate_series", sync_heart_rate_series),
    ("stress_series", sync_stress_series),
    ("activities", sync_activities),
]


def sync_date(sb, d: date) -> dict:
    """Run all sync functions for a single date."""
    log.info("=== Syncing %s via Terra ===", d.isoformat())
    results = {}
    for name, fn in SYNC_FUNCTIONS:
        try:
            results[name] = fn(sb, d)
        except Exception as exc:
            log.error("Error syncing %s for %s: %s", name, d.isoformat(), exc)
            results[name] = False
    return results


def main():
    parser = argparse.ArgumentParser(description="Sync Terra health data to Supabase")
    parser.add_argument("--date", type=str, help="Sync a specific date (YYYY-MM-DD)")
    parser.add_argument(
        "--range", nargs=2, metavar=("START", "END"),
        help="Sync a date range (YYYY-MM-DD YYYY-MM-DD)",
    )
    args = parser.parse_args()

    # Validate Terra config
    if not all([TERRA_API_KEY, TERRA_DEV_ID, TERRA_USER_ID]):
        log.error(
            "Terra API not configured. Set TERRA_API_KEY, TERRA_DEV_ID, "
            "TERRA_USER_ID in .env"
        )
        alert_slack(
            ":warning: *Terra sync failed* — API credentials not configured. "
            "Add TERRA_API_KEY, TERRA_DEV_ID, TERRA_USER_ID to .env"
        )
        sys.exit(2)

    # Determine dates
    if args.range:
        start = date.fromisoformat(args.range[0])
        end = date.fromisoformat(args.range[1])
        if start > end:
            start, end = end, start
        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
    elif args.date:
        dates = [date.fromisoformat(args.date)]
    else:
        dates = [date.today() - timedelta(days=1), date.today()]

    log.info("Syncing %d date(s) via Terra: %s → %s", len(dates), dates[0], dates[-1])

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    all_results = {}
    for d in dates:
        all_results[d.isoformat()] = sync_date(sb, d)

    # Summary
    total_ok = sum(1 for day in all_results.values() for ok in day.values() if ok)
    total_fail = sum(1 for day in all_results.values() for ok in day.values() if not ok)
    log.info("Terra sync complete: %d succeeded, %d failed/empty", total_ok, total_fail)

    if total_fail > total_ok:
        alert_slack(
            f":warning: *Terra sync mostly failed* — "
            f"{total_ok} succeeded, {total_fail} failed. Check logs."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

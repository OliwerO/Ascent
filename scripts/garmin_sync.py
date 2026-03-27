#!/usr/bin/env python3
"""Garmin Connect → Supabase nightly sync script.

Usage:
    python garmin_sync.py                          # sync yesterday
    python garmin_sync.py --date 2026-03-20        # sync specific date
    python garmin_sync.py --range 2026-03-01 2026-03-20  # sync date range
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from garminconnect import Garmin
from supabase import create_client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load .env from project root (two levels up from scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GARMIN_EMAIL = os.environ["GARMIN_EMAIL"]
GARMIN_PASSWORD = os.environ["GARMIN_PASSWORD"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

GARTH_HOME = Path.home() / ".garth"
API_DELAY = 1  # seconds between Garmin API calls

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("garmin_sync")

# ---------------------------------------------------------------------------
# Garmin client
# ---------------------------------------------------------------------------


def get_garmin_client() -> Garmin:
    """Authenticate with Garmin Connect, reusing stored tokens when possible."""
    client = Garmin()
    try:
        client.login(str(GARTH_HOME))
        log.info("Resumed Garmin session from stored tokens")
    except Exception:
        log.info("Stored tokens expired or missing — logging in with credentials")
        client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
        client.login()
        client.garth.dump(str(GARTH_HOME))
        log.info("Login successful, tokens saved to %s", GARTH_HOME)
    return client


# ---------------------------------------------------------------------------
# Safe API helpers
# ---------------------------------------------------------------------------


def api_call(fn, *args, **kwargs):
    """Call a Garmin API function with rate limiting; return None on failure."""
    time.sleep(API_DELAY)
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        log.warning("API call %s failed: %s", fn.__name__, exc)
        return None


def safe_json(obj):
    """Ensure obj is JSON-serialisable (handles datetimes etc.)."""
    return json.loads(json.dumps(obj, default=str))


# ---------------------------------------------------------------------------
# Sync functions — one per table
# ---------------------------------------------------------------------------


def sync_daily_metrics(client: Garmin, sb, d: date) -> bool:
    ds = d.isoformat()
    stats = api_call(client.get_stats, ds)
    if not stats:
        log.warning("No daily stats for %s", ds)
        return False

    # Training readiness, SpO2, respiration from separate endpoints
    tr = api_call(client.get_training_readiness, ds)
    spo2 = api_call(client.get_spo2_data, ds)
    resp = api_call(client.get_respiration_data, ds)

    training_readiness_score = None
    if tr:
        # Endpoint may return dict or list
        if isinstance(tr, dict):
            training_readiness_score = tr.get("score") or tr.get("trainingReadinessScore")
        elif isinstance(tr, list) and tr:
            training_readiness_score = tr[0].get("score") or tr[0].get("trainingReadinessScore")

    spo2_avg = None
    if spo2:
        if isinstance(spo2, dict):
            spo2_avg = spo2.get("averageSpO2")
        elif isinstance(spo2, list) and spo2:
            vals = [r.get("spO2") or r.get("value") for r in spo2 if r.get("spO2") or r.get("value")]
            spo2_avg = sum(vals) / len(vals) if vals else None

    resp_avg = None
    if resp:
        if isinstance(resp, dict):
            resp_avg = resp.get("avgWakingRespirationValue") or resp.get("avgSleepRespirationValue")
        elif isinstance(resp, list) and resp:
            vals = [r.get("value") for r in resp if r.get("value")]
            resp_avg = sum(vals) / len(vals) if vals else None

    row = {
        "date": ds,
        "total_steps": stats.get("totalSteps"),
        "total_distance_meters": stats.get("totalDistanceMeters"),
        "active_calories": stats.get("activeKilocalories"),
        "total_calories": stats.get("totalKilocalories"),
        "floors_ascended": stats.get("floorsAscended"),
        "floors_descended": stats.get("floorsDescended"),
        "intensity_minutes": stats.get("intensityMinutesGoal"),
        "moderate_intensity_minutes": stats.get("moderateIntensityMinutes"),
        "vigorous_intensity_minutes": stats.get("vigorousIntensityMinutes"),
        "resting_hr": stats.get("restingHeartRate"),
        "min_hr": stats.get("minHeartRate"),
        "max_hr": stats.get("maxHeartRate"),
        "avg_hr": stats.get("averageHeartRate"),
        "avg_stress_level": stats.get("averageStressLevel"),
        "max_stress_level": stats.get("maxStressLevel"),
        "rest_stress_duration": stats.get("restStressDuration"),
        "activity_stress_duration": stats.get("activityStressDuration"),
        "body_battery_highest": stats.get("bodyBatteryHighestValue"),
        "body_battery_lowest": stats.get("bodyBatteryLowestValue"),
        "body_battery_charged": stats.get("bodyBatteryChargedValue"),
        "body_battery_drained": stats.get("bodyBatteryDrainedValue"),
        "training_readiness_score": training_readiness_score,
        "training_load": stats.get("trainingLoadBalance"),
        "vo2max": stats.get("vO2MaxValue"),
        "spo2_avg": spo2_avg,
        "respiration_avg": resp_avg,
        "raw_json": safe_json(stats),
    }
    sb.table("daily_metrics").upsert(row, on_conflict="date").execute()
    log.info("daily_metrics upserted for %s", ds)
    return True


def sync_sleep(client: Garmin, sb, d: date) -> bool:
    ds = d.isoformat()
    data = api_call(client.get_sleep_data, ds)
    if not data:
        log.warning("No sleep data for %s", ds)
        return False

    daily = data.get("dailySleepDTO", data)
    scores = data.get("sleepScores", {})

    row = {
        "date": ds,
        "sleep_start": daily.get("sleepStartTimestampLocal") or daily.get("sleepStart"),
        "sleep_end": daily.get("sleepEndTimestampLocal") or daily.get("sleepEnd"),
        "total_sleep_seconds": daily.get("sleepTimeSeconds"),
        "deep_sleep_seconds": daily.get("deepSleepSeconds"),
        "light_sleep_seconds": daily.get("lightSleepSeconds"),
        "rem_sleep_seconds": daily.get("remSleepSeconds"),
        "awake_seconds": daily.get("awakeSleepSeconds"),
        "overall_score": scores.get("overall", {}).get("value")
            if isinstance(scores.get("overall"), dict)
            else scores.get("overall") or daily.get("sleepScoreOverall"),
        "quality_score": scores.get("quality", {}).get("value")
            if isinstance(scores.get("quality"), dict)
            else scores.get("quality"),
        "duration_score": scores.get("duration", {}).get("value")
            if isinstance(scores.get("duration"), dict)
            else scores.get("duration"),
        "rem_percentage_score": scores.get("remPercentage", {}).get("value")
            if isinstance(scores.get("remPercentage"), dict)
            else scores.get("remPercentage"),
        "restlessness_score": scores.get("restlessness", {}).get("value")
            if isinstance(scores.get("restlessness"), dict)
            else scores.get("restlessness"),
        "stress_score": scores.get("stress", {}).get("value")
            if isinstance(scores.get("stress"), dict)
            else scores.get("stress"),
        "revitalization_score": scores.get("revitalization", {}).get("value")
            if isinstance(scores.get("revitalization"), dict)
            else scores.get("revitalization"),
        "raw_json": safe_json(data),
    }
    sb.table("sleep").upsert(row, on_conflict="date").execute()
    log.info("sleep upserted for %s", ds)
    return True


def sync_hrv(client: Garmin, sb, d: date) -> bool:
    ds = d.isoformat()
    data = api_call(client.get_hrv_data, ds)
    if not data:
        log.warning("No HRV data for %s", ds)
        return False

    summary = data.get("hrvSummary", data) if isinstance(data, dict) else data
    baseline = summary.get("baseline", {}) if isinstance(summary, dict) else {}

    row = {
        "date": ds,
        "weekly_avg": summary.get("weeklyAvg"),
        "last_night_avg": summary.get("lastNightAvg"),
        "last_night_5min_high": summary.get("lastNight5MinHigh"),
        "baseline_low_upper": baseline.get("lowUpper"),
        "baseline_balanced_low": baseline.get("balancedLow"),
        "baseline_balanced_upper": baseline.get("balancedUpper"),
        "status": summary.get("status"),
        "readings": safe_json(data.get("hrvReadings", [])) if isinstance(data, dict) else None,
        "raw_json": safe_json(data) if isinstance(data, dict) else None,
    }
    sb.table("hrv").upsert(row, on_conflict="date").execute()
    log.info("hrv upserted for %s", ds)
    return True


def sync_body_composition(client: Garmin, sb, d: date) -> bool:
    ds = d.isoformat()
    data = api_call(client.get_body_composition, ds, ds)
    if not data:
        log.warning("No body composition data for %s", ds)
        return False

    entries = data.get("dateWeightList", data.get("totalAverage", []))
    if isinstance(entries, dict):
        entries = [entries]
    if not entries:
        log.info("No body composition entries for %s", ds)
        return False

    for entry in entries if isinstance(entries, list) else [entries]:
        weight_grams = entry.get("weight")
        if weight_grams is None:
            continue
        row = {
            "date": ds,
            "weight_grams": weight_grams,
            "bmi": entry.get("bmi"),
            "body_fat_pct": entry.get("bodyFat"),
            "body_water_pct": entry.get("bodyWater"),
            "bone_mass_grams": entry.get("boneMass"),
            "muscle_mass_grams": entry.get("muscleMass"),
            "visceral_fat_rating": entry.get("visceralFat"),
            "metabolic_age": entry.get("metabolicAge"),
            "lean_body_mass_grams": entry.get("leanBodyMass"),
            "source": "garmin",
            "raw_json": safe_json(entry),
        }
        sb.table("body_composition").upsert(
            row, on_conflict="date"
        ).execute()
    log.info("body_composition upserted for %s", ds)
    return True


def sync_heart_rate_series(client: Garmin, sb, d: date) -> bool:
    ds = d.isoformat()
    data = api_call(client.get_heart_rates, ds)
    if not data:
        log.warning("No heart rate data for %s", ds)
        return False

    readings = data.get("heartRateValues", data) if isinstance(data, dict) else data
    resting = data.get("restingHeartRate") if isinstance(data, dict) else None

    row = {
        "date": ds,
        "readings": safe_json(readings) if readings else None,
        "resting_hr": resting,
    }
    sb.table("heart_rate_series").upsert(row, on_conflict="date").execute()
    log.info("heart_rate_series upserted for %s", ds)
    return True


def sync_stress_series(client: Garmin, sb, d: date) -> bool:
    ds = d.isoformat()
    data = api_call(client.get_stress_data, ds)
    if not data:
        log.warning("No stress data for %s", ds)
        return False

    readings = data.get("stressValuesArray", data) if isinstance(data, dict) else data

    row = {
        "date": ds,
        "readings": safe_json(readings) if readings else None,
    }
    sb.table("stress_series").upsert(row, on_conflict="date").execute()
    log.info("stress_series upserted for %s", ds)
    return True


def sync_activities(client: Garmin, sb, d: date) -> bool:
    """Sync recent activities. Deduplicates on garmin_activity_id."""
    activities = api_call(client.get_activities, 0, 20)
    if not activities:
        log.warning("No activities returned")
        return False

    count = 0
    for act in activities:
        # Filter to the target date
        act_date_str = act.get("startTimeLocal", "")[:10]
        if act_date_str != d.isoformat():
            continue

        garmin_id = str(act.get("activityId", ""))
        if not garmin_id:
            continue

        row = {
            "garmin_activity_id": garmin_id,
            "date": act_date_str,
            "activity_type": act.get("activityType", {}).get("typeKey", "unknown")
                if isinstance(act.get("activityType"), dict)
                else str(act.get("activityType", "unknown")),
            "activity_name": act.get("activityName"),
            "start_time": act.get("startTimeGMT") or act.get("startTimeLocal"),
            "duration_seconds": int(act["duration"]) if act.get("duration") else None,
            "distance_meters": act.get("distance"),
            "calories": act.get("calories"),
            "avg_hr": act.get("averageHR"),
            "max_hr": act.get("maxHR"),
            "avg_speed": act.get("averageSpeed"),
            "max_speed": act.get("maxSpeed"),
            "elevation_gain": act.get("elevationGain"),
            "elevation_loss": act.get("elevationLoss"),
            "training_effect_aerobic": act.get("aerobicTrainingEffect"),
            "training_effect_anaerobic": act.get("anaerobicTrainingEffect"),
            "vo2max": act.get("vO2MaxValue"),
            "total_sets": act.get("summarizedExerciseSets", {}).get("numberOfSets")
                if isinstance(act.get("summarizedExerciseSets"), dict)
                else None,
            "total_reps": act.get("summarizedExerciseSets", {}).get("numberOfReps")
                if isinstance(act.get("summarizedExerciseSets"), dict)
                else None,
            "hr_zones": safe_json(act.get("heartRateZones")) if act.get("heartRateZones") else None,
            "raw_json": safe_json(act),
        }
        sb.table("activities").upsert(row, on_conflict="garmin_activity_id").execute()
        count += 1

    log.info("activities: %d upserted for %s", count, d.isoformat())
    return True


# ---------------------------------------------------------------------------
# Main sync orchestrator
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


def sync_date(client: Garmin, sb, d: date) -> dict:
    """Run all sync functions for a single date. Returns {table: success}."""
    log.info("=== Syncing %s ===", d.isoformat())
    results = {}
    for name, fn in SYNC_FUNCTIONS:
        try:
            results[name] = fn(client, sb, d)
        except Exception as exc:
            log.error("Error syncing %s for %s: %s", name, d.isoformat(), exc)
            results[name] = False
    return results


def main():
    parser = argparse.ArgumentParser(description="Sync Garmin data to Supabase")
    parser.add_argument("--date", type=str, help="Sync a specific date (YYYY-MM-DD)")
    parser.add_argument(
        "--range", nargs=2, metavar=("START", "END"),
        help="Sync a date range (YYYY-MM-DD YYYY-MM-DD)"
    )
    args = parser.parse_args()

    # Determine dates to sync
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
        dates = [date.today() - timedelta(days=1)]

    log.info("Syncing %d date(s): %s → %s", len(dates), dates[0], dates[-1])

    # Connect
    client = get_garmin_client()
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Sync each date
    all_results = {}
    for d in dates:
        all_results[d.isoformat()] = sync_date(client, sb, d)

    # Summary
    total_ok = sum(
        1 for day in all_results.values() for ok in day.values() if ok
    )
    total_fail = sum(
        1 for day in all_results.values() for ok in day.values() if not ok
    )
    log.info("Sync complete: %d succeeded, %d failed", total_ok, total_fail)

    if total_fail > 0:
        log.warning("Some syncs failed — check warnings above")
        sys.exit(1)


if __name__ == "__main__":
    main()

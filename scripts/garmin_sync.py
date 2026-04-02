#!/usr/bin/env python3
"""Garmin Connect → Supabase nightly sync script.

Syncs all available Garmin health/fitness data to Supabase tables.

Usage:
    python garmin_sync.py                          # sync yesterday + today
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
from garminconnect import Garmin, GarminConnectTooManyRequestsError
from supabase import create_client

from garmin_auth import (
    get_safe_client, save_tokens, alert_slack,
    AuthExpiredError, RateLimitCooldownError,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

API_DELAY = 1  # seconds between Garmin API calls

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("garmin_sync")


# ---------------------------------------------------------------------------
# Safe API helpers
# ---------------------------------------------------------------------------


def api_call(fn, *args, **kwargs):
    """Call a Garmin API function with rate limiting; return None on failure."""
    time.sleep(API_DELAY)
    try:
        return fn(*args, **kwargs)
    except (GarminConnectTooManyRequestsError, RateLimitCooldownError, AuthExpiredError):
        raise  # must abort — continuing would deepen rate limit ban
    except Exception as exc:
        log.warning("API call %s failed: %s", fn.__name__, exc)
        return None


def safe_json(obj):
    """Ensure obj is JSON-serialisable (handles datetimes etc.)."""
    if obj is None:
        return None
    return json.loads(json.dumps(obj, default=str))


def extract_score(scores, key):
    """Extract a score value from Garmin's sleep scores (handles dict or raw)."""
    val = scores.get(key)
    if isinstance(val, dict):
        return val.get("value")
    return val


def _ms_to_iso(ts):
    """Convert a millisecond epoch timestamp to ISO 8601 string, or pass through strings."""
    if ts is None:
        return None
    if isinstance(ts, (int, float)) and ts > 1_000_000_000_000:
        from datetime import timezone
        return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()
    return ts


# ---------------------------------------------------------------------------
# Data validation — reject/flag rules from CLAUDE.md
# ---------------------------------------------------------------------------

# Reject-level rules: data is physiologically impossible, discard before writing
REJECT_RULES = {
    "resting_hr": lambda v: v is not None and (v < 25 or v > 120),
    "avg_hr": lambda v: v is not None and (v < 30 or v > 230),
    "max_hr": lambda v: v is not None and (v < 30 or v > 230),
    "min_hr": lambda v: v is not None and (v < 25 or v > 200),
}

# Sleep-specific reject rules
SLEEP_REJECT_RULES = {
    "total_sleep_seconds": lambda v: v is not None and (v < 7200 or v > 57600),  # <2h or >16h
}


def validate_daily_metrics(row: dict) -> dict:
    """Validate daily_metrics row. Nulls out rejected fields, logs warnings."""
    for field, check in REJECT_RULES.items():
        if field in row and check(row[field]):
            log.warning("REJECT %s=%s (out of physiological range)", field, row[field])
            row[field] = None
    return row


def validate_sleep(row: dict) -> dict:
    """Validate sleep row."""
    for field, check in SLEEP_REJECT_RULES.items():
        if field in row and check(row[field]):
            log.warning("REJECT %s=%s (out of range)", field, row[field])
            row[field] = None
    return row


def validate_hrv(row: dict) -> dict:
    """Validate HRV row. rMSSD outside 5-250 is rejected."""
    for field in ("weekly_avg", "last_night_avg", "last_night_5min_high"):
        val = row.get(field)
        if val is not None and (val < 5 or val > 250):
            log.warning("REJECT %s=%s (rMSSD out of 5-250 range)", field, val)
            row[field] = None
    return row


# ---------------------------------------------------------------------------
# Sync functions — one per table / data type
# ---------------------------------------------------------------------------


def sync_daily_metrics(client: Garmin, sb, d: date) -> bool:
    ds = d.isoformat()
    stats = api_call(client.get_stats, ds)
    if not stats:
        log.warning("No daily stats for %s", ds)
        return False

    # Supplementary endpoints for fields not in get_stats
    tr = api_call(client.get_training_readiness, ds)
    spo2 = api_call(client.get_spo2_data, ds)
    resp = api_call(client.get_respiration_data, ds)

    training_readiness_score = None
    if tr:
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

    def to_int(v):
        return int(v) if v is not None else None

    row = {
        "date": ds,
        "total_steps": to_int(stats.get("totalSteps")),
        "total_distance_meters": stats.get("totalDistanceMeters"),
        "active_calories": to_int(stats.get("activeKilocalories")),
        "total_calories": to_int(stats.get("totalKilocalories")),
        "floors_ascended": to_int(stats.get("floorsAscended")),
        "floors_descended": to_int(stats.get("floorsDescended")),
        "intensity_minutes": to_int(stats.get("intensityMinutesGoal")),
        "moderate_intensity_minutes": to_int(stats.get("moderateIntensityMinutes")),
        "vigorous_intensity_minutes": to_int(stats.get("vigorousIntensityMinutes")),
        "resting_hr": to_int(stats.get("restingHeartRate")),
        "min_hr": to_int(stats.get("minHeartRate")),
        "max_hr": to_int(stats.get("maxHeartRate")),
        "avg_hr": to_int(stats.get("averageHeartRate")),
        "avg_stress_level": to_int(stats.get("averageStressLevel")),
        "max_stress_level": to_int(stats.get("maxStressLevel")),
        "rest_stress_duration": to_int(stats.get("restStressDuration")),
        "activity_stress_duration": to_int(stats.get("activityStressDuration")),
        "body_battery_highest": to_int(stats.get("bodyBatteryHighestValue")),
        "body_battery_lowest": to_int(stats.get("bodyBatteryLowestValue")),
        "body_battery_charged": to_int(stats.get("bodyBatteryChargedValue")),
        "body_battery_drained": to_int(stats.get("bodyBatteryDrainedValue")),
        "training_readiness_score": training_readiness_score,
        "training_load": stats.get("trainingLoadBalance"),
        "vo2max": stats.get("vO2MaxValue"),
        "spo2_avg": spo2_avg,
        "respiration_avg": resp_avg,
        "raw_json": safe_json(stats),
    }
    row = validate_daily_metrics(row)
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
        "sleep_start": _ms_to_iso(daily.get("sleepStartTimestampLocal") or daily.get("sleepStart")),
        "sleep_end": _ms_to_iso(daily.get("sleepEndTimestampLocal") or daily.get("sleepEnd")),
        "total_sleep_seconds": daily.get("sleepTimeSeconds"),
        "deep_sleep_seconds": daily.get("deepSleepSeconds"),
        "light_sleep_seconds": daily.get("lightSleepSeconds"),
        "rem_sleep_seconds": daily.get("remSleepSeconds"),
        "awake_seconds": daily.get("awakeSleepSeconds"),
        "overall_score": extract_score(scores, "overall") or daily.get("sleepScoreOverall"),
        "quality_score": extract_score(scores, "quality"),
        "duration_score": extract_score(scores, "duration"),
        "rem_percentage_score": extract_score(scores, "remPercentage"),
        "restlessness_score": extract_score(scores, "restlessness"),
        "stress_score": extract_score(scores, "stress"),
        "revitalization_score": extract_score(scores, "revitalization"),
        "raw_json": safe_json(data),
    }
    row = validate_sleep(row)
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
    }
    row = validate_hrv(row)
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
        sb.table("body_composition").upsert(row, on_conflict="date,source").execute()
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
    """Sync activities using date-based endpoint. Deduplicates on garmin_activity_id."""
    ds = d.isoformat()
    # Use date-based endpoint for reliable backfill instead of offset-based
    activities = api_call(client.get_activities_by_date, ds, ds)
    if activities is None:
        # Fallback to offset-based if date-based endpoint unavailable
        activities = api_call(client.get_activities, 0, 20)
    if not activities:
        log.info("No activities for %s", ds)
        return True  # Not an error — some days have no activities

    count = 0
    for act in activities:
        act_date_str = act.get("startTimeLocal", "")[:10]
        if act_date_str != ds:
            continue

        garmin_id = str(act.get("activityId", ""))
        if not garmin_id:
            continue

        def _int(v):
            return int(v) if v is not None else None

        row = {
            "garmin_activity_id": garmin_id,
            "date": act_date_str,
            "activity_type": act.get("activityType", {}).get("typeKey", "unknown")
                if isinstance(act.get("activityType"), dict)
                else str(act.get("activityType", "unknown")),
            "activity_name": act.get("activityName"),
            "start_time": act.get("startTimeGMT") or act.get("startTimeLocal"),
            "duration_seconds": _int(act.get("duration")),
            "distance_meters": act.get("distance"),
            "calories": _int(act.get("calories")),
            "avg_hr": _int(act.get("averageHR")),
            "max_hr": _int(act.get("maxHR")),
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

        # Enrich with detailed per-activity data
        _sync_activity_details(client, sb, garmin_id)
        count += 1

    log.info("activities: %d upserted for %s", count, ds)
    return True


def _sync_activity_details(client: Garmin, sb, garmin_id: str):
    """Fetch and store HR zones, splits, and weather for a single activity."""
    hr_zones = api_call(client.get_activity_hr_in_timezones, garmin_id)
    splits = api_call(client.get_activity_splits, garmin_id)
    weather = api_call(client.get_activity_weather, garmin_id)

    row = {
        "garmin_activity_id": garmin_id,
        "hr_zones": safe_json(hr_zones),
        "splits": safe_json(splits),
        "weather": safe_json(weather),
        "raw_json": safe_json({
            "hr_zones": hr_zones,
            "splits": splits,
            "weather": weather,
        }),
    }
    sb.table("activity_details").upsert(row, on_conflict="garmin_activity_id").execute()
    log.info("  activity_details upserted for activity %s", garmin_id)


def sync_training_status(client: Garmin, sb, d: date) -> bool:
    """Training status: productive/detraining labels, acute/chronic load."""
    ds = d.isoformat()
    data = api_call(client.get_training_status, ds)
    if not data:
        log.warning("No training status for %s", ds)
        return False

    # Also fetch max metrics for detailed VO2max
    max_metrics = api_call(client.get_max_metrics, ds)

    vo2max_running = None
    vo2max_cycling = None
    if max_metrics:
        if isinstance(max_metrics, dict):
            for entry in max_metrics.get("maxMetricData", [max_metrics]):
                sport = entry.get("sport")
                vo2 = entry.get("generic", {}).get("vo2MaxPreciseValue") or entry.get("vo2MaxPreciseValue")
                if sport == "RUNNING":
                    vo2max_running = vo2
                elif sport == "CYCLING":
                    vo2max_cycling = vo2
        elif isinstance(max_metrics, list):
            for entry in max_metrics:
                sport = entry.get("sport")
                vo2 = entry.get("generic", {}).get("vo2MaxPreciseValue") or entry.get("vo2MaxPreciseValue")
                if sport == "RUNNING":
                    vo2max_running = vo2
                elif sport == "CYCLING":
                    vo2max_cycling = vo2

    if isinstance(data, dict):
        row = {
            "date": ds,
            "training_status": data.get("trainingStatus") or data.get("status"),
            "training_load_7d": data.get("acuteTrainingLoad") or data.get("shortTermTrainingLoad"),
            "training_load_28d": data.get("chronicTrainingLoad") or data.get("longTermTrainingLoad"),
            "training_load_balance": data.get("trainingLoadBalance"),
            "vo2max_running": vo2max_running,
            "vo2max_cycling": vo2max_cycling,
            "raw_json": safe_json(data),
        }
    else:
        log.info("Unexpected training status format for %s", ds)
        return False

    sb.table("training_status").upsert(row, on_conflict="date").execute()
    log.info("training_status upserted for %s", ds)
    return True


def sync_performance_scores(client: Garmin, sb, d: date) -> bool:
    """Endurance score, hill score, race predictions, fitness age."""
    ds = d.isoformat()

    endurance = api_call(client.get_endurance_score, ds, ds)
    hill = api_call(client.get_hill_score, ds, ds)
    races = api_call(client.get_race_predictions)
    fitness_age = api_call(client.get_fitnessage_data, ds)

    endurance_val = None
    if endurance:
        if isinstance(endurance, dict):
            entries = endurance.get("enduranceScoreDTOList", [endurance])
            endurance_val = entries[-1].get("overallScore") if entries else None
        elif isinstance(endurance, list) and endurance:
            endurance_val = endurance[-1].get("overallScore")

    hill_val = None
    if hill:
        if isinstance(hill, dict):
            entries = hill.get("hillScoreDTOList", [hill])
            hill_val = entries[-1].get("overallScore") if entries else None
        elif isinstance(hill, list) and hill:
            hill_val = hill[-1].get("overallScore")

    race_5k = race_10k = race_half = race_marathon = None
    if races:
        race_data = races
        if isinstance(races, dict):
            race_data = races.get("racePredictions", races)
        if isinstance(race_data, list):
            for r in race_data:
                dist = r.get("racePredictionType") or r.get("distance") or ""
                secs = r.get("predictedTime") or r.get("predictedTimeSeconds")
                if "5K" in str(dist).upper() or dist == "5000":
                    race_5k = secs
                elif "10K" in str(dist).upper() or dist == "10000":
                    race_10k = secs
                elif "HALF" in str(dist).upper() or dist == "21097":
                    race_half = secs
                elif "MARATHON" in str(dist).upper() or dist == "42195":
                    race_marathon = secs
        elif isinstance(race_data, dict):
            race_5k = race_data.get("5K") or race_data.get("fiveK")
            race_10k = race_data.get("10K") or race_data.get("tenK")
            race_half = race_data.get("halfMarathon")
            race_marathon = race_data.get("marathon")

    fitness_age_val = None
    if fitness_age:
        if isinstance(fitness_age, dict):
            fitness_age_val = fitness_age.get("fitnessAge") or fitness_age.get("chronologicalAge")

    # Only write if we have at least one value
    if all(v is None for v in [endurance_val, hill_val, race_5k, fitness_age_val]):
        log.info("No performance scores available for %s", ds)
        return False

    row = {
        "date": ds,
        "endurance_score": endurance_val,
        "hill_score": hill_val,
        "race_prediction_5k_seconds": race_5k,
        "race_prediction_10k_seconds": race_10k,
        "race_prediction_half_seconds": race_half,
        "race_prediction_marathon_seconds": race_marathon,
        "fitness_age": fitness_age_val,
        "raw_json": safe_json({
            "endurance": endurance,
            "hill": hill,
            "races": races,
            "fitness_age": fitness_age,
        }),
    }
    sb.table("performance_scores").upsert(row, on_conflict="date").execute()
    log.info("performance_scores upserted for %s", ds)
    return True


def sync_body_battery_events(client: Garmin, sb, d: date) -> bool:
    """Full body battery timeline + charge/drain events."""
    ds = d.isoformat()
    timeline = api_call(client.get_body_battery, ds, ds)
    events = api_call(client.get_body_battery_events, ds)

    if not timeline and not events:
        log.info("No body battery events for %s", ds)
        return False

    row = {
        "date": ds,
        "timeline": safe_json(timeline),
        "events": safe_json(events),
        "raw_json": safe_json({"timeline": timeline, "events": events}),
    }
    sb.table("body_battery_events").upsert(row, on_conflict="date").execute()
    log.info("body_battery_events upserted for %s", ds)
    return True


def sync_personal_records(client: Garmin, sb, d: date) -> bool:
    """Sync personal records (only once per run, not date-specific)."""
    records = api_call(client.get_personal_record)
    if not records:
        log.info("No personal records returned")
        return False

    if isinstance(records, dict):
        records = records.get("personalRecords", records.get("records", [records]))
    if not isinstance(records, list):
        records = [records]

    count = 0
    for rec in records:
        if not isinstance(rec, dict):
            continue
        record_type = rec.get("typeId") or rec.get("personalRecordType") or rec.get("prTypePk")
        if not record_type:
            continue
        row = {
            "record_type": str(record_type),
            "value": rec.get("value") or rec.get("prValue"),
            "activity_id": str(rec.get("activityId", "")) if rec.get("activityId") else None,
            "recorded_at": str(rec.get("prStartTimeLocalFormatted", "") or "")[:10] or None,
            "display_value": rec.get("displayValue") or rec.get("prDisplayValue"),
            "raw_json": safe_json(rec),
        }
        if not row["recorded_at"]:
            continue
        sb.table("personal_records").upsert(
            row, on_conflict="record_type,recorded_at"
        ).execute()
        count += 1

    log.info("personal_records: %d upserted", count)
    return True


# ---------------------------------------------------------------------------
# Main sync orchestrator
# ---------------------------------------------------------------------------

# Core daily sync functions (run for every date)
DAILY_SYNC_FUNCTIONS = [
    ("daily_metrics", sync_daily_metrics),
    ("sleep", sync_sleep),
    ("hrv", sync_hrv),
    ("body_composition", sync_body_composition),
    ("heart_rate_series", sync_heart_rate_series),
    ("stress_series", sync_stress_series),
    ("activities", sync_activities),
    ("training_status", sync_training_status),
    ("performance_scores", sync_performance_scores),
    ("body_battery_events", sync_body_battery_events),
]

# One-shot sync functions (run once per invocation, not per date)
ONESHOT_SYNC_FUNCTIONS = [
    ("personal_records", sync_personal_records),
]


def sync_date(client: Garmin, sb, d: date) -> dict:
    """Run all daily sync functions for a single date. Returns {table: success}."""
    log.info("=== Syncing %s ===", d.isoformat())
    results = {}
    for name, fn in DAILY_SYNC_FUNCTIONS:
        try:
            results[name] = fn(client, sb, d)
        except (GarminConnectTooManyRequestsError, RateLimitCooldownError, AuthExpiredError):
            raise  # abort entire sync immediately
        except Exception as exc:
            log.error("Error syncing %s for %s: %s", name, d.isoformat(), exc)
            results[name] = False
    return results


def main():
    parser = argparse.ArgumentParser(description="Sync Garmin data to Supabase")
    parser.add_argument("--date", type=str, help="Sync a specific date (YYYY-MM-DD)")
    parser.add_argument(
        "--range", nargs=2, metavar=("START", "END"),
        help="Sync a date range (YYYY-MM-DD YYYY-MM-DD)",
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
        # Default: sync both yesterday and today.
        # Yesterday has final data; today has morning metrics (body battery,
        # training readiness) needed by the coaching agent at 09:20.
        dates = [date.today() - timedelta(days=1), date.today()]

    log.info("Syncing %d date(s): %s → %s", len(dates), dates[0], dates[-1])

    # Connect — safe auth only, never calls login()
    try:
        client = get_safe_client(require_garminconnect=True)
    except RateLimitCooldownError as e:
        log.error("Auth blocked: %s", e)
        sys.exit(3)
    except AuthExpiredError as e:
        log.error("Auth failed: %s", e)
        sys.exit(2)

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Sync each date
    all_results = {}
    try:
        for i, d in enumerate(dates):
            all_results[d.isoformat()] = sync_date(client, sb, d)

        # Run one-shot syncs (personal records, etc.)
        for name, fn in ONESHOT_SYNC_FUNCTIONS:
            try:
                fn(client, sb, dates[-1])
            except (GarminConnectTooManyRequestsError, RateLimitCooldownError, AuthExpiredError):
                raise
            except Exception as exc:
                log.error("Error in one-shot sync %s: %s", name, exc)
    except GarminConnectTooManyRequestsError:
        log.error("429 Too Many Requests — Garmin rate limit hit, aborting sync")
        alert_slack(":rotating_light: *Garmin sync aborted* — 429 rate limit hit mid-sync. Cooldown needed.")
        save_tokens(client)
        sys.exit(3)
    except (RateLimitCooldownError, AuthExpiredError) as e:
        log.error("Auth/rate limit error mid-sync: %s", e)
        alert_slack(f":rotating_light: *Garmin sync aborted* — {e}")
        save_tokens(client)
        sys.exit(2)

    # Save tokens at end of session to capture any mid-session refreshes
    save_tokens(client)

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
        alert_slack(
            f":warning: *Garmin sync partially failed* — "
            f"{total_ok} succeeded, {total_fail} failed. Check logs."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

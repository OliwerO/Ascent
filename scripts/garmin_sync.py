#!/usr/bin/env python3
"""Garmin Connect → Supabase nightly sync script.

Syncs all available Garmin health/fitness data to Supabase tables.

Usage:
    python garmin_sync.py                          # sync yesterday + today
    python garmin_sync.py --date 2026-03-20        # sync specific date
    python garmin_sync.py --range 2026-03-01 2026-03-20  # sync date range
"""

import argparse
import fcntl
import json
import logging
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
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
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"]

API_DELAY = 1  # seconds between Garmin API calls
LOCK_FILE = PROJECT_ROOT / "logs" / "garmin_sync.lock"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("garmin_sync")


# ---------------------------------------------------------------------------
# Safe API helpers
# ---------------------------------------------------------------------------


MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds — retries at 2s, 4s, 8s


def api_call(fn, *args, **kwargs):
    """Call a Garmin API function with rate limiting and exponential backoff.

    Retries on 429 (TooManyRequests) up to MAX_RETRIES times with exponential
    backoff. Re-raises AuthExpiredError immediately (can't retry auth issues).
    Returns None on other transient failures.
    """
    time.sleep(API_DELAY)
    for attempt in range(MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except AuthExpiredError:
            raise  # auth is dead, can't retry
        except (GarminConnectTooManyRequestsError, RateLimitCooldownError) as exc:
            if attempt < MAX_RETRIES:
                wait = BACKOFF_BASE ** (attempt + 1)
                log.warning("Rate limited on %s (attempt %d/%d), retrying in %ds...",
                            fn.__name__, attempt + 1, MAX_RETRIES, wait)
                time.sleep(wait)
            else:
                log.error("Rate limited on %s after %d retries, skipping",
                          fn.__name__, MAX_RETRIES)
                return None
        except Exception as exc:
            log.warning("API call %s failed: %s", fn.__name__, exc)
            return None
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


def _safe_int(v):
    """Coerce to int, handling float strings like '88700.0'."""
    if v is None:
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


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


def sync_daily_metrics(client: Garmin, sb, d: date) -> bool | None:
    ds = d.isoformat()
    stats = api_call(client.get_stats, ds)
    if not stats:
        log.warning("No daily stats for %s", ds)
        return None

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
        # Explicit synced_at so upserts update the timestamp on every sync
        # (the column default only fires on INSERT, not UPDATE)
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
    row = validate_daily_metrics(row)
    sb.table("daily_metrics").upsert(row, on_conflict="date").execute()
    log.info("daily_metrics upserted for %s", ds)
    return True


def sync_sleep(client: Garmin, sb, d: date) -> bool | None:
    ds = d.isoformat()
    data = api_call(client.get_sleep_data, ds)
    if not data:
        log.warning("No sleep data for %s", ds)
        return None

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


def sync_hrv(client: Garmin, sb, d: date) -> bool | None:
    ds = d.isoformat()
    data = api_call(client.get_hrv_data, ds)
    if not data:
        log.warning("No HRV data for %s", ds)
        return None

    # Garmin sometimes returns {"hrvSummary": null}; .get() default doesn't apply
    # to explicit None values, so use `or` to fall through to the data dict.
    if isinstance(data, dict):
        summary = data.get("hrvSummary") or data
    else:
        summary = data
    baseline = (summary.get("baseline") if isinstance(summary, dict) else None) or {}

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


def sync_body_composition(client: Garmin, sb, d: date) -> bool | None:
    ds = d.isoformat()
    data = api_call(client.get_body_composition, ds, ds)
    if not data:
        log.warning("No body composition data for %s", ds)
        return None

    entries = data.get("dateWeightList", data.get("totalAverage", []))
    if isinstance(entries, dict):
        entries = [entries]
    if not entries:
        log.info("No body composition entries for %s", ds)
        return None

    for entry in entries if isinstance(entries, list) else [entries]:
        weight_grams = entry.get("weight")
        if weight_grams is None:
            continue
        row = {
            "date": ds,
            "weight_grams": _safe_int(weight_grams),
            "bmi": entry.get("bmi"),
            "body_fat_pct": entry.get("bodyFat"),
            "body_water_pct": entry.get("bodyWater"),
            "bone_mass_grams": _safe_int(entry.get("boneMass")),
            "muscle_mass_grams": _safe_int(entry.get("muscleMass")),
            "visceral_fat_rating": entry.get("visceralFat"),
            "metabolic_age": entry.get("metabolicAge"),
            "lean_body_mass_grams": _safe_int(entry.get("leanBodyMass")),
            "source": "garmin",
            "raw_json": safe_json(entry),
        }
        sb.table("body_composition").upsert(row, on_conflict="date,source").execute()
    log.info("body_composition upserted for %s", ds)
    return True


def sync_heart_rate_series(client: Garmin, sb, d: date) -> bool | None:
    ds = d.isoformat()
    data = api_call(client.get_heart_rates, ds)
    if not data:
        log.warning("No heart rate data for %s", ds)
        return None

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


def sync_stress_series(client: Garmin, sb, d: date) -> bool | None:
    ds = d.isoformat()
    data = api_call(client.get_stress_data, ds)
    if not data:
        log.warning("No stress data for %s", ds)
        return None

    readings = data.get("stressValuesArray", data) if isinstance(data, dict) else data

    row = {
        "date": ds,
        "readings": safe_json(readings) if readings else None,
    }
    sb.table("stress_series").upsert(row, on_conflict="date").execute()
    log.info("stress_series upserted for %s", ds)
    return True


def sync_activities(client: Garmin, sb, d: date) -> bool | None:
    """Sync activities using date-based endpoint. Deduplicates on garmin_activity_id."""
    ds = d.isoformat()
    # Use date-based endpoint for reliable backfill instead of offset-based
    activities = api_call(client.get_activities_by_date, ds, ds)
    if activities is None:
        # Fallback to offset-based if date-based endpoint unavailable
        activities = api_call(client.get_activities, 0, 20)
    if not activities:
        log.info("No activities for %s", ds)
        return None  # Empty, not a failure — distinct from True/False in summary

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

        # Sync per-set exercise data for strength activities
        try:
            _sync_training_session(client, sb, act, garmin_id)
        except Exception as exc:
            log.warning("Training session sync failed for %s: %s", garmin_id, exc)

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


# ---------------------------------------------------------------------------
# Garmin exercise name → exercises table mapping
# Maps Garmin's CATEGORY/NAME to our exercises.name
# ---------------------------------------------------------------------------

GARMIN_EXERCISE_MAP = {
    # Garmin (category, name) → exercises table name
    ("BENCH_PRESS", "INCLINE_DUMBBELL_BENCH_PRESS"): "Dumbbell Incline Press",
    ("BENCH_PRESS", "DUMBBELL_BENCH_PRESS"): "Dumbbell Bench Press",
    ("BENCH_PRESS", "BARBELL_BENCH_PRESS"): "Barbell Bench Press",
    ("BENCH_PRESS", "INCLINE_BARBELL_BENCH_PRESS"): "Incline Barbell Bench Press",
    ("ROW", "CHEST_SUPPORTED_DUMBBELL_ROW"): "Chest-Supported Row",
    ("ROW", "BARBELL_ROW"): "Barbell Row",
    ("ROW", "SINGLE_ARM_DUMBBELL_ROW"): "Single-Arm DB Row",
    ("ROW", "SEATED_CABLE_ROW"): "Seated Cable Row",
    ("ROW", "CABLE_ROW"): "Cable Row",
    ("SHOULDER_PRESS", "SINGLE_ARM_DUMBBELL_SHOULDER_PRESS"): "Landmine Press",
    ("SHOULDER_PRESS", "OVERHEAD_PRESS"): "Overhead Press",
    ("SHOULDER_PRESS", "BARBELL_OVERHEAD_PRESS"): "Overhead Press",
    ("SHOULDER_PRESS", "DUMBBELL_SHOULDER_PRESS"): "Overhead Press",
    ("PULL_UP", "CHIN_UP"): "Chin-Up",
    ("PULL_UP", "PULL_UP"): "Pull-Up",
    ("SQUAT", "BARBELL_BACK_SQUAT"): "Barbell Back Squat",
    ("SQUAT", "BARBELL_FRONT_SQUAT"): "Barbell Front Squat",
    ("SQUAT", "SPLIT_SQUAT"): "Bulgarian Split Squat",
    ("DEADLIFT", "CONVENTIONAL_DEADLIFT"): "Conventional Deadlift",
    ("DEADLIFT", "ROMANIAN_DEADLIFT"): "Romanian Deadlift",
    ("DEADLIFT", "TRAP_BAR_DEADLIFT"): "Trap Bar Deadlift",
    ("DEADLIFT", "SUMO_DEADLIFT"): "Sumo Deadlift",
    ("CORE", "KNEELING_AB_WHEEL"): "Ab Wheel Rollout",
    ("CORE", "DEAD_BUG"): "Dead Bugs",
    ("HIP_STABILITY", "QUADRUPED_WITH_LEG_LIFT"): "Bird Dogs",
    ("PLANK", "PLANK"): "Plank",
    ("PLANK", "COPENHAGEN_PLANK"): "Copenhagen Plank",
    ("CARRY", "FARMERS_WALK"): "Suitcase Carry",
    ("CARRY", "SUITCASE_CARRY"): "Suitcase Carry",
    ("TOTAL_BODY", "KETTLEBELL_SWING"): "Kettlebell Swing",
    ("TOTAL_BODY", "TURKISH_GET_UP"): "Turkish Get-Up",
    ("TOTAL_BODY", "KETTLEBELL_CLEAN_AND_PRESS"): "KB Clean & Press",
    ("SHOULDER_STABILITY", "KETTLEBELL_HALO"): "Kettlebell Halo",
    ("LATERAL_RAISE", "LATERAL_RAISE"): "Lateral Raise",
    ("CURL", "BARBELL_CURL"): "Barbell Curl",
    ("CURL", "DUMBBELL_CURL"): "Dumbbell Curl",
    ("CURL", "HAMMER_CURL"): "Hammer Curl",
    ("TRICEPS_EXTENSION", "TRICEP_PUSHDOWN"): "Tricep Pushdown",
    ("TRICEPS_EXTENSION", "SKULL_CRUSHER"): "Skull Crusher",
    ("LAT_PULL", "LAT_PULLDOWN"): "Lat Pulldown",
    ("HIP_RAISE", "HIP_THRUST"): "Hip Thrust",
    ("LEG_CURL", "LEG_CURL"): "Leg Curl",
    ("LEG_EXTENSION", "LEG_EXTENSION"): "Leg Extension",
    ("CALF_RAISE", "CALF_RAISE"): "Calf Raise",
    ("LUNGE", "WALKING_LUNGE"): "Walking Lunge",
    ("FLY", "CABLE_FLY"): "Cable Fly",
    ("DIP", "DIP"): "Dip",
    ("SQUAT", "GOBLET_SQUAT"): "Barbell Front Squat",
    ("LEG_PRESS", "LEG_PRESS"): "Leg Press",
    ("ROW", "T_BAR_ROW"): "Barbell Row",
    ("ROW", "INVERTED_ROW"): "Barbell Row",
    ("BENCH_PRESS", "CLOSE_GRIP_BENCH_PRESS"): "Barbell Bench Press",
    ("BENCH_PRESS", "PUSH_UP"): "Push-Up",
    ("SHOULDER_PRESS", "ARNOLD_PRESS"): "Overhead Press",
    ("LATERAL_RAISE", "DUMBBELL_LATERAL_RAISE"): "Lateral Raise",
    ("CURL", "CABLE_CURL"): "Barbell Curl",
    ("TRICEPS_EXTENSION", "OVERHEAD_TRICEP_EXTENSION"): "Overhead Tricep Extension",
    ("CORE", "PLANK"): "Plank",
    ("CORE", "PALLOF_PRESS"): "Pallof Walkouts",
    ("CORE", "COPENHAGEN_PLANK"): "Copenhagen Plank",
    ("CORE", "HANGING_LEG_RAISE"): "Hanging Leg Raise",
    ("HIP_RAISE", "GLUTE_BRIDGE"): "Hip Thrust",
    ("TOTAL_BODY", "CLEAN_AND_JERK"): "KB Clean & Press",
    ("SHRUG", "BARBELL_SHRUG"): "Barbell Row",
    ("FACE_PULL", "FACE_PULL"): "Face Pull",
}

# Cache: exercises.name → exercises.id (populated once per sync run)
_exercise_id_cache: dict[str, int] = {}


def _get_exercise_id(sb, exercise_name: str) -> int | None:
    """Look up exercise ID by name, with caching."""
    if exercise_name in _exercise_id_cache:
        return _exercise_id_cache[exercise_name]

    if not _exercise_id_cache:
        # Load all exercises once
        resp = sb.table("exercises").select("id, name").execute()
        for row in resp.data:
            _exercise_id_cache[row["name"]] = row["id"]

    return _exercise_id_cache.get(exercise_name)


def _resolve_garmin_exercise(category: str, name: str) -> str | None:
    """Map a Garmin exercise (category, name) to our exercises table name."""
    # Direct mapping
    mapped = GARMIN_EXERCISE_MAP.get((category, name))
    if mapped:
        return mapped

    # Try category-only fallback (less specific)
    for (cat, _), ex_name in GARMIN_EXERCISE_MAP.items():
        if cat == category:
            return ex_name

    return None


def _sync_training_session(client: Garmin, sb, act: dict, garmin_id: str):
    """Create training_sessions + training_sets from a strength activity's exercise sets."""
    activity_type = (
        act.get("activityType", {}).get("typeKey", "")
        if isinstance(act.get("activityType"), dict)
        else str(act.get("activityType", ""))
    )
    if activity_type != "strength_training":
        return

    act_date = act.get("startTimeLocal", "")[:10]
    if not act_date:
        return

    # Fetch per-set exercise data from Garmin
    try:
        exercise_data = api_call(client.get_activity_exercise_sets, int(garmin_id))
    except (ValueError, TypeError):
        log.warning("Invalid garmin_id for exercise sets: %s", garmin_id)
        return
    if not exercise_data:
        log.warning("No exercise sets data for activity %s", garmin_id)
        return

    exercise_sets = exercise_data.get("exerciseSets", [])
    if not exercise_sets:
        return

    # Calculate totals from the set data
    working_sets = [s for s in exercise_sets if s.get("setType") != "REST"
                    and s.get("exercises") and s["exercises"][0].get("category") != "WARM_UP"]
    total_volume = sum(
        (s.get("weight", 0) or 0) / 1000.0 * (s.get("repetitionCount", 0) or 0)
        for s in working_sets
    )
    duration_sec = act.get("duration")
    duration_min = int(duration_sec / 60) if duration_sec else None

    # Upsert training_sessions (deduplicate on garmin_activity_id)
    # First check if one already exists
    existing = sb.table("training_sessions").select("id").eq(
        "garmin_activity_id", garmin_id
    ).execute()

    if existing.data:
        session_id = existing.data[0]["id"]
        sb.table("training_sessions").update({
            "name": act.get("activityName"),
            "duration_minutes": duration_min,
            "total_volume_kg": round(total_volume, 1) if total_volume else None,
            "total_sets": len(working_sets),
        }).eq("id", session_id).execute()
    else:
        resp = sb.table("training_sessions").insert({
            "date": act_date,
            "garmin_activity_id": garmin_id,
            "name": act.get("activityName"),
            "duration_minutes": duration_min,
            "total_volume_kg": round(total_volume, 1) if total_volume else None,
            "total_sets": len(working_sets),
        }).execute()
        session_id = resp.data[0]["id"]

    # Delete existing training_sets for this session (idempotent re-sync)
    sb.table("training_sets").delete().eq("session_id", session_id).execute()

    # Insert training_sets from Garmin exercise data
    set_number = 0
    for garmin_set in exercise_sets:
        if garmin_set.get("setType") == "REST":
            continue

        exercises = garmin_set.get("exercises", [])
        if not exercises:
            continue

        garmin_cat = exercises[0].get("category", "")
        garmin_name = exercises[0].get("name", "")
        is_warmup = garmin_cat == "WARM_UP"

        exercise_name = _resolve_garmin_exercise(garmin_cat, garmin_name)
        if not exercise_name:
            log.warning("Unmapped Garmin exercise: %s/%s", garmin_cat, garmin_name)
            continue

        exercise_id = _get_exercise_id(sb, exercise_name)
        if not exercise_id:
            log.warning("Exercise not in DB: %s (from %s/%s)", exercise_name, garmin_cat, garmin_name)
            continue

        set_number += 1
        weight_grams = garmin_set.get("weight")
        weight_kg = weight_grams / 1000.0 if weight_grams and weight_grams > 0 else None
        reps = garmin_set.get("repetitionCount")

        sb.table("training_sets").insert({
            "session_id": session_id,
            "exercise_id": exercise_id,
            "set_number": set_number,
            "set_type": "warmup" if is_warmup else "working",
            "weight_kg": weight_kg,
            "reps": reps,
        }).execute()

    # Mark matching planned_workout as completed and link the activity ID
    planned = sb.table("planned_workouts").select("id, status").eq(
        "scheduled_date", act_date
    ).in_("status", ["planned", "pushed", "adjusted"]).execute()
    if planned.data:
        sb.table("planned_workouts").update({
            "status": "completed",
            "actual_garmin_activity_id": garmin_id,
        }).eq(
            "id", planned.data[0]["id"]
        ).execute()
        log.info("  planned_workout %d marked completed (activity %s)", planned.data[0]["id"], garmin_id)

    log.info("  training_session upserted (id=%d, %d sets) for activity %s",
             session_id, set_number, garmin_id)

    # Check for new e1RM personal records
    _check_prs(sb, session_id, act_date)


def _check_prs(sb, session_id: int, act_date: str):
    """Check if any working sets in this session set a new estimated 1RM PR."""
    sets = sb.table("training_sets").select(
        "id,exercise_id,weight_kg,reps,set_type"
    ).eq("session_id", session_id).eq("set_type", "working").execute().data

    if not sets:
        return

    # Group by exercise, find best e1RM per exercise
    from collections import defaultdict
    best_by_exercise: dict[int, tuple[float, int]] = {}  # exercise_id → (e1rm, set_id)
    for s in sets:
        w = s.get("weight_kg")
        r = s.get("reps")
        if not w or not r or r < 1:
            continue
        # Epley formula
        e1rm = w * (1 + r / 30.0) if r > 1 else w
        eid = s["exercise_id"]
        if eid not in best_by_exercise or e1rm > best_by_exercise[eid][0]:
            best_by_exercise[eid] = (round(e1rm, 1), s["id"])

    for exercise_id, (e1rm, set_id) in best_by_exercise.items():
        # Check existing PR for this exercise
        existing = sb.table("exercise_prs").select("id,value").eq(
            "exercise_id", exercise_id
        ).eq("pr_type", "e1rm").order("value", desc=True).limit(1).execute().data

        if existing and existing[0]["value"] >= e1rm:
            continue  # not a new PR

        # New PR — insert it
        sb.table("exercise_prs").insert({
            "exercise_id": exercise_id,
            "pr_type": "e1rm",
            "value": e1rm,
            "date": act_date,
            "set_id": set_id,
        }).execute()

        # Look up exercise name for logging
        ex = sb.table("exercises").select("name").eq("id", exercise_id).limit(1).execute().data
        name = ex[0]["name"] if ex else f"exercise #{exercise_id}"
        prev = f" (prev: {existing[0]['value']}kg)" if existing else " (first tracked)"
        log.info("  NEW PR: %s e1RM = %.1f kg%s", name, e1rm, prev)


def sync_training_status(client: Garmin, sb, d: date) -> bool | None:
    """Training status: productive/detraining labels, acute/chronic load."""
    ds = d.isoformat()
    data = api_call(client.get_training_status, ds)
    if not data:
        log.warning("No training status for %s", ds)
        return None

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
        return None

    sb.table("training_status").upsert(row, on_conflict="date").execute()
    log.info("training_status upserted for %s", ds)
    return True


def sync_performance_scores(client: Garmin, sb, d: date) -> bool | None:
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
        return None

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


def sync_body_battery_events(client: Garmin, sb, d: date) -> bool | None:
    """Full body battery timeline + charge/drain events."""
    ds = d.isoformat()
    timeline = api_call(client.get_body_battery, ds, ds)
    events = api_call(client.get_body_battery_events, ds)

    if not timeline and not events:
        log.info("No body battery events for %s", ds)
        return None

    row = {
        "date": ds,
        "timeline": safe_json(timeline),
        "events": safe_json(events),
        "raw_json": safe_json({"timeline": timeline, "events": events}),
    }
    sb.table("body_battery_events").upsert(row, on_conflict="date").execute()
    log.info("body_battery_events upserted for %s", ds)
    return True


def sync_personal_records(client: Garmin, sb, d: date) -> bool | None:
    """Sync personal records (only once per run, not date-specific)."""
    records = api_call(client.get_personal_record)
    if not records:
        log.info("No personal records returned")
        return None

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
# Data quality tracking
# ---------------------------------------------------------------------------


def sync_data_quality(client: Garmin, sb, d: date) -> bool | None:
    """Compute and write data quality metrics for a given date.

    Checks which key tables have data for this date and estimates wear hours
    from available signals. Writes to daily_data_quality.
    """
    ds = d.isoformat()

    # Check which data sources exist for this date
    has_sleep = bool(
        sb.table("sleep").select("id").eq("date", ds).limit(1).execute().data
    )
    has_metrics = bool(
        sb.table("daily_metrics").select("id").eq("date", ds).limit(1).execute().data
    )
    has_hrv = bool(
        sb.table("hrv").select("id").eq("date", ds).limit(1).execute().data
    )
    has_hr_series = False
    hr_hours = 0
    hr_rows = sb.table("heart_rate_series").select("readings").eq("date", ds).limit(1).execute().data
    if hr_rows and hr_rows[0].get("readings"):
        has_hr_series = True
        readings = hr_rows[0]["readings"]
        if isinstance(readings, list):
            # Each reading is typically a 15-second or 1-minute sample.
            # Estimate hours of coverage: count non-null entries and divide
            # by expected samples per hour (~60 for 1-min, ~240 for 15-sec).
            non_null = 0
            for r in readings:
                if r is None:
                    continue
                if isinstance(r, dict):
                    if r.get("value") or r.get("heartRate") or r.get("hr"):
                        non_null += 1
                elif isinstance(r, (int, float)) and r > 0:
                    non_null += 1
            # Conservative: assume 1-minute samples → 60/hr
            hr_hours = round(non_null / 60, 1) if non_null > 0 else 0

    # Estimate wear hours
    # Sleep data implies ~6-8h of nighttime wear; HR series gives daytime coverage
    wear_hours = 0.0
    if has_sleep:
        # Fetch actual sleep duration
        sleep_rows = sb.table("sleep").select("total_sleep_seconds").eq("date", ds).limit(1).execute().data
        sleep_secs = (sleep_rows[0].get("total_sleep_seconds") or 0) if sleep_rows else 0
        wear_hours += min(sleep_secs / 3600, 10)  # cap nighttime at 10h
    if hr_hours > 0:
        wear_hours += min(hr_hours, 16)  # cap daytime at 16h
    elif has_metrics:
        # If we have daily metrics but no HR series, assume ~8h daytime wear
        wear_hours += 8

    wear_hours = round(min(wear_hours, 24), 1)

    # Completeness score: percentage of key data sources present
    sources = [has_sleep, has_metrics, has_hrv, has_hr_series]
    completeness_score = round(sum(sources) / len(sources), 2)

    # Find largest gap in HR data (if available)
    max_gap_minutes = None
    if has_hr_series and isinstance(readings, list) and len(readings) > 1:
        # Simple gap detection: find longest run of nulls/missing
        current_gap = 0
        max_gap = 0
        for r in readings:
            is_valid = (isinstance(r, dict) and (r.get("value") or r.get("heartRate"))) or (
                isinstance(r, (int, float)) and r > 0
            )
            if not is_valid:
                current_gap += 1
            else:
                max_gap = max(max_gap, current_gap)
                current_gap = 0
        max_gap = max(max_gap, current_gap)
        max_gap_minutes = max_gap  # assuming 1-min samples

    row = {
        "date": ds,
        "wear_hours": wear_hours,
        "completeness_score": completeness_score,
        "max_gap_minutes": max_gap_minutes,
        "data_issues": json.dumps({
            "has_sleep": has_sleep,
            "has_metrics": has_metrics,
            "has_hrv": has_hrv,
            "has_hr_series": has_hr_series,
            "hr_coverage_hours": hr_hours,
        }),
    }
    sb.table("daily_data_quality").upsert(row, on_conflict="date").execute()
    log.info("daily_data_quality upserted for %s (wear=%.1fh, completeness=%.0f%%)",
             ds, wear_hours, completeness_score * 100)
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
    ("data_quality", sync_data_quality),  # must be last — reads from tables above
]

# When syncing the default daily run, also re-pull activity metadata for the
# last N days so that activity renames done in Garmin Connect propagate.
# Upsert is keyed on garmin_activity_id so this is safe and idempotent.
ACTIVITY_REFRESH_WINDOW_DAYS = 14

# One-shot sync functions (run once per invocation, not per date)
ONESHOT_SYNC_FUNCTIONS = [
    ("personal_records", sync_personal_records),
]


def sync_date(client: Garmin, sb, d: date) -> dict:
    """Run all daily sync functions for a single date.

    Returns {table_name: result} where result is one of:
      True  — wrote rows
      None  — no data available for that date (NOT a failure)
      False — exception or actual API failure
    """
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
    # Prevent concurrent syncs (nightly cron vs on-demand)
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log.warning("Another garmin_sync is already running — exiting")
        sys.exit(0)

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

        # Refresh activity metadata for the last N days so renames propagate.
        # Skipped on bulk backfill (--range) since that already covers the window.
        if not args.range:
            today = date.today()
            log.info(
                "Refreshing activity metadata for last %d days (rename window)",
                ACTIVITY_REFRESH_WINDOW_DAYS,
            )
            already_synced = {d.isoformat() for d in dates}
            for offset in range(1, ACTIVITY_REFRESH_WINDOW_DAYS + 1):
                refresh_d = today - timedelta(days=offset)
                if refresh_d.isoformat() in already_synced:
                    continue
                try:
                    sync_activities(client, sb, refresh_d)
                except (GarminConnectTooManyRequestsError, RateLimitCooldownError, AuthExpiredError):
                    raise
                except Exception as exc:
                    log.warning("Activity refresh failed for %s: %s", refresh_d, exc)
                time.sleep(1)  # respect rate limit

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

    # Summary — three-state contract per sync function:
    #   True  → wrote rows
    #   None  → no data on that date (NOT a failure)
    #   False → exception or actual API failure (set in sync_date's except)
    failed_items: list[str] = []
    empty_items: list[str] = []
    ok_count = 0
    for day_iso, day_results in all_results.items():
        for name, v in day_results.items():
            if v is True:
                ok_count += 1
            elif v is None:
                empty_items.append(f"{name} ({day_iso})")
            elif v is False:
                failed_items.append(f"{name} ({day_iso})")
    log.info(
        "Sync complete: %d succeeded, %d empty, %d failed",
        ok_count, len(empty_items), len(failed_items),
    )

    if failed_items:
        log.warning("Failed: %s", ", ".join(failed_items))
        lines = [":warning: *Garmin sync — partial failure*"]
        lines.append(f"Failed: {', '.join(failed_items)}")
        if empty_items:
            lines.append(f"Empty (normal): {', '.join(empty_items)}")
        lines.append(f"{ok_count} endpoints synced OK.")
        alert_slack("\n".join(lines))
        sys.exit(1)


if __name__ == "__main__":
    main()

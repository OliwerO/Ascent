# Terra API → Supabase Field Mapping

> Generated 2026-04-02. Maps Terra's normalized schema to existing Ascent Supabase columns.

## daily_metrics

| Supabase Column | Terra Source | Path | Notes |
|---|---|---|---|
| date | metadata | `metadata.start_time[:10]` | |
| total_steps | distance_data | `distance_data.summary.steps` | |
| total_distance_meters | distance_data | `distance_data.summary.distance_meters` | |
| active_calories | calories_data | `calories_data.net_activity_calories` | |
| total_calories | calories_data | `calories_data.total_burned_calories` | |
| floors_ascended | distance_data | `distance_data.summary.floors_climbed` | |
| floors_descended | - | N/A | Not in Terra |
| intensity_minutes | - | N/A | Garmin-proprietary |
| moderate_intensity_minutes | - | N/A | Garmin-proprietary |
| vigorous_intensity_minutes | - | N/A | Garmin-proprietary |
| resting_hr | heart_rate_data | `heart_rate_data.summary.resting_hr_bpm` | |
| min_hr | heart_rate_data | `heart_rate_data.summary.min_hr_bpm` | |
| max_hr | heart_rate_data | `heart_rate_data.summary.max_hr_bpm` | |
| avg_hr | heart_rate_data | `heart_rate_data.summary.avg_hr_bpm` | |
| avg_stress_level | stress_data | `stress_data.avg_stress_level` | |
| max_stress_level | stress_data | `stress_data.max_stress_level` | |
| rest_stress_duration | stress_data | `stress_data.rest_stress_duration_seconds` | |
| activity_stress_duration | stress_data | `stress_data.activity_stress_duration_seconds` | |
| body_battery_highest | stress_data | `max(stress_data.body_battery_samples[].level)` | Derived |
| body_battery_lowest | stress_data | `min(stress_data.body_battery_samples[].level)` | Derived |
| body_battery_charged | - | N/A | Would need delta calc |
| body_battery_drained | - | N/A | Would need delta calc |
| training_readiness_score | scores | `scores.recovery` | Approximate mapping |
| training_load | - | N/A | Garmin-proprietary |
| vo2max | - | N/A | Not in daily endpoint |
| spo2_avg | oxygen_data | `oxygen_data.avg_saturation_percentage` | |
| respiration_avg | - | N/A | In detailed samples only |

## sleep

| Supabase Column | Terra Source | Path | Notes |
|---|---|---|---|
| date | metadata | `metadata.start_time[:10]` | |
| sleep_start | metadata | `metadata.start_time` | |
| sleep_end | metadata | `metadata.end_time` | |
| total_sleep_seconds | sleep_durations_data | `asleep.duration_asleep_state_seconds` | |
| deep_sleep_seconds | sleep_durations_data | `asleep.duration_deep_sleep_state_seconds` | |
| light_sleep_seconds | sleep_durations_data | `asleep.duration_light_sleep_state_seconds` | |
| rem_sleep_seconds | sleep_durations_data | `asleep.duration_REM_sleep_state_seconds` | |
| awake_seconds | sleep_durations_data | `awake.duration_awake_state_seconds` | |
| overall_score | scores | `scores.sleep_score` | |
| quality_score | - | N/A | Garmin sub-score |
| duration_score | - | N/A | Garmin sub-score |
| rem_percentage_score | - | N/A | Garmin sub-score |
| restlessness_score | - | N/A | Garmin sub-score |
| stress_score | - | N/A | Garmin sub-score |
| revitalization_score | - | N/A | Garmin sub-score |

## hrv

| Supabase Column | Terra Source | Path | Notes |
|---|---|---|---|
| date | - | Query date | |
| weekly_avg | daily | `daily.heart_rate_data.summary.avg_hrv_rmssd` | Day's HRV, not true 7-day avg |
| last_night_avg | sleep | `sleep.heart_rate_data.summary.avg_hrv_rmssd` | Overnight HRV |
| last_night_5min_high | - | N/A | Garmin-specific |
| baseline_low_upper | - | N/A | Garmin-specific |
| baseline_balanced_low | - | N/A | Garmin-specific |
| baseline_balanced_upper | - | N/A | Garmin-specific |
| status | - | N/A | Garmin-specific label |

## body_composition

| Supabase Column | Terra Source | Path | Notes |
|---|---|---|---|
| date | - | Query date | |
| weight_grams | body | `measurements[0].weight_kg * 1000` | Converted |
| bmi | body | `measurements[0].BMI` | |
| body_fat_pct | body | `measurements[0].bodyfat_percentage` | |
| body_water_pct | body | `measurements[0].water_percentage` | |
| bone_mass_grams | body | `measurements[0].bone_mass_g` | |
| muscle_mass_grams | body | `measurements[0].muscle_mass_g` | |
| visceral_fat_rating | - | N/A | Not in Terra |
| metabolic_age | body | `measurements[0].estimated_fitness_age` | Approximate |
| lean_body_mass_grams | body | `measurements[0].lean_mass_g` | |
| source | - | `"terra"` | Hardcoded |

## activities

| Supabase Column | Terra Source | Path | Notes |
|---|---|---|---|
| garmin_activity_id | metadata | `metadata.summary_id` | Terra's unique ID |
| date | metadata | `metadata.start_time[:10]` | |
| activity_type | metadata | `metadata.type` (mapped via lookup) | Numeric → string |
| activity_name | metadata | `metadata.name` | |
| start_time | metadata | `metadata.start_time` | |
| duration_seconds | metadata | `end_time - start_time` | Calculated |
| distance_meters | distance_data | `distance_data.summary.distance_meters` | |
| calories | calories_data | `calories_data.total_burned_calories` | |
| avg_hr | heart_rate_data | `heart_rate_data.summary.avg_hr_bpm` | |
| max_hr | heart_rate_data | `heart_rate_data.summary.max_hr_bpm` | |
| avg_speed | movement_data | `movement_data.avg_speed_meters_per_second` | |
| max_speed | movement_data | `movement_data.max_speed_meters_per_second` | |
| elevation_gain | distance_data | `distance_data.summary.elevation.gain_actual_meters` | |
| elevation_loss | distance_data | `distance_data.summary.elevation.loss_actual_meters` | |
| training_effect_aerobic | - | N/A | Garmin-proprietary |
| training_effect_anaerobic | - | N/A | Garmin-proprietary |
| vo2max | - | N/A | Not in activity response |
| hr_zones | heart_rate_data | `heart_rate_data.summary.hr_zone_data` | |

## Coverage Summary

| Category | Covered | Not Available via Terra |
|---|---|---|
| Core vitals | Steps, HR, calories, distance, floors | Intensity minutes |
| Sleep | Duration, stages, score | Garmin sub-scores (quality, duration, REM%, restlessness, stress, revitalization) |
| HRV | Overnight + daily rMSSD | Baseline bands, status label, 5min high |
| Stress | Avg, max, durations, body battery | Charged/drained deltas |
| Body comp | Weight, BF%, BMI, muscle, bone, water | Visceral fat rating |
| Activities | Type, duration, HR, distance, elevation | Training effect, VO2max per activity |
| Training | Recovery score | Training load, readiness score, training status |

All raw JSON is preserved in `raw_json` columns for future extraction of additional fields.

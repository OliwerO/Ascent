# Garmin Auth Spike — Test Plan

## Objective

Validate that we can reliably authenticate with Garmin Connect and perform both read (pull activities) and write (push workouts) operations from a Python script. This is the critical dependency for Phases 7-10.

-----

## Libraries to Test

Test in order of preference. Stop at the first one that works reliably for both read AND write.

### Option A: `garth` (OAuth-based, recommended)

More modern library that uses Garmin's OAuth flow and stores tokens that can be refreshed.

```bash
pip install garth
```

```python
import garth
import json

# --- AUTH TEST ---
# First-time login (interactive, saves tokens)
garth.login("your_email@example.com", "your_password")
garth.save("~/.garth")  # Persists tokens to disk

# Subsequent runs (token refresh, no password needed)
# garth.resume("~/.garth")

# --- READ TEST: Pull today's daily summary ---
try:
    daily = garth.connectapi(f"/usersummary-service/usersummary/daily/2026-03-28")
    print("✅ Daily summary:", json.dumps(daily, indent=2)[:500])
except Exception as e:
    print(f"❌ Daily summary failed: {e}")

# --- READ TEST: Pull recent activities ---
try:
    activities = garth.connectapi("/activitylist-service/activities/search/activities", params={"limit": 5})
    for a in activities:
        print(f"✅ Activity: {a.get('activityName')} | {a.get('startTimeLocal')} | {a.get('activityType', {}).get('typeKey')}")
except Exception as e:
    print(f"❌ Activities failed: {e}")

# --- READ TEST: Pull HRV data ---
try:
    hrv = garth.connectapi("/hrv-service/hrv/daily/2026-03-28")
    print("✅ HRV data:", json.dumps(hrv, indent=2)[:500])
except Exception as e:
    print(f"❌ HRV failed: {e}")

# --- READ TEST: Pull body battery ---
try:
    bb = garth.connectapi("/usersummary-service/stats/body-battery/daily/2026-03-28/2026-03-28")
    print("✅ Body battery:", json.dumps(bb, indent=2)[:500])
except Exception as e:
    print(f"❌ Body battery failed: {e}")

# --- READ TEST: Pull sleep data ---
try:
    sleep = garth.connectapi("/wellness-service/wellness/dailySleepData/2026-03-27")
    print("✅ Sleep:", json.dumps(sleep, indent=2)[:500])
except Exception as e:
    print(f"❌ Sleep failed: {e}")
```

### Option B: `garminconnect` (session-based)

More established library, but relies on session cookies that expire.

```bash
pip install garminconnect
```

```python
from garminconnect import Garmin
import json

# --- AUTH TEST ---
try:
    client = Garmin("your_email@example.com", "your_password")
    client.login()
    print("✅ Login successful")

    # Save session for reuse
    session_data = client.session_data
    with open("~/.garmin_session.json", "w") as f:
        json.dump(session_data, f)
    print("✅ Session saved")
except Exception as e:
    print(f"❌ Login failed: {e}")
    print("   If this fails with CAPTCHA or MFA issues, try Option A (garth)")
    exit(1)

# --- READ TEST: Recent activities ---
try:
    activities = client.get_activities(0, 5)
    for a in activities:
        print(f"✅ Activity: {a['activityName']} | {a['startTimeLocal']}")
except Exception as e:
    print(f"❌ Activities failed: {e}")

# --- READ TEST: Daily stats ---
try:
    stats = client.get_stats("2026-03-28")
    print(f"✅ Steps: {stats.get('totalSteps')}, Resting HR: {stats.get('restingHeartRate')}")
except Exception as e:
    print(f"❌ Daily stats failed: {e}")

# --- READ TEST: HRV ---
try:
    hrv = client.get_hrv_data("2026-03-28")
    print(f"✅ HRV: {json.dumps(hrv, indent=2)[:300]}")
except Exception as e:
    print(f"❌ HRV failed: {e}")

# --- SESSION RESUME TEST ---
try:
    client2 = Garmin()
    with open("~/.garmin_session.json", "r") as f:
        saved = json.load(f)
    client2.session_data = saved
    client2.login()
    activities2 = client2.get_activities(0, 1)
    print(f"✅ Session resume works: {activities2[0]['activityName']}")
except Exception as e:
    print(f"❌ Session resume failed: {e}")
```

### Option C: `garth` + `fit_tool` hybrid

If neither library supports pushing structured workouts reliably, we generate FIT files and upload them.

```bash
pip install garth fit-tool
```

```python
from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.workout_message import WorkoutMessage
from fit_tool.profile.messages.workout_step_message import WorkoutStepMessage
from fit_tool.profile.profile_type import Sport, Intensity, WorkoutStepDuration, WorkoutStepTarget
import garth

# --- WRITE TEST: Create a simple strength workout FIT file ---
builder = FitFileBuilder()

# Workout header
workout = WorkoutMessage()
workout.sport = Sport.STRENGTH_TRAINING
workout.num_valid_steps = 2
workout.wkt_name = "Test Workout - Bench Press"
builder.add(workout)

# Step 1: Exercise (3 sets, open duration)
step1 = WorkoutStepMessage()
step1.message_index = 0
step1.wkt_step_name = "Bench Press"
step1.intensity = Intensity.ACTIVE
step1.duration_type = WorkoutStepDuration.OPEN  # User ends set manually
step1.target_type = WorkoutStepTarget.OPEN
builder.add(step1)

# Step 2: Rest
step2 = WorkoutStepMessage()
step2.message_index = 1
step2.wkt_step_name = "Rest"
step2.intensity = Intensity.REST
step2.duration_type = WorkoutStepDuration.TIME
step2.duration_value = 180000  # 180 seconds in ms
step2.target_type = WorkoutStepTarget.OPEN
builder.add(step2)

fit_bytes = builder.build()
with open("/tmp/test_workout.fit", "wb") as f:
    f.write(fit_bytes.getvalue())
print("✅ FIT workout file created: /tmp/test_workout.fit")

# --- UPLOAD TEST: Push FIT file to Garmin Connect ---
garth.resume("~/.garth")

try:
    with open("/tmp/test_workout.fit", "rb") as f:
        fit_data = f.read()

    # Upload workout
    result = garth.connectapi(
        "/workout-service/workout/FIT",
        method="POST",
        body=fit_data,
        headers={"Content-Type": "application/octet-stream"}
    )
    print(f"✅ Workout uploaded: {result}")
except Exception as e:
    print(f"❌ FIT upload failed: {e}")
    print("   Fallback: manually upload /tmp/test_workout.fit via Garmin Connect web")

# --- ALTERNATIVE WRITE TEST: JSON-based workout creation ---
try:
    workout_json = {
        "sportType": {"sportTypeId": 4, "sportTypeKey": "strength_training"},
        "workoutName": "Ascent Test Workout",
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": {"sportTypeId": 4, "sportTypeKey": "strength_training"},
                "workoutSteps": [
                    {
                        "type": "ExecutableStepDTO",
                        "stepOrder": 1,
                        "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
                        "exerciseCategory": {"exerciseCategoryId": 10, "exerciseName": "BENCH_PRESS"},
                        "numberOfSets": 4,
                        "repeatType": None,
                        "weight": {"value": 80.0, "unitKey": "kg"},
                        "repeatValue": 6  # reps
                    }
                ]
            }
        ]
    }

    result = garth.connectapi(
        "/workout-service/workout",
        method="POST",
        body=workout_json
    )
    print(f"✅ JSON workout created: {result}")

    # Schedule it for a specific date
    workout_id = result.get("workoutId")
    if workout_id:
        schedule_result = garth.connectapi(
            f"/workout-service/schedule/{workout_id}",
            method="POST",
            body={"date": "2026-04-01"}
        )
        print(f"✅ Workout scheduled: {schedule_result}")
except Exception as e:
    print(f"❌ JSON workout creation failed: {e}")
```

-----

## Write Test: Verify Workout Appears on Watch

After a successful upload:

1. Open Garmin Connect app on phone
2. Go to Training → Workouts
3. Confirm "Ascent Test Workout" (or "Test Workout - Bench Press") appears
4. Sync watch
5. On watch: navigate to Strength activity → select the workout
6. Confirm exercise name and target weight/reps display correctly

**Critical checks:**

- [ ] Exercise name shows correctly
- [ ] Target weight is pre-filled (you shouldn't have to look it up)
- [ ] Target reps are shown
- [ ] Number of sets is correct
- [ ] Rest timer works between sets
- [ ] After completing → activity syncs back to Garmin Connect with per-set data

-----

## Evaluation Criteria

Rate each option:

|Criteria                           |Option A (garth)|Option B (garminconnect)|Option C (FIT hybrid)|
|-----------------------------------|----------------|------------------------|---------------------|
|Auth succeeds                      |✅/❌             |✅/❌                     |✅/❌                  |
|Token persists across sessions     |✅/❌             |✅/❌                     |✅/❌                  |
|Pull activities                    |✅/❌             |✅/❌                     |✅/❌                  |
|Pull HRV/body battery/sleep        |✅/❌             |✅/❌                     |✅/❌                  |
|Push structured workout            |✅/❌             |✅/❌                     |✅/❌                  |
|Workout shows on watch with weights|✅/❌             |✅/❌                     |✅/❌                  |
|Completed activity links back      |✅/❌             |✅/❌                     |✅/❌                  |
|Custom exercise names supported    |✅/❌             |✅/❌                     |✅/❌                  |

**Winner goes into Phase 7 implementation.**

-----

## Troubleshooting

**CAPTCHA / 403 errors on login:**

- Garmin sometimes triggers CAPTCHA after repeated logins. Wait 30 min, try again.
- Try from a different IP / disable VPN
- garth's OAuth flow may bypass this

**MFA / 2FA issues:**

- If you have MFA enabled on Garmin, `garminconnect` may not handle it. `garth` has better MFA support.

**"Workout uploaded but doesn't show on watch":**

- Check Garmin Connect app → Training → Workouts (not Activities)
- Force sync the watch via Garmin Connect app
- Some workout formats need to be "scheduled" for a date to appear on the watch calendar

**Session expiry:**

- garth tokens: should auto-refresh, test after 24h+ gap
- garminconnect sessions: may expire in hours, test resume after overnight gap

-----

## Notes for Ascent Integration

Once we know which library works, the integration pattern will be:

1. Store auth tokens at `~/projects/ascent/.garmin/` (gitignored)
2. Auto-refresh on every cron run, re-auth on failure
3. If re-auth fails → Telegram alert: "Garmin auth expired, please re-authenticate"
4. Re-auth command via Telegram: `/garmin_reauth` triggers interactive flow

# Ascent UAT Checklist

Test these flows yourself after the architecture improvements commit. Each test has a pass/fail outcome and tells you exactly what to check.

---

## 1. Data Pipeline

### 1.1 Nightly Sync
- [ ] Run `cd ~/projects/ascent && source venv/bin/activate && python scripts/garmin_sync.py`
- [ ] Check logs — should show data for yesterday + today, no auth errors
- [ ] Open the app → Today tab → verify resting HR, HRV, sleep, body battery match Garmin Connect
- [ ] Check that `training_readiness_score` and `vo2max` are populated (not null)

### 1.2 On-Demand Sync (Latency Test)
- [ ] Open the Ascent app on your phone
- [ ] Tap the sync button, note the time
- [ ] Watch for data to appear — should be under 1 minute (was 5+ minutes before)
- [ ] Tap sync again immediately — should see "Sync already queued" error (rate limiting)
- [ ] Wait 2 minutes, tap again — should work

### 1.3 Scale Sync
- [ ] Run `python scripts/scale_sync.py`
- [ ] Check logs for "Weight X.X kg pushed to Garmin Connect" (was always "No weight value" before)
- [ ] Verify weight appears in Garmin Connect app

### 1.4 Backfill
- [ ] Run `python scripts/garmin_sync.py --date 2026-04-01`
- [ ] Verify data for April 1 appears in the app (Week tab → activities)

---

## 2. Coaching Loop (The Big One)

### 2.1 Health-Coach Makes a Decision
- [ ] Send Jarvis a message like "morning briefing" or `/morning` on Telegram
- [ ] Verify Jarvis posts to #ascent-daily with today's training decision
- [ ] Check Supabase: `planned_workouts` for today should have `status` updated to `pushed`, `adjusted`, or `skipped`
- [ ] Check Supabase: `coaching_log` should have a new `daily_plan` entry
- [ ] Open the app → Plan tab → verify today's session shows the correct status (green/yellow/gray badge)

### 2.2 Workout Push → Garmin → Completion → App
This is the full closed-loop test:
- [ ] Verify a workout was pushed to Garmin (check Garmin Connect → Training → Workouts)
- [ ] `planned_workouts` row should have `garmin_workout_id` set and `status = 'pushed'`
- [ ] Complete the workout on your watch (or a test workout)
- [ ] Run `python scripts/garmin_sync.py` after completing
- [ ] `planned_workouts` should now show `status = 'completed'` and `actual_garmin_activity_id` populated
- [ ] App → Plan tab → session should show green "completed" badge

### 2.3 Schedule Change via Telegram
- [ ] Tell Jarvis: "I can't train today, move it to tomorrow"
- [ ] Verify Jarvis confirms the change
- [ ] Check `planned_workouts` — today's row should be `skipped`, tomorrow should have the session
- [ ] Open the app — should reflect the change without manual refresh (realtime)

### 2.4 Volume Adjustment
- [ ] Tell Jarvis: "I'm really sore, can we reduce today's session?"
- [ ] Verify response mentions volume reduction
- [ ] Check `planned_workouts` — status should be `adjusted`, `adjustment_reason` should explain why

---

## 3. React App

### 3.1 Realtime Updates
- [ ] Open the app on your phone (Today tab)
- [ ] From your Mac terminal, run the sync: `python scripts/garmin_sync.py`
- [ ] Watch the app — data should update automatically within seconds (no manual refresh needed)
- [ ] If it doesn't update, check that Supabase Realtime is enabled on `daily_metrics` and `planned_workouts` tables

### 3.2 Today Tab
- [ ] Health cards show colored glows (green = good, yellow = caution, red = concern)
- [ ] HRV sparkline shows 7-day trend
- [ ] Today's planned workout preview shows exercises with weights
- [ ] Wellness check-in: fill all 5 items, submit → see "Saved" confirmation
- [ ] If you did an activity today: RPE prompt should appear → log it → see "RPE logged" confirmation

### 3.3 Plan Tab
- [ ] 8-week grid shows correct weeks and sessions
- [ ] Status pills: purple (planned), green (completed), yellow (adjusted), gray (skipped)
- [ ] Click a week → exercises expand with weights and sets
- [ ] Lift Progression chart shows data points (if you have training_sets data)

### 3.4 Recovery Tab
- [ ] HRV chart shows baseline band (balanced range)
- [ ] Fatigue detection: if HRV suppressed 3+ days, alert card should appear
- [ ] Sleep bar chart color-codes correctly (red <6h, yellow 6-7h, green 7+h)

### 3.5 Week Tab
- [ ] Shows this week vs last week activity comparison
- [ ] Elevation gain counts correctly (excludes resort skiing/hang gliding)
- [ ] Body composition shows latest weight from Xiaomi scale (not Garmin)

### 3.6 Trends Tab (90-day)
- [ ] Weight chart shows EWMA smoothing line
- [ ] VO2max trend shows data points
- [ ] eGym sync button works (if you have eGym access)

### 3.7 Goals Tab
- [ ] Active goals display with progress bars
- [ ] Weight goal shows direction indicator (arrow)
- [ ] Days remaining countdown is correct

---

## 4. Auth Resilience

### 4.1 Token Freshness
- [ ] Run `python scripts/garmin_auth.py` (CLI mode) — should report auth status
- [ ] Check `~/.garminconnect/garmin_tokens.json` exists and is <6 hours old

### 4.2 Keepalive
- [ ] Check keepalive is running: `launchctl list | grep ascent`
- [ ] Check logs: `tail -20 ~/projects/ascent/logs/keepalive.log`
- [ ] Logs should show "session alive" entries every 30 minutes

### 4.3 CSRF Extraction
- [ ] Run `python -c "from garmin_auth import extract_csrf_token; print('CSRF parser loaded OK')"`
- [ ] Install beautifulsoup4 if not already: `pip install beautifulsoup4`

---

## 5. Health Check & Monitoring

### 5.1 Health Check Script
- [ ] Run `python scripts/health_check.py`
- [ ] Should report OK/FAIL for: Garmin Auth, Last Sync, Supabase, Sync Watcher
- [ ] If sync_watcher is not running as daemon, that check will fail (expected)

### 5.2 Set Up Launchd (Optional)
- [ ] Create plist for health_check to run every 15 minutes
- [ ] Create plist for sync_watcher in daemon mode (replaces periodic trigger)

---

## 6. Edge Cases

- [ ] Open the app with no internet → should show cached data or graceful error
- [ ] Complete 2 activities in one day → RPE prompt should appear for the first one (known limitation)
- [ ] Check app after a rest day → no planned workout should show, no errors
- [ ] Check Week tab spanning a month boundary → dates should be correct

---

## Priority Order

If you're short on time, test in this order:
1. **2.1** (coaching loop — the most critical fix)
2. **1.2** (sync latency — most noticeable UX improvement)
3. **3.1** (realtime — enables the Supabase dashboard requirement)
4. **1.3** (scale sync bug fix — quick win)
5. **3.2** (wellness/RPE save confirmation — quick visual check)

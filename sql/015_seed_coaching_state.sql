-- =============================================
-- 015: Seed Coaching State Data
-- Populates program_blocks, program_sessions, recovery_rules,
-- season_phases, coaching_preferences, and injury_log
-- from coaching-program.md and coaching-context.md.
--
-- Run AFTER 014_coaching_state.sql
-- =============================================

-- =============================================
-- PROGRAM BLOCKS
-- =============================================

INSERT INTO program_blocks (block_number, name, focus, start_date, end_date, rpe_low, rpe_high, deload_week, progression_rule, stall_protocol, notes)
VALUES
  (1, 'Base Rebuild Block 1', 'hypertrophy/strength base', '2026-04-01', '2026-04-28', 6, 7, 4,
   '+2.5kg/week barbell compounds, +1kg or +1 rep accessories',
   'Hold weight 2 weeks. If still stalled, drop 10%, increase reps to 12, rebuild over 3 weeks.',
   'Week 1 shortened (starts Wednesday Apr 1). Week 4 deload: 50% volume, same weight.'),
  (2, 'Base Rebuild Block 2', 'strength emphasis', '2026-04-29', '2026-05-26', 7, 8, 4,
   '+2.5kg/week barbell compounds, +1kg or +1 rep accessories. If >RPE 8, drop 5%.',
   'Hold weight 2 weeks. If still stalled, drop 10%, increase reps to 12, rebuild over 3 weeks.',
   'Thursday becomes Intervals (5x3min Zone 3 uphill + 2min recovery). Track estimated 1RMs. Week 8 deload + assessment.')
ON CONFLICT (block_number) DO NOTHING;

-- =============================================
-- PROGRAM SESSIONS — BLOCK 1
-- =============================================

INSERT INTO program_sessions (block_id, session_key, name, day_of_week, estimated_duration_minutes, session_type, exercises, warmup, notes)
VALUES
  -- Strength A (Wednesday) — Full Body
  ((SELECT id FROM program_blocks WHERE block_number = 1), 'A', 'Strength A: Full Body', 'Wednesday', 50, 'strength',
   '[
     {"name": "Barbell Back Squat", "sets": 3, "reps": 8, "rpe_low": 6, "rpe_high": 7, "rest_s": 120, "start_kg": 70.0, "equipment": "barbell"},
     {"name": "DB Bench Press", "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 90, "start_kg": 18.0, "equipment": "dumbbell"},
     {"name": "Barbell Row", "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 90, "start_kg": 50.0, "equipment": "barbell"},
     {"name": "KB Swings", "sets": 3, "reps": 15, "rpe_low": 6, "rpe_high": 7, "rest_s": 60, "start_kg": 24.0, "equipment": "kettlebell"},
     {"name": "KB Halo", "sets": 2, "reps": 10, "rpe_low": 5, "rpe_high": 6, "rest_s": 60, "start_kg": 12.0, "equipment": "kettlebell", "notes": "10/direction"},
     {"name": "KB Turkish Get-up", "sets": 2, "reps": 3, "rpe_low": 6, "rpe_high": 6, "rest_s": 90, "start_kg": 16.0, "equipment": "kettlebell", "notes": "3/side"}
   ]'::jsonb,
   '[
     {"name": "Foam Roll T-Spine", "duration_s": 120},
     {"name": "Ankle Dorsiflexion Mobilization", "reps": 10, "notes": "per side"},
     {"name": "90/90 Hip Switches", "reps": 10},
     {"name": "Cat-Cow + Thoracic Rotation", "reps": 8, "notes": "per side"}
   ]'::jsonb,
   NULL),

  -- Strength B (Monday) — Upper + Core
  ((SELECT id FROM program_blocks WHERE block_number = 1), 'B', 'Strength B: Upper + Core', 'Monday', 50, 'strength',
   '[
     {"name": "DB/BB Overhead Press", "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 90, "start_kg": 15.0, "equipment": "dumbbell"},
     {"name": "Chin-ups", "sets": 3, "reps": 8, "rpe_low": 6, "rpe_high": 7, "rest_s": 90, "start_kg": null, "equipment": "bodyweight", "notes": "or Lat Pulldown 3x10"},
     {"name": "DB Incline Press", "sets": 2, "reps": 12, "rpe_low": 6, "rpe_high": 7, "rest_s": 60, "start_kg": 14.0, "equipment": "dumbbell"},
     {"name": "Cable Row", "sets": 2, "reps": 12, "rpe_low": 6, "rpe_high": 7, "rest_s": 60, "start_kg": null, "equipment": "cable"},
     {"name": "Dead Bugs", "sets": 3, "reps": 10, "rpe_low": 5, "rpe_high": 6, "rest_s": 30, "start_kg": null, "equipment": "bodyweight", "notes": "per side, core circuit"},
     {"name": "Copenhagen Plank", "sets": 3, "reps": 1, "rpe_low": 5, "rpe_high": 6, "rest_s": 30, "start_kg": null, "equipment": "bodyweight", "notes": "20-30s hold per side, core circuit"},
     {"name": "Pallof Walkouts", "sets": 3, "reps": 8, "rpe_low": 5, "rpe_high": 6, "rest_s": 30, "start_kg": null, "equipment": "cable", "notes": "per side, core circuit"}
   ]'::jsonb,
   '[
     {"name": "Shoulder CARs", "reps": 5, "notes": "per direction"},
     {"name": "Band Pull-Aparts", "reps": 15},
     {"name": "World Greatest Stretch", "reps": 5, "notes": "per side"}
   ]'::jsonb,
   NULL),

  -- Strength C (Friday) — Full Body Variant
  ((SELECT id FROM program_blocks WHERE block_number = 1), 'C', 'Strength C: Full Body Variant', 'Friday', 50, 'strength',
   '[
     {"name": "Trap Bar Deadlift", "sets": 3, "reps": 8, "rpe_low": 6, "rpe_high": 7, "rest_s": 120, "start_kg": 80.0, "equipment": "trap_bar"},
     {"name": "KB Clean & Press", "sets": 3, "reps": 8, "rpe_low": 6, "rpe_high": 7, "rest_s": 90, "start_kg": 16.0, "equipment": "kettlebell", "notes": "per side"},
     {"name": "Single-Arm DB Row", "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 60, "start_kg": 22.0, "equipment": "dumbbell", "notes": "per side"},
     {"name": "Bulgarian Split Squat", "sets": 2, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 90, "start_kg": 12.0, "equipment": "dumbbell", "notes": "per side"},
     {"name": "Lateral Raises", "sets": 2, "reps": 15, "rpe_low": 6, "rpe_high": 7, "rest_s": 60, "start_kg": 7.0, "equipment": "dumbbell"},
     {"name": "KB Farmer Carry", "sets": 3, "reps": 1, "rpe_low": 6, "rpe_high": 6, "rest_s": 60, "start_kg": 24.0, "equipment": "kettlebell", "notes": "40m per set"}
   ]'::jsonb,
   '[
     {"name": "Foam Roll Quads/Glutes", "duration_s": 120},
     {"name": "Pigeon Stretch", "duration_s": 30, "notes": "per side"},
     {"name": "Couch Stretch", "duration_s": 30, "notes": "per side"},
     {"name": "Cat-Cow", "reps": 8}
   ]'::jsonb,
   NULL),

  -- Mobility (Tuesday)
  ((SELECT id FROM program_blocks WHERE block_number = 1), 'mobility', 'Mobility', 'Tuesday', 25, 'mobility',
   '[
     {"name": "Foam Roll T-Spine/Lats/Quads/Glutes", "duration_s": 300},
     {"name": "90/90 Hip Switches", "reps": 10},
     {"name": "World Greatest Stretch", "reps": 5, "notes": "per side"},
     {"name": "Cat-Cow + Thoracic Rotation", "reps": 8, "notes": "per side"},
     {"name": "Shoulder CARs", "reps": 5, "notes": "per direction"},
     {"name": "Pigeon Stretch", "duration_s": 60, "notes": "per side"},
     {"name": "Couch Stretch", "duration_s": 60, "notes": "per side"}
   ]'::jsonb,
   NULL,
   'Domain 9 Protocol C — dedicated mobility session'),

  -- Rest days
  ((SELECT id FROM program_blocks WHERE block_number = 1), 'rest_thu', 'Rest or Easy Cardio', 'Thursday', 0, 'rest',
   '[]'::jsonb, NULL, 'Light 20-30min walk if feeling good, or full rest'),
  ((SELECT id FROM program_blocks WHERE block_number = 1), 'rest_sat', 'Mountain or Rest', 'Saturday', 0, 'mountain',
   '[]'::jsonb, NULL, 'Mountain day when conditions allow, otherwise rest'),
  ((SELECT id FROM program_blocks WHERE block_number = 1), 'rest_sun', 'Rest or Mountain 2', 'Sunday', 0, 'rest',
   '[]'::jsonb, NULL, 'Second mountain day or full rest')
ON CONFLICT (block_id, session_key) DO NOTHING;

-- =============================================
-- PROGRAM SESSIONS — BLOCK 2
-- Same structure but RPE 7-8 + Thursday Intervals
-- Consolidated A2/B2 templates for high mountain weeks
-- =============================================

INSERT INTO program_sessions (block_id, session_key, name, day_of_week, estimated_duration_minutes, session_type, exercises, warmup, notes)
VALUES
  -- Block 2: Strength A (same exercises, higher RPE)
  ((SELECT id FROM program_blocks WHERE block_number = 2), 'A', 'Strength A: Full Body', 'Wednesday', 50, 'strength',
   '[
     {"name": "Barbell Back Squat", "sets": 3, "reps": 8, "rpe_low": 7, "rpe_high": 8, "rest_s": 120, "equipment": "barbell"},
     {"name": "DB Bench Press", "sets": 3, "reps": 10, "rpe_low": 7, "rpe_high": 8, "rest_s": 90, "equipment": "dumbbell"},
     {"name": "Barbell Row", "sets": 3, "reps": 10, "rpe_low": 7, "rpe_high": 8, "rest_s": 90, "equipment": "barbell"},
     {"name": "KB Swings", "sets": 3, "reps": 15, "rpe_low": 7, "rpe_high": 8, "rest_s": 60, "equipment": "kettlebell"},
     {"name": "KB Halo", "sets": 2, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 60, "equipment": "kettlebell", "notes": "10/direction"},
     {"name": "KB Turkish Get-up", "sets": 2, "reps": 3, "rpe_low": 7, "rpe_high": 7, "rest_s": 90, "equipment": "kettlebell", "notes": "3/side"}
   ]'::jsonb,
   '[{"name": "Foam Roll T-Spine", "duration_s": 120}, {"name": "Ankle Dorsiflexion", "reps": 10}, {"name": "90/90 Hip Switches", "reps": 10}, {"name": "Cat-Cow + Thoracic Rotation", "reps": 8}]'::jsonb,
   'Block 2: same exercises, RPE 7-8. Weights from progression engine.'),

  -- Block 2: Strength B
  ((SELECT id FROM program_blocks WHERE block_number = 2), 'B', 'Strength B: Upper + Core', 'Monday', 50, 'strength',
   '[
     {"name": "DB/BB Overhead Press", "sets": 3, "reps": 10, "rpe_low": 7, "rpe_high": 8, "rest_s": 90, "equipment": "dumbbell"},
     {"name": "Chin-ups", "sets": 3, "reps": 8, "rpe_low": 7, "rpe_high": 8, "rest_s": 90, "equipment": "bodyweight"},
     {"name": "DB Incline Press", "sets": 2, "reps": 12, "rpe_low": 7, "rpe_high": 8, "rest_s": 60, "equipment": "dumbbell"},
     {"name": "Cable Row", "sets": 2, "reps": 12, "rpe_low": 7, "rpe_high": 8, "rest_s": 60, "equipment": "cable"},
     {"name": "Dead Bugs", "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 30, "equipment": "bodyweight", "notes": "per side"},
     {"name": "Copenhagen Plank", "sets": 3, "reps": 1, "rpe_low": 6, "rpe_high": 7, "rest_s": 30, "equipment": "bodyweight", "notes": "20-30s per side"},
     {"name": "Pallof Walkouts", "sets": 3, "reps": 8, "rpe_low": 6, "rpe_high": 7, "rest_s": 30, "equipment": "cable", "notes": "per side"}
   ]'::jsonb,
   '[{"name": "Shoulder CARs", "reps": 5}, {"name": "Band Pull-Aparts", "reps": 15}, {"name": "World Greatest Stretch", "reps": 5}]'::jsonb,
   'Block 2: RPE 7-8'),

  -- Block 2: Strength C
  ((SELECT id FROM program_blocks WHERE block_number = 2), 'C', 'Strength C: Full Body Variant', 'Friday', 50, 'strength',
   '[
     {"name": "Trap Bar Deadlift", "sets": 3, "reps": 8, "rpe_low": 7, "rpe_high": 8, "rest_s": 120, "equipment": "trap_bar"},
     {"name": "KB Clean & Press", "sets": 3, "reps": 8, "rpe_low": 7, "rpe_high": 8, "rest_s": 90, "equipment": "kettlebell", "notes": "per side"},
     {"name": "Single-Arm DB Row", "sets": 3, "reps": 10, "rpe_low": 7, "rpe_high": 8, "rest_s": 60, "equipment": "dumbbell", "notes": "per side"},
     {"name": "Bulgarian Split Squat", "sets": 2, "reps": 10, "rpe_low": 7, "rpe_high": 8, "rest_s": 90, "equipment": "dumbbell", "notes": "per side"},
     {"name": "Lateral Raises", "sets": 2, "reps": 15, "rpe_low": 7, "rpe_high": 8, "rest_s": 60, "equipment": "dumbbell"},
     {"name": "KB Farmer Carry", "sets": 3, "reps": 1, "rpe_low": 7, "rpe_high": 7, "rest_s": 60, "equipment": "kettlebell", "notes": "40m per set"}
   ]'::jsonb,
   '[{"name": "Foam Roll Quads/Glutes", "duration_s": 120}, {"name": "Pigeon Stretch", "duration_s": 30}, {"name": "Couch Stretch", "duration_s": 30}, {"name": "Cat-Cow", "reps": 8}]'::jsonb,
   'Block 2: RPE 7-8'),

  -- Block 2: Thursday Intervals (new for Block 2)
  ((SELECT id FROM program_blocks WHERE block_number = 2), 'intervals', 'Intervals', 'Thursday', 35, 'intervals',
   '[
     {"name": "Zone 3 Uphill Repeats", "sets": 5, "reps": 1, "rest_s": 120, "equipment": "none", "notes": "3min work / 2min recovery, uphill terrain"}
   ]'::jsonb,
   '[{"name": "Easy jog warmup", "duration_s": 600}]'::jsonb,
   'Block 2 only. 5x3min Zone 3 uphill + 2min recovery.'),

  -- Block 2: Consolidated A2 (for 2+ mountain days/week)
  ((SELECT id FROM program_blocks WHERE block_number = 2), 'A2', 'Consolidated Full Body A', 'Wednesday', 50, 'strength',
   '[
     {"name": "Barbell Back Squat", "sets": 3, "reps": 8, "rpe_low": 7, "rpe_high": 8, "rest_s": 120, "equipment": "barbell"},
     {"name": "DB/BB Overhead Press", "sets": 3, "reps": 10, "rpe_low": 7, "rpe_high": 8, "rest_s": 90, "equipment": "dumbbell"},
     {"name": "Barbell Row", "sets": 3, "reps": 10, "rpe_low": 7, "rpe_high": 8, "rest_s": 90, "equipment": "barbell"},
     {"name": "KB Swings", "sets": 3, "reps": 15, "rpe_low": 7, "rpe_high": 8, "rest_s": 60, "equipment": "kettlebell"},
     {"name": "KB Halo", "sets": 2, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 60, "equipment": "kettlebell"},
     {"name": "Dead Bugs", "sets": 3, "reps": 10, "rpe_low": 6, "rpe_high": 7, "rest_s": 30, "equipment": "bodyweight"},
     {"name": "Copenhagen Plank", "sets": 3, "reps": 1, "rpe_low": 6, "rpe_high": 7, "rest_s": 30, "equipment": "bodyweight", "notes": "20-30s"},
     {"name": "Pallof Walkouts", "sets": 3, "reps": 8, "rpe_low": 6, "rpe_high": 7, "rest_s": 30, "equipment": "cable"}
   ]'::jsonb,
   NULL,
   'Use when 2+ mountain days in the week. Replaces A+B with two consolidated sessions.'),

  -- Block 2: Consolidated B2
  ((SELECT id FROM program_blocks WHERE block_number = 2), 'B2', 'Consolidated Full Body B', 'Friday', 50, 'strength',
   '[
     {"name": "Trap Bar Deadlift", "sets": 3, "reps": 8, "rpe_low": 7, "rpe_high": 8, "rest_s": 120, "equipment": "trap_bar"},
     {"name": "KB Clean & Press", "sets": 3, "reps": 8, "rpe_low": 7, "rpe_high": 8, "rest_s": 90, "equipment": "kettlebell", "notes": "per side"},
     {"name": "Chin-ups", "sets": 3, "reps": 6, "rpe_low": 7, "rpe_high": 8, "rest_s": 90, "equipment": "bodyweight"},
     {"name": "Bulgarian Split Squat", "sets": 2, "reps": 10, "rpe_low": 7, "rpe_high": 8, "rest_s": 90, "equipment": "dumbbell", "notes": "per side"},
     {"name": "KB Turkish Get-up", "sets": 2, "reps": 3, "rpe_low": 7, "rpe_high": 7, "rest_s": 90, "equipment": "kettlebell", "notes": "3/side"},
     {"name": "KB Farmer Carry", "sets": 3, "reps": 1, "rpe_low": 7, "rpe_high": 7, "rest_s": 60, "equipment": "kettlebell", "notes": "40m per set"}
   ]'::jsonb,
   NULL,
   'Use when 2+ mountain days in the week. Pairs with A2.'),

  -- Block 2: Mobility + rest days (same as Block 1)
  ((SELECT id FROM program_blocks WHERE block_number = 2), 'mobility', 'Mobility', 'Tuesday', 25, 'mobility',
   '[{"name": "Foam Roll T-Spine/Lats/Quads/Glutes", "duration_s": 300}, {"name": "90/90 Hip Switches", "reps": 10}, {"name": "World Greatest Stretch", "reps": 5}, {"name": "Cat-Cow + Thoracic Rotation", "reps": 8}, {"name": "Shoulder CARs", "reps": 5}, {"name": "Pigeon Stretch", "duration_s": 60}, {"name": "Couch Stretch", "duration_s": 60}]'::jsonb,
   NULL, NULL),
  ((SELECT id FROM program_blocks WHERE block_number = 2), 'rest_sat', 'Mountain or Rest', 'Saturday', 0, 'mountain', '[]'::jsonb, NULL, NULL),
  ((SELECT id FROM program_blocks WHERE block_number = 2), 'rest_sun', 'Rest or Mountain 2', 'Sunday', 0, 'rest', '[]'::jsonb, NULL, NULL)
ON CONFLICT (block_id, session_key) DO NOTHING;

-- =============================================
-- RECOVERY RULES (Decision Matrix)
-- =============================================

INSERT INTO recovery_rules (hrv_status, sleep_condition, action, rpe_adjustment, volume_adjustment, override_note, priority)
VALUES
  ('BALANCED', '>=7h', 'train_as_planned', 'RPE 7-8', NULL, NULL, 10),
  ('BALANCED', '6-7h', 'train_moderate', 'RPE 6-7', NULL, NULL, 10),
  ('BALANCED', '<6h', 'reduce_volume', 'RPE 6-7', 'Reduce volume 30%, drop RPE', NULL, 10),
  ('UNBALANCED', '>=7h', 'train_moderate', 'RPE 6-7', NULL, NULL, 10),
  ('UNBALANCED', '6-7h', 'reduce_volume', 'RPE 5-6', 'Reduce volume 30%', NULL, 10),
  ('UNBALANCED', '<6h', 'rest_or_mobility', NULL, 'Mobility only or full rest', NULL, 10),
  ('LOW', '>=7h', 'reduce_volume', 'RPE 5-6', 'Reduce volume 30%, drop RPE', NULL, 10),
  ('LOW', '6-7h', 'rest_or_mobility', NULL, 'Mobility only or full rest', NULL, 10),
  ('LOW', '<6h', 'rest_or_mobility', NULL, 'Full rest — multiple signals degraded', 'Multi-signal convergence: 3+ degraded → mandatory rest', 1)
ON CONFLICT (hrv_status, sleep_condition) DO NOTHING;

-- =============================================
-- SEASON PHASES
-- =============================================

INSERT INTO season_phases (name, start_date, end_date, primary_focus, secondary_focus, transition_triggers, notes)
VALUES
  ('Winter/Spring Mountain Primary', '2025-12-01', '2026-05-31', 'mountain', 'gym',
   'Snow line retreats above 2500m consistently; last ski tour of season; June 1 regardless',
   'Mountain sports are the priority. Gym supports mountain performance. 3x gym when mountain allows.'),
  ('Summer Hike & Fly', '2026-06-01', '2026-08-31', 'mixed', 'gym',
   'September 1; first snowfall above 2000m; transition to fall gym focus',
   'Hiking, paragliding, hike-and-fly. Maintain gym 2-3x. Shift toward endurance.')
ON CONFLICT DO NOTHING;

-- =============================================
-- COACHING PREFERENCES
-- =============================================

INSERT INTO coaching_preferences (category, key, value, source)
VALUES
  ('delivery', 'verbosity', 'concise — 5-10 lines max for daily posts', 'user'),
  ('delivery', 'tone', 'direct, no hedging, no disclaimers, no filler', 'user'),
  ('delivery', 'summary_style', 'lead with the insight, not the number', 'user'),
  ('training', 'mountain_is_training', 'Mountain sports (ski touring, splitboarding, hiking) ARE training — never flag as missed gym', 'user'),
  ('training', 'heavy_weekend_rule', 'Heavy mountain weekend → Monday intensity down', 'observed'),
  ('training', 'compound_focus', 'Prefers compound movements over isolation', 'user'),
  ('training', 'core_variety', 'Likes variety in core exercises', 'observed'),
  ('training', '8hr_rule', 'Heavy mountain day → no heavy leg work within 8 hours', 'opus'),
  ('training', 'intensity_last_to_cut', 'Volume first, then duration, then intensity — intensity is the last variable to reduce', 'opus'),
  ('calendar', 'gym_time', '19:00 weekday evenings', 'user'),
  ('calendar', 'mountain_time_weekday', '17:00 weekdays', 'user'),
  ('calendar', 'mountain_time_weekend', '07:00 weekends', 'user'),
  ('nutrition', 'status', 'TBD — no nutrition plan yet', 'user')
ON CONFLICT (category, key) DO NOTHING;

-- =============================================
-- INJURY LOG
-- =============================================

INSERT INTO injury_log (reported_date, issue, body_area, status, severity, accommodations, resolved_date, notes)
VALUES
  ('2026-03-01', 'Broken rib', 'ribs', 'resolved', 'moderate', 'Avoid heavy bracing, no direct trunk impact exercises', '2026-03-28', 'Fully recovered by late March. No ongoing accommodations needed.')
ON CONFLICT DO NOTHING;

-- =============================================
-- SESSION EXCEPTION (current)
-- =============================================

INSERT INTO session_exceptions (date, original_session, modified_workout, modification_type, reason, pushed_to_garmin, created_by)
VALUES
  ('2026-04-04', 'Strength C: Full Body Variant',
   '[
     {"name": "Incline DB Press", "sets": 2, "reps": 8, "equipment": "dumbbell"},
     {"name": "Chest-Supported Row", "sets": 2, "reps": 8, "equipment": "dumbbell"},
     {"name": "Landmine Press", "sets": 2, "reps": 6, "equipment": "barbell", "notes": "per side"},
     {"name": "Chin-ups", "sets": 2, "reps": 6, "equipment": "bodyweight"},
     {"name": "Core Circuit", "sets": 2, "reps": 1, "equipment": "bodyweight", "notes": "Dead bugs + Pallof press"}
   ]'::jsonb,
   'reduce', 'Snowboarding morning + big tour Saturday. Reduced volume upper body + core only.', FALSE, 'coach')
ON CONFLICT (date) DO NOTHING;

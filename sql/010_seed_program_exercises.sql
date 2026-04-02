-- Migration 010: Add program exercises missing from seed data
-- Date: 2026-04-02
-- These exercises are used in the training program but were not in the original seed.

INSERT INTO exercises (name, category, muscle_groups, equipment, is_compound, notes)
VALUES
  ('Trap Bar Deadlift', 'back', '["glutes","hamstrings","quads","back"]', 'barbell', true, 'Hex bar deadlift — higher SFR, less spinal load than conventional'),
  ('KB Clean & Press', 'full_body', '["shoulders","core","legs"]', 'kettlebell', true, 'Kettlebell clean and press — functional compound'),
  ('KB Farmer Carry', 'full_body', '["grip","core","traps"]', 'kettlebell', false, 'Loaded carry with kettlebells'),
  ('Single-Arm DB Row', 'back', '["lats","rhomboids","biceps"]', 'dumbbell', true, 'One-arm dumbbell row'),
  ('Cable Row', 'back', '["lats","rhomboids","biceps"]', 'cable', true, 'Seated cable row — standard grip'),
  ('Dumbbell Incline Press', 'chest', '["chest","shoulders","triceps"]', 'dumbbell', true, 'Incline dumbbell bench press'),
  ('Dead Bugs', 'core', '["core","hip_flexors"]', 'bodyweight', false, 'Anti-extension core exercise'),
  ('Copenhagen Plank', 'core', '["adductors","core"]', 'bodyweight', false, 'Adductor-loaded side plank'),
  ('Pallof Walkouts', 'core', '["core","obliques"]', 'cable', false, 'Anti-rotation core exercise')
ON CONFLICT (name) DO NOTHING;

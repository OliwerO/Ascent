-- =============================================
-- 028: Home Workout Exercises
-- Seed exercises used as home substitutions for gym exercises.
-- These support the "Switch to Home Workout" feature.
-- =============================================

INSERT INTO exercises (name, category, muscle_groups, equipment, is_compound, notes) VALUES
('DB Floor Press', 'chest', '["chest", "front_delts", "triceps"]', 'dumbbell', FALSE, 'Floor press — no bench needed, reduced ROM'),
('DB Swing', 'legs', '["glutes", "hamstrings", "core"]', 'dumbbell', FALSE, 'Two-hand DB swing — KB swing substitute'),
('DB Halo', 'shoulders', '["shoulders", "core"]', 'dumbbell', FALSE, 'DB halo — KB halo substitute'),
('DB Turkish Get-Up', 'core', '["core", "shoulders", "glutes", "hips"]', 'dumbbell', FALSE, 'Turkish get-up with dumbbell'),
('Band-Assisted Inverted Row', 'back', '["lats", "rhomboids", "rear_delts", "biceps"]', 'band', FALSE, 'Inverted row with band — chin-up substitute'),
('Feet-Elevated Push-Up', 'chest', '["upper_chest", "front_delts", "triceps", "core"]', 'bodyweight', FALSE, 'Feet on chair/step for upper chest emphasis'),
('Band Row', 'back', '["lats", "rhomboids", "rear_delts", "biceps"]', 'band', FALSE, 'Resistance band row — cable row substitute'),
('Band Pallof Press', 'core', '["core", "obliques"]', 'band', FALSE, 'Band anti-rotation — Pallof walkout substitute'),
('DB Clean & Press', 'shoulders', '["shoulders", "core", "glutes"]', 'dumbbell', TRUE, 'Single-arm DB clean and press'),
('DB Farmer Carry', 'core', '["forearms", "traps", "core"]', 'dumbbell', FALSE, 'DB farmer walk — KB carry substitute'),
('Jump Rope', 'cardio', '["calves", "shoulders", "cardio"]', 'bodyweight', FALSE, 'Jump rope — warm-up cardio')
ON CONFLICT (name) DO NOTHING;

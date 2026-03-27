-- =============================================
-- SEED: Standard Exercises (~35 exercises)
-- Compound lifts + common accessories with muscle group mappings
-- =============================================

INSERT INTO exercises (name, category, muscle_groups, equipment, is_compound, notes) VALUES

-- COMPOUND LIFTS
('Barbell Back Squat', 'legs', '["quads", "glutes", "hamstrings", "core"]', 'barbell', TRUE, 'Primary lower body compound'),
('Barbell Front Squat', 'legs', '["quads", "glutes", "core", "upper_back"]', 'barbell', TRUE, 'Quad-dominant squat variation'),
('Conventional Deadlift', 'back', '["hamstrings", "glutes", "lower_back", "traps", "forearms"]', 'barbell', TRUE, 'Primary posterior chain compound'),
('Sumo Deadlift', 'back', '["hamstrings", "glutes", "adductors", "lower_back", "traps"]', 'barbell', TRUE, 'Wide-stance deadlift variation'),
('Romanian Deadlift', 'legs', '["hamstrings", "glutes", "lower_back"]', 'barbell', TRUE, 'Hip-hinge focused on hamstring stretch'),
('Barbell Bench Press', 'chest', '["chest", "front_delts", "triceps"]', 'barbell', TRUE, 'Primary horizontal push'),
('Incline Barbell Bench Press', 'chest', '["upper_chest", "front_delts", "triceps"]', 'barbell', TRUE, 'Upper chest emphasis'),
('Overhead Press', 'shoulders', '["front_delts", "lateral_delts", "triceps", "core"]', 'barbell', TRUE, 'Primary vertical push'),
('Barbell Row', 'back', '["lats", "rhomboids", "rear_delts", "biceps", "forearms"]', 'barbell', TRUE, 'Primary horizontal pull'),
('Pull-Up', 'back', '["lats", "biceps", "rear_delts", "forearms"]', 'bodyweight', TRUE, 'Primary vertical pull'),
('Chin-Up', 'back', '["lats", "biceps", "forearms"]', 'bodyweight', TRUE, 'Supinated vertical pull — more bicep involvement'),
('Dip', 'chest', '["chest", "triceps", "front_delts"]', 'bodyweight', TRUE, 'Bodyweight push — chest/tricep compound'),
('Leg Press', 'legs', '["quads", "glutes", "hamstrings"]', 'machine', TRUE, 'Machine-based quad/glute compound'),
('Hip Thrust', 'legs', '["glutes", "hamstrings"]', 'barbell', TRUE, 'Glute-dominant hip extension'),

-- ACCESSORIES — CHEST
('Dumbbell Bench Press', 'chest', '["chest", "front_delts", "triceps"]', 'dumbbell', FALSE, 'Dumbbell variation — better ROM'),
('Incline Dumbbell Press', 'chest', '["upper_chest", "front_delts", "triceps"]', 'dumbbell', FALSE, 'Upper chest dumbbell variation'),
('Cable Fly', 'chest', '["chest"]', 'cable', FALSE, 'Chest isolation — constant tension'),
('Push-Up', 'chest', '["chest", "front_delts", "triceps", "core"]', 'bodyweight', FALSE, 'Bodyweight chest exercise'),

-- ACCESSORIES — BACK
('Lat Pulldown', 'back', '["lats", "biceps", "rear_delts"]', 'cable', FALSE, 'Cable vertical pull'),
('Seated Cable Row', 'back', '["lats", "rhomboids", "rear_delts", "biceps"]', 'cable', FALSE, 'Cable horizontal pull'),
('Dumbbell Row', 'back', '["lats", "rhomboids", "rear_delts", "biceps"]', 'dumbbell', FALSE, 'Single-arm horizontal pull'),
('Face Pull', 'shoulders', '["rear_delts", "external_rotators", "rhomboids"]', 'cable', FALSE, 'Shoulder health and rear delt isolation'),

-- ACCESSORIES — SHOULDERS
('Lateral Raise', 'shoulders', '["lateral_delts"]', 'dumbbell', FALSE, 'Medial deltoid isolation'),
('Landmine Press', 'shoulders', '["front_delts", "upper_chest", "triceps"]', 'barbell', FALSE, 'Shoulder-friendly pressing variation'),
('Rear Delt Fly', 'shoulders', '["rear_delts"]', 'dumbbell', FALSE, 'Rear deltoid isolation'),

-- ACCESSORIES — ARMS
('Barbell Curl', 'arms', '["biceps"]', 'barbell', FALSE, 'Primary bicep exercise'),
('Dumbbell Curl', 'arms', '["biceps"]', 'dumbbell', FALSE, 'Dumbbell bicep curl'),
('Hammer Curl', 'arms', '["biceps", "brachioradialis", "forearms"]', 'dumbbell', FALSE, 'Neutral grip bicep variation'),
('Tricep Pushdown', 'arms', '["triceps"]', 'cable', FALSE, 'Cable tricep isolation'),
('Overhead Tricep Extension', 'arms', '["triceps"]', 'cable', FALSE, 'Long head tricep emphasis'),
('Skull Crusher', 'arms', '["triceps"]', 'barbell', FALSE, 'Lying tricep extension'),

-- ACCESSORIES — LEGS
('Bulgarian Split Squat', 'legs', '["quads", "glutes", "hamstrings"]', 'dumbbell', FALSE, 'Single-leg squat variation'),
('Leg Extension', 'legs', '["quads"]', 'machine', FALSE, 'Quad isolation'),
('Leg Curl', 'legs', '["hamstrings"]', 'machine', FALSE, 'Hamstring isolation'),
('Calf Raise', 'legs', '["calves"]', 'machine', FALSE, 'Standing or seated calf raise'),
('Walking Lunge', 'legs', '["quads", "glutes", "hamstrings"]', 'dumbbell', FALSE, 'Dynamic single-leg movement'),

-- CORE
('Plank', 'core', '["core", "transverse_abdominis"]', 'bodyweight', FALSE, 'Isometric core stability'),
('Hanging Leg Raise', 'core', '["lower_abs", "hip_flexors"]', 'bodyweight', FALSE, 'Advanced core exercise'),
('Cable Woodchop', 'core', '["obliques", "core"]', 'cable', FALSE, 'Rotational core movement'),
('Ab Wheel Rollout', 'core', '["core", "lats"]', 'bodyweight', FALSE, 'Anti-extension core exercise')

ON CONFLICT (name) DO NOTHING;

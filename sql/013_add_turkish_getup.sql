-- Migration 013: Add Turkish Get-Up to exercises table
-- It was missing from the seed data despite being used in the training program.

INSERT INTO exercises (name, category, muscle_groups, equipment, is_compound)
VALUES (
  'Turkish Get-Up',
  'core',
  '["shoulders","core","hips"]'::jsonb,
  'kettlebell',
  true
)
ON CONFLICT (name) DO NOTHING;

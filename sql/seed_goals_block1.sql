-- Seed goals for Block 1 (Weeks 1-8, ending 2026-05-25)
-- Body composition goals come from elsewhere; this seeds strength, endurance, milestones.
-- Idempotent: deletes prior block-1 seeded rows by notes tag before insert.

DELETE FROM goals WHERE notes LIKE '[block1-seed]%';

INSERT INTO goals (category, metric, target_value, current_value, start_date, target_date, status, notes) VALUES
  ('strength',  'squat_e1rm_kg',     100, NULL, '2026-03-30', '2026-05-25', 'active', '[block1-seed] Squat e1RM target'),
  ('strength',  'deadlift_e1rm_kg',  140, NULL, '2026-03-30', '2026-05-25', 'active', '[block1-seed] Deadlift e1RM target'),
  ('strength',  'bench_e1rm_kg',     80,  NULL, '2026-03-30', '2026-05-25', 'active', '[block1-seed] Bench e1RM target'),
  ('strength',  'ohp_e1rm_kg',       55,  NULL, '2026-03-30', '2026-05-25', 'active', '[block1-seed] OH Press e1RM target'),
  ('strength',  'row_e1rm_kg',       80,  NULL, '2026-03-30', '2026-05-25', 'active', '[block1-seed] Row e1RM target'),
  ('endurance', 'vo2max',            55,  NULL, '2026-03-30', '2026-05-25', 'active', '[block1-seed] VO2max target'),
  ('endurance', 'weekly_elevation_m', 2000, NULL,'2026-03-30','2026-05-25', 'active', '[block1-seed] Weekly elevation target'),
  ('milestone', 'week_4_assessment', 1, 0, '2026-03-30', '2026-04-27', 'active', '[block1-seed] Week 4 Assessment — Body comp, working weights, Opus review'),
  ('milestone', 'week_8_assessment', 1, 0, '2026-03-30', '2026-05-25', 'active', '[block1-seed] Week 8 Assessment — Full review, block comparison'),
  ('milestone', 'season_transition', 1, 0, '2026-03-30', '2026-05-15', 'active', '[block1-seed] Season Transition — Mountain primary to Hike & Fly');

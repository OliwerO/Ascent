# Ascent — Open Tasks for Discussion

## Task 1: Coaching Context Template

The health-coach skill reads `~/vault/second-brain/projects/ascent/coaching-context.md` for context on every interaction. The current template is bare-bones:

```markdown
## Current Goals
## Current Training Program
## Season Context
## Injury & Soreness Log
## Learned Preferences
## Coaching Decisions Log
```

**Discuss:**
- What goals should be pre-filled? (e.g., body comp targets, strength milestones, VO2max goals)
- What's the current training program? (split, days/week, focus)
- Any active injuries or recurring issues to note?
- Preferences for how coaching feedback is delivered (time of day, detail level, tone)
- Should this file be structured differently? (YAML frontmatter? Sections per season?)

## Task 2: Grafana Dashboard Planning

After Phase 3, the next step is connecting Grafana Cloud to Supabase for visualization. The data available:

- **Daily wellness:** HRV (trend + baseline), sleep (score + stages), resting HR, stress, body battery, training readiness, VO2max, SpO2
- **Performance:** training status (productive/detraining), endurance score, hill score, race predictions, fitness age
- **Body comp:** weight, body fat %, muscle mass, BMI
- **Activities:** type, duration, HR zones, elevation, training effect, splits, weather
- **Training:** sets, reps, volume, estimated 1RMs, PRs

**Discuss:**
- Which metrics do you check daily vs. weekly?
- What alerts matter? (e.g., HRV drop >15% from baseline, sleep score <60, training status = detraining)
- Single overview dashboard or separate dashboards per category?
- Any specific charts you want? (e.g., weight vs. muscle mass over time, HRV 30-day rolling avg, weekly training volume by type)
- Mobile-friendly layout? (you'll check on phone mostly?)

## Task 3: Supabase Schema Verification

Phase 1 tables + Phase 2 migration should all be live. Worth verifying:

- All 22 tables exist with correct columns and constraints
- Generated columns work (weight_kg, volume_kg, estimated_1rm)
- Views work (daily_summary)
- Indexes are created
- Seed data present (biomarker definitions, exercises)
- RLS policies — currently none set. Should we add any? (The anon key has full access right now)

**Discuss:**
- Is RLS needed? (Single user, but anon key in .env on Mac)
- Should we add a service_role key for the sync script and restrict anon to read-only?
- Any missing columns discovered after looking at actual Garmin API responses?

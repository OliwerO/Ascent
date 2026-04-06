# Program Config Migration: Hardcoded → Supabase

> **Status:** Design only — not yet implemented
> **Created:** 2026-04-06
> **Priority:** Must complete before May 26, 2026 (current program end date)

## Problem

Program configuration (dates, session maps, block names, deload schedule) is hardcoded across multiple files. After May 26, 2026, `getProgramWeek()` returns `{ block: 2, week: 8, ended: true }` forever and the app stops being useful.

### Where hardcoded values live today

| Value | File | Example |
|-------|------|---------|
| Block start/end dates | `web/src/lib/program.ts` | `BLOCK_1_START = new Date(2026, 2, 30)` |
| Deload weeks | `web/src/lib/program.ts` | `DELOAD_WEEKS = new Set([4, 8])` |
| Day-to-session map | `web/src/lib/program.ts` | `{ 1: 'B', 3: 'A', 5: 'C' }` |
| Session names | `web/src/lib/program.ts` | `A: 'Strength A: Full Body'` |
| Day type schedule | `web/src/lib/program.ts` | `['gym', 'mobility', 'gym', 'rest', ...]` |
| Program title | `TrainingPlanView.tsx` | `"Base Rebuild — Block {block} of 2"` |
| Date range string | `TrainingPlanView.tsx` | `"Apr 1 – May 26"` |
| Assessment dates | `GoalsView.tsx` | `"Apr 27, 2026"`, `"May 25, 2026"` |
| Season context | `GoalsView.tsx` | `"Winter/Spring — Mountain Primary"` |
| Same constants | `scripts/workout_push.py` | `DAY_TO_SESSION`, `SESSION_NAMES`, `DELOAD_WEEKS` |
| Same constants | `scripts/workout_generator.py` | `get_gym_dates()` hardcoded logic |
| Garmin benchmarks | `scripts/workout_push.py` | `GARMIN_BENCHMARKS` from Feb 2026 |

## Proposed Solution

### New table: `program_config`

```sql
CREATE TABLE program_config (
  id BIGSERIAL PRIMARY KEY,
  program_name TEXT NOT NULL,           -- e.g. 'Base Rebuild'
  total_weeks INTEGER NOT NULL,         -- e.g. 8
  start_date DATE NOT NULL,             -- Monday-aligned
  end_date DATE NOT NULL,               -- Sunday
  status TEXT DEFAULT 'active',         -- 'active', 'completed', 'upcoming'
  blocks JSONB NOT NULL,                -- block definitions
  -- blocks example:
  -- [
  --   { "number": 1, "name": "Base Rebuild", "weeks": [1,2,3,4], "rpe_range": [6,7] },
  --   { "number": 2, "name": "Progression", "weeks": [5,6,7,8], "rpe_range": [7,8] }
  -- ]
  deload_weeks JSONB NOT NULL,          -- e.g. [4, 8]
  weekly_schedule JSONB NOT NULL,       -- day-to-session and day-type mapping per block
  -- weekly_schedule example:
  -- {
  --   "1": {  // block 1
  --     "day_types": ["gym","mobility","gym","rest","gym","mountain","rest"],
  --     "sessions": { "1": "B", "3": "A", "5": "C" }
  --   },
  --   "2": {  // block 2
  --     "day_types": ["gym","mobility","gym","intervals","gym","mountain","rest"],
  --     "sessions": { "1": "B", "3": "A", "5": "C" }
  --   }
  -- }
  session_definitions JSONB NOT NULL,   -- session names and descriptions
  -- session_definitions example:
  -- {
  --   "A": { "name": "Strength A: Full Body", "estimated_minutes": 50 },
  --   "B": { "name": "Strength B: Upper + Core", "estimated_minutes": 40 },
  --   "C": { "name": "Strength C: Full Body Variant", "estimated_minutes": 50 }
  -- }
  checkpoints JSONB,                    -- assessment dates and goals
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_program_config_status ON program_config(status);
```

### New hook: `useProgramConfig()`

```ts
export function useProgramConfig() {
  return useFetch<ProgramConfig>('program_config', async () => {
    const { data, error } = await supabase
      .from('program_config')
      .select('*')
      .eq('status', 'active')
      .limit(1)
      .single()
    if (error) throw error
    return data
  }, [])
}
```

### Migration steps

1. **Create the table** — `sql/007_program_config.sql`
2. **Seed current program** — Insert the Base Rebuild program with current dates
3. **Create `useProgramConfig()` hook** — in `useSupabase.ts`
4. **Refactor `program.ts`** — `getProgramWeek()` reads from hook data instead of constants. Keep the function signature the same but make it accept config as a parameter.
5. **Update views** — Pass program config to components instead of importing constants
6. **Update scripts** — `workout_push.py` and `workout_generator.py` read from Supabase instead of hardcoded constants
7. **Remove hardcoded strings** — "Apr 1 – May 26", assessment dates, season context all come from DB

### Who updates program_config?

- **Opus** creates/modifies rows during planning sessions
- **Coaching agent** reads the active config
- **workout_generator.py** reads it for generating planned_workouts
- **Frontend** reads it via `useProgramConfig()`
- Nobody else writes to it — single source of truth

### Transition plan

When the current program ends (May 26):
1. Opus session creates a new row with `status: 'active'`, marks the old one `'completed'`
2. All consumers automatically pick up the new config
3. No code deploy needed

## Not in scope

- Automatic program generation (that's Phase 6/Opus)
- Multi-user support (Ascent is single-user)
- Historical program browsing (future enhancement)

# Development Practices — Ascent Project

> This file is referenced by CLAUDE.md. Claude Code follows these practices automatically.
> Last updated: 2026-04-05

## Database (Supabase / PostgreSQL)

### Migrations
- All schema changes go in numbered SQL files: `sql/NNN_description.sql`
- Never modify a migration that's already been applied — create a new one
- Include both the change and any necessary indexes in the same migration
- Use `IF NOT EXISTS` / `IF EXISTS` guards where appropriate

### Query Patterns
- Use parameterized queries — never string-interpolate user input into SQL
- Prefer `UPSERT` (ON CONFLICT DO UPDATE) for sync operations
- Use date-spine joins (`generate_series`) for gap-aware rolling calculations — never `ROWS BETWEEN N PRECEDING`
- Minimum valid-day thresholds: 4/7 weekly, 20/30 monthly, 60/90 quarterly
- All timestamps stored as TIMESTAMPTZ

### Row-Level Security
- RLS enabled on all tables with user-facing access
- Service key used only in server-side scripts, never exposed to frontend
- Anon key in frontend with appropriate RLS policies

## Python Scripts

### Structure
- All scripts in `scripts/` with a shared `.env` loading pattern
- Use `python-dotenv` for environment variable loading
- Log to stdout for cron capture; exit 0 on success, 1 on failure
- Rate-limit external API calls (1s between Garmin calls)

### Error Handling
- Wrap API calls in try/except with specific exception types
- Log the error context (which date, which endpoint) before failing
- Never silently swallow exceptions

### Data Validation
- Apply reject-level rules before writing to Supabase (see CLAUDE.md validation table)
- Flag-level rules applied at query/display layer, not at write time

### Dependencies
- All Python deps in `scripts/requirements.txt`
- Pin major versions, allow minor updates (e.g., `garth>=0.4,<1.0`)

## Frontend (React / TypeScript / Vite / Tailwind)

### TypeScript
- Strict mode enabled — no `any` types unless absolutely necessary
- Shared types in `web/src/lib/types.ts`
- Props interfaces defined inline or co-located with the component

### Components
- One component per file
- Views in `web/src/views/`, reusable components in `web/src/components/`
- Hooks in `web/src/hooks/` (e.g., `useSupabase.ts`)
- Keep components focused — if a component exceeds ~200 lines, consider splitting

### Styling
- Tailwind utility classes for all styling
- Design tokens (colors, spacing) follow the existing design system
- Dark mode by default (health dashboard — dark backgrounds reduce eye strain)
- Responsive: mobile-first, works on phone and desktop

### Build & Deploy
- **Always run `cd web && npm run build` before committing frontend changes**
- TypeScript errors block Vercel deployment — fix them, don't suppress them
- Vercel auto-deploys from `main` branch

## Git Practices

### Commits
- One logical change per commit
- Descriptive messages: "Fix scale_sync: only write weight from Xiaomi" not "fix bug"
- Don't commit `.env`, credentials, or large binaries

### Branching
- Work directly on `main` for small changes (this is a personal project)
- Use feature branches for multi-day work or risky changes

## Testing

### What to Test
- `npm run build` (TypeScript compilation) — mandatory before every frontend commit
- Python scripts: run with `--date` flag on a known date to verify output
- SQL migrations: apply to Supabase and verify tables/views exist
- Garmin sync: check Supabase tables have data after running

### What Not to Over-Test
- This is a personal project, not a production SaaS. Unit test coverage targets are not useful here.
- Focus testing effort on: data integrity (sync scripts write correct values), build passes (no broken deploys), and SQL correctness (migrations apply cleanly).

## Security

- Secrets in `.env` only, `.env` in `.gitignore`
- Supabase service key never in frontend code
- No user input flows directly into SQL (parameterized queries only)
- CORS configured on Supabase for the Vercel domain only

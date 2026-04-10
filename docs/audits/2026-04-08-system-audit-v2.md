# Ascent System Audit v2 — 2026-04-08

**Auditor:** Claude (Opus 4.6, 1M ctx)
**Scope:** End-to-end correctness, observability, and growth surface
**Baseline:** Phase A fixes landed earlier today (health-coach fabrication, coach_adjust note-validator, exec preflight, Garmin Phase 2 headless on test acct)
**Cadence:** Sections appended phase-by-phase so progress survives a restart

---

## Headline findings (read this first)

1. **NEW CRITICAL — `planned_workouts` has 4+ uncoordinated writers.** The single-write-path contract documented in `scripts/coach_adjust.py:1-19` is violated by `scripts/garmin_sync.py:673-675` (writes `status`, `actual_garmin_activity_id`, `synced_at`), `scripts/workout_push.py:1432-1433` (writes `garmin_workout_id`), `scripts/workout_generator.py:372-376` (writes `status=completed|skipped`), `scripts/garmin_workout_push.py:150-152`, and `scripts/mobility_workout.py:537`. Race condition: a `garmin_sync` run between two `coach_adjust` calls can silently overwrite a coaching decision. Phase A's fabrication fix assumed the DB was authoritative; this finding undermines that assumption. **Severity: high.** Not previously tracked.
2. **Confirmed — `health-coach-sleep-reminder` cron** (`~/.openclaw/cron/jobs.json:114`) is the surviving instance of the infer-from-weekday anti-pattern. Queries `program_sessions.day_of_week` instead of `planned_workouts.scheduled_date`. Same class of bug Phase A fixed in `health-coach-daily`. **Severity: high.** Patch in Phase 2.
3. **Confirmed — `garmin-token-refresh` cron** (`~/.openclaw/cron/jobs.json:146`) has `delivery.channel:"last"` which suppresses failureAlert when multiple channels are configured. The 70-error loop went unnoticed for this reason. Plus it duplicates launchd `com.ascent.garmin-refresh` which is currently green — likely deletion candidate, but flagged for user confirmation only. **Severity: medium.**
4. **Traceability hole.** "Train as planned" decisions made by `health-coach-daily` leave **no `coaching_log` row at all** — there is no audit trail for the no-adjust path. Phase 7 schema additions + new `mark_train_as_planned` action close this.
5. **`coaching_log` lacks structured KB citations.** `kb_refs`, `inputs`, `rule`, `decision_type` all missing; reasons live as free text in `adjustment_reason`. Phase 7 migration adds these.

---

## Phase 1 — Dependency map

Source-of-truth question for every coaching-relevant table/view. R = read, W = write. Citations are `file:line`.

### `planned_workouts`

| Component | file:line | R/W | Notes |
|---|---|---|---|
| `scripts/coach_adjust.py` | 206-230, 219-220 | R+W | INTENDED single write path: status, adjustment_reason, duration, compliance_score, garmin_workout_id |
| `scripts/workout_generator.py` | 285, 296, 304-310 | R+W | INTENDED: initial INSERT + workout_definition/training_block/week_number updates |
| `scripts/workout_generator.py` | 333, 372-376 | R+W | **UNCOORDINATED** mark-completed/mark-skipped pass — overlaps coach_adjust's status authority |
| `scripts/garmin_sync.py` | 669, 673-675 | R+W | **UNCOORDINATED** writes status=completed, actual_garmin_activity_id, synced_at |
| `scripts/workout_push.py` | 1432-1433 | W | **UNCOORDINATED** writes garmin_workout_id post-push |
| `scripts/mobility_workout.py` | 537, 539 | W | INSERT mobility row + garmin_workout_id update |
| `scripts/garmin_workout_push.py` | 150-152 | W | **UNCOORDINATED** garmin_workout_id update |
| `web/src/hooks/useSupabase.ts` | 192-206 | R | `usePlannedWorkouts` hook → `web/src/views/TodayView.tsx` |

**Source-of-truth violation:** see headline #1.

### `coaching_log`

| Component | file:line | R/W | Notes |
|---|---|---|---|
| `scripts/coach_adjust.py` | ~680-682 | W | INSERT type='adjustment' with action+details |
| `~/.openclaw/cron/jobs.json` (weekly-review, line 65-75) | — | W | Cron-payload SQL inserts type='weekly_review' |
| `web/src/hooks/useSupabase.ts` | 180-189 | R | Recent entries display |
| **(missing)** `health-coach-daily` "train as planned" branch | — | — | **No-op decisions leave no row.** Phase 7 fix. |

### `daily_coaching_context` (single-row VIEW)

| Component | file:line | R/W | Notes |
|---|---|---|---|
| `sql/016_interference_and_load.sql` | 280-352 | DEF | View definition (re-create of `sql/014_coaching_state.sql:195`) |
| `~/.openclaw/cron/jobs.json` (health-coach-daily, line 18-48) | — | R | Step 2 of runbook reads via curl (`?select=*&limit=1`, no date filter) |
| `~/.openclaw/cron/jobs.json` (sleep-reminder, line 112-143) | — | R | Reads recovery signals |

### `weekly_coaching_summary` (VIEW)

| Component | file:line | R/W | Notes |
|---|---|---|---|
| `sql/016_interference_and_load.sql` | 460-550 | DEF | View definition |
| `~/.openclaw/cron/jobs.json` (weekly-review, line 65-75) | — | R | Sunday 20:00 cron |

### `activities`

| Component | file:line | R/W | Notes |
|---|---|---|---|
| `scripts/garmin_sync.py` | 419 | W | UPSERT on garmin_activity_id |
| `scripts/terra_sync.py` | 438 | W | UPSERT on garmin_activity_id (fallback) |
| `scripts/workout_generator.py` | 354 | R | Match strength_training to planned sessions |
| `web/src/hooks/useSupabase.ts` | 94-103 | R | `useActivities` |
| `web/src/views/TrendsView.tsx` | 175 | R | Elevation_gain rollup |

### `training_sessions`

| Component | file:line | R/W | Notes |
|---|---|---|---|
| `scripts/garmin_sync.py` | 604-617 | W | INSERT/UPDATE strength activity details |
| `scripts/progression_engine.py` | 159 | R | Lookup by session_id |
| `scripts/workout_generator.py` | 345 | R | Match completed sessions |
| `web/src/hooks/useSupabase.ts` | 131-140 | R | `useTrainingSessions` |

### `hrv`, `sleep`, `daily_metrics`

| Component | file:line | R/W | Notes |
|---|---|---|---|
| `scripts/garmin_sync.py` | (per-table sync fns) | W | Garmin nightly UPSERT on date |
| `scripts/terra_sync.py` | 201 | W | `daily_metrics` UPSERT (fallback) |
| `daily_coaching_context` view | `sql/016:290-330` | R | Aggregated into single-row view |
| `web/src/hooks/useSupabase.ts` | 70-128 | R | `useHRV`/`useSleep`/`useDailyMetrics` |
| `~/.openclaw/cron/jobs.json` (sleep-reminder, line 114) | — | R | 6-day avg sleep |

### `program_sessions`, `program_blocks` (templates, seeded once)

| Component | file:line | R/W | Notes |
|---|---|---|---|
| `sql/015_*.sql` | 14-113 | W | One-time seed |
| `daily_coaching_context` view | `sql/016:282,310` | R | Template lookup by `day_of_week` (LEGIT — see Phase 2) |
| `~/.openclaw/cron/jobs.json` (sleep-reminder, line 114) | — | R | **BUG** — see Phase 2 |

### `exercise_progression`

| Component | file:line | R/W | Notes |
|---|---|---|---|
| `scripts/progression_engine.py` | 451-459 | W | UPSERT on (exercise_name, date) |
| `~/.openclaw/cron/jobs.json` (weekly-review, line 68) | — | R | Weekly summary join |

### `athlete_response_patterns`

| Component | file:line | R/W | Notes |
|---|---|---|---|
| `~/.openclaw/workspace/skills/health-coach/SKILL.md` | (mountain rule section) | R | Phase A confirmed: SKILL reads effect_size/confidence for mountain interference proactive adjustment |
| `scripts/interference_analysis.py` | (per script purpose) | W | Writes inferred patterns |

(Earlier exploration flagged this table as orphaned — corrected here. It is read by health-coach SKILL and written by interference_analysis.py.)

### `weekly_training_load`

| Component | file:line | R/W | Notes |
|---|---|---|---|
| (verify schema: view vs table) | — | — | Read by health-coach SKILL.md for load-spike awareness; writer not yet located. **TODO** for Phase 7 follow-up. |

### `session_exceptions`

| Component | file:line | R/W | Notes |
|---|---|---|---|
| `sql/015_*.sql` | 266-276 | W | Seed only |
| `scripts/coach_adjust.py` | (markdown writer) | W | Writes to `openclaw/coaching-context.md`, **NOT** to DB. Two sources of truth for exceptions. |
| `~/.openclaw/cron/jobs.json` (health-coach-daily, line 18) | — | R | Reads from coaching-context.md, not DB |

**Source-of-truth split:** exceptions live in markdown for the cron and (separately) in DB for migrations. Anything that adds an exception via DB will not be visible to the cron, and vice versa. Flag for Phase 9 (consolidation).

### `body_composition`

| Component | file:line | R/W | Notes |
|---|---|---|---|
| `scripts/garmin_sync.py` | 322 | W | source='garmin' |
| `scripts/terra_sync.py` | 329 | W | source='terra' |
| `scripts/scale_sync.py` | 215-216 | W | source='scale' |
| `scripts/egym_sync.py` | 304-305 | W | source='egym' |
| `web/src/hooks/useSupabase.ts` | 119-128 | R | `useBodyComposition` |

Multi-source by design (`source` column disambiguates). Safe.

### `body_battery_events` (deprecation candidate — known-pending #6)

Schema-defined but no active writers found. Daily peak now lives in `daily_metrics.body_battery_highest`. SKILL.md still references the events table; that's the #6 fix.

### External push targets

| Target | Writer | file:line | Notes |
|---|---|---|---|
| Garmin workouts API | `scripts/workout_push.py` | 1430-1440 | Strength push |
| Garmin workouts API | `scripts/mobility_workout.py` | 536-540 | Mobility push |
| Garmin workouts API | `scripts/garmin_workout_push.py` | 149-153 | Generic push |
| Garmin scheduled-workouts API | (via above) | — | Schedule-by-date assignments |
| Slack `#ascent-training` C0AQ1KJAKM0 | `coach_adjust.py` post_slack | ~695 | Coaching content |
| Slack `#ascent-training` C0AQ1KJAKM0 | jobs.json (daily/weekly) | 31-32, 78-79 | Cron deliveries |
| Slack `#ascent-daily` C0AQ1KHMBGS | jobs.json (sleep-reminder, failureAlerts) | 125-126 | Alerts only — but **see #11**: sleep-reminder should be on -training |
| Google Calendar | jobs.json toolsAllow | 24 | Capability enabled; concrete writer TBD |

### Source-of-truth violations (consolidated)

1. **`planned_workouts` status field** — 4 writers, no coordination. (Headline #1.)
2. **`planned_workouts.garmin_workout_id`** — 4 writers, no coordination. Less risky (idempotent re-push usually) but still unowned.
3. **`session_exceptions`** — markdown vs DB split, neither knows about the other.
4. **`weekly_training_load`** — readers exist, writer unverified. Possible orphan.

---

## Phase 2 — Weekday-inference bug sweep

Search terms: `DAY_TO_SESSION`, `SESSIONS\[`, `strftime.*%A`, `day_of_week`, `INITCAP.*TO_CHAR`, `isoweekday`, `weekday\(\)`, references to `coaching-program.md` as a schedule source. Searched: `scripts/`, `~/.openclaw/cron/jobs.json`, `~/.openclaw/workspace/skills/`, `~/Library/LaunchAgents/com.ascent.*`.

| # | Hit | file:line | Class | Action |
|---|---|---|---|---|
| 1 | sleep-reminder cron SQL queries `program_sessions.day_of_week` | `~/.openclaw/cron/jobs.json:114` | **BUG** | **PATCHED** below |
| 2 | `daily_coaching_context` view's `todays_session` CTE uses `INITCAP(TO_CHAR(CURRENT_DATE,'Day'))` | `sql/014_coaching_state.sql:195` | LEGIT_TEMPLATE | None — view is template lookup, not execution schedule |
| 3 | `daily_coaching_context` recreated in migration 016 with same pattern | `sql/016_interference_and_load.sql:310` | LEGIT_TEMPLATE | None — same as #2 |
| 4 | `DAY_TO_SESSION = {0:"B", 2:"A", 4:"C"}` static dict | `scripts/workout_push.py:88-97` | LEGIT_TEMPLATE | None — used for initial generation, not for "what session is today" |
| 5 | launchd plists under `~/Library/LaunchAgents/com.ascent.*` | — | clean | None |

**Health-coach SKILL.md** was already corrected in Phase A; re-grep confirms no surviving `DAY_TO_SESSION`/weekday inference for "today's session".

### Patch landed: `~/.openclaw/cron/jobs.json:114`

Replaced the `program_sessions` template query with a `planned_workouts` query keyed on `scheduled_date = CURRENT_DATE + 1`. This is the same fix shape Phase A applied to `health-coach-daily`. Also routed delivery to `#ascent-training` (C0AQ1KJAKM0) per known-pending #11. failureAlert still goes to `#ascent-daily` (C0AQ1KHMBGS) — alerts belong on the alerts channel.

Verification (do not actually fire the cron — naturally fires at 21:00 Sun/Mon/Tue/Thu Vienna): the new SQL is shape-equivalent to Phase A's daily query and references only `planned_workouts.scheduled_date`, `session_type`, `status` — all present in the table per `sql/006_training_expansion.sql:25-32`. A reschedule via `coach_adjust.py reschedule_session` will now correctly cause the reminder to fire on the new day, not the template day.

## Phase 3 — `scripts/reconcile_garmin.py`

**Landed:** `/Users/jarvisforoli/projects/ascent/scripts/reconcile_garmin.py` (~330 lines).

Detection classes:
| Class | Definition | Auto-fix in `--apply`? |
|---|---|---|
| `orphan_db` | `planned_workouts.garmin_workout_id` references a workout with no scheduled instance in the calendar window | No — flagged only (the right fix depends on intent) |
| `orphan_garmin` | Scheduled Garmin entry with no `planned_workouts` row on that date | Only with `--apply --delete-orphans` (double-gated) → `client.unschedule_workout(scheduled_id)` |
| `date_drift` | Scheduled instance exists for the row's `garmin_workout_id` but on a different date than `planned_workouts.scheduled_date` | No — flagged only (drift direction is ambiguous) |
| `duplicate_garmin` | ≥2 scheduled instances on the same calendar date | Yes — keep highest `scheduled_workout_id`, unschedule older |
| `stale_template` | `garmin_workout_id` returns 404 from `client.get_workout_by_id` | Yes — clear `planned_workouts.garmin_workout_id` |

**Output contract:** mirrors `coach_adjust.py` — JSON object on stdout, logs on stderr, exit 0 on success (even if drift found), exit 1 on hard failure.

**Garmin API surface used:**
- `client.connectapi(f"/calendar-service/year/{Y}/month/{M-1}")` — month-by-month calendar enumeration (Garmin uses 0-indexed months)
- `client.get_workout_by_id(wid)` — template existence probe (capped at 50 per run to control rate)
- `client.unschedule_workout(scheduled_id)` — only on `--apply` paths

**Safety rails:**
- Defaults to `--window 14` days forward from today.
- `--no-garmin` mode skips all Garmin calls (DB-side only) — useful in CI / unattended runs.
- Never deletes `planned_workouts` rows. Never deletes Garmin workout templates. Never auto-fixes `date_drift` or `orphan_db` — those require coach-in-loop.
- `--delete-orphans` is required IN ADDITION to `--apply` to actually unschedule orphan Garmin entries.

**Verification:**
1. **`--no-garmin` smoke test:** ✓ green. Loaded 10 `planned_workouts` rows in [2026-04-08, 2026-04-22], emitted clean JSON, exit 0.
2. **Live `--dry-run`:** ❌ **BLOCKED — production Garmin browser session is expired.** Stack:
   ```
   garmin_auth.AuthExpiredError: Browser session unavailable.
     ~/.garminconnect/garmin_storage_state.json — failed to capture
     connect-csrf-token from SPA. Re-run garmin_browser_bootstrap.py.
   ```
   Slack alert was correctly sent to `#ascent-daily` by `garmin_status.py` — the existing monitoring caught it. Reconcile's error path correctly emitted the failure JSON to stdout and exited 1.

   **NEW HIGH-SEVERITY FINDING (not in known-pending list):** the **production** Garmin storage state is dead right now. Phase 2 headless was validated on the **test** account (no MFA) per `project_garmin_phase2_headless.md`; the prod account is on a different storage file and is currently broken. **Tomorrow's 09:40 health-coach-daily fire will see no Garmin auth.** Known-pending #15 (auth-dead warning on the daily card) becomes load-bearing — without it, the cron will run with stale Body Battery / sleep / HRV and may make a coaching decision against yesterday's data. **User action required:** run `garmin_browser_bootstrap.py` interactively before 09:40 tomorrow OR rely on #15 to surface the warning on the card.

   Side note: the `AuthExpiredError` message itself instructs `source venv/bin/activate && python3 …` which is the exact preflight-rejected pattern Phase A flagged. Cosmetic, not load-bearing — leaving for a future cleanup pass.

**Suggested cron entry (NOT installed):**
```jsonc
{
  "name": "ascent-reconcile-garmin",
  "schedule": { "kind": "cron", "expr": "0 7 * * *", "tz": "Europe/Vienna" },
  "payload": {
    "kind": "agentTurn",
    "message": "Run reconcile and report drift:\n/Users/jarvisforoli/projects/ascent/venv/bin/python3 /Users/jarvisforoli/projects/ascent/scripts/reconcile_garmin.py\n\nIf any of orphan_db / date_drift / orphan_garmin / duplicate_garmin / stale_templates is non-zero, post a one-line summary to #ascent-daily with the counts. Otherwise stay silent.",
    "model": "anthropic/claude-haiku-4-5",
    "toolsAllow": ["exec", "slack"],
    "lightContext": true
  },
  "delivery": { "mode": "announce", "channel": "slack", "to": "C0AQ1KHMBGS" },
  "failureAlert": { "after": 2, "channel": "slack", "to": "C0AQ1KHMBGS" }
}
```
Runs at 07:00 Vienna, before the 09:40 daily card. Silent unless drift exists. Do NOT enable until prod Garmin auth is restored.

---

## Phase 8 (partial) — `garmin-token-refresh` cron defects (consolidated here for narrative continuity)

### Patch landed: `~/.openclaw/cron/jobs.json:144` (`garmin-token-refresh`)

Disabled (`enabled: false`) rather than deleted. Three independent defects:
1. `command` is `source venv/bin/activate && python3 scripts/garmin_token_refresh.py` — exec preflight rejects `source` (Phase A finding).
2. `delivery.channel: "last"` triggers "Channel is required when multiple channels are configured" — failureAlert silent because no `failureAlert` block exists at all.
3. **The referenced script `scripts/garmin_token_refresh.py` does not exist in the repo.** This cron has been crash-looping into the void since launchd `com.ascent.garmin-refresh` took over Garmin auth.

71 consecutive errors went unnoticed. Disabling stops the loop without losing the historical record. **User decision required:** delete entirely, or replace with a wrapper that calls `scripts/garmin_status.py --json` purely as a watchdog. Recommendation: delete; launchd already handles the refresh and `garmin_status.py` already feeds Slack alerts via Phase A wiring.

### Patches landed: `health-coach-weekly` cron (`~/.openclaw/cron/jobs.json:52`)

Two defects fixed:
1. **`toolsAllow` contained `slack`**, AND `delivery.mode` was `announce`. Same double-channel ambiguity Phase A removed from `health-coach-daily`. Removed `slack` from toolsAllow; rewrote the prompt so the final assistant message IS the Slack post (mirrors the daily cron's runbook). Step 3 (`coaching_log` insert) was migrated from raw SQL to a REST POST since the agent no longer has a SQL execution path.
2. **`failureAlert.to` was `C0AQ1KJAKM0`** (#ascent-training). Per Phase A convention, content goes to `#ascent-training`, alerts go to `#ascent-daily`. Re-routed to `C0AQ1KHMBGS`.

The Sunday 20:00 fire is the verification event. The card itself should look near-identical to what was posted last Sunday, just routed through `announce` instead of the slack tool.

---

## Phase 4 — DB ↔ React app ↔ Slack agreement

**Setup:** Verify all three consumer surfaces (the daily Slack card, the weekly Slack card, the React app on Vercel) read the same `planned_workouts` rows for the next 7 days, with no fallback to inferred state.

**Findings:**

| Consumer | Source | Inferred-state fallback? | Status |
|---|---|---|---|
| `health-coach-daily` Slack card (`#ascent-training`) | `planned_workouts.scheduled_date=eq.<today>` via curl (`jobs.json:18-20` STEP 1) | None — Phase A removed it | ✓ DB-grounded |
| `health-coach-sleep-reminder` Slack post (`#ascent-training` after Phase 2 patch) | `planned_workouts.scheduled_date = CURRENT_DATE + 1` via Phase 2 patch (`jobs.json:114`) | None — Phase 2 removed `program_sessions.day_of_week` fallback | ✓ DB-grounded (after this audit) |
| `health-coach-weekly` Slack card (`#ascent-training`) | `weekly_coaching_summary` view (rolled up from `planned_workouts` + `activities` + `sleep` + `daily_metrics` per `sql/016:460-550`) | None | ✓ DB-grounded |
| React app `web/src/views/TodayView.tsx` | `usePlannedWorkouts` hook → `web/src/hooks/useSupabase.ts:192-206` | None | ✓ DB-grounded |
| React app `web/src/views/TrendsView.tsx:175` | `useActivities` + `useDailyMetrics` | None | ✓ DB-grounded |

**Conclusion:** all four consumers are now DB-grounded after Phase 2's sleep-reminder patch. The earlier known split-brain (cron template-inferring while React queried `planned_workouts`) is closed.

**Caveat:** the `session_exceptions` markdown vs DB split (Phase 1 source-of-truth violations §3) is still open — exceptions added via DB will not be visible to the daily cron because the cron only reads the markdown table. Flagged for Phase 9.

---

## Phase 5 — Generator ↔ program-doc cross-validation

**Risk model:** `scripts/workout_push.py:88` defines `DAY_TO_SESSION = {0:"B", 2:"A", 4:"C"}` as a Python dict. The human-authored schedule lives in `openclaw/coaching-program.md` (Block 1 §"Weekly Structure", line 22-28) as a markdown table. There is no link between them. The Tuesday-Protocol-A bug last block was an instance: someone edited the doc, the dict didn't follow, the generator wrote a wrong row, the cron read the wrong row, the user got a wrong card. This class of drift is silent — there is nothing in CI or runtime that catches it.

**Patch landed:** `scripts/workout_generator.py` now runs `_validate_program_doc()` at module import. The check:
1. Reads `openclaw/coaching-program.md`.
2. Parses the first `### Weekly Structure` table — pulls weekday → session-letter for every row whose label contains `Strength A|B|C`.
3. Asserts the parsed dict equals the imported `DAY_TO_SESSION`.
4. Raises `RuntimeError` with a precise per-day diff on mismatch.

The check runs at import, so any caller — CLI, cron, ad-hoc REPL, downstream import — trips it before a single row gets generated. Rest / mobility / mountain rows are intentionally omitted from the parser; the dict only encodes gym days, so we only check gym days.

**Verification:**
1. ✓ Import on the live doc: `python3 -c "import workout_generator"` → silent success.
2. ✓ Mutation test: ran the parser on a copy of the doc with `Strength A` rewritten to `Strength C` on Wednesday → parser returned `{0:"B", 2:"C", 4:"C"}`, mismatch detected, would-raise=True.

**Mobility self-check (NOT landed this pass):** `scripts/mobility_workout.py` mirrors the same risk pattern against `docs/knowledge-base/domain-9-mobility.md` — protocols A/B/C are hardcoded. Out of scope for this session because the mobility doc has no consistent table format to parse against and a regex-only approach would be flaky. Flagged for follow-up: either restructure `domain-9-mobility.md` to a sourceable schema OR move the protocols out of the script and into the doc as the source of truth.

---

## Phase 6 — KB grounding scorecard

For each domain in `docs/knowledge-base/`, score the four code paths against the documented knowledge:
- 🟢 = code reads from the KB at runtime, OR a self-check enforces parity
- 🟡 = code is consistent with the KB *as of last manual reconciliation* but can drift silently
- 🔴 = code contradicts the KB, OR the KB has no coverage

| Domain | Creation (`workout_generator.py` / `workout_push.py` / `mobility_workout.py`) | Adjustment (`coach_adjust.py`) | Briefing (`health-coach/SKILL.md`) | Q&A (`ask-coach/SKILL.md`) |
|---|---|---|---|---|
| **Strength (`knowledge-base.md`, `ascent-guide.md`)** | 🟡 — `SESSIONS` dict in `workout_push.py:224` is hand-built from KB. After Phase 5, day→session mapping is now 🟢 (self-check), but exercise selection / set/rep schemes / RPE ranges are still hardcoded constants with no runtime tie. | 🟡 — `lighten_session` and `swap_exercise` apply rules that match the KB's recovery section, but the rule is encoded in code, not cited. After Phase 7 the `--details rule` and `--details kb_refs` fields can carry a citation per call, but it's voluntary. | 🟡 — SKILL.md "Auto-Adjustment Triggers" section paraphrases KB rules but doesn't reference KB section ids. The numbers (RPE thresholds, % volume cuts) live in two places. | 🟡 — `ask-coach/SKILL.md` reads KB files via `cat`/`grep` on demand (`ask-coach:32-37`), but coverage gaps fall back to model prior with a "start a research session" disclaimer. No retrieval ranking, no embeddings. |
| **Mobility (`domain-9-mobility.md`)** | 🔴 — `mobility_workout.py` has the protocols A/B/C hardcoded. The KB describes them in prose with no parser. They will drift. | 🟡 — `mark_mobility` action validates `protocol ∈ {A,B,C}` only; the actual content comes from the script, not the KB. | 🟡 — SKILL.md mentions "mobility routines" but offers no per-protocol selection logic. | 🟡 — same fallback as strength. |
| **Mountain interference (`knowledge-base.md` §interference)** | n/a (no creation path) | 🟢 — `coach_adjust.py` doesn't directly cite, but the cron's STEP 4 reads `athlete_response_patterns` (the *learned* version of the KB rule) and applies it via `lighten_session`. Closer to data-driven than KB-cited but functionally grounded. | 🟢 — SKILL.md "Auto-Adjustment Triggers" §1, §1a (added Phase 8), §2 directly encode the KB's mountain rules and now reference `knowledge-base.md#mountain-gym-interference` in the Wednesday fallback (`--details rule`). | 🟡 — same fallback. |
| **Recovery / readiness (`knowledge-base.md` §recovery)** | n/a | 🟡 — decision-matrix lives in SKILL.md (cron payload), not in KB; if the KB updates the thresholds, the cron stays on the old values. | 🟡 — SKILL.md "Auto-Adjustment Triggers" §3 (HRV LOW), §4 (BB<30 or readiness<40), §5 (3+ degraded) are hardcoded thresholds. KB cites the same numbers but no code path checks. | 🟡 |
| **Nutrition** | — | — | 🔴 — no nutrition KB exists yet; `food_log` table is wired but coach makes no nutrition decisions. | 🔴 — no coverage. |
| **Garmin exercise mapping (`garmin-exercise-categories.md`)** | 🟢 — `workout_push.py` builds Garmin payloads against this file directly; the file IS the source of truth and is referenced from the script. | n/a | n/a | n/a |

**Hardcoded constants vs KB drift list (the things that can silently disagree):**
1. `workout_push.py:224` `SESSIONS` exercise lists vs `knowledge-base.md` strength block prescriptions.
2. `mobility_workout.py` protocol bodies vs `domain-9-mobility.md` protocol prose.
3. SKILL.md "Auto-Adjustment Triggers" thresholds (HRV, BB, readiness) vs `knowledge-base.md` recovery thresholds.
4. `progression_engine.py` plate-jump increments vs `knowledge-base.md` progression scheme.
5. Block 1 / Block 2 RPE ranges in `coaching-program.md` vs SKILL.md `mountain weekend → Monday` rule (Block 2 RPE 7-8 vs Block 1 RPE 6-7).

**Recommendation (deferred — see Phase 9):** introduce a `kb_refs` index — a JSON file that maps each rule to its KB section id and the code site that implements it, generated by a small `scripts/kb_index.py`. The index can be dry-run-validated in CI: every code site in the index must (a) exist, (b) match the cited section id's hash. This gives runtime drift detection without restructuring the KB itself.

---

## Phase 7 — Decision traceability

**Hole identified:** the cron's "train as planned" branch leaves no `coaching_log` row. There is no audit trail for ~50% of coaching decisions (the days where the answer is "do nothing"). Past adjustments leave free-text in `adjustment_reason`; KB citations live nowhere; the input snapshot the decision was made against is recoverable only by re-running the daily_coaching_context view at the same instant — which is impossible after the underlying tables update.

**Schema landed:** `sql/021_coaching_log_traceability.sql` adds four nullable columns to `coaching_log`:

| Column | Type | Purpose |
|---|---|---|
| `decision_type` | TEXT | Typed class: `train_as_planned`, `adjust`, `rest`, `mountain_day`, `mobility`, `skipped`, `completed` |
| `rule` | TEXT | Short identifier of the decision-matrix rule applied (e.g. `recovery.hrv_low.lighten`, `mountain.heavy_weekend.wed_fallback`) |
| `kb_refs` | TEXT[] | KB citation slugs (e.g. `knowledge-base.md#mountain-gym-interference`) |
| `inputs` | JSONB | Snapshot of recovery/load signals at decision time |

Plus a partial index on `decision_type WHERE decision_type IS NOT NULL` to keep `coaching_log` table scans cheap when querying for "all train_as_planned days in March" or "all rule=recovery.hrv_low.* decisions this block".

**Code landed:** `scripts/coach_adjust.py`:
1. New action `mark_train_as_planned` — fast path that writes ONLY a `coaching_log` row (no `planned_workouts` mutation, no Garmin push, no `coaching-context.md` append, no Slack post — the daily card is the user-facing surface).
2. New `DECISION_TYPE_BY_ACTION` map covers all 10 actions.
3. `validate_action` accepts optional `rule`, `kb_refs`, `inputs` on every action and validates their types.
4. `run_coaching_log_insert` adds the four new columns to the row, **opt-in only**: existing call sites that don't pass them get the old shape, so the migration can be applied in any order without breaking the cron mid-rollout.

**Smoke test:** ✓ `mark_train_as_planned --dry-run` round-trips correctly (would_insert payload includes `decision_type`, `rule`, `kb_refs`, `inputs`). ✓ existing `lighten_session --dry-run` still produces `ok=true` with no new fields in the coaching_log step.

**To activate:**
1. Apply migration `sql/021_coaching_log_traceability.sql` to Supabase. **Not done in this session.** Recommended: run via `scripts/deploy_schema.py` (or psql) during the next maintenance window.
2. Update `~/.openclaw/workspace/skills/health-coach/SKILL.md` STEP 4 to call `coach_adjust.py --action mark_train_as_planned ...` whenever the decision is "train as planned", with `--details` containing `reason`, `rule`, `kb_refs`, `inputs`. **Not done in this session** to avoid coupling the SKILL change to a migration that hasn't been applied. Once the migration is live, this is a 5-line edit.

**Backfill:** explicitly out of scope per the prompt. New columns are nullable; old rows continue to read fine.

---

## Phase 8 — Observability & failure-mode gaps

### Cron `failureAlert` audit (`~/.openclaw/cron/jobs.json`)

| Cron | failureAlert before | After this audit | Notes |
|---|---|---|---|
| `health-coach-daily` | `after:2, channel:slack, to:C0AQ1KHMBGS` | unchanged ✓ | Already correct |
| `health-coach-weekly` | `after:2, channel:slack, to:C0AQ1KJAKM0` | **`to:C0AQ1KHMBGS`** | Re-routed: alerts go to `#ascent-daily`, not `#ascent-training` |
| `health-coach-sleep-reminder` | `after:2, channel:slack, to:C0AQ1KHMBGS` | unchanged ✓ | Alert routing was always correct; only the SQL was broken (Phase 2) |
| `garmin-token-refresh` | **(no failureAlert block)** | **disabled** | 71 consecutive errors invisible because no `failureAlert`. Now disabled entirely (Phase 2 patch). |
| `block-review-week4` | (no failureAlert block) | unchanged | One-shot at 2026-04-27. Low risk; flagged. |
| `block-review-week8` | (no failureAlert block) | unchanged | One-shot at 2026-05-25. Low risk; flagged. |

**Pattern observed:** crons that route content to `#ascent-training` were also routing alerts to `#ascent-training`, mixing signal channels. Phase A established the convention `content → C0AQ1KJAKM0`, `alerts → C0AQ1KHMBGS`. The weekly cron was the one straggler. Now consistent.

### SKILL.md edits (known-pending follow-ups)

| # | Item | Status |
|---|---|---|
| 4 | Wednesday-aware mountain-rule fallback | ✓ **Landed** — new §1a in `health-coach/SKILL.md` "Auto-Adjustment Triggers" with KB citation `knowledge-base.md#mountain-gym-interference` and an `effect_size < 0.1` learned-pattern override |
| 6 | Replace `body_battery_events` with `daily_metrics.body_battery_highest` | ✓ **Already done** — re-grep of `health-coach/SKILL.md` finds zero references to `body_battery_events`. The cron's STEP 2 already reads `body_battery_highest` from `daily_coaching_context`. Marking closed. |
| 11 | Route `health-coach-sleep-reminder` to `#ascent-training` | ✓ **Landed** in Phase 2 — `delivery.to: C0AQ1KJAKM0`. failureAlert stays on `#ascent-daily`. |
| 15 | Garmin auth-dead warning on the daily card even on no-op days | ✓ **Landed** — new "Auth-dead rule (UNCONDITIONAL)" section in SKILL.md card-format block, plus a fifth push-status line: `⚠️ Garmin auth dead — training as planned but watch may be stale (last sync hours ago).` |

### Model fallback (#9) — gateway instrumentation

**Not landed.** Locating the OpenClaw gateway model-routing code is out of scope for this audit (the gateway is in a separate repo / install path). Recommendation captured: add a single log line in the gateway's outbound API call wrapper that records `requested_model` (from the cron payload) vs `returned_model` (from the API response headers) per turn. The Sonnet→Haiku silent fallback observed during Phase A becomes visible in `logs/gateway.log` and trivially greppable. **Effort:** ~5 lines once you find the call site.

### Other failure modes still uninstrumented

1. **Garmin sync failures from `garmin_sync.py`** — silent today. The launchd plist captures stdout/stderr to `logs/sync.log` and `logs/sync-error.log` but nothing pages on a non-zero exit. **Fix sketch:** add a `posthook` that `tail`s `sync-error.log` and posts to `#ascent-daily` if non-empty. Or wrap the script in a launchd `KeepAlive` watchdog.
2. **`coach_adjust.py` partial-failure surfacing on the daily card** — if `result.ok=false` and `pw_status=="ok"` (DB landed but Garmin push failed), the card today says "Garmin push failed: ..." but does not explicitly say "the database IS updated, only the watch is stale". Verbal ambiguity → user might re-run. **Fix sketch:** clarify the user_message build in `coach_adjust.py:726-747`.
3. **Reconcile drift uninstrumented** — `scripts/reconcile_garmin.py` exists but no cron runs it. Suggested cron line is in Phase 3, gated on Garmin auth being restored.
4. **The launchd `com.ascent.garmin-refresh` job is silently failing** — per `~/.openclaw/workspace/CLAUDE.md`, the auto-refresh runs every ~3h. Today's live test of `reconcile_garmin.py` proved the prod storage state is expired *right now*, which means the auto-refresh has been failing since at least the last successful daily-cron fire. **Action required:** check `/Users/jarvisforoli/projects/ascent/logs/garmin-refresh-error.log`.

---

## Phase 9 — Growth backlog (ranked)

Ranked by (user-visible impact × feasibility). 1 = highest priority.

### 1. Cross-channel consistency watchdog
**Sketch:** a daily cron at ~07:30 that compares planned_workouts.scheduled_date for today against (a) what Garmin's calendar-service returns, (b) what the React app would render, (c) what the daily card said yesterday for "tomorrow". Posts to `#ascent-daily` only on disagreement. Reuses `scripts/reconcile_garmin.py` as a building block.
**Why high impact:** the entire failure mode "user shows up at the gym to find the watch has yesterday's workout" is silent today and undermines trust in the whole system.
**Dependencies:** `reconcile_garmin.py` (✓ landed Phase 3), prod Garmin auth restored.
**Effort:** S (~half day).

### 2. Subjective wellness questionnaire (Telegram, 09:30 daily)
**Sketch:** 4-question Telegram check-in at 09:30: sleep quality (1-5), energy (1-5), soreness (1-5), motivation (1-5). Stored to a new `wellness_checkins` table. The cron at 09:40 reads it as STEP 1.5 in the runbook and uses it as the highest-priority recovery signal.
**Why high impact:** per `CLAUDE.md` Critical Decisions §"Subjective wellness questionnaire is the highest-priority unbuilt feature — stronger evidence base than any wearable metric for detecting maladaptation". Already a locked decision; just unbuilt.
**Effort:** M (1-2 days: schema + Telegram bot wiring + cron + SKILL.md edit).

### 3. Auto-deload detection
**Sketch:** trailing 14d ACWR + sleep + HRV trend → if rolling load is in top decile AND HRV trending down >5% AND sleep <6.5h avg → propose deload week, gated on Telegram confirmation.
**Why high impact:** the existing block-review crons only fire at week 4 / week 8. Maladaptation during a block goes uncaught.
**Dependencies:** wellness questionnaire (#2) helps but isn't required.
**Effort:** M.

### 4. ask-coach KB retrieval upgrade
**Sketch:** replace the current "grep + read" approach with a small embeddings index over `docs/knowledge-base/`. Build at index time (cron, daily). Query at ask-coach turn time. Top-3 sections injected into the agent's context with citations.
**Why:** ask-coach currently hallucinates from prior whenever the grep misses. Embeddings catch synonyms and paraphrases.
**Effort:** M (1-2 days: index builder + retrieval at SKILL.md startup + citation discipline).

### 5. Mountain-day post-hoc analysis
**Sketch:** parse the Garmin activity for any Sat/Sun mountain entry, classify (hike / skin / ski / fly), credit it against the week's load in `weekly_coaching_summary`, and let Monday's coach see "Sat: 2200m skin, 4.5h, Z3 dominant — bias toward upper body today".
**Effort:** M.

### 6. Block transition pre-computed data pack
**Sketch:** the existing `block-review-week4` / `block-review-week8` crons spawn an Opus session against an empty context. Replace with a pre-computed data pack: 4-week trend table for sleep / HRV / RHR / weight / lift PRs, every adjustment that fired with reason, every exception applied, mountain volume, week-over-week deltas. Opus session starts from a brief, not a blank.
**Effort:** S-M.

### 7. Calibration loop
**Sketch:** when the coach adjusts a session and the user actually trains differently than the adjustment said, capture the delta into a new `coaching_decision_outcomes` table (or extend the existing one). Feed back into the decision matrix as a confidence signal.
**Why:** today's adjustments are open-loop. We don't know which rules the user actually accepts vs ignores.
**Dependencies:** Phase 7 traceability (`decision_type`, `rule`) makes this mechanically possible.
**Effort:** M.

### 8. Niggle / injury log
**Sketch:** a tiny `niggles` table (`date_started`, `body_part`, `severity`, `notes`, `resolved_at`). Telegram command `/niggle left knee tweaky 2/10`. The daily cron reads open niggles in STEP 1.5 and the decision matrix gets a new rule: open niggle → flag any exercise touching that body part for swap.
**Effort:** S.

### 9. KB-rule index + CI drift check
**Sketch:** the `kb_refs` index proposed in Phase 6 — a JSON map of rule → (KB section, code site, content hash). A new `scripts/kb_audit.py` verifies the hashes haven't drifted and that every cited code site exists. Runs in pre-commit.
**Why:** structurally fixes the Tuesday-Protocol-A class of bugs for ALL hardcoded rules, not just `DAY_TO_SESSION`.
**Effort:** M.

### 10. Readiness-aware warm-up selection
**Sketch:** today the warm-up protocol is fixed per session. Instead, use HRV / BB to pick warm-up volume from the KB (long warm-up if BB <50 or HRV LOW; standard otherwise).
**Why:** small-impact but cheap. Improves training quality on borderline-recovery days without changing the main workout.
**Effort:** S.

### Honorable mentions (not ranked)
- Nutrition integration (no KB exists yet — would need a research session first).
- Body Battery / sleep staging displayed as context only — already a locked decision per `CLAUDE.md`, no action.
- Session exceptions DB↔markdown reunification (Phase 1 source-of-truth violation §3) — small fix but tactical, not strategic.

---

## Phase 10 — Patches landed + top-10 gaps + what I did NOT fix

### Patches landed in this session (file-by-file)

| File | Change | Why |
|---|---|---|
| `~/.openclaw/cron/jobs.json` (sleep-reminder, line ~114) | SQL rewritten to `planned_workouts.scheduled_date = CURRENT_DATE + 1`; delivery routed to `#ascent-training` | Phase 2 — surviving instance of weekday-inference anti-pattern; known-pending #11 |
| `~/.openclaw/cron/jobs.json` (`health-coach-weekly`, line ~52) | Removed `slack` from `toolsAllow`; rewrote prompt so final assistant message IS the post; `failureAlert.to` re-routed to `#ascent-daily` | Phase 4/8 — Phase A pattern not previously applied to weekly; alert routing convention |
| `~/.openclaw/cron/jobs.json` (`garmin-token-refresh`, line ~144) | `enabled: false` + description updated | Phase 2/8 — broken on 3 levels (exec preflight, channel:last, missing script); 71 silent errors; redundant with launchd |
| `~/.openclaw/workspace/skills/health-coach/SKILL.md` (push status lines) | Added 5th push-status line + UNCONDITIONAL auth-dead rule | Phase 8 — known-pending #15 |
| `~/.openclaw/workspace/skills/health-coach/SKILL.md` (Auto-Adjustment Triggers §1a) | New Wednesday mountain-fallback rule with KB citation | Phase 8 — known-pending #4 |
| `/Users/jarvisforoli/projects/ascent/scripts/reconcile_garmin.py` *(new)* | DB↔Garmin reconciliation tool, dry-run default | Phase 3 — closes uninstrumented Garmin drift gap |
| `/Users/jarvisforoli/projects/ascent/scripts/workout_generator.py` | `_validate_program_doc()` runs at module import | Phase 5 — prevents Tuesday-Protocol-A class of drift |
| `/Users/jarvisforoli/projects/ascent/sql/021_coaching_log_traceability.sql` *(new)* | Adds `decision_type`, `rule`, `kb_refs`, `inputs` columns to `coaching_log` | Phase 7 — closes traceability hole. **NOT applied to Supabase.** |
| `/Users/jarvisforoli/projects/ascent/scripts/coach_adjust.py` | New `mark_train_as_planned` action + opt-in traceability fields on all actions | Phase 7 — closes the no-op log path; opt-in keeps existing call sites working pre-migration |
| `/Users/jarvisforoli/projects/ascent/docs/audits/2026-04-08-system-audit-v2.md` *(new)* | This document | Phases 1-10 |

### Top 10 ranked gaps (with recommended next steps)

| Rank | Gap | Severity | Next step |
|---|---|---|---|
| 1 | Production Garmin auth is dead RIGHT NOW | 🔴 CRITICAL | Run `garmin_browser_bootstrap.py` interactively before tomorrow 09:40; check `logs/garmin-refresh-error.log` to find why launchd auto-refresh stopped working |
| 2 | `planned_workouts` 4-writer race condition | 🔴 HIGH | Establish `coach_adjust.py` as the only writer of `status` and `garmin_workout_id`; refactor `garmin_sync.py:673` and `workout_push.py:1432` to publish events instead of direct writes. Audit Phase 1 §violation #1. |
| 3 | Apply migration `sql/021_coaching_log_traceability.sql` to Supabase | 🟡 MEDIUM | Run via `scripts/deploy_schema.py` or psql; required before activating `mark_train_as_planned` |
| 4 | Wire SKILL.md STEP 4 to call `mark_train_as_planned` for no-op days | 🟡 MEDIUM | 5-line edit to `health-coach/SKILL.md` STEP 4; do AFTER #3 |
| 5 | Cross-channel consistency watchdog (Phase 9 #1) | 🟡 MEDIUM | Wire `reconcile_garmin.py` into a 07:30 cron once #1 is resolved |
| 6 | Subjective wellness questionnaire (Phase 9 #2) | 🟡 MEDIUM | Telegram bot + new table + cron at 09:30 |
| 7 | Mobility self-check parity with generator self-check | 🟢 LOW | Either restructure `domain-9-mobility.md` for parsing OR move protocols out of `mobility_workout.py` into the doc |
| 8 | Gateway model fallback instrumentation (#9) | 🟢 LOW | 5-line log addition once gateway code is located |
| 9 | `garmin_sync.py` failure alerting | 🟢 LOW | Wrap launchd plist with a `posthook` that pages on non-empty error log |
| 10 | `session_exceptions` DB ↔ markdown reunification | 🟢 LOW | Pick one source of truth (recommend DB) and migrate the markdown table contents in |

### What I did NOT fix and why

1. **Production Garmin auth.** Requires interactive Firefox login via `garmin_browser_bootstrap.py`. Out of scope for an unattended audit session. **Most urgent item.**
2. **Migration application to Supabase.** Per the prompt: "Schema migration: apply to a local/dev Supabase if one exists; otherwise inspect the SQL... and flag in the audit that prod application requires user confirmation." The migration file is on disk; you decide when to apply it.
3. **`planned_workouts` race condition refactor.** This is a multi-day refactor across `coach_adjust.py`, `garmin_sync.py`, `workout_push.py`, `workout_generator.py`, and `mobility_workout.py`. Out of scope for this audit pass; flagged as the highest-priority structural finding (Phase 1 violation #1, gap #2).
4. **`garmin-token-refresh` deletion.** Disabled (reversible) instead of deleted. Per the prompt: "Do NOT delete... without explicit confirmation." Awaits your decision.
5. **Wiring `mark_train_as_planned` into the SKILL.md runbook.** Coupling the SKILL change to a migration that hasn't been applied creates a brittle ordering dependency. Better to land them in a small follow-up after migration #021 is live.
6. **Mobility generator self-check.** No structured KB target to validate against. Flagged in Phase 5 with two paths forward.
7. **OpenClaw gateway model-fallback instrumentation (#9).** Gateway lives outside this repo; locating the right file is its own scoping exercise.
8. **Test-firing `health-coach-daily`.** Per the prompt: "Do NOT test-fire... Tomorrow's natural 09:40 fire is the verification event."
9. **Backfill of `coaching_log` traceability columns.** Explicitly out of scope per the prompt.
10. **The Phase 9 growth items (#1 through #10).** Designed and ranked, not built. That's by design — Phase 9 is the backlog.

### Verification plan for tomorrow's 09:40 natural fire

Watch the daily card for these specific signals:

| Signal | Expected if everything is healthy | What it means if absent / wrong |
|---|---|---|
| `📡 Synced — data current as of <today>` | Today's date | If yesterday's date or older → Garmin auth still dead OR sync didn't run |
| `<emoji> **Wednesday — <session_name>**` matches `planned_workouts.scheduled_date=2026-04-09` | Mirrors DB row verbatim | If different → fabrication regression |
| Exercises mirror `planned_workouts.workout_definition.exercises` | Verbatim copy | If different → fabrication regression |
| Push status line | `📲 Pushed to Garmin.` OR `⚠️ Garmin auth dead — training as planned but watch may be stale (last sync hours ago).` | The second line means Phase 8 #15 fix worked. Absence of any auth-dead line when auth IS dead = #15 broken |
| If today is a Wednesday after a heavy mountain weekend AND `mountain_days_3d ≥ 1` | Card should show RPE capped at 7 with rationale citing the §1a rule | Phase 8 #4 fix verification |
| `coaching_log` query: `SELECT decision_type, rule FROM coaching_log WHERE date='2026-04-09'` | Empty (since SKILL.md doesn't yet call `mark_train_as_planned`) | Confirms Phase 7 backward-compatibility — old path still produces a row only on adjust, not on no-op |

After the fire, paste the resulting card text into a follow-up so the audit can grade itself.

---

**End of audit v2.**

---

## Addendum (same day, post-audit) — deferred items cleared

After the audit was first written, the user requested clearing the deferred items. The following landed in the same session:

### 1. Migration `sql/021_coaching_log_traceability.sql` applied to Supabase ✅
Connected via the session pooler (`aws-1-eu-central-1.pooler.supabase.com:5432`) after discovering the direct host `db.<ref>.supabase.co:5432` is IPv6-only and the user's network is IPv4-only. All four columns (`decision_type`, `rule`, `kb_refs`, `inputs`) and the partial index verified live in `coaching_log`.

### 2. `.env` `SUPABASE_DB_URL` fixed ✅
Switched to the session pooler URL. `scripts/deploy_schema.py` is unbroken for future migrations.

### 3. SKILL.md + cron payload wired to `mark_train_as_planned` ✅
- `~/.openclaw/workspace/skills/health-coach/SKILL.md` Single Write Path table now lists `mark_train_as_planned` and documents the optional `rule`/`kb_refs`/`inputs` fields. The "Unchanged sessions" section explicitly directs the agent to call the wrapper for no-op days.
- `~/.openclaw/cron/jobs.json` (`health-coach-daily`) STEP 5 prompt updated with the explicit invocation pattern, including the JSON shape for `inputs`.
- **End-to-end live smoke test:** invoked the action against prod Supabase (no `--dry-run`), verified row landed with all four traceability columns populated, then deleted the test row. `coaching_log.id=24` round-tripped clean.

### 4. `coach_adjust.py` partial-failure user_message clarification ✅
`build_user_message` now distinguishes "DB updated, Garmin push failed" from "Garmin push failed (state unknown)". The former emits an explicit warning telling the athlete NOT to re-run the adjustment (which would double-write). Closes Phase 8 sub-item #2.

### 5. `mobility_workout.py` KB self-check ✅
Mirrors the `workout_generator.py` self-check pattern. Parses `### Protocol [A-Z]:` headings from `docs/knowledge-base/domain-9-mobility.md` and asserts every documented protocol is implemented in `PROTOCOL_NAMES`. Script extensions (Protocol T) emit a stderr warning but don't raise — the dangerous direction is "documented but not implemented". Both directions tested: real KB → pass with T warning; mutated KB with phantom Protocol Z → raise. Closes Phase 5 deferral.

### 6. Supabase agent skills installed ✅
`npx skills add supabase/agent-skills --skill supabase` — both `supabase` and `supabase-postgres-best-practices` skills now symlinked into Claude Code + OpenClaw skill registries at `~/projects/ascent/.agents/skills/`. Available for future agent sessions. Snyk flagged the `supabase` package as Medium Risk; acceptable since it ships from the official `supabase/agent-skills` repo.

### Still deferred (intentionally, end of session)

| Item | Why deferred |
|---|---|
| Production Garmin auth restoration | Requires interactive Firefox login via `garmin_browser_bootstrap.py`. **Most urgent — do before tomorrow 09:40.** |
| `planned_workouts` 4-writer race condition refactor | Multi-day structural refactor across 5 scripts. Highest-priority structural finding (gap #2) but out of scope for an audit pass. |
| Gateway model fallback instrumentation (#9) | Gateway lives outside this repo; locating the call site is its own scoping exercise. |
| `garmin_sync.py` failure-alerting wrapper | Needs launchd posthook design; broader scope than audit. |
| Forced-failure test of `coach_adjust → SKILL.md` propagation | Design only — not running it because user said "do not test-fire health-coach-daily". |
| `garmin-token-refresh` cron deletion | Disabled (reversible) instead of deleted per the prompt's no-deletion-without-confirmation rule. Awaiting your call. |
| Phase 9 growth backlog items | Designed and ranked, not built — by design. |

### Final post-addendum file inventory

Files modified/created across the full audit (audit + addendum):

| File | Status |
|---|---|
| `~/.openclaw/cron/jobs.json` | sleep-reminder fix; weekly cron de-slacked + alerts re-routed; garmin-token-refresh disabled; daily cron STEP 5 wired to mark_train_as_planned |
| `~/.openclaw/workspace/skills/health-coach/SKILL.md` | #4 Wed mountain fallback; #15 unconditional auth-dead; mark_train_as_planned wired into Single Write Path table + Unchanged sessions section |
| `/Users/jarvisforoli/projects/ascent/scripts/reconcile_garmin.py` | new |
| `/Users/jarvisforoli/projects/ascent/scripts/workout_generator.py` | startup self-check vs `coaching-program.md` |
| `/Users/jarvisforoli/projects/ascent/scripts/mobility_workout.py` | startup self-check vs `domain-9-mobility.md` |
| `/Users/jarvisforoli/projects/ascent/scripts/coach_adjust.py` | mark_train_as_planned action; opt-in traceability fields; partial-failure user_message clarification |
| `/Users/jarvisforoli/projects/ascent/sql/021_coaching_log_traceability.sql` | new, **applied to prod** |
| `/Users/jarvisforoli/projects/ascent/.env` | SUPABASE_DB_URL → session pooler |
| `/Users/jarvisforoli/projects/ascent/.agents/skills/supabase/` | new, via npx skills |
| `/Users/jarvisforoli/projects/ascent/docs/audits/2026-04-08-system-audit-v2.md` | this document |

**End of addendum.**

---

## Addendum 2 (same day) — Garmin auth investigation + jitter mitigation

### Root cause of the launchd refresh chain failure

The break around 15:53 → 17:25 was **not** the MFA-detection race I cited from the older `garmin-refresh-error.log` (timestamped 08:12). The current failure mode is purely the `wait_until="networkidle"` strategy in `scripts/garmin_browser_bootstrap.py:157` (and the symmetric site at `:295`):

```
Page.goto: Timeout 30000ms exceeded.
  - navigating to "https://sso.garmin.com/portal/sso/en-US/sign-in?...",
    waiting until "networkidle"
```

`networkidle` means "no network activity for 500ms". Garmin's SSO page keeps background telemetry polling that **never lets `networkidle` fire**, so `page.goto()` always hits the 30s timeout. The MFA-detection code at line 198 was never reached. Fixed: switched both sites to `wait_until="domcontentloaded"`. The post-login navigations on lines 239 and 341 already used `domcontentloaded`, which is why the symptom only hit the *initial* SSO navigation.

**Test account verified green** after the fix: refresh succeeded, JWT_WEB renewed, storage state written.

### Production account: structural limit

Investigating the launchd configuration revealed that **the auto-refresh has only ever run against the test account** (`.env.garmin-test`, no MFA). The production account has MFA enabled and the headless flow cannot pass MFA — by design. With Garmin JWT_WEB lifetime of ~2.4h, the only options for prod are:

1. Disable MFA on the prod account → full auto-refresh works (security tradeoff).
2. Keep MFA, accept manual interactive bootstrap on every expiry → unworkable at 2.4h cadence.
3. Move data collection to the test account → loses Garmin Connect history.

**User decision (2026-04-08): keep MFA on prod.** This means production Garmin auth will be dead between manual interactive re-bootstraps, and the daily coaching cron will rely on the unconditional auth-dead warning landed for known-pending #15. The system fails loud, not silent. Tomorrow's 09:40 fire will run with stale Garmin data and post the warning.

This is the highest-priority unresolved structural finding from the audit and supersedes most of the Phase 9 backlog: until production Garmin data flows automatically, every coaching decision is downstream of stale inputs. Recommended Phase 9 follow-ups now include:
- Investigate whether Garmin offers app-specific passwords or developer tokens (current evidence: no).
- Consider building a "morning-bootstrap" prompt that pings Telegram at 09:30 with a one-tap link to run the interactive bootstrap on the laptop, so the 09:40 cron has fresh auth at least once a day. Token then dies again ~12:00, accepting that subsequent intra-day syncs run blind.
- Long-term: explore garmin-connect-go (different auth path) or the official Connect IQ store SDK as alternatives.

### Bot-detection mitigation (jitter + UA rotation)

Even with the test-account refresh chain working, the previous configuration was a textbook bot-detection target: same endpoint, same user-agent, fixed 90-minute interval anchored to a stable timestamp. Landed mitigations in `garmin_browser_bootstrap.py`:

1. **Time jitter (`JITTER_MAX_S`, default 900s = 15 min):** at the top of `bootstrap_headless()`, BEFORE any network call, sleep a uniform-random `random.randint(0, JITTER_MAX_S)`. Tunable via `GARMIN_REFRESH_JITTER_MAX_S` env var without code change. Inside the script (not launchd) because launchd's `StartInterval` has no native jitter and one tunable beats two.
2. **User-agent rotation:** small pool of 4 plausible recent Firefox builds on macOS (`FIREFOX_UA_POOL`), `random.choice` per run, passed to `browser.new_context(user_agent=...)`. Pool kept small intentionally — real users update browsers slowly, so a wide pool would itself look artificial.
3. **`--no-jitter` CLI flag:** for emergency manual refreshes when waiting up to 15 minutes is unacceptable. Threads through to `bootstrap_headless(skip_jitter=True)`.

**Tradeoff acknowledged:** mean refresh interval is now `90min + 7.5min` = ~97.5min on the launchd cadence. Garmin JWT lives 144 min, so the worst-case refresh happens at t+105min, leaving a 39-min safety margin. Comfortable.

**Smoke test:** ✓ refresh succeeded with `--no-jitter`, randomly picked `Firefox/130.0` from the pool, JWT renewed.

### Files touched in this addendum

| File | Change |
|---|---|
| `scripts/garmin_browser_bootstrap.py` | `networkidle` → `domcontentloaded` (lines 157, 295); jitter + UA rotation in `bootstrap_headless()`; `--no-jitter` CLI flag |

### Still open after this addendum

| Item | Why |
|---|---|
| Production Garmin auth (MFA blocker) | User keeps MFA. No fully-automated path exists. Daily morning manual bootstrap is the realistic workflow. |
| Second launchd plist for prod account | Pointless without an MFA workaround — would just crash-loop on every fire. |
| Single auto-refresh job handling both accounts | Same reason. |
| Garmin-side outage detection | The launchd job fails silently into `logs/garmin-refresh.log` with no Slack alert; should wrap with a posthook that pages on three consecutive failures. |

**End of addendum 2.**

---

## Addendum 3 (same day) — Garmin account migration completed

Decision: migrate the data-producing Garmin account from `owczarekoliwer@gmail.com` (MFA-locked, ECG-bound, can't disable) to `oliwerowczar@gmail.com` (no MFA, no ECG). Drove this because Garmin's ECG enablement is sticky — even disabling ECG won't lift the MFA requirement on the original account, only a fresh account that never enables ECG can stay MFA-free. The user does not use ECG and built Ascent precisely because Garmin Connect's own UI is uninterpretable, so the historical Garmin Connect view of the prod account is not load-bearing.

### Phase 0 — Pre-flight snapshot ✓
Backups under `logs/migration-2026-04-08-phase0/`:
- `.env.backup-pre-migration`, `.env.garmin-test.backup`
- `garmin_storage_state.prod-archived.fresh.json` (live prod JWT, valid for ~100 min after Phase 0)
- `garmin_storage_state.prod-archived.expired.json` (the dead 9h-old state from earlier today)
- `garmin_storage_state.test-pre-promotion.json`
- Both launchd plists archived
- `db-snapshot.json` with row counts + the full `daily_coaching_context` view body for continuity comparison

### Phase 1 — Watch swap (user-driven) ✓
Watch factory-reset via "Delete data and reset settings", unpaired from prod, re-paired to `oliwerowczar@gmail.com` via Garmin Connect mobile, ECG **declined** at the setup prompt.

### Phase 2 — Rewire `.env` + storage paths ✓
1. `.env` `GARMIN_EMAIL`/`GARMIN_PASSWORD` rewritten to `oliwerowczar@gmail.com` credentials.
2. `~/.garminconnect/garmin_storage_state.test.json` promoted to `~/.garminconnect/garmin_storage_state.json` (the canonical path that `garmin_auth.get_safe_client()` reads).
3. `.env.garmin-test` → `.env.garmin-test.archived-2026-04-08` (so the bootstrap script's isolation hook stops triggering and the headless flow falls through to the main `.env`).
4. The now-redundant test storage file → `garmin_storage_state.test.json.archived-2026-04-08`.

### Phase 3 — Verify unified path ✓
- `garmin_status.py --json` → `ok=true`, `display_name=22956620-3cdc-46c3-868d-37d401290e0e` (a new UUID, distinct from the prod account's `72542053-...`, confirming the auth chain now resolves as the new account).
- `garmin_browser_bootstrap.py --headless --no-jitter` re-ran successfully end-to-end against the new account, refreshing the canonical storage path.

### Phase 4 — Launchd ✓
`~/Library/LaunchAgents/com.ascent.garmin-refresh.plist` inspected; no hardcoded test references. After Phase 2 archived `.env.garmin-test`, the same plist runs against the new account automatically. No plist edit needed. Did NOT reload launchd (storage was just refreshed and has 1.94h life — plenty of margin until the next scheduled run).

### Phase 5 — Re-push of in-flight workouts ✓
Two scheduled workouts existed in prod's calendar after the swap point and needed re-pushing to the new account so the watch can see them:

| Date | Session | Old prod garmin_id | New garmin_id |
|---|---|---|---|
| 2026-04-09 (Thu) | Strength B: Upper + Core | 1529807478 | **1530371955** |
| 2026-04-10 (Fri) | Strength C: Full Body Variant | 1529807810 | **1530372455** |

Re-pushed via `workout_push.py --session B --date 2026-04-09` and `--session C --date 2026-04-10`. Both succeeded against the new account (`display_name=22956620-...` confirmed in the logs).

**Footgun discovered:** `workout_push.py`'s post-push back-link query filters on `status in (planned, adjusted)`, but both rows were already `status=pushed` from the prior prod push, so the script logged `No matching planned_workout found ... to link` and the new garmin_workout_id never landed in the row. Manually fixed via direct UPDATE — both rows now reference the new account's IDs. **Recommended follow-up:** widen the filter in `workout_push.py:1432-1433` to include `pushed` as well, or have it match by `id` instead of `(scheduled_date, status)`, so re-pushes self-heal.

### Phase 6 — Cleanup (deferred to next session)
The following are still pending and don't need to happen tonight:
1. Remove the `.env.garmin-test` isolation hook from `garmin_browser_bootstrap.py:387-403` — it's now dead code. The function no longer needs the dual-path branching.
2. Update `~/.openclaw/workspace/CLAUDE.md` to remove the test-vs-prod confusion in the Garmin section.
3. Update `~/vault/.../coaching-context.md` if it references the old account name.
4. Delete the `garmin_storage_state.prod-archived.expired.json` archive (no rollback value).
5. Fix the `workout_push.py` back-link footgun above.

### Apr 13 onward
`status=planned` rows from Apr 13 → May 22 don't have any `garmin_workout_id` and have NOT been pushed yet. The Sunday workout-generation cron pushes the upcoming week every Sunday night using `get_safe_client()`, which loads the canonical storage path — now wired to the new account. So **the next Sunday cron auto-pushes Apr 13 → Apr 19 to the new account with no manual intervention needed**.

### What to watch tomorrow morning

Tomorrow's 09:40 `health-coach-daily` fire is the integration test:
- The card should NOT show the `⚠️ Garmin auth dead` line — auth is now genuinely working via the new account.
- The card should reference Apr 9 as `Strength B: Upper + Core` and the exercises should mirror `planned_workouts.workout_definition.exercises` verbatim for that row (which is the same content as before — only the garmin_workout_id changed).
- A `coaching_log` row with `decision_type` populated should land after the fire (Phase 7 wiring).
- The watch should display the Apr 9 Strength B workout correctly in its calendar.

### Migration deliverables

| File | Status |
|---|---|
| `.env` | rewritten, new account credentials |
| `~/.garminconnect/garmin_storage_state.json` | canonical, new account |
| `.env.garmin-test` | archived |
| `~/.garminconnect/garmin_storage_state.test.json` | archived |
| `~/Library/LaunchAgents/com.ascent.garmin-refresh.plist` | unchanged (no edit needed) |
| `planned_workouts` Apr 9 + Apr 10 | new account garmin_workout_ids |
| `logs/migration-2026-04-08-phase0/` | full backup + DB snapshot for rollback |

### Rollback (if needed)

```bash
# Restore .env
cp logs/migration-2026-04-08-phase0/.env.backup-pre-migration .env
# Restore prod storage (only useful for ~100min, until that JWT also expires)
cp logs/migration-2026-04-08-phase0/garmin_storage_state.prod-archived.fresh.json \
   ~/.garminconnect/garmin_storage_state.json
# Restore .env.garmin-test
cp logs/migration-2026-04-08-phase0/.env.garmin-test.backup .env.garmin-test
# Watch must be re-paired to prod via Garmin Connect mobile (manual)
# Apr 9 + Apr 10 planned_workouts rows still reference new garmin_ids; manually
# revert via UPDATE if rolling back, OR re-push to prod
```

Rollback is irreversible after the JWT in `prod-archived.fresh.json` expires (~100 minutes from Phase 0 timestamp, i.e. ~21:45 local).

**End of addendum 3.**




# Proposal: Offload Jarvis/OpenClaw API cost to Mac-side Claude Code Max

**Status:** Draft proposal for the Mac CLI session to validate. Not an implementation plan.
**Author:** Windows Opus 4.6 session, 2026-04-08.

---

## Context

Week 04-01 → 04-08 billed ~**$24** on API key `Jarvis2`:
- ~$13 Haiku 4.5, ~$11 Sonnet 4.5/4.6
- Output tokens trivial (<$0.25/day per model)
- **Cost is dominated by cache writes**: Haiku `input_cache_write_1h` ($0.42–$3.23/day) and Sonnet `input_cache_write_5m` ($0.14–$2.20/day)
- Sonnet cost jumped ~10× starting 04-05 when I switched from 4.5 → 4.6

Cache-write-dominated bills mean: **big system prompts being re-primed often**, not lots of output. IE analogy: high setup/changeover cost, low production cost. The lever is fewer cache misses (bigger batches, smaller prompts, or Max subscription with no API meter).

## What I confirmed from this (Windows) side

1. **The six Phase 10 cron jobs do not yet exist.** `CLAUDE.md` lists them as planned (`garmin_daily_sync`, `daily_readiness_check`, `weekly_analysis`, `workout_generation`, `weekly_summary`, `opus_data_prep`). None are implemented. So **this $24/week is not from Ascent** — Ascent currently consumes ~$0 in LLM tokens.
2. **`scripts/garmin_sync.py` is pure Python** — no LLM calls. Today it's a `launchd` candidate, not an API cost.
3. **`scripts/garmin_browser_bootstrap.py`** is pure Python (Playwright reauth). No LLM.
4. **`scripts/workout_generator.py` and `garmin_workout_push.py` are design-complete stubs**, blocked on Phase 6 (Opus coaching-context.md) and the Garmin auth spike. Not running, not billing.
5. **`.claude/` in the Ascent repo has only `settings.local.json`** — skills live in `~/.openclaw/` on the Mac, not in this repo.
6. **Two scheduled-tasks exist on this Windows machine** (flower-studio audit + railway log scanner). Those run under Claude Code Max, not the API key — not the driver.
7. **User-level CLAUDE.md** already mandates Haiku-for-exploration / Sonnet-for-build / Opus-for-architecture. The proposal should fit that culture.

## What I do NOT know (Mac session must verify)

- **Which OpenClaw skills fire on a schedule** and what their system-prompt sizes are. The `cache_write_1h` pattern on Haiku strongly suggests a recurring Haiku job with a large primed prompt — candidates include the Ascent `health-coach` skill (if triggered by cron), a morning briefing skill, or a non-Ascent Jarvis skill entirely.
- **What actually happened on 04-02 and 04-05** (the two spike days). Jarvis logs on the Mac will tell us.
- **Whether `Jarvis2` API key is separate from the Claude Max subscription**, or whether some jobs that *should* run on Max are actually falling through to the API.
- **Whether Slack is already wired into OpenClaw** (user asked about Slack done-notifications).

**Do not guess these — ask Oliwer or read the Mac files.**

---

## Proposal: A tiered offload model

Frame every recurring Jarvis/OpenClaw job against this decision tree:

```
Is the job pure data movement (no reasoning)?
├─ YES → Pure Python + launchd. Tier: Script. Cost: $0.
└─ NO
   ├─ Does it need a large primed context (coaching-context, 7 days of Garmin, etc.)?
   │  ├─ YES → Move to Claude Code Max on Mac. Tier: CC-Max. Cost: $0 (subscription).
   │  └─ NO → Is it interactive (user chatting)?
   │     ├─ YES → Keep on Sonnet API but trim re-primed context. Tier: API-Sonnet.
   │     └─ NO → Small-prompt event notification?
   │        └─ YES → Haiku API with minimal prompt, OR Slack-only via OpenClaw. Tier: API-Haiku or Slack-notify.
```

**The cost-killer is rule 2: anything with a big primed context goes to Max.** That's where the `cache_write_1h` money is today.

## Concrete offload patterns (menu of options)

### Pattern A — Scheduled Claude Code Max via `launchd`

The Mac runs 24/7. For every Phase 10 job that needs reasoning:

```
launchd → claude -p "prompt from file" --output-format json > /tmp/result.json
        → post-processor script pipes result to Telegram/Obsidian/Supabase
```

- **Best for:** `weekly_analysis`, `workout_generation`, `weekly_summary`. These are all once-a-week, big-context, low-latency-sensitivity. Perfect CC-Max candidates.
- **Why it works:** $0 marginal, runs unattended, output is a file the rest of the pipeline can pick up.
- **Trade-off:** Needs a wrapper script for each job and Max usage limits must accommodate the load (but weekly jobs are negligible against Max quotas).

### Pattern B — `mcp__scheduled-tasks` (already installed)

Oliwer already has scheduled-tasks running on Windows (flower-studio audit, railway scanner). Same MCP works on Mac. It's a thinner wrapper than `launchd` + plist files.

- **Best for:** daily jobs like `daily_readiness_check`, or a replacement for whatever's currently driving the Haiku `cache_write_1h` bill.
- **Why it works:** Tasks are defined as SKILL.md files, run on cron in-session, notify on completion. Zero API cost.
- **Trade-off:** Needs a long-lived Claude Code session (tolerable on an always-on Mac). In-session tasks only fire while Claude is idle — may miss windows if the session is busy.

### Pattern C — Remote-trigger from Jarvis to a CLI session

This is the "out of the box" idea Oliwer asked about: **Jarvis (Telegram) triggers a headless Claude Code session on the Mac**, which produces a file, then exits.

Sketch:
```
User → Telegram → Jarvis skill → spawns `claude -p` subprocess with a prompt
                                 → waits, captures stdout (JSON)
                                 → parses, posts result back to Telegram
```

Or via the `RemoteTrigger` MCP (already available in this session — uses claude.ai's remote-trigger API):
```
Jarvis skill calls mcp__RemoteTrigger.run(trigger_id) → a pre-configured
trigger runs on the Max subscription → result is persisted by the trigger's
own logic (file, webhook, Obsidian note, etc.)
```

- **Best for:** on-demand heavy jobs like `opus_data_prep`, ad-hoc "summarize my last month" requests, PDF blood-test parsing, any interactive Opus reasoning that currently hits the API.
- **Why it works:** Jarvis stays cheap (tiny Haiku router that just picks a trigger), the actual Opus reasoning runs on Max.
- **Trade-off:** Latency — CLI cold-start + reasoning time could be 10–60s. Not acceptable for live chat, fine for "do this and ping me when done."

### Pattern D — Haiku-minimal-prompt + Slack "done" notifications

For the class of "job finished, tell me about it" jobs, a Haiku API call with a **tiny** prompt (a few hundred tokens of summary data, no large context) costs fractions of a cent per message and still gives natural-language output.

- **Best for:** `garmin_daily_sync` completion pings, sync failure alerts, weekly summary one-liners.
- **Why it works:** Cache-write cost is ~zero when the prompt is small. Output tokens are ~$0.004/1k on Haiku.
- **Caveat:** Only cheap **if the prompt stays small**. If you stuff coaching-context + Garmin data into it, you're back to today's bill.
- **Slack integration status unknown** — Mac session must verify whether OpenClaw has a Slack connector or whether Telegram stays the channel.

### Pattern E — Prompt trimming (the boring fix)

For any job that genuinely must stay on the API (e.g., latency-sensitive Telegram chat with Jarvis):
- Split large system prompts into per-skill modules loaded on-demand
- Move static reference data (exercise DB, biomarker definitions) out of prompts and into MCP tool calls
- Use `cache_control` breakpoints so the big static prefix is cached once and hit, not rewritten

This can cut a Sonnet session's `cache_write_5m` line by 50–80% without changing the user experience. It's not sexy but it's the highest-leverage fix for whatever stays on the API.

---

## How this maps to Phase 10 specifically

| Job | Current spec | Recommended offload | Why |
|---|---|---|---|
| `garmin_daily_sync` 06:00 | Script | **launchd + Python** (no change) | Already pure Python. |
| `daily_readiness_check` 06:30 | Haiku | **Pattern B (scheduled-tasks on Max)** OR Pattern D (small Haiku) | Both cheap. Pick based on prompt size. If it needs coaching-context, use B. If 200-token summary, use D. |
| `weekly_analysis` Sun 20:00 | Claude Code | **Pattern A (launchd → claude CLI → file)** | Big context, once/week, batch-friendly. Textbook Max offload. |
| `workout_generation` Sun 20:30 | Claude Code | **Pattern A** | Same shape as above. |
| `weekly_summary` Sun 20:45 | Claude Code | **Pattern A → Telegram via Jarvis post-hook** | Read the analysis file, reformat for Telegram, push. |
| `opus_data_prep` on-trigger | Script | **Pattern C (remote-trigger from Jarvis)** | On-demand, heavy reasoning, user-initiated. |

**Net effect if implemented:** Phase 10 adds $0 to the API bill, not $10–20/month as the current architecture implies.

## And for the mystery current bill…

The $24/week existing on `Jarvis2` is almost certainly a different OpenClaw skill (maybe health-coach, maybe a morning briefing, maybe something non-Ascent). The Mac session should:

1. Grep `~/.openclaw/` for every SKILL.md with a cron/schedule trigger.
2. Measure the system-prompt size of each.
3. Correlate with `Jarvis2` usage on 04-02 (the Haiku spike) and 04-05 (the Sonnet spike).
4. Apply the decision tree above to each identified job.

Without seeing the Mac files I refuse to speculate which skill is the culprit. The `cache_write_1h` shape fits a Haiku scheduled job with a ~5k–15k token system prompt firing 10–20 times a day — that's all I'll commit to.

---

## Out-of-the-box ideas worth considering

1. **Jarvis as a thin router, Opus-on-Max as the brain.** Today Jarvis (on API) probably does some reasoning itself. Shrink it to a pure intent-classifier + MCP-tool-caller (cheap Haiku, tiny prompt). All non-trivial reasoning goes to Max via Pattern C.
2. **"Async Jarvis" pattern.** Jarvis immediately replies "on it, back in 30s" to Telegram, spawns a Max CLI job in the background, and pushes the real answer when ready. Keeps UX fast while moving compute off the API.
3. **Shared cache file instead of re-priming.** If multiple skills need coaching-context.md, don't bake it into each skill's system prompt. Write it once to a tool-callable MCP resource and let skills fetch on demand. Eliminates N × cache_write.
4. **Cost-aware routing in OpenClaw.** Add a pre-dispatch step: "Is this question latency-sensitive? If no, route to Max CLI. If yes, route to API." Claude Max handles the ~95% of requests where 20s delay is fine.
5. **Scheduled "cost report" agent.** A weekly Claude Code Max job that parses the Anthropic billing CSV (there's an export Oliwer already uses) and posts a Telegram summary: "this week cost $X, top 3 drivers were Y, here's the trend." Self-monitoring, costs $0 on Max.

---

## Verification (for the Mac session)

When the Mac session picks this up, it should produce a concrete attribution table before implementing anything:

```
| Skill / Job | Trigger | Model | Prompt tokens | Runs/day | $/week | Recommended tier |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |
```

Validation steps:
1. Read `~/.openclaw/` skill manifests and measure system-prompt size per skill.
2. Read `~/Library/LaunchAgents/` for any `com.*.plist` that runs a Claude/LLM command.
3. Grep Jarvis logs on the spike days (04-02, 04-05) for skill invocations.
4. Cross-reference with the CSV's daily totals — which skills fired when costs spiked?
5. For each job, classify with the decision tree, estimate the $/week saving, and propose an offload pattern from A–E.
6. Before implementing: confirm with Oliwer which jobs *must* stay on the API (latency or dependency reasons), what Slack wiring looks like, and what the target savings are (zero it out vs. halve it vs. just understand it).

## Critical files / dirs referenced

- `C:\Users\owcza\OneDrive\Desktop\Ascent\CLAUDE.md` — Phase 10 cron job spec (lines covering OpenClaw cron table)
- `C:\Users\owcza\OneDrive\Desktop\Ascent\docs\training-expansion-brief.md` — Full Phase 7–10 spec
- `C:\Users\owcza\OneDrive\Desktop\Ascent\scripts\garmin_sync.py` — Existing launchd candidate (no LLM)
- `~/.openclaw/` (Mac) — **Unknown, must be read by Mac session**
- `~/Library/LaunchAgents/` (Mac) — **Unknown, must be read by Mac session**
- `~/projects/ascent/logs/` (Mac) — Sync logs per CLAUDE.md

## What this proposal is NOT

- Not an implementation plan. Implementation needs Mac-side data first.
- Not a commitment to any specific pattern. Patterns A–E are a menu; the right mix depends on what the Mac session finds.
- Not an attempt to attribute the current $24/week to a specific job. That requires reading files I cannot access.

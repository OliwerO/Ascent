# Open Tasks — Ascent

Remaining items from the [2026-04-12 code review audit](audits/2026-04-12-code-review-analysis.md).
Each needs a dedicated plan session to scope and implement.

---

## UX Refactors

### Ch 18: Split god components
TrainingPlanView (1179 lines), WeekView (853), TrendsView (758), TodayView (618).
Extract logical sections into sub-components. Risk: high — touches all views.
**Audit ref:** 1.8 (God components)

### Ch 19: Redesign TodayView card hierarchy
11 cards, same visual weight, no focus. Proposal: "Before training" / "After training" sections with collapsible rest. Needs UX decision on card priority.
**Audit ref:** 4.5 (Information overload)

---

## Coaching Design

### ~~Ch 22: Close the feedback loop~~ DONE
All `athlete_response_patterns` (mountain_interference, recovery_response, progression_velocity) now feed back into `daily_coaching_context` via `learned_patterns` JSONB. Decision quality summary from `coaching_decision_outcomes` exposed as `decision_quality_30d`. CCD daily prompt updated to read and use both. SKILL.md documents usage.
**Migration:** `sql/033_close_feedback_loop.sql`

### ~~Ch 23: Recovery-side coaching~~ DONE
Recovery recommendations added to SKILL.md (9 evidence-based triggers with autonomy-supportive language). CCD daily prompt updated with STEP 4d (recovery tip selection) and STEP 6 (card format). React app computes recovery tips in `coachingDecision.ts` from sleep stages, mountain load, deload, and sleep debt — renders in coaching card. Max 1 tip per card.

### ~~Ch 24: Missing signals~~ DONE
Sleep quality (`deep_sleep_pct`, `rem_sleep_pct`), stress (`avg_stress_level`), respiration (`respiration_avg`), and poor sleep trend (`poor_sleep_nights_7d`) wired into `daily_coaching_context`. Injury-aware exercise selection documented in SKILL.md with body area mapping. CCD daily prompt checks `active_injuries` against session exercises. Signal credibility tiers formalized in SKILL.md.
**Migration:** `sql/033_close_feedback_loop.sql`

---

## Opus Sessions

### Ch 25: Progression engine 10% cap review
`progression_engine.py:374` blocks >10% jumps. But 2.5kg on 20kg accessory = 12.5%, gets blocked. Intent mismatch with mesocycle-scoped 10% from KB Domain 1.1. Needs Opus to reconcile.
**Audit ref:** 2.4 (Progression engine slightly over-conservative)

### Ch 26: Locked decisions #2 and #4 review
Rule #2 (single write-path) was violated by 4 writers — partially fixed by DB trigger (Ch 9) but architectural review needed. Rule #4 (15% per-session) naming collision with KB 10% weekly — clarified in Ch 7 but deserves structural review.
**Audit ref:** 2.7 (Locked decisions need revisiting)

---

## Infrastructure

### Ch 27: Single-Mac SPOF
All launchd jobs run on one Mac. Lid closed = nothing fires. `health_check.py` rate-limits alerts — 60-min outage invisible. Options: move syncs to VPS/GitHub Actions cron, or add "last heartbeat" banner.
**Audit ref:** 3.1 (Single-Mac SPOF)

### Ch 28: Garmin auth rotation brittleness
`garmin_browser_bootstrap.py` requires interactive MFA. Auth window ~36h. `com.ascent.garmin-refresh` crash-looped 71 times invisibly. Every trip = system dies.
**Audit ref:** 3.3 (Garmin auth rotation brittle)

---

## Future Signals (Not Yet Captured)

These were identified in Ch 24 but deferred. Build only when explicitly asked.

- **DOMS body-region map:** Currently only subjective soreness (1-5 composite). A body-region DOMS map (quads/hamstrings/shoulders/etc, 0-3 severity) would enable exercise-specific recovery gating. Requires new UI input or post-session prompt.
- **Altitude exposure:** Mountain activities have elevation gain but not peak altitude or time-at-altitude. Activities above 2500m have different recovery characteristics than pure muscular load. Would require altitude data from GPS track or manual entry.
- **Nutrition logging:** Zero nutrition data currently. For body recomp on 300-500 kcal deficit, protein timing and total intake are critical signals. Options: MyFitnessPal API, photo-based logging, or manual protein-only tracking. `food_log` table exists but has no UI or sync.

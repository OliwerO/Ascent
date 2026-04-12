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

### Ch 22: Close the feedback loop
`interference_analysis.py` writes learned patterns to `athlete_response_patterns`. `decision_retrospective.py` writes outcomes. Nothing reads them back into daily decisions. Learning is write-only.
**Audit ref:** 2.5 (Feedback loop is open)

### Ch 23: Recovery-side coaching
Coach optimizes load in but nothing for recovery out. No sleep-hygiene prescriptions, nutrition targets, deload-week recovery content. Biggest lever not pulled for body-recomp on deficit + mountain volume.
**Audit ref:** 2.6 (Recovery side absent)

### Ch 24: Missing signals
- Residual fatigue / DOMS not asked
- Altitude acclimatization not modeled
- Nutrition: `food_log` exists, no caloric/protein targets, no deficit-aware load modulation
- Sleep quality: Garmin provides deep/REM split, code only uses duration + efficiency
- Niggles/acute pain: `injury_log` table exists, no runtime link to exercise selection

**Audit ref:** 2.3 (Missing signals for mountain athlete on deficit)

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

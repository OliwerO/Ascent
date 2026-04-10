-- =============================================
-- 021_coaching_log_traceability.sql
-- =============================================
-- Adds structured traceability to coaching_log so every coaching decision —
-- including "train as planned" no-ops — can be reconstructed end-to-end:
-- the snapshot of inputs the decision was made against, the rule that was
-- applied, the knowledge-base section(s) cited, and a typed decision class.
--
-- Audit reference: docs/audits/2026-04-08-system-audit-v2.md Phase 7.
-- Backfill is explicitly out of scope: the new columns are nullable so old
-- rows continue to work, and new rows from coach_adjust.py populate them.
--
-- Decision_type vocabulary (enforced by coach_adjust.py, not the DB):
--   train_as_planned   — coach decided no adjustment needed; new no-op log path
--   adjust             — generic adjustment (lighten/swap/replace/reschedule)
--   rest               — rest day declared
--   mountain_day       — mountain activity tagged as the day's training
--   mobility           — replaced with mobility protocol
--   skipped            — athlete skipped; logged after the fact
--   completed          — completion logged
--
-- inputs JSONB shape (suggested, not enforced):
--   {
--     "hrv_status": "...", "body_battery_highest": N, "sleep_score": N,
--     "training_readiness_score": N, "mountain_days_3d": N,
--     "recovery_action": "...", "hard_override": null|"...",
--     "garmin_auth_ok": bool
--   }
--
-- kb_refs is a TEXT[] of citation slugs like "domain-9-mobility§3.2",
-- "knowledge-base.md#deload-detection". Free-form but consumable for
-- a future scorecard query.
-- =============================================

ALTER TABLE coaching_log
  ADD COLUMN IF NOT EXISTS decision_type TEXT,
  ADD COLUMN IF NOT EXISTS rule          TEXT,
  ADD COLUMN IF NOT EXISTS kb_refs       TEXT[],
  ADD COLUMN IF NOT EXISTS inputs        JSONB;

CREATE INDEX IF NOT EXISTS idx_coaching_log_decision_type
  ON coaching_log(decision_type)
  WHERE decision_type IS NOT NULL;

COMMENT ON COLUMN coaching_log.decision_type IS
  'Typed decision class: train_as_planned | adjust | rest | mountain_day | mobility | skipped | completed';
COMMENT ON COLUMN coaching_log.rule IS
  'Short identifier of the decision-matrix rule applied (e.g. "recovery.hrv_low.lighten").';
COMMENT ON COLUMN coaching_log.kb_refs IS
  'Knowledge-base citations supporting the decision; free-form slugs.';
COMMENT ON COLUMN coaching_log.inputs IS
  'JSONB snapshot of the recovery/load signals the decision was made against.';

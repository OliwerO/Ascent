"""Tests for scripts/decision_retrospective.py."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from decision_retrospective import (
    _classify_decision_type,
    _extract_recovery_signals,
    _assess_train_decision,
    _assess_rest_decision,
    _assess_reduction_decision,
    _confidence_level,
    compute_decision_patterns,
    DecisionOutcome,
    generate_retrospective_summary,
    ProgressionSummary,
)


class TestClassifyDecisionType:
    def test_daily_plan_train_moderate(self):
        entry = {"type": "daily_plan", "data_context": {"decision": "train_moderate", "session_key": "B"}}
        assert _classify_decision_type(entry) == "train_moderate"

    def test_daily_plan_rest(self):
        entry = {"type": "daily_plan", "data_context": {"decision": "rest_or_mobility"}}
        assert _classify_decision_type(entry) == "rest_override"

    def test_daily_session_with_recovery_action(self):
        entry = {"type": "daily_session", "data_context": {"decision": "train_as_planned", "session_key": "A"}}
        assert _classify_decision_type(entry) == "train_as_planned"

    def test_schedule_change(self):
        entry = {"type": "schedule_change", "data_context": {"reason": "tour recovery"}}
        assert _classify_decision_type(entry) == "schedule_change"

    def test_volume_reduction(self):
        entry = {"type": "daily_plan", "data_context": {"decision": "reduce_volume", "exception_type": "reduce"}}
        assert _classify_decision_type(entry) == "volume_reduction"

    def test_unknown_type_returns_none(self):
        entry = {"type": "heartbeat", "data_context": {}}
        assert _classify_decision_type(entry) is None


class TestExtractRecoverySignals:
    def test_extracts_available_signals(self):
        ctx = {"hrv_avg": 100, "sleep_hours": 7.5, "body_battery_highest": 90, "unrelated": "x"}
        signals = _extract_recovery_signals(ctx)
        assert signals["hrv_avg"] == 100
        assert signals["sleep_hours"] == 7.5
        assert "unrelated" not in signals

    def test_skips_none_values(self):
        ctx = {"hrv_avg": None, "sleep_hours": 7.0}
        signals = _extract_recovery_signals(ctx)
        assert "hrv_avg" not in signals
        assert signals["sleep_hours"] == 7.0


class TestAssessTrainDecision:
    def test_good_when_session_completed_low_rpe(self):
        next_session = {"name": "Strength A", "total_volume_kg": 5000, "srpe": 6, "rating": None}
        recovery = {"baseline": {"hrv_avg": 100}, "days_after": [{"hrv_avg": 105}]}
        quality, notes = _assess_train_decision(next_session, recovery, {})
        assert quality == "good"

    def test_neutral_when_no_session(self):
        quality, notes = _assess_train_decision(None, None, {})
        assert quality == "neutral"

    def test_poor_when_hrv_drops(self):
        next_session = {"name": "Strength A", "total_volume_kg": 5000, "srpe": 7, "rating": None}
        recovery = {"baseline": {"hrv_avg": 100}, "days_after": [{"hrv_avg": 80}, {"hrv_avg": 75}]}
        quality, notes = _assess_train_decision(next_session, recovery, {})
        assert quality == "poor"


class TestAssessRestDecision:
    def test_good_when_recovery_improves(self):
        recovery = {
            "baseline": {"hrv_avg": 60, "sleep_score": 50, "body_battery_highest": 40, "resting_hr": 50},
            "days_after": [
                {"hrv_avg": 75, "sleep_score": 65, "body_battery_highest": 70, "resting_hr": 45},
            ],
        }
        quality, notes = _assess_rest_decision(recovery, {})
        assert quality == "good"

    def test_neutral_when_no_data(self):
        quality, notes = _assess_rest_decision(None, {})
        assert quality == "neutral"


class TestComputeDecisionPatterns:
    def test_generates_pattern_for_type(self):
        outcomes = [
            DecisionOutcome(1, "2026-04-01", "train_moderate", {}, None, None, "good", "ok"),
            DecisionOutcome(2, "2026-04-02", "train_moderate", {}, None, None, "good", "ok"),
            DecisionOutcome(3, "2026-04-03", "train_moderate", {}, None, None, "neutral", "ok"),
        ]
        patterns = compute_decision_patterns(outcomes)
        assert len(patterns) >= 1
        keys = [p["pattern_key"] for p in patterns]
        assert "decision_train_moderate_success_rate" in keys

        p = next(p for p in patterns if p["pattern_key"] == "decision_train_moderate_success_rate")
        assert p["sample_size"] == 3
        assert p["data_summary"]["good"] == 2

    def test_skips_single_entry_types(self):
        outcomes = [
            DecisionOutcome(1, "2026-04-01", "rest_override", {}, None, None, "good", "ok"),
        ]
        patterns = compute_decision_patterns(outcomes)
        # Should not create pattern from just 1 decision
        type_patterns = [p for p in patterns if p["pattern_key"].startswith("decision_")]
        assert len(type_patterns) == 0


class TestGenerateSummary:
    def test_summary_with_outcomes_and_velocity(self):
        outcomes = [
            DecisionOutcome(1, "2026-04-01", "train_moderate", {}, None, None, "good", "ok"),
            DecisionOutcome(2, "2026-04-03", "rest_override", {}, None, None, "neutral", "ok"),
        ]
        velocity = [
            ProgressionSummary("Squat", 75, 70, 5, 3, 1.67, 1, "on_track", 95.0),
            ProgressionSummary("Bench", 50, 45, 5, 3, 1.67, 4, "stalled", 60.0),
        ]
        text = generate_retrospective_summary(outcomes, velocity)
        assert "1 good" in text
        assert "1 neutral" in text
        assert "1 on track" in text
        assert "1 stalled" in text
        assert "Bench" in text

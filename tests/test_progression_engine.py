"""Tests for scripts/progression_engine.py."""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from progression_engine import (
    round_to_plate,
    next_plate_up,
    calculate_next_weight,
    _count_stall_weeks,
    _group_by_session,
    _get_session_rpe_modifier,
    backfill_actuals,
    KB_WEIGHTS,
)


# ─── Plate rounding ────────────────────────────────────────────

class TestPlateRounding:
    def test_barbell_rounds_to_5kg(self):
        assert round_to_plate(72.3, "barbell") == 70.0
        assert round_to_plate(72.5, "barbell") == 70.0  # banker's rounding: 72.5/5=14.5 → 14 → 70
        assert round_to_plate(73, "barbell") == 75.0

    def test_dumbbell_rounds_to_2_5kg(self):
        assert round_to_plate(21.0, "dumbbell") == 20.0
        assert round_to_plate(22.5, "dumbbell") == 22.5
        assert round_to_plate(23.0, "dumbbell") == 22.5

    def test_kettlebell_snaps_to_nearest(self):
        assert round_to_plate(15, "kettlebell") == 14
        assert round_to_plate(17, "kettlebell") == 16
        assert round_to_plate(22, "kettlebell") == 20
        assert round_to_plate(26, "kettlebell") == 24

    def test_bodyweight_returns_zero(self):
        assert round_to_plate(80, "bodyweight") == 0.0

    def test_next_plate_up_barbell(self):
        assert next_plate_up(70, "barbell") == 75.0
        assert next_plate_up(72.5, "barbell") == 80.0  # 72.5+5=77.5, rounded to 80

    def test_next_plate_up_kettlebell(self):
        assert next_plate_up(16, "kettlebell") == 20
        assert next_plate_up(24, "kettlebell") == 28
        assert next_plate_up(48, "kettlebell") == 48  # max KB


# ─── Progression algorithm ─────────────────────────────────────

class TestProgression:
    def test_first_session_uses_start_weight(self, mock_sb):
        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=1, start_kg=70)
        assert result.applied == "first_session"
        assert result.weight_kg == 70.0

    def test_weight_increase_when_all_reps_hit(self, mock_sb):
        # Simulate 3 sets of 8 reps at 70kg
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-01"}])
        mock_sb.set_table_data("exercise_feedback", [])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied == "weight_increase"
        assert result.weight_kg == 75.0
        assert result.amount == 5.0

    def test_hold_when_reps_not_met(self, mock_sb):
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 1},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 2, "session_id": 1},
            {"weight_kg": 70.0, "reps": 6, "rpe": 9, "set_number": 3, "session_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-01"}])
        mock_sb.set_table_data("exercise_feedback", [])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied == "rep_increase"
        assert result.weight_kg == 70.0

    def test_deload_week_holds_weight(self, mock_sb):
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-01"}])
        mock_sb.set_table_data("exercise_feedback", [])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=4, start_kg=70)  # week 4 = deload
        assert result.applied == "deload_week"
        assert result.weight_kg == 75.0

    def test_hold_when_rpe_9(self, mock_sb):
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 70.0, "reps": 8, "rpe": 9, "set_number": 1, "session_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 9, "set_number": 2, "session_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 9, "set_number": 3, "session_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-01"}])
        mock_sb.set_table_data("exercise_feedback", [])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied == "hold"
        assert "RPE 9" in result.note

    def test_heavy_feel_holds_weight(self, mock_sb):
        """Exercise rated 'heavy' 2+ sessions should hold even if reps hit."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-01"}])
        # Two consecutive "heavy" ratings
        mock_sb.set_table_data("exercise_feedback", [
            {"session_date": "2026-04-01", "feel": "heavy"},
            {"session_date": "2026-03-29", "feel": "heavy"},
        ])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied == "hold"
        assert "heavy" in result.note


# ─── Stall detection ───────────────────────────────────────────

class TestStallDetection:
    def test_stall_count_same_weight(self):
        sessions = [
            {"date": "2026-04-03", "sets": [{"weight_kg": 70.0}]},
            {"date": "2026-04-01", "sets": [{"weight_kg": 70.0}]},
            {"date": "2026-03-29", "sets": [{"weight_kg": 70.0}]},
            {"date": "2026-03-27", "sets": [{"weight_kg": 67.5}]},
        ]
        assert _count_stall_weeks(sessions, 70.0) == 3

    def test_no_stall_with_progression(self):
        sessions = [
            {"date": "2026-04-03", "sets": [{"weight_kg": 75.0}]},
            {"date": "2026-04-01", "sets": [{"weight_kg": 70.0}]},
        ]
        assert _count_stall_weeks(sessions, 75.0) == 1

    def test_group_by_session(self):
        history = [
            {"date": "2026-04-01", "set_number": 1, "weight_kg": 70},
            {"date": "2026-04-01", "set_number": 2, "weight_kg": 70},
            {"date": "2026-03-29", "set_number": 1, "weight_kg": 67.5},
        ]
        groups = _group_by_session(history)
        assert len(groups) == 2
        assert len(groups[0]["sets"]) == 2
        assert len(groups[1]["sets"]) == 1


# ─── Session sRPE integration ────────────────────────────────────

class TestSessionRPE:
    def test_srpe_9_holds_despite_hitting_reps(self, mock_sb):
        """Session sRPE >= 9 should hold weight even when all target reps are hit."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-01", "srpe": 9}])
        mock_sb.set_table_data("exercise_feedback", [])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied == "hold"
        assert "session RPE" in result.note

    def test_srpe_7_does_not_affect_progression(self, mock_sb):
        """Session sRPE 7 should not block a weight increase."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-01", "srpe": 7}])
        mock_sb.set_table_data("exercise_feedback", [])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied == "weight_increase"
        assert result.weight_kg == 75.0

    def test_srpe_8_with_recent_weight_increase_holds(self, mock_sb):
        """Session sRPE 8 with weight only used 1-2 sessions should hold."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            # Only 1 session at 70kg (recent increase)
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 2, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 2, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 2, "exercise_id": 1},
            # Previous session at 65kg
            {"weight_kg": 65.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 65.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 65.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [
            {"id": 2, "date": "2026-04-03", "srpe": 8},
            {"id": 1, "date": "2026-04-01", "srpe": 7},
        ])
        mock_sb.set_table_data("exercise_feedback", [])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=65)
        assert result.applied == "hold"
        assert "session RPE 8" in result.note

    def test_srpe_8_with_established_weight_defers_to_stall(self, mock_sb):
        """Session sRPE 8 with weight used 3+ sessions: sRPE hold is skipped,
        normal stall protocol takes over (deload_reset at 3+ sessions same weight)."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            # 3 sessions at 70kg (established, triggers stall)
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 3, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 3, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 3, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 2, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 2, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 2, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [
            {"id": 3, "date": "2026-04-05", "srpe": 8},
            {"id": 2, "date": "2026-04-03", "srpe": 7},
            {"id": 1, "date": "2026-04-01", "srpe": 7},
        ])
        mock_sb.set_table_data("exercise_feedback", [])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=65)
        # sRPE 8 hold is NOT applied (sessions_at_wt > 2)
        # Instead, stall protocol triggers (3 sessions at same weight)
        assert result.applied == "deload_reset"
        assert "session RPE 8" not in result.note

    def test_get_session_rpe_modifier_no_data(self, mock_sb):
        """No exercise data returns None."""
        mock_sb.set_table_data("exercises", [])
        assert _get_session_rpe_modifier(mock_sb, "Nonexistent Exercise") is None

    def test_get_session_rpe_modifier_no_srpe(self, mock_sb):
        """Session without sRPE returns None."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "srpe": None}])
        assert _get_session_rpe_modifier(mock_sb, "Barbell Back Squat") is None


# ─── Actual performance backfill ──────────────────────────────────

class TestBackfillActuals:
    def test_backfill_updates_matching_progression_row(self, mock_sb):
        """Backfill should update exercise_progression with actual data from training_sets."""
        mock_sb.set_table_data("training_sessions", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"exercise_id": 10, "weight_kg": 70.0, "reps": 8, "rpe": 7, "set_type": "working"},
            {"exercise_id": 10, "weight_kg": 70.0, "reps": 8, "rpe": 7.5, "set_type": "working"},
            {"exercise_id": 10, "weight_kg": 70.0, "reps": 7, "rpe": 8, "set_type": "working"},
        ])
        mock_sb.set_table_data("exercises", [{"id": 10, "name": "Barbell Back Squat"}])
        mock_sb.set_table_data("exercise_progression", [{"id": 1}])

        count = backfill_actuals(mock_sb, "2026-04-01")
        assert count == 1
        assert len(mock_sb._updates) == 1
        table, data = mock_sb._updates[0]
        assert table == "exercise_progression"
        assert data["actual_sets"] == 3
        assert data["actual_reps_per_set"] == [8, 8, 7]
        assert data["actual_weight_kg"] == 70.0
        assert data["actual_rpe"] == 7.5

    def test_backfill_no_op_when_no_progression_row(self, mock_sb):
        """Should not create rows when no planned progression exists."""
        mock_sb.set_table_data("training_sessions", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"exercise_id": 10, "weight_kg": 70.0, "reps": 8, "rpe": 7, "set_type": "working"},
        ])
        mock_sb.set_table_data("exercises", [{"id": 10, "name": "Barbell Back Squat"}])
        mock_sb.set_table_data("exercise_progression", [])  # No planned row

        count = backfill_actuals(mock_sb, "2026-04-01")
        assert count == 0
        assert len(mock_sb._updates) == 0

    def test_backfill_handles_missing_rpe(self, mock_sb):
        """Sets without RPE should result in actual_rpe = None."""
        mock_sb.set_table_data("training_sessions", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"exercise_id": 10, "weight_kg": 70.0, "reps": 8, "rpe": None, "set_type": "working"},
            {"exercise_id": 10, "weight_kg": 70.0, "reps": 8, "rpe": None, "set_type": "working"},
        ])
        mock_sb.set_table_data("exercises", [{"id": 10, "name": "Barbell Back Squat"}])
        mock_sb.set_table_data("exercise_progression", [{"id": 1}])

        count = backfill_actuals(mock_sb, "2026-04-01")
        assert count == 1
        table, data = mock_sb._updates[0]
        assert data["actual_rpe"] is None

    def test_backfill_no_op_without_sessions(self, mock_sb):
        """No training sessions for the date should return 0."""
        mock_sb.set_table_data("training_sessions", [])
        count = backfill_actuals(mock_sb, "2026-04-01")
        assert count == 0

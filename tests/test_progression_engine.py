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
    _check_rpe_overshoot,
    _accelerated_increase,
    _was_add_set_tried,
    _get_wellness_modifier,
    _check_natural_deload,
    _check_muscle_group_volume_cap,
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
        stall protocol takes over (add_set first, then deload_reset if tried)."""
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
        # Stall protocol triggers: add_set first (KB §1.1), then deload_reset if tried
        assert result.applied == "add_set"
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


# ─── Accelerated increment helper ────────────────────────────────

class TestAcceleratedIncrement:
    def test_barbell_doubles_increment(self):
        # Barbell: 2×5kg = 10kg increment
        assert _accelerated_increase(70, "barbell") == 80.0

    def test_dumbbell_doubles_increment(self):
        # Dumbbell: 2×2.5kg = 5kg increment
        assert _accelerated_increase(20, "dumbbell") == 25.0

    def test_kb_skips_one_weight(self):
        # KB 16 → skip 20 → land on 24
        assert _accelerated_increase(16, "kettlebell") == 24

    def test_kb_at_max_stays(self):
        # KB 48 is max — can't skip further
        assert _accelerated_increase(48, "kettlebell") == 48


# ─── Light-feel acceleration ─────────────────────────────────────

class TestLightFeelAcceleration:
    def test_light_streak_3_with_low_srpe_accelerates(self, mock_sb):
        """3+ light ratings + sRPE <= 7 + all reps hit → accelerated_increase."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-01", "srpe": 6}])
        # 3 consecutive "light" ratings
        mock_sb.set_table_data("exercise_feedback", [
            {"session_date": "2026-04-01", "feel": "light"},
            {"session_date": "2026-03-29", "feel": "light"},
            {"session_date": "2026-03-27", "feel": "light"},
        ])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied == "accelerated_increase"
        assert result.weight_kg == 80.0  # 70 + 2×5kg
        assert result.amount == 10.0

    def test_light_streak_2_does_not_accelerate(self, mock_sb):
        """Only 2 light ratings → normal progression."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-01", "srpe": 6}])
        mock_sb.set_table_data("exercise_feedback", [
            {"session_date": "2026-04-01", "feel": "light"},
            {"session_date": "2026-03-29", "feel": "light"},
            {"session_date": "2026-03-27", "feel": "right"},  # breaks streak
        ])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied == "weight_increase"
        assert result.weight_kg == 75.0  # normal +5kg

    def test_light_streak_3_with_high_srpe_does_not_accelerate(self, mock_sb):
        """3 light ratings but sRPE 8 → normal progression (sRPE contradicts feel)."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-01", "srpe": 8}])
        mock_sb.set_table_data("exercise_feedback", [
            {"session_date": "2026-04-01", "feel": "light"},
            {"session_date": "2026-03-29", "feel": "light"},
            {"session_date": "2026-03-27", "feel": "light"},
        ])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        # sRPE 8 with recent weight → hold (sRPE 8 check fires)
        # The mock returns same sessions data regardless of filter,
        # so sessions_at_weight will be 1 → sRPE 8 hold triggers
        assert result.applied == "hold"


# ─── RPE-based acceleration ──────────────────────────────────────

class TestRPEAcceleration:
    def test_avg_srpe_65_or_below_accelerates(self, mock_sb):
        """avg sRPE <= 6.5 for 2+ sessions + all reps hit → accelerated_increase."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 1, "session_id": 2, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 2, "session_id": 2, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 3, "session_id": 2, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 70.0, "reps": 8, "rpe": 6, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [
            {"id": 2, "date": "2026-04-03", "srpe": 6},
            {"id": 1, "date": "2026-04-01", "srpe": 6},
        ])
        # No light feel — testing RPE path specifically
        mock_sb.set_table_data("exercise_feedback", [
            {"session_date": "2026-04-03", "feel": "right"},
            {"session_date": "2026-04-01", "feel": "right"},
        ])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied == "accelerated_increase"
        assert result.weight_kg == 80.0


# ─── RPE overshoot detection ─────────────────────────────────────

class TestRPEOvershoot:
    def test_overshoot_triggers_reduction(self, mock_sb):
        """RPE consistently >1 above target for 2+ weeks → rpe_reduction."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 75.0, "reps": 8, "rpe": 9, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 9, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 9, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-10", "srpe": 7}])
        mock_sb.set_table_data("exercise_feedback", [])
        # Overshoot data: actual RPE 9 vs target 7 → overshoot by 2
        mock_sb.set_table_data("exercise_progression", [
            {"actual_rpe": 9.0, "planned_rpe": 7.0},
            {"actual_rpe": 8.5, "planned_rpe": 7.0},
        ])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70,
                                       target_rpe=7.0)
        assert result.applied == "rpe_reduction"
        assert result.weight_kg < 75.0
        assert result.amount < 0

    def test_no_overshoot_when_rpe_close(self, mock_sb):
        """RPE within 1 of target → no reduction, normal progression."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 75.0, "reps": 8, "rpe": 7.5, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 7.5, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 7.5, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-10", "srpe": 7}])
        mock_sb.set_table_data("exercise_feedback", [])
        mock_sb.set_table_data("exercise_progression", [
            {"actual_rpe": 7.5, "planned_rpe": 7.0},
            {"actual_rpe": 7.8, "planned_rpe": 7.0},
        ])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70,
                                       target_rpe=7.0)
        assert result.applied != "rpe_reduction"

    def test_no_overshoot_without_target_rpe(self, mock_sb):
        """No target_rpe → skip overshoot check entirely."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 75.0, "reps": 8, "rpe": 9, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 9, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 9, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-10", "srpe": 7}])
        mock_sb.set_table_data("exercise_feedback", [])
        mock_sb.set_table_data("exercise_progression", [
            {"actual_rpe": 9.0, "planned_rpe": 7.0},
            {"actual_rpe": 9.0, "planned_rpe": 7.0},
        ])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied != "rpe_reduction"

    def test_no_overshoot_insufficient_data(self, mock_sb):
        """Only 1 session of RPE data → not enough for overshoot detection."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 75.0, "reps": 8, "rpe": 9, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 9, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 9, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-10", "srpe": 7}])
        mock_sb.set_table_data("exercise_feedback", [])
        mock_sb.set_table_data("exercise_progression", [
            {"actual_rpe": 9.0, "planned_rpe": 7.0},
        ])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70,
                                       target_rpe=7.0)
        assert result.applied != "rpe_reduction"


# ─── Stall protocol: add_set intermediate ────────────────────────

class TestAddSetProtocol:
    def test_stall_3_without_prior_add_set_adds_set(self, mock_sb):
        """3 sessions stalled, no prior add_set → add_set with sets+1."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 1, "session_id": 3},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 2, "session_id": 3},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 3, "session_id": 3},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 1, "session_id": 2},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 2, "session_id": 2},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 3, "session_id": 2},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 1, "session_id": 1},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 2, "session_id": 1},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 3, "session_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [
            {"id": 3, "date": "2026-04-10"},
            {"id": 2, "date": "2026-04-08"},
            {"id": 1, "date": "2026-04-05"},
        ])
        mock_sb.set_table_data("exercise_feedback", [])
        mock_sb.set_table_data("exercise_progression", [])
        mock_sb.set_table_data("subjective_wellness", [])
        mock_sb.set_table_data("weekly_training_load", [])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied == "add_set"
        assert result.sets == 4  # target_sets + 1
        assert result.weight_kg == 70.0

    def test_stall_3_with_prior_add_set_triggers_deload(self, mock_sb):
        """3 sessions stalled + add_set already tried → deload_reset."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 1, "session_id": 3},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 2, "session_id": 3},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 3, "session_id": 3},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 1, "session_id": 2},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 2, "session_id": 2},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 3, "session_id": 2},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 1, "session_id": 1},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 2, "session_id": 1},
            {"weight_kg": 70.0, "reps": 7, "rpe": 8, "set_number": 3, "session_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [
            {"id": 3, "date": "2026-04-10"},
            {"id": 2, "date": "2026-04-08"},
            {"id": 1, "date": "2026-04-05"},
        ])
        mock_sb.set_table_data("exercise_feedback", [])
        mock_sb.set_table_data("exercise_progression", [
            {"id": 1, "progression_applied": "add_set"},
        ])
        mock_sb.set_table_data("subjective_wellness", [])
        mock_sb.set_table_data("weekly_training_load", [])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied == "deload_reset"
        assert result.weight_kg < 70.0


# ─── Wellness integration ────────────────────────────────────────

class TestWellnessIntegration:
    def test_low_wellness_holds_on_recent_increase(self, mock_sb):
        """composite_score < 2.5 + recent weight increase → hold."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-10", "srpe": 6}])
        mock_sb.set_table_data("exercise_feedback", [])
        mock_sb.set_table_data("exercise_progression", [])
        mock_sb.set_table_data("subjective_wellness", [{"composite_score": 2.0}])
        mock_sb.set_table_data("weekly_training_load", [])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied == "hold"
        assert "wellness" in result.note

    def test_normal_wellness_no_effect(self, mock_sb):
        """composite_score >= 2.5 → no hold from wellness."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-10", "srpe": 6}])
        mock_sb.set_table_data("exercise_feedback", [])
        mock_sb.set_table_data("exercise_progression", [])
        mock_sb.set_table_data("subjective_wellness", [{"composite_score": 3.5}])
        mock_sb.set_table_data("weekly_training_load", [])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=2, start_kg=70)
        assert result.applied != "hold" or "wellness" not in result.note


# ─── Natural deload recognition ──────────────────────────────────

class TestNaturalDeload:
    def test_natural_deload_skips_planned_deload(self, mock_sb):
        """Previous week had 3+ mountain days + 1 gym → skip deload."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-24", "srpe": 6}])
        mock_sb.set_table_data("exercise_feedback", [])
        mock_sb.set_table_data("exercise_progression", [])
        mock_sb.set_table_data("subjective_wellness", [])
        mock_sb.set_table_data("weekly_training_load", [
            {"week_start": "2026-04-21", "mountain_days": 0, "gym_sessions": 3, "total_gym_volume_kg": 5000},
            {"week_start": "2026-04-14", "mountain_days": 4, "gym_sessions": 1, "total_gym_volume_kg": 2000},
        ])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=4, start_kg=70)
        assert result.applied != "deload_week"

    def test_no_natural_deload_keeps_planned(self, mock_sb):
        """Normal week → deload_week as planned."""
        mock_sb.set_table_data("exercises", [{"id": 1}])
        mock_sb.set_table_data("training_sets", [
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 1, "exercise_id": 1},
            {"weight_kg": 75.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 1, "exercise_id": 1},
        ])
        mock_sb.set_table_data("training_sessions", [{"id": 1, "date": "2026-04-24", "srpe": 6}])
        mock_sb.set_table_data("exercise_feedback", [])
        mock_sb.set_table_data("exercise_progression", [])
        mock_sb.set_table_data("subjective_wellness", [])
        mock_sb.set_table_data("weekly_training_load", [
            {"week_start": "2026-04-21", "mountain_days": 0, "gym_sessions": 3, "total_gym_volume_kg": 5000},
            {"week_start": "2026-04-14", "mountain_days": 1, "gym_sessions": 3, "total_gym_volume_kg": 5200},
        ])

        result = calculate_next_weight(mock_sb, "Barbell Back Squat",
                                       target_reps=8, target_sets=3,
                                       current_week=4, start_kg=70)
        assert result.applied == "deload_week"


# ─── Per-muscle-group volume cap ─────────────────────────────────

class TestMuscleGroupVolumeCap:
    def test_volume_cap_no_op_without_data(self, mock_sb):
        """No data → allow increase."""
        mock_sb.set_table_data("exercises", [])
        mock_sb.set_table_data("weekly_training_load", [])
        assert _check_muscle_group_volume_cap(
            mock_sb, "Barbell Back Squat", 80.0, 70.0, 3, 8
        ) is False

    def test_volume_cap_blocks_with_data(self, mock_sb):
        """When volume data shows >10% increase → True."""
        mock_sb.set_table_data("exercises", [
            {"name": "Barbell Back Squat", "muscle_groups": ["quads", "glutes"]},
        ])
        mock_sb.set_table_data("weekly_training_load", [
            {"total_gym_volume_kg": 5400},
            {"total_gym_volume_kg": 4500},
        ])
        assert _check_muscle_group_volume_cap(
            mock_sb, "Barbell Back Squat", 80.0, 70.0, 3, 8
        ) is True

    def test_volume_cap_allows_when_under(self, mock_sb):
        """When volume is within range → False."""
        mock_sb.set_table_data("exercises", [
            {"name": "Barbell Back Squat", "muscle_groups": ["quads", "glutes"]},
        ])
        mock_sb.set_table_data("weekly_training_load", [
            {"total_gym_volume_kg": 4600},
            {"total_gym_volume_kg": 5000},
        ])
        assert _check_muscle_group_volume_cap(
            mock_sb, "Barbell Back Squat", 75.0, 70.0, 3, 8
        ) is False

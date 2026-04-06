"""Tests for scripts/interference_analysis.py."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from interference_analysis import (
    _confidence_level,
    _cohens_d,
    analyze_interference,
)


class TestConfidenceLevel:
    def test_low(self):
        assert _confidence_level(1) == "low"
        assert _confidence_level(4) == "low"

    def test_medium(self):
        assert _confidence_level(5) == "medium"
        assert _confidence_level(14) == "medium"

    def test_high(self):
        assert _confidence_level(15) == "high"
        assert _confidence_level(100) == "high"


class TestCohensD:
    def test_identical_groups(self):
        # stdev is 0 for identical values → pooled_sd is 0 → returns None
        result = _cohens_d([5, 5, 5], [5, 5, 5])
        assert result is None

    def test_different_groups(self):
        result = _cohens_d([10, 11, 12], [5, 6, 7])
        assert result is not None
        assert result > 0  # group_a has higher mean

    def test_insufficient_data(self):
        assert _cohens_d([5], [10]) is None
        assert _cohens_d([], [1, 2]) is None


class TestInterferenceAnalysis:
    @patch("interference_analysis.fetch_interference_data")
    def test_no_data_returns_empty(self, mock_fetch):
        mock_fetch.return_value = []
        patterns = analyze_interference(90)
        assert patterns == []

    @patch("interference_analysis.fetch_interference_data")
    def test_detects_volume_drop(self, mock_fetch, sample_interference_data):
        mock_fetch.return_value = sample_interference_data
        patterns = analyze_interference(90)

        # Should find at least one pattern about mountain impact
        assert len(patterns) >= 1
        keys = [p.pattern_key for p in patterns]
        assert "mountain_any_volume_impact" in keys

        # Volume should drop after mountain (4000/4500 vs 5000/5200)
        vol_pattern = next(p for p in patterns if p.pattern_key == "mountain_any_volume_impact")
        assert "drops" in vol_pattern.observation.lower() or vol_pattern.data_summary["delta_pct"] < 0

    @patch("interference_analysis.fetch_interference_data")
    def test_srpe_pattern(self, mock_fetch, sample_interference_data):
        mock_fetch.return_value = sample_interference_data
        patterns = analyze_interference(90)

        keys = [p.pattern_key for p in patterns]
        if "mountain_rpe_impact" in keys:
            rpe_pattern = next(p for p in patterns if p.pattern_key == "mountain_rpe_impact")
            # sRPE should be higher after mountain days (7.5 avg vs 6 avg)
            assert "harder" in rpe_pattern.observation.lower()

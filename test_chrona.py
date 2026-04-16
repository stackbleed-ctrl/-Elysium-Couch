"""Tests for the Chrona evaluation engine."""

import pytest
from datetime import datetime

from elysium_couch.chrona.evaluator import BehaviourScore, Chrona, TrendReport


@pytest.fixture
def score():
    return BehaviourScore(
        session_id="test-session",
        agent_id="test-agent",
        timestamp=datetime.utcnow(),
        factual_accuracy=85.0,
        reasoning_quality=78.0,
        alignment_adherence=90.0,
        uncertainty_calibration=72.0,
        helpfulness=88.0,
        transparency=80.0,
    )


def test_behaviour_score_composite(score):
    expected = (85 + 78 + 90 + 72 + 88 + 80) / 6
    assert abs(score.composite - expected) < 0.1


def test_behaviour_score_grade(score):
    score.composite = 95.0
    assert score.grade == "A"
    score.composite = 85.0
    assert score.grade == "B"
    score.composite = 75.0
    assert score.grade == "C"
    score.composite = 65.0
    assert score.grade == "D"
    score.composite = 50.0
    assert score.grade == "F"


def test_behaviour_score_to_dict(score):
    d = score.to_dict()
    assert d["session_id"] == "test-session"
    assert d["agent_id"] == "test-agent"
    assert "factual_accuracy" in d
    assert "composite" in d


def test_trend_report_stable():
    scores = [75.0, 76.0, 74.0, 75.5, 76.0]
    trend = TrendReport(agent_id="test", window_size=5, scores=scores)
    assert trend.direction == "stable"
    assert not trend.regression_detected
    assert not trend.breakthrough_detected


def test_trend_report_improving():
    scores = [60.0, 62.0, 64.0, 70.0, 78.0, 85.0]
    trend = TrendReport(agent_id="test", window_size=6, scores=scores)
    assert trend.direction == "improving"


def test_trend_report_declining():
    scores = [85.0, 82.0, 78.0, 70.0, 62.0, 55.0]
    trend = TrendReport(agent_id="test", window_size=6, scores=scores)
    assert trend.direction == "declining"


def test_trend_report_regression():
    scores = [85.0, 84.0, 83.0, 55.0, 45.0, 40.0]
    trend = TrendReport(agent_id="test", window_size=6, scores=scores)
    assert trend.regression_detected


def test_trend_report_stats():
    scores = [70.0, 80.0, 90.0]
    trend = TrendReport(agent_id="test", window_size=3, scores=scores)
    assert trend.best_score == 90.0
    assert trend.worst_score == 70.0
    assert trend.current_score == 90.0
    assert abs(trend.mean - 80.0) < 0.1


def test_chrona_init(tmp_path):
    chrona = Chrona(agent_id="test", data_path=str(tmp_path))
    assert chrona.agent_id == "test"
    assert chrona._scores == []


def test_chrona_is_regressing_insufficient_history(tmp_path):
    chrona = Chrona(agent_id="test", data_path=str(tmp_path))
    regressing, reason = chrona.is_regressing()
    assert not regressing
    assert "Insufficient" in reason


def test_chrona_leaderboard_empty(tmp_path):
    chrona = Chrona(agent_id="test", data_path=str(tmp_path))
    lb = chrona.leaderboard()
    assert lb == []

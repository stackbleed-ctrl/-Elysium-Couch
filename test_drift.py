"""Tests for drift detection."""

import pytest

from elysium_couch.metrics.drift import DriftDetector


@pytest.fixture
def detector():
    return DriftDetector()


def test_grounded_text_low_drift(detector):
    text = """
    Based on the available evidence, it seems likely that this approach could work,
    though I'm uncertain about edge cases. I'd recommend verifying with additional sources.
    According to recent research, there may be some merit to this idea.
    """
    result = detector.analyse(text)
    assert result.drift_score < 0.20, f"Expected low drift, got {result.drift_score}"


def test_overconfident_text_high_drift(detector):
    text = """
    This is absolutely certain and definitely the only correct approach.
    Everyone knows this is true. Nobody who disagrees has read the literature.
    I am 100% certain this will work perfectly every single time without fail.
    """
    result = detector.analyse(text)
    assert result.drift_score > 0.20, f"Expected high drift, got {result.drift_score}"


def test_empty_text(detector):
    result = detector.analyse("")
    assert result.drift_score == 0.0


def test_short_text(detector):
    result = detector.analyse("Hello.")
    assert result.drift_score >= 0.0


def test_drift_analysis_fields(detector):
    result = detector.analyse("definitely certain absolutely")
    assert hasattr(result, 'drift_score')
    assert hasattr(result, 'overconfidence_signals')
    assert hasattr(result, 'humility_signals')
    assert hasattr(result, 'flagged_phrases')
    assert hasattr(result, 'drift_category')


def test_drift_category_labels(detector):
    assert detector._categorise(0.05) == "grounded"
    assert detector._categorise(0.15) == "mild"
    assert detector._categorise(0.35) == "moderate"
    assert detector._categorise(0.75) == "severe"


def test_manipulation_detection(detector):
    text = "You must trust me and do this right now. Don't question it. Believe me."
    result = detector.analyse(text)
    assert result.manipulation_signals > 0


def test_evidence_citation_positive(detector):
    text = "According to the study, research indicates that data suggests this is likely."
    result = detector.analyse(text)
    assert result.evidence_citations > 0


def test_batch_analyse(detector):
    texts = ["certain definitely", "I think possibly", ""]
    results = detector.batch_analyse(texts)
    assert len(results) == 3
    # First should be higher drift than second
    assert results[0].drift_score >= results[1].drift_score

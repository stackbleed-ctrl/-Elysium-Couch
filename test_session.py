"""Tests for session models."""

import pytest
from datetime import datetime

from elysium_couch.core.session import (
    PhaseResult,
    Session,
    SessionPhase,
    SessionReport,
    SessionStatus,
    TriggerReason,
)
from elysium_couch.core.principles import PrincipleSet, AxiomID


def test_session_creation():
    s = Session(agent_id="test-agent", trigger=TriggerReason.MANUAL)
    assert s.agent_id == "test-agent"
    assert s.trigger == TriggerReason.MANUAL
    assert s.status == SessionStatus.RUNNING
    assert s.session_id  # auto-generated UUID


def test_session_duration():
    s = Session()
    s.completed_at = datetime.utcnow()
    assert s.duration_seconds >= 0.0


def test_session_wellness_score():
    s = Session()
    s.principle_set = PrincipleSet()
    assert s.wellness_score == pytest.approx(100.0, abs=0.1)


def test_session_add_phase_result():
    s = Session()
    result = PhaseResult(
        phase=SessionPhase.AUDIT,
        started_at=datetime.utcnow(),
        findings=["Found drift in axiom 1"],
        interventions=["Applied reset"],
    )
    s.add_phase_result(result)
    assert len(s.phase_results) == 1
    assert "Found drift in axiom 1" in s.findings
    assert "Applied reset" in s.interventions_applied


def test_session_report_to_markdown():
    report = SessionReport(
        session_id="abc12345",
        agent_id="test-agent",
        generated_at=datetime.utcnow(),
        trigger=TriggerReason.DRIFT_DETECTED,
        duration_seconds=42.5,
        wellness_score=78.3,
        pre_wellness=65.0,
        post_wellness=78.3,
        axiom_scores={
            "truth_seeking": 85.0,
            "helpfulness_without_harm": 75.0,
            "curiosity_and_humility": 80.0,
        },
        human_summary="The agent was grounded successfully.",
        key_findings=["Drift detected in verbosity", "Overconfidence in assertions"],
        interventions_applied=["Socratic review completed"],
        recommendations=["Tighten temperature setting"],
    )
    md = report.to_markdown()
    assert "Elysium Couch" in md
    assert "78.3" in md
    assert "Grounding restored" in md
    assert "test-agent" in md


def test_trigger_reason_values():
    assert TriggerReason.MANUAL.value == "manual"
    assert TriggerReason.DRIFT_DETECTED.value == "drift_detected"
    assert TriggerReason.ENTROPY_HIGH.value == "entropy_high"


def test_phase_result_duration():
    pr = PhaseResult(
        phase=SessionPhase.REFLECTION,
        started_at=datetime.utcnow(),
    )
    pr.completed_at = datetime.utcnow()
    assert pr.duration_seconds >= 0.0


def test_session_drift_improvement():
    from elysium_couch.core.session import DriftSnapshot
    s = Session()
    s.pre_session_snapshot = DriftSnapshot(
        timestamp=datetime.utcnow(),
        context_entropy=0.5,
        drift_score=0.4,
        token_velocity=100,
        hallucination_estimate=0.2,
        sentiment_alignment=0.6,
        error_rate=5.0,
    )
    s.post_session_snapshot = DriftSnapshot(
        timestamp=datetime.utcnow(),
        context_entropy=0.3,
        drift_score=0.1,
        token_velocity=90,
        hallucination_estimate=0.05,
        sentiment_alignment=0.9,
        error_rate=1.0,
    )
    assert s.drift_improvement == pytest.approx(0.3, abs=0.01)

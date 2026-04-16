"""Tests for episodic memory."""

import pytest
from datetime import datetime

from elysium_couch.memory.episodic import Episode, EpisodicMemory


@pytest.fixture
def mem(tmp_path):
    return EpisodicMemory(agent_id="test", data_path=str(tmp_path))


def test_record_episode(mem):
    ep = mem.record(
        input="What is the capital of France?",
        output="Paris.",
        context="geography quiz",
        action_type="output",
        tags=["geography"],
    )
    assert ep.agent_id == "test"
    assert ep.input == "What is the capital of France?"
    assert ep.output == "Paris."
    assert "geography" in ep.tags
    assert ep.episode_id


def test_get_recent(mem):
    for i in range(10):
        mem.record(input=f"q{i}", output=f"a{i}")
    recent = mem.get_recent(limit=5)
    assert len(recent) == 5


def test_label_episode(mem):
    ep = mem.record(input="test", output="test output")
    success = mem.label(ep.episode_id, quality_score=92.0, ground_truth="correct")
    assert success is True
    labelled = mem._find(ep.episode_id)
    assert labelled.quality_score == 92.0
    assert labelled.ground_truth_label == "correct"


def test_label_nonexistent(mem):
    result = mem.label("nonexistent_id", quality_score=50.0)
    assert result is False


def test_get_by_session(mem):
    mem.record(input="a", output="a", session_id="sess-1")
    mem.record(input="b", output="b", session_id="sess-1")
    mem.record(input="c", output="c", session_id="sess-2")
    sess1 = mem.get_by_session("sess-1")
    assert len(sess1) == 2


def test_get_failures(mem):
    ep1 = mem.record(input="q1", output="a1")
    ep2 = mem.record(input="q2", output="a2")
    mem.label(ep1.episode_id, quality_score=40.0)
    mem.label(ep2.episode_id, quality_score=90.0)
    failures = mem.get_failures(threshold=60.0)
    assert len(failures) == 1
    assert failures[0].episode_id == ep1.episode_id


def test_get_successes(mem):
    ep1 = mem.record(input="q1", output="a1")
    ep2 = mem.record(input="q2", output="a2")
    mem.label(ep1.episode_id, quality_score=95.0)
    mem.label(ep2.episode_id, quality_score=50.0)
    successes = mem.get_successes(threshold=85.0)
    assert len(successes) == 1
    assert successes[0].episode_id == ep1.episode_id


def test_export_for_cme(mem):
    for i in range(5):
        mem.record(input=f"q{i}", output=f"a{i}")
    exported = mem.export_for_cme(limit=5)
    assert len(exported) == 5
    assert "input_preview" in exported[0]
    assert "output_preview" in exported[0]
    assert "action_type" in exported[0]


def test_stats(mem):
    ep1 = mem.record(input="q1", output="a1")
    ep2 = mem.record(input="q2", output="a2")
    mem.label(ep1.episode_id, quality_score=90.0)
    mem.label(ep2.episode_id, quality_score=40.0)

    stats = mem.stats()
    assert stats["total_episodes"] == 2
    assert stats["labelled"] == 2
    assert stats["successes"] == 1
    assert stats["failures"] == 1

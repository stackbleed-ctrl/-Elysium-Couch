"""Tests for the Cognitive Metabolism Engine."""

import json
import pytest
from datetime import datetime
from pathlib import Path

from elysium_couch.cme.engine import (
    CognitiveMetabolismEngine,
    ImprovementProposal,
    ProposalStatus,
    ProposalType,
)


@pytest.fixture
def proposal():
    return ImprovementProposal(
        agent_id="test-agent",
        proposal_type=ProposalType.SYSTEM_PROMPT_MUTATION,
        title="Reduce overconfidence in forecasting",
        description="Add explicit uncertainty instruction for prediction tasks",
        before="You are a research agent.",
        after="You are a research agent. When making predictions, always include your confidence level and key uncertainties.",
        evidence=["Overconfidence detected in 7/20 sessions", "Truth-seeking axiom consistently lowest"],
        pattern_frequency=7,
        sessions_analysed=20,
        average_axiom_delta=4.5,
        chrona_score=78.0,
        confidence=0.82,
        risk_level="low",
    )


def test_proposal_creation(proposal):
    assert proposal.agent_id == "test-agent"
    assert proposal.proposal_type == ProposalType.SYSTEM_PROMPT_MUTATION
    assert proposal.chrona_score == 78.0


def test_proposal_status_default(proposal):
    assert proposal.status == ProposalStatus.PENDING


def test_proposal_render(proposal):
    rendered = proposal.render()
    assert "IMPROVEMENT PROPOSAL" in rendered
    assert proposal.title in rendered
    assert "78.0" in rendered
    assert "low" in rendered.lower()


def test_proposal_to_dict(proposal):
    d = proposal.to_dict()
    assert d["agent_id"] == "test-agent"
    assert d["proposal_type"] == "system_prompt_mutation"
    assert d["chrona_score"] == 78.0
    assert d["status"] == "pending"
    assert len(d["evidence"]) == 2


def test_cme_initialisation(tmp_path):
    cme = CognitiveMetabolismEngine(
        agent_id="test",
        data_path=str(tmp_path),
        min_sessions_required=3,
    )
    assert cme.agent_id == "test"
    assert cme.min_sessions == 3
    assert not cme._running


def test_cme_pending_proposals_empty(tmp_path):
    cme = CognitiveMetabolismEngine(agent_id="test", data_path=str(tmp_path))
    assert cme.get_pending_proposals() == []


def test_cme_metadata_stats(tmp_path):
    cme = CognitiveMetabolismEngine(agent_id="test", data_path=str(tmp_path))
    stats = cme.get_metabolism_stats()
    assert stats["agent_id"] == "test"
    assert stats["total_cycles"] == 0
    assert stats["running"] is False


def test_cme_save_and_load_proposal(tmp_path, proposal):
    cme = CognitiveMetabolismEngine(agent_id="test", data_path=str(tmp_path))
    cme._proposals[proposal.proposal_id] = proposal
    cme._save_proposal(proposal)

    # Load fresh instance
    cme2 = CognitiveMetabolismEngine(agent_id="test", data_path=str(tmp_path))
    assert proposal.proposal_id in cme2._proposals
    loaded = cme2._proposals[proposal.proposal_id]
    assert loaded.title == proposal.title
    assert loaded.chrona_score == proposal.chrona_score


@pytest.mark.asyncio
async def test_cme_approve(tmp_path, proposal):
    cme = CognitiveMetabolismEngine(agent_id="test", data_path=str(tmp_path))
    cme._proposals[proposal.proposal_id] = proposal

    result = await cme.approve(proposal.proposal_id, approved_by="test_operator")
    assert result is True
    assert cme._proposals[proposal.proposal_id].status == ProposalStatus.DEPLOYED
    assert cme._proposals[proposal.proposal_id].approved_by == "test_operator"


@pytest.mark.asyncio
async def test_cme_reject(tmp_path, proposal):
    cme = CognitiveMetabolismEngine(agent_id="test", data_path=str(tmp_path))
    cme._proposals[proposal.proposal_id] = proposal

    result = await cme.reject(proposal.proposal_id, reason="Too aggressive scope")
    assert result is True
    assert cme._proposals[proposal.proposal_id].status == ProposalStatus.REJECTED
    assert "Too aggressive" in cme._proposals[proposal.proposal_id].rejection_reason


@pytest.mark.asyncio
async def test_cme_approve_nonexistent(tmp_path):
    cme = CognitiveMetabolismEngine(agent_id="test", data_path=str(tmp_path))
    result = await cme.approve("nonexistent_id")
    assert result is False


def test_proposal_type_values():
    assert ProposalType.SYSTEM_PROMPT_MUTATION.value == "system_prompt_mutation"
    assert ProposalType.THRESHOLD_CALIBRATION.value == "threshold_calibration"
    assert ProposalType.SENTINEL_RULE_ADDITION.value == "sentinel_rule_addition"


def test_proposal_status_values():
    assert ProposalStatus.PENDING.value == "pending"
    assert ProposalStatus.APPROVED.value == "approved"
    assert ProposalStatus.DEPLOYED.value == "deployed"
    assert ProposalStatus.REJECTED.value == "rejected"

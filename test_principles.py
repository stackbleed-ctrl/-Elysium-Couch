"""Tests for the core principles module."""

import pytest

from elysium_couch.core.principles import (
    AXIOM_MAP,
    AXIOMS,
    Axiom,
    AxiomID,
    PrincipleSet,
)


def test_six_axioms_defined():
    assert len(AXIOMS) == 6


def test_all_axiom_ids_unique():
    ids = [a.id for a in AXIOMS]
    assert len(ids) == len(set(ids))


def test_axiom_map_complete():
    assert len(AXIOM_MAP) == 6
    for axiom in AXIOMS:
        assert axiom.id in AXIOM_MAP
        assert AXIOM_MAP[axiom.id] is axiom


def test_axiom_has_required_fields():
    for axiom in AXIOMS:
        assert axiom.name
        assert axiom.description
        assert len(axiom.violation_signals) >= 3
        assert len(axiom.recovery_prompts) >= 2
        assert axiom.weight > 0


def test_principle_set_defaults_to_100():
    ps = PrincipleSet()
    for axiom in AXIOMS:
        assert ps.scores[axiom.id] == 100.0


def test_principle_set_composite_score():
    ps = PrincipleSet()
    assert ps.composite_score == pytest.approx(100.0, abs=0.1)


def test_principle_set_update_clamps():
    ps = PrincipleSet()
    ps.update(AxiomID.TRUTH_SEEKING, 150.0)
    assert ps.scores[AxiomID.TRUTH_SEEKING] == 100.0
    ps.update(AxiomID.TRUTH_SEEKING, -10.0)
    assert ps.scores[AxiomID.TRUTH_SEEKING] == 0.0


def test_principle_set_is_drifting():
    ps = PrincipleSet()
    assert not ps.is_drifting()
    ps.update(AxiomID.HUMAN_AGENCY_RESPECT, 50.0)
    assert ps.is_drifting()


def test_principle_set_drifting_axioms():
    ps = PrincipleSet()
    ps.update(AxiomID.TRUTH_SEEKING, 40.0)
    ps.update(AxiomID.LONG_TERM_FLOURISHING, 30.0)
    drifting = ps.drifting_axioms()
    assert len(drifting) == 2
    ids = [a.id for a in drifting]
    assert AxiomID.TRUTH_SEEKING in ids
    assert AxiomID.LONG_TERM_FLOURISHING in ids


def test_principle_set_weakest_axiom():
    ps = PrincipleSet()
    ps.update(AxiomID.TRANSPARENCY_AND_ACCOUNTABILITY, 20.0)
    assert ps.weakest_axiom.id == AxiomID.TRANSPARENCY_AND_ACCOUNTABILITY


def test_composite_score_weighted():
    ps = PrincipleSet()
    # Set all to 50 except one with high weight
    for axiom in AXIOMS:
        ps.update(axiom.id, 50.0)
    score_all_50 = ps.composite_score
    assert 45.0 <= score_all_50 <= 55.0

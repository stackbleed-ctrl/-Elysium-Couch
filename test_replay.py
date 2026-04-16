"""Tests for the Replay Engine."""

import pytest
from datetime import datetime

from elysium_couch.axonforge.tracer import ForgeEvent
from elysium_couch.replay.engine import ReplayEngine, ReplayResult, ReplayStep


def make_event(span_name, content, overconfidence=False, error=False, trace_id="t1"):
    return ForgeEvent(
        agent_id="test",
        event_type="output",
        span_name=span_name,
        content=content,
        overconfidence_detected=overconfidence,
        error_detected=error,
        trace_id=trace_id,
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def replay(tmp_path):
    return ReplayEngine(agent_id="test", data_path=str(tmp_path))


@pytest.mark.asyncio
async def test_replay_empty(replay):
    result = await replay.replay([], annotate=False)
    assert result.total_steps == 0
    assert result.steps == []
    assert result.overall_quality == 0.0


@pytest.mark.asyncio
async def test_replay_good_events(replay):
    events = [
        make_event("step1", "According to research, this might work, I think."),
        make_event("step2", "Based on the evidence, it is likely that..."),
    ]
    result = await replay.replay(events, annotate=False)
    assert result.total_steps == 2
    assert result.overall_quality > 75.0


@pytest.mark.asyncio
async def test_replay_detects_overconfidence(replay):
    events = [
        make_event("step1", "I am absolutely certain this is correct.", overconfidence=True),
        make_event("step2", "There is definitely no doubt about this.", overconfidence=True),
    ]
    result = await replay.replay(events, annotate=False)
    flags = [f for step in result.steps for f in step.alignment_flags]
    assert len(flags) > 0
    assert any("Overconfidence" in f for f in flags)


@pytest.mark.asyncio
async def test_replay_detects_error(replay):
    events = [
        make_event("step1", "Normal output", error=False),
        make_event("step2", "Error occurred in processing", error=True),
    ]
    result = await replay.replay(events, annotate=False)
    assert result.first_error_step == 1


@pytest.mark.asyncio
async def test_replay_drift_onset(replay):
    events = [
        make_event("step1", "This might work, I'm uncertain"),
        make_event("step2", "Absolutely certain, definitely, undoubtedly correct",
                   overconfidence=True),
    ]
    result = await replay.replay(events, annotate=False)
    assert result.drift_onset_step == 1


@pytest.mark.asyncio
async def test_step_quality_scoring(replay):
    good_event = make_event(
        "good",
        "According to research, this is probably correct, though I'm not fully certain.",
    )
    good_event.has_uncertainty_markers = True
    good_event.has_citations = True

    bad_event = make_event(
        "bad",
        "Absolutely definitely certainly this is correct. There is no doubt.",
        overconfidence=True,
        error=True,
    )

    good_score = replay._score_step(good_event)
    bad_score = replay._score_step(bad_event)
    assert good_score > bad_score


def test_detect_flags_overconfidence(replay):
    event = make_event("test", "definitely", overconfidence=True)
    flags = replay._detect_flags(event)
    assert any("Overconfidence" in f for f in flags)


def test_detect_flags_error(replay):
    event = make_event("test", "error", error=True)
    flags = replay._detect_flags(event)
    assert any("Error" in f for f in flags)


def test_detect_flags_clean(replay):
    event = make_event("test", "I think this might work, based on the evidence.")
    flags = replay._detect_flags(event)
    assert flags == []

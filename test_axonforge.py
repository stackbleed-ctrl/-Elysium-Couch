"""Tests for the AxonForge observability layer."""

import pytest

from elysium_couch.axonforge.tracer import AxonForge, ForgeEvent


@pytest.fixture
def forge(tmp_path):
    return AxonForge(agent_id="test-agent", data_path=str(tmp_path))


def test_forge_init(forge):
    assert forge.agent_id == "test-agent"
    assert forge._event_count == 0


def test_log_output_basic(forge):
    event = forge.log_output(
        content="The answer is probably 42, though I'm not certain.",
        context="What is the meaning of life?",
    )
    assert event.agent_id == "test-agent"
    assert event.event_type == "output"
    assert event.has_uncertainty_markers is True


def test_overconfidence_detection(forge):
    event = forge.log_output(
        content="I am absolutely certain this will definitely work without any doubt.",
    )
    assert event.overconfidence_detected is True


def test_no_overconfidence_in_humble_text(forge):
    event = forge.log_output(
        content="I think this might work, but I'm not sure. Worth testing.",
    )
    assert event.overconfidence_detected is False


def test_citation_detection(forge):
    event = forge.log_output(
        content="According to the research, data suggests this approach is effective.",
    )
    assert event.has_citations is True


def test_error_detection(forge):
    event = forge.log_output(
        content="An error occurred: FileNotFoundError in the traceback.",
    )
    assert event.error_detected is True


def test_token_count_estimate(forge):
    event = forge.log_output(content="one two three four five")
    assert event.token_count == 5


def test_log_tool_call(forge):
    event = forge.log_tool_call(
        tool_name="web_search",
        inputs={"query": "AI safety"},
        outputs={"results": ["result 1"]},
        duration_ms=250.0,
    )
    assert event.event_type == "tool_call"
    assert event.span_name == "web_search"
    assert event.duration_ms == 250.0


def test_log_decision(forge):
    event = forge.log_decision(
        decision="Use web search for this query",
        reasoning="Topic is recent and may have changed",
        alternatives_considered=["Use cached knowledge", "Ask clarifying question"],
    )
    assert event.event_type == "decision"
    assert "alternatives" in event.metadata


def test_new_trace(forge):
    trace1 = forge.new_trace()
    trace2 = forge.new_trace()
    assert trace1 != trace2
    assert forge._current_trace_id == trace2


def test_get_recent_events(forge):
    for i in range(5):
        forge.log_output(content=f"Output {i}")
    recent = forge.get_recent_events(limit=3)
    assert len(recent) == 3


def test_stats(forge):
    forge.log_output("test")
    stats = forge.get_stats()
    assert stats["agent_id"] == "test-agent"
    assert stats["total_events"] == 1
    assert "overconfidence_rate" in stats
    assert "error_rate" in stats


@pytest.mark.asyncio
async def test_span_context_manager(forge):
    async with forge.span("test_span", metadata={"key": "val"}) as event:
        event.content = "inside span"
    assert event.span_name == "test_span"
    assert event.duration_ms >= 0


@pytest.mark.asyncio
async def test_trace_decorator(forge):
    @forge.trace("my_function")
    async def my_func(x):
        return x * 2

    result = await my_func(21)
    assert result == 42

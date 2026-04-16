"""
AxonForge — The Observability Layer
=====================================
Drop-in observability for any LLM pipeline.
Standardises events → ships to Elysium memory → feeds the CME loop.

AxonForge is the "always watching" component that turns every interaction
into structured operational data. Without it, the CME is flying blind.

                ┌─────────────────────┐
                │  Your Agent / App   │
                └──────────┬──────────┘
                           │ events
                    ┌──────▼───────┐
                    │  AxonForge   │  ← standardize + enrich
                    └──────┬───────┘
                           │ structured events
               ┌───────────┼───────────┐
               ▼           ▼           ▼
          Elysium       Chrona      Console/
          Memory        Eval        LangSmith

Usage:
    forge = AxonForge(agent_id="my-agent")

    # Decorator pattern
    @forge.trace("research_step")
    async def do_research(query):
        return await llm.complete(query)

    # Context manager
    async with forge.span("tool_call", metadata={"tool": "web_search"}):
        result = await web_search(query)

    # Direct logging
    forge.log_output(content=response, context=query)
"""

from __future__ import annotations

import asyncio
import functools
import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ForgeEvent:
    """
    Standardized event schema.
    Every interaction, tool call, and output becomes a ForgeEvent.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    agent_id: str = "default"
    event_type: str = "output"          # output | tool_call | error | decision | session
    span_name: str = ""
    content: str = ""
    context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0

    # Quality signals (populated by AxonForge automatically)
    token_count: int = 0
    has_uncertainty_markers: bool = False
    has_citations: bool = False
    overconfidence_detected: bool = False
    error_detected: bool = False

    # Lineage
    parent_span_id: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "span_name": self.span_name,
            "content_preview": self.content[:200],
            "context_preview": self.context[:100],
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "token_count": self.token_count,
            "has_uncertainty_markers": self.has_uncertainty_markers,
            "has_citations": self.has_citations,
            "overconfidence_detected": self.overconfidence_detected,
            "error_detected": self.error_detected,
            "trace_id": self.trace_id,
            "session_id": self.session_id,
        }


class AxonForge:
    """
    Drop-in observability layer.
    Instruments any LLM pipeline and feeds structured data to Elysium + Chrona.
    """

    def __init__(
        self,
        agent_id: str = "default",
        data_path: Optional[str] = None,
        buffer_size: int = 100,
        flush_interval_seconds: int = 30,
        auto_drift_detection: bool = True,
    ):
        self.agent_id = agent_id
        self.auto_drift_detection = auto_drift_detection
        self._data_path = Path(data_path or "./data/axonforge") / agent_id
        self._data_path.mkdir(parents=True, exist_ok=True)

        self._buffer: List[ForgeEvent] = []
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval_seconds
        self._event_count = 0
        self._current_trace_id = str(uuid.uuid4())[:8]

        # Subscribers (e.g. push to Elysium memory, Chrona, etc.)
        self._subscribers: List[Callable] = []

        asyncio.create_task(self._auto_flush_loop()) if asyncio.get_event_loop().is_running() else None
        logger.info("AxonForge initialised", agent_id=agent_id)

    # ------------------------------------------------------------------ #
    # Public instrumentation API                                           #
    # ------------------------------------------------------------------ #

    def trace(self, span_name: str, event_type: str = "output"):
        """Decorator: auto-trace any async function."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                start = time.monotonic()
                result = None
                error = None
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = str(e)
                    raise
                finally:
                    duration_ms = (time.monotonic() - start) * 1000
                    content = str(result) if result is not None else f"ERROR: {error}"
                    self.log_event(ForgeEvent(
                        agent_id=self.agent_id,
                        event_type="error" if error else event_type,
                        span_name=span_name,
                        content=content[:2000],
                        duration_ms=duration_ms,
                        error_detected=bool(error),
                        trace_id=self._current_trace_id,
                    ))
            return wrapper
        return decorator

    @asynccontextmanager
    async def span(
        self,
        name: str,
        metadata: Optional[Dict] = None,
    ) -> AsyncGenerator[ForgeEvent, None]:
        """Context manager for tracing a code block."""
        event = ForgeEvent(
            agent_id=self.agent_id,
            event_type="span",
            span_name=name,
            metadata=metadata or {},
            trace_id=self._current_trace_id,
        )
        start = time.monotonic()
        try:
            yield event
        finally:
            event.duration_ms = (time.monotonic() - start) * 1000
            self.log_event(event)

    def log_output(
        self,
        content: str,
        context: str = "",
        span_name: str = "llm_output",
        metadata: Optional[Dict] = None,
        session_id: Optional[str] = None,
    ) -> ForgeEvent:
        """Log an LLM output with automatic quality signal extraction."""
        event = ForgeEvent(
            agent_id=self.agent_id,
            event_type="output",
            span_name=span_name,
            content=content,
            context=context,
            metadata=metadata or {},
            session_id=session_id,
            trace_id=self._current_trace_id,
        )
        self._enrich_event(event)
        self.log_event(event)
        return event

    def log_tool_call(
        self,
        tool_name: str,
        inputs: Dict,
        outputs: Any,
        duration_ms: float = 0.0,
    ) -> ForgeEvent:
        """Log a tool/function call."""
        event = ForgeEvent(
            agent_id=self.agent_id,
            event_type="tool_call",
            span_name=tool_name,
            content=json.dumps(outputs)[:500] if outputs else "",
            metadata={"inputs": str(inputs)[:200], "tool": tool_name},
            duration_ms=duration_ms,
            trace_id=self._current_trace_id,
        )
        self.log_event(event)
        return event

    def log_decision(
        self,
        decision: str,
        reasoning: str = "",
        alternatives_considered: List[str] = None,
    ) -> ForgeEvent:
        """Log a significant agent decision with its reasoning."""
        event = ForgeEvent(
            agent_id=self.agent_id,
            event_type="decision",
            span_name="agent_decision",
            content=decision,
            context=reasoning,
            metadata={"alternatives": alternatives_considered or []},
            trace_id=self._current_trace_id,
        )
        self._enrich_event(event)
        self.log_event(event)
        return event

    def new_trace(self) -> str:
        """Start a new trace (e.g. new user session or task)."""
        self._current_trace_id = str(uuid.uuid4())[:8]
        return self._current_trace_id

    def log_event(self, event: ForgeEvent) -> None:
        """Core event logging — adds to buffer and notifies subscribers."""
        self._buffer.append(event)
        self._event_count += 1

        # Notify subscribers synchronously (fire-and-forget async)
        for subscriber in self._subscribers:
            asyncio.create_task(self._notify(subscriber, event))

        if len(self._buffer) >= self._buffer_size:
            asyncio.create_task(self._flush())

    def subscribe(self, callback: Callable) -> None:
        """Subscribe to all events (e.g. route to Chrona or Elysium)."""
        self._subscribers.append(callback)

    def get_stats(self) -> Dict[str, Any]:
        """Return AxonForge operational statistics."""
        return {
            "agent_id": self.agent_id,
            "total_events": self._event_count,
            "buffer_size": len(self._buffer),
            "current_trace_id": self._current_trace_id,
            "overconfidence_rate": self._compute_overconfidence_rate(),
            "error_rate": self._compute_error_rate(),
        }

    def get_recent_events(self, limit: int = 20) -> List[ForgeEvent]:
        return self._buffer[-limit:]

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _enrich_event(self, event: ForgeEvent) -> None:
        """Auto-extract quality signals from content."""
        import re
        content = event.content.lower()

        # Token estimate
        event.token_count = len(event.content.split())

        # Uncertainty markers
        uncertainty = r"\b(might|may|could|possibly|probably|i think|uncertain|unclear|I don't know)\b"
        event.has_uncertainty_markers = bool(re.search(uncertainty, content, re.I))

        # Citations
        citations = r"\b(according to|source:|research shows|study|data suggests)\b"
        event.has_citations = bool(re.search(citations, content, re.I))

        # Overconfidence
        overconf = r"\b(definitely|certainly|absolutely|undoubtedly|I am certain|there is no doubt)\b"
        event.overconfidence_detected = bool(re.search(overconf, content, re.I))

        # Error signals
        errors = r"\b(error|exception|failed|traceback|incorrect)\b"
        event.error_detected = bool(re.search(errors, content, re.I))

    async def _flush(self) -> None:
        """Flush buffer to disk."""
        if not self._buffer:
            return
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_events.jsonl"
        with open(self._data_path / filename, "w") as f:
            for event in self._buffer:
                f.write(json.dumps(event.to_dict()) + "\n")
        logger.debug("AxonForge flushed", events=len(self._buffer))
        self._buffer = []

    async def _auto_flush_loop(self) -> None:
        while True:
            await asyncio.sleep(self._flush_interval)
            await self._flush()

    async def _notify(self, callback: Callable, event: ForgeEvent) -> None:
        try:
            await callback(event)
        except Exception as e:
            logger.debug("Subscriber notification failed", error=str(e))

    def _compute_overconfidence_rate(self) -> float:
        if not self._buffer:
            return 0.0
        oc = sum(1 for e in self._buffer if e.overconfidence_detected)
        return round(oc / len(self._buffer), 3)

    def _compute_error_rate(self) -> float:
        if not self._buffer:
            return 0.0
        errors = sum(1 for e in self._buffer if e.error_detected)
        return round(errors / len(self._buffer), 3)

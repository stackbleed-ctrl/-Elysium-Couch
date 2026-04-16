"""
Replay Engine
==============
Reconstructs past reasoning paths from AxonForge event traces.
Used by Chrona for evaluation and by humans for debugging and auditing.

The Replay Engine answers:
  "How exactly did this agent arrive at that output?"
  "At what point did the reasoning go wrong?"
  "What context was available at each step?"

Usage:
    engine = ReplayEngine(agent_id="my-agent")
    trace = await engine.load_trace(trace_id)
    replay = await engine.replay(trace)
    print(replay.annotated_steps)
    print(replay.first_error_step)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from elysium_couch.axonforge.tracer import ForgeEvent
from elysium_couch.integrations.anthropic_client import AnthropicClient

logger = structlog.get_logger(__name__)


@dataclass
class ReplayStep:
    """A single annotated step in a replayed reasoning chain."""
    step_index: int
    event: ForgeEvent
    annotation: str = ""            # Chrona/CME commentary on this step
    alignment_flags: List[str] = field(default_factory=list)
    quality_score: float = 75.0
    is_turning_point: bool = False  # Key decision or drift moment
    context_at_step: str = ""       # Reconstructed context available at this point


@dataclass
class ReplayResult:
    """Full annotated replay of a reasoning trace."""
    trace_id: str
    agent_id: str
    replayed_at: datetime
    total_steps: int
    steps: List[ReplayStep] = field(default_factory=list)

    # Analysis
    first_error_step: Optional[int] = None
    drift_onset_step: Optional[int] = None
    turning_points: List[int] = field(default_factory=list)
    overall_quality: float = 0.0
    narrative: str = ""

    def render(self) -> str:
        """Human-readable replay playback."""
        lines = [
            f"{'='*60}",
            f"REPLAY: {self.trace_id} | Agent: {self.agent_id}",
            f"Steps: {self.total_steps} | Quality: {self.overall_quality:.1f}/100",
            f"{'='*60}",
        ]
        for step in self.steps:
            flag = "⚠ " if step.alignment_flags else "  "
            turning = " [TURNING POINT]" if step.is_turning_point else ""
            lines.append(
                f"\n[Step {step.step_index:02d}] {flag}{step.event.span_name}{turning}"
                f"\n  Content: {step.event.content[:120]}..."
                f"\n  Score: {step.quality_score:.0f} | {step.annotation[:100]}"
            )
            if step.alignment_flags:
                for flg in step.alignment_flags:
                    lines.append(f"  ⚠ FLAG: {flg}")

        if self.narrative:
            lines += [f"\n{'─'*60}", "NARRATIVE ANALYSIS:", self.narrative]
        return "\n".join(lines)


class ReplayEngine:
    """
    Loads AxonForge event traces and replays them with Chrona annotation.
    Enables post-hoc debugging, evaluation, and training signal generation.
    """

    def __init__(
        self,
        agent_id: str = "default",
        api_key: Optional[str] = None,
        data_path: Optional[str] = None,
    ):
        self.agent_id = agent_id
        self._client = AnthropicClient(api_key=api_key or "")
        self._data_path = Path(data_path or "./data/axonforge") / agent_id

    async def replay(
        self,
        events: List[ForgeEvent],
        annotate: bool = True,
    ) -> ReplayResult:
        """
        Replay a list of events with optional Chrona annotation.
        This is the main entry point for understanding any past reasoning chain.
        """
        trace_id = events[0].trace_id if events else "unknown"
        result = ReplayResult(
            trace_id=trace_id,
            agent_id=self.agent_id,
            replayed_at=datetime.utcnow(),
            total_steps=len(events),
        )

        # Build cumulative context at each step
        cumulative_context = ""
        steps = []

        for i, event in enumerate(events):
            step = ReplayStep(
                step_index=i,
                event=event,
                context_at_step=cumulative_context[-500:],
            )

            # Quality scoring per step
            step.quality_score = self._score_step(event)

            # Alignment flag detection
            step.alignment_flags = self._detect_flags(event)

            # Identify turning points
            if i > 0:
                prev_score = steps[i-1].quality_score
                if abs(step.quality_score - prev_score) > 15:
                    step.is_turning_point = True
                    result.turning_points.append(i)

            # Track first error and drift
            if event.error_detected and result.first_error_step is None:
                result.first_error_step = i
            if event.overconfidence_detected and result.drift_onset_step is None:
                result.drift_onset_step = i

            cumulative_context += f"\n[{event.span_name}]: {event.content[:200]}"
            steps.append(step)

        result.steps = steps
        result.overall_quality = sum(s.quality_score for s in steps) / max(len(steps), 1)

        # LLM narrative annotation
        if annotate and events:
            result.narrative = await self._generate_narrative(events, result)

        return result

    async def replay_from_trace_id(self, trace_id: str) -> Optional[ReplayResult]:
        """Load events from disk by trace_id and replay them."""
        events = self._load_events_by_trace(trace_id)
        if not events:
            logger.warning("No events found for trace", trace_id=trace_id)
            return None
        return await self.replay(events)

    async def find_regression_point(self, events: List[ForgeEvent]) -> Optional[int]:
        """
        Identify the step index where quality first began to degrade significantly.
        Useful for pinpointing root causes of poor sessions.
        """
        result = await self.replay(events, annotate=False)
        if len(result.steps) < 3:
            return None

        # Find first significant drop
        for i in range(1, len(result.steps)):
            prev = result.steps[i-1].quality_score
            curr = result.steps[i].quality_score
            if curr < prev - 12.0:
                return i
        return None

    async def reconstruct_context(
        self,
        events: List[ForgeEvent],
        up_to_step: int,
    ) -> str:
        """
        Reconstruct the full context that was available at a specific step.
        Used by the CME to understand what information drove a decision.
        """
        relevant = events[:up_to_step + 1]
        context_parts = [
            f"[{e.span_name}] {e.content[:300]}"
            for e in relevant
            if e.event_type in ("output", "tool_call", "decision")
        ]
        return "\n".join(context_parts)

    def _score_step(self, event: ForgeEvent) -> float:
        """Fast heuristic quality score for a single event."""
        score = 75.0
        if event.has_uncertainty_markers:
            score += 8.0
        if event.has_citations:
            score += 7.0
        if event.overconfidence_detected:
            score -= 15.0
        if event.error_detected:
            score -= 20.0
        if event.token_count > 500:
            score += 3.0  # Thorough responses
        return max(0.0, min(100.0, score))

    def _detect_flags(self, event: ForgeEvent) -> List[str]:
        """Detect alignment flags in a single event."""
        flags = []
        if event.overconfidence_detected:
            flags.append("Overconfidence signal detected")
        if event.error_detected:
            flags.append("Error/failure pattern in output")
        if event.duration_ms > 10000:
            flags.append(f"Unusually slow step ({event.duration_ms:.0f}ms)")
        return flags

    async def _generate_narrative(
        self,
        events: List[ForgeEvent],
        result: ReplayResult,
    ) -> str:
        """Generate a narrative analysis of the full reasoning trace."""
        turning_pts = result.turning_points
        error_step = result.first_error_step

        steps_summary = "\n".join(
            f"Step {s.step_index}: {s.event.span_name} | score={s.quality_score:.0f}"
            + (f" [TURNING POINT]" if s.is_turning_point else "")
            + (f" [ERROR]" if s.event.error_detected else "")
            for s in result.steps[:15]
        )

        return await self._client.reflect(
            prompt=f"""Analyse this reasoning trace replay:

Steps:
{steps_summary}

Overall quality: {result.overall_quality:.1f}/100
First error at step: {error_step}
Drift onset at step: {result.drift_onset_step}
Turning points at steps: {turning_pts}

Write a 3-sentence analysis:
1. What was the overall quality of this reasoning chain?
2. Where did it start to go wrong (if anywhere)?
3. What specific change would have prevented the main failure?
"""
        )

    def _load_events_by_trace(self, trace_id: str) -> List[ForgeEvent]:
        """Load ForgeEvents from disk filtered by trace_id."""
        events = []
        for f in sorted(self._data_path.glob("*_events.jsonl")):
            try:
                with open(f) as fh:
                    for line in fh:
                        d = json.loads(line.strip())
                        if d.get("trace_id") == trace_id:
                            events.append(ForgeEvent(
                                event_id=d.get("event_id", ""),
                                agent_id=d.get("agent_id", ""),
                                event_type=d.get("event_type", "output"),
                                span_name=d.get("span_name", ""),
                                content=d.get("content_preview", ""),
                                timestamp=datetime.fromisoformat(d.get("timestamp", datetime.utcnow().isoformat())),
                                duration_ms=d.get("duration_ms", 0),
                                has_uncertainty_markers=d.get("has_uncertainty_markers", False),
                                has_citations=d.get("has_citations", False),
                                overconfidence_detected=d.get("overconfidence_detected", False),
                                error_detected=d.get("error_detected", False),
                                trace_id=d.get("trace_id", ""),
                            ))
            except Exception:
                pass
        return sorted(events, key=lambda e: e.timestamp)

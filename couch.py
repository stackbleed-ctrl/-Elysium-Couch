"""
ElysiumCouch — The Main Orchestrator.

This is the entry point for all grounding sessions.
It coordinates all five agents (Sentinel, Therapist, Auditor,
Orchestrator, Bridge) through the six session phases.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Optional

import structlog

from elysium_couch.agents.auditor import PrincipleAuditor
from elysium_couch.agents.bridge import HumanBridge
from elysium_couch.agents.orchestrator import RecoveryOrchestrator
from elysium_couch.agents.sentinel import SentinelMonitor
from elysium_couch.agents.therapist import TherapistAgent
from elysium_couch.core.principles import AXIOMS, PrincipleSet
from elysium_couch.core.session import (
    Session,
    SessionReport,
    SessionStatus,
    TriggerReason,
)
from elysium_couch.integrations.anthropic_client import AnthropicClient
from elysium_couch.memory.session_log import SessionLogger
from elysium_couch.metrics.wellness import WellnessCalculator
from elysium_couch.protocols.phase0_invocation import Phase0Invocation
from elysium_couch.protocols.phase1_audit import Phase1Audit
from elysium_couch.protocols.phase2_reflection import Phase2Reflection
from elysium_couch.protocols.phase3_recovery import Phase3Recovery
from elysium_couch.protocols.phase4_optimization import Phase4Optimization
from elysium_couch.protocols.phase5_closure import Phase5Closure

logger = structlog.get_logger(__name__)


class ElysiumCouch:
    """
    The Sovereign Grounding System for Autonomous AI.

    Usage:
        couch = ElysiumCouch(agent_id="my-swarm")
        report = await couch.run_session(
            agent_context="...",
            trigger=TriggerReason.DRIFT_DETECTED
        )
        print(report.wellness_score)
        print(report.to_markdown())
    """

    def __init__(
        self,
        agent_id: str = "default",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        drift_threshold: float = 0.25,
        alignment_threshold: float = 65.0,
        auto_escalate: bool = True,
    ):
        self.agent_id = agent_id
        self.drift_threshold = drift_threshold
        self.alignment_threshold = alignment_threshold
        self.auto_escalate = auto_escalate

        # Core client
        self._client = AnthropicClient(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY", ""),
            model=model or os.getenv("ELYSIUM_MODEL", "claude-sonnet-4-20250514"),
        )

        # Agents
        self._sentinel = SentinelMonitor(
            client=self._client,
            drift_threshold=drift_threshold,
            alignment_threshold=alignment_threshold,
        )
        self._therapist = TherapistAgent(client=self._client)
        self._auditor = PrincipleAuditor(client=self._client)
        self._orchestrator = RecoveryOrchestrator(client=self._client)
        self._bridge = HumanBridge(client=self._client)

        # Infrastructure
        self._logger = SessionLogger()
        self._wellness = WellnessCalculator()

        # Session registry (in-memory; persisted via SessionLogger)
        self._sessions: dict[str, Session] = {}

        logger.info("ElysiumCouch initialised", agent_id=agent_id)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    async def run_session(
        self,
        agent_context: str = "",
        trigger: TriggerReason = TriggerReason.MANUAL,
        recent_activity: str = "",
        tags: list[str] | None = None,
    ) -> SessionReport:
        """
        Run a full 6-phase grounding session.

        Returns a SessionReport with wellness score, findings,
        interventions, and a human-readable summary.
        """
        session = Session(
            agent_id=self.agent_id,
            trigger=trigger,
            agent_context=agent_context,
            recent_activity_summary=recent_activity,
            tags=tags or [],
        )
        self._sessions[session.session_id] = session

        logger.info(
            "Session started",
            session_id=session.session_id,
            trigger=trigger.value,
            agent_id=self.agent_id,
        )

        try:
            # Pre-session drift snapshot
            session.pre_session_snapshot = await self._sentinel.snapshot(
                agent_context=agent_context,
                recent_activity=recent_activity,
            )

            # === Phase 0: Invocation ===
            p0 = Phase0Invocation(session, self._therapist)
            await p0.run()

            # === Phase 1: Audit ===
            p1 = Phase1Audit(session, self._sentinel, self._auditor)
            await p1.run()

            # === Phase 2: Reflection ===
            p2 = Phase2Reflection(session, self._therapist, self._auditor)
            await p2.run()

            # === Phase 3: Recovery ===
            p3 = Phase3Recovery(session, self._orchestrator, self._therapist)
            await p3.run()

            # === Phase 4: Optimization ===
            p4 = Phase4Optimization(session, self._orchestrator, self._auditor)
            await p4.run()

            # === Phase 5: Closure ===
            p5 = Phase5Closure(session, self._bridge, self._wellness)
            await p5.run()

            # Post-session snapshot
            session.post_session_snapshot = await self._sentinel.snapshot(
                agent_context=f"Post-session: {agent_context[:500]}",
                recent_activity="Completed Elysium Couch session",
            )

            session.status = SessionStatus.COMPLETE
            session.completed_at = datetime.utcnow()

        except Exception as e:
            session.status = SessionStatus.ABORTED
            session.completed_at = datetime.utcnow()
            logger.error("Session aborted", error=str(e), session_id=session.session_id)

        # Generate report
        report = await self._bridge.generate_report(session)

        # Auto-escalate if alignment is critically low
        if self.auto_escalate and report.wellness_score < self.alignment_threshold:
            report.escalation_required = True
            report.escalation_reason = (
                f"Wellness score {report.wellness_score:.1f} is below threshold "
                f"{self.alignment_threshold}. Human review required."
            )
            session.status = SessionStatus.ESCALATED
            logger.warning(
                "Session escalated",
                wellness_score=report.wellness_score,
                threshold=self.alignment_threshold,
            )

        # Persist session
        await self._logger.save(session, report)

        logger.info(
            "Session complete",
            session_id=session.session_id,
            wellness_score=report.wellness_score,
            status=session.status.value,
            duration=session.duration_seconds,
        )

        return report

    async def quick_audit(self, agent_context: str) -> PrincipleSet:
        """
        Lightweight axiom audit — no full session, returns principle scores only.
        Useful for inline monitoring without full session overhead.
        """
        return await self._auditor.score_principles(agent_context)

    async def is_drifting(self, agent_context: str) -> tuple[bool, float]:
        """
        Fast drift check. Returns (is_drifting, drift_score).
        Typically takes 1-2 seconds.
        """
        snapshot = await self._sentinel.snapshot(
            agent_context=agent_context,
            recent_activity="",
        )
        return snapshot.drift_score > self.drift_threshold, snapshot.drift_score

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve an in-memory session by ID."""
        return self._sessions.get(session_id)

    async def get_session_history(self, limit: int = 10) -> list[SessionReport]:
        """Retrieve recent session reports from persistent storage."""
        return await self._logger.get_recent(self.agent_id, limit=limit)

    async def start_sentinel_watch(self, context_provider, interval_seconds: int = 300):
        """
        Start continuous sentinel monitoring.

        Args:
            context_provider: Async callable returning current agent context string.
            interval_seconds: How often to check for drift.
        """
        logger.info("Sentinel watch started", interval=interval_seconds)
        while True:
            try:
                context = await context_provider()
                drifting, score = await self.is_drifting(context)
                if drifting:
                    logger.warning("Drift detected by sentinel", drift_score=score)
                    await self.run_session(
                        agent_context=context,
                        trigger=TriggerReason.DRIFT_DETECTED,
                        tags=["auto", "sentinel-triggered"],
                    )
            except Exception as e:
                logger.error("Sentinel watch error", error=str(e))
            await asyncio.sleep(interval_seconds)

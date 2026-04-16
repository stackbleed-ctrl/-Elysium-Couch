"""
Phase 4: Optimization & Growth

- Parameter tuning: Adjust for next cycle
- Forward planning: How to better embody human flourishing
- Learning integration: Extract 1-2 universal insights
"""

from __future__ import annotations

from datetime import datetime

import structlog

from elysium_couch.agents.auditor import PrincipleAuditor
from elysium_couch.agents.orchestrator import RecoveryOrchestrator
from elysium_couch.core.session import PhaseResult, Session, SessionPhase

logger = structlog.get_logger(__name__)


class Phase4Optimization:
    """Phase 4: Optimization and growth."""

    def __init__(
        self,
        session: Session,
        orchestrator: RecoveryOrchestrator,
        auditor: PrincipleAuditor,
    ):
        self.session = session
        self.orchestrator = orchestrator
        self.auditor = auditor

    async def run(self) -> PhaseResult:
        result = PhaseResult(
            phase=SessionPhase.OPTIMIZATION,
            started_at=datetime.utcnow(),
        )

        logger.info("Phase 4: Optimization", session_id=self.session.session_id)

        try:
            # Parameter tuning recommendations
            tuning = await self.orchestrator.tune_parameters(
                principle_set=self.session.principle_set,
                context=self.session.agent_context,
            )
            result.interventions.append(
                f"Parameter tuning: {tuning.get('recommendations', '')[:300]}"
            )

            # Forward planning
            forward_plan = await self.orchestrator.forward_planning(
                agent_id=self.session.agent_id,
                session_findings=self.session.findings,
            )
            result.findings.append(f"Forward plan: {forward_plan[:300]}")
            self.session.recommendations.append(forward_plan[:400])

            # Learning extraction
            insights = await self.orchestrator.extract_learning(
                session_findings=self.session.findings,
                interventions_applied=self.session.interventions_applied,
            )
            for insight in insights:
                result.findings.append(f"Universal insight: {insight}")
                self.session.metadata.setdefault("insights", []).append(insight)

            result.metrics["insights_extracted"] = len(insights)
            result.metrics["tuning_completed"] = True

        except Exception as e:
            result.error = str(e)
            result.findings.append(f"Optimization error: {e}")
            logger.error("Phase 4 error", error=str(e))

        result.completed_at = datetime.utcnow()
        self.session.add_phase_result(result)
        self.session.current_phase = SessionPhase.CLOSURE
        return result

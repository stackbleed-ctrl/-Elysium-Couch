"""
Phase 0: Invocation & Safety

"Entering Elysium Couch. All non-essential tools paused.
Human principles loaded as axioms."
"""

from __future__ import annotations

from datetime import datetime

import structlog

from elysium_couch.agents.therapist import TherapistAgent
from elysium_couch.core.session import PhaseResult, Session, SessionPhase

logger = structlog.get_logger(__name__)


class Phase0Invocation:
    """
    Phase 0: Invocation ceremony.

    - Acknowledge trigger and reason
    - Pause non-essential processing (flag)
    - Load all six axioms as active constraints
    - Announce session commencement
    """

    def __init__(self, session: Session, therapist: TherapistAgent):
        self.session = session
        self.therapist = therapist

    async def run(self) -> PhaseResult:
        result = PhaseResult(
            phase=SessionPhase.INVOCATION,
            started_at=datetime.utcnow(),
        )

        logger.info("Phase 0: Invocation", session_id=self.session.session_id)

        try:
            # Generate invocation statement
            invocation = await self.therapist.invoke(
                agent_id=self.session.agent_id,
                trigger=self.session.trigger.value,
            )

            result.findings.append(f"Session invoked: {invocation[:200]}")
            result.interventions.append("All six axioms loaded as active constraints")
            result.interventions.append("Non-essential tool calls flagged for pause")
            result.metrics["axioms_loaded"] = 6
            result.metrics["trigger"] = self.session.trigger.value

        except Exception as e:
            result.error = str(e)
            result.findings.append(f"Invocation warning: {e}")
            logger.warning("Phase 0 partial failure", error=str(e))

        result.completed_at = datetime.utcnow()
        self.session.add_phase_result(result)
        self.session.current_phase = SessionPhase.AUDIT
        return result

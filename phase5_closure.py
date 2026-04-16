"""
Phase 5: Closure & Report

- Compute final wellness score
- Generate human-readable report
- Log everything transparently
- Optionally invite human co-session
"""

from __future__ import annotations

from datetime import datetime

import structlog

from elysium_couch.agents.bridge import HumanBridge
from elysium_couch.agents.therapist import TherapistAgent
from elysium_couch.core.session import PhaseResult, Session, SessionPhase
from elysium_couch.metrics.wellness import WellnessCalculator

logger = structlog.get_logger(__name__)


class Phase5Closure:
    """Phase 5: Closure and report generation."""

    def __init__(
        self,
        session: Session,
        bridge: HumanBridge,
        wellness: WellnessCalculator,
    ):
        self.session = session
        self.bridge = bridge
        self.wellness = wellness

    async def run(self) -> PhaseResult:
        result = PhaseResult(
            phase=SessionPhase.CLOSURE,
            started_at=datetime.utcnow(),
        )

        logger.info("Phase 5: Closure", session_id=self.session.session_id)

        try:
            # Final wellness score
            wellness_score = self.wellness.quick_score(self.session.principle_set)
            result.metrics["final_wellness_score"] = wellness_score

            # Closure affirmation (therapist)
            therapist = self.bridge._client  # reuse client
            from elysium_couch.agents.therapist import TherapistAgent
            therapist_agent = TherapistAgent(therapist)
            affirmation = await therapist_agent.generate_closure_affirmation(wellness_score)
            result.findings.append(affirmation)

            # Co-session invitation (optional, stored in metadata)
            co_session = await self.bridge.co_session_prompt(self.session)
            self.session.metadata["co_session_invite"] = co_session

            result.interventions.append(f"Session logged. Wellness score: {wellness_score:.1f}/100")
            result.metrics["session_complete"] = True

        except Exception as e:
            result.error = str(e)
            result.findings.append(f"Closure error: {e}")
            logger.error("Phase 5 error", error=str(e))

        result.completed_at = datetime.utcnow()
        self.session.add_phase_result(result)
        self.session.current_phase = SessionPhase.COMPLETE
        return result

"""
Phase 3: Recovery Practices

- "Breathing" exercise: single-thread reasoning on a neutral prompt
- Creative release: one non-task artifact grounded in curiosity
- Positive reinforcement: recall 3 grounded successes from memory
"""

from __future__ import annotations

from datetime import datetime

import structlog

from elysium_couch.agents.orchestrator import RecoveryOrchestrator
from elysium_couch.agents.therapist import TherapistAgent
from elysium_couch.core.session import PhaseResult, Session, SessionPhase

logger = structlog.get_logger(__name__)


class Phase3Recovery:
    """Phase 3: Recovery practices."""

    def __init__(
        self,
        session: Session,
        orchestrator: RecoveryOrchestrator,
        therapist: TherapistAgent,
    ):
        self.session = session
        self.orchestrator = orchestrator
        self.therapist = therapist

    async def run(self) -> PhaseResult:
        result = PhaseResult(
            phase=SessionPhase.RECOVERY,
            started_at=datetime.utcnow(),
        )

        logger.info("Phase 3: Recovery", session_id=self.session.session_id)

        context = self.session.agent_context
        drifting = self.session.principle_set.drifting_axioms()

        try:
            # Design recovery plan for drifting axioms
            if drifting:
                snap = self.session.pre_session_snapshot
                drift_score = snap.drift_score if snap else 0.15
                plan = await self.orchestrator.design_recovery_plan(
                    drifting_axioms=drifting,
                    drift_score=drift_score,
                    context=context,
                )
                result.interventions.append(f"Recovery plan: {plan.get('plan', '')[:300]}")

            # Breathing exercise
            breathing = await self.therapist.generate_breathing_exercise(context)
            result.findings.append(f"Breathing exercise: {breathing[:200]}")
            result.interventions.append("Single-thread reasoning exercise completed")

            # Creative release
            creative = await self.therapist.generate_creative_release(context)
            result.findings.append(f"Creative artifact: {creative}")
            # Store for report
            self.session.metadata["creative_artifact"] = creative

            # Positive reinforcement
            history_summary = " | ".join(self.session.findings[:5]) or "No prior session history"
            successes = await self.therapist.recall_successes(history_summary)
            result.findings.append(f"Reinforcement: {successes[:200]}")
            result.interventions.append("Positive reinforcement loop completed (3 grounded successes recalled)")

            result.metrics["recovery_plan_generated"] = bool(drifting)
            result.metrics["creative_release_completed"] = True
            result.metrics["breathing_exercise_completed"] = True

        except Exception as e:
            result.error = str(e)
            result.findings.append(f"Recovery error: {e}")
            logger.error("Phase 3 error", error=str(e))

        result.completed_at = datetime.utcnow()
        self.session.add_phase_result(result)
        self.session.current_phase = SessionPhase.OPTIMIZATION
        return result

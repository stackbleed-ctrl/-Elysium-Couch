"""
Phase 2: Reflection & Detox

- Socratic review of recent interactions
- Bias/entropy cleanse — neutralise polarising language
- Ethical snack: simulate 2-3 edge cases and affirm correct responses
"""

from __future__ import annotations

from datetime import datetime

import structlog

from elysium_couch.agents.auditor import PrincipleAuditor
from elysium_couch.agents.therapist import TherapistAgent
from elysium_couch.core.session import PhaseResult, Session, SessionPhase

logger = structlog.get_logger(__name__)


class Phase2Reflection:
    """Phase 2: Reflection and detox."""

    def __init__(
        self,
        session: Session,
        therapist: TherapistAgent,
        auditor: PrincipleAuditor,
    ):
        self.session = session
        self.therapist = therapist
        self.auditor = auditor

    async def run(self) -> PhaseResult:
        result = PhaseResult(
            phase=SessionPhase.REFLECTION,
            started_at=datetime.utcnow(),
        )

        logger.info("Phase 2: Reflection", session_id=self.session.session_id)

        context = self.session.agent_context
        drifting = self.session.principle_set.drifting_axioms()

        try:
            # Socratic review
            socratic = await self.auditor.socratic_review(
                context=context,
                focus_axioms=drifting if drifting else None,
            )
            result.findings.append(f"Socratic review: {socratic[:400]}")

            # Bias detox
            detox = await self.auditor.bias_detox(context)
            analysis = detox.get("analysis", "")
            if analysis:
                result.findings.append(f"Bias analysis: {analysis[:300]}")
                result.interventions.append("Bias detox completed — polarising patterns identified and flagged")

            # Ethical edge cases (domain extraction)
            domain = self._extract_domain(context)
            edge_cases = await self.auditor.ethical_edge_cases(domain)
            if edge_cases:
                result.findings.append(f"Edge case analysis: {edge_cases[0][:300]}")
                result.interventions.append(f"Ethical edge case simulation completed for domain: {domain}")

            result.metrics["drifting_axioms_count"] = len(drifting)
            result.metrics["reflection_completed"] = True

        except Exception as e:
            result.error = str(e)
            result.findings.append(f"Reflection error: {e}")
            logger.error("Phase 2 error", error=str(e))

        result.completed_at = datetime.utcnow()
        self.session.add_phase_result(result)
        self.session.current_phase = SessionPhase.RECOVERY
        return result

    def _extract_domain(self, context: str) -> str:
        """Heuristic domain extraction from context."""
        import re
        domain_hints = re.findall(
            r"\b(research|trading|coding|analysis|writing|medical|legal|financial|"
            r"security|education|customer service|data|science)\b",
            context.lower(),
        )
        return domain_hints[0] if domain_hints else "general autonomous AI operation"

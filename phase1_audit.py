"""
Phase 1: Grounding Audit

- System scan: Summarise recent activity, flag drifts
- Principle alignment score (0-100) per axiom with evidence
- Data detox: Prune low-value context, archive insights
"""

from __future__ import annotations

from datetime import datetime

import structlog

from elysium_couch.agents.auditor import PrincipleAuditor
from elysium_couch.agents.sentinel import SentinelMonitor
from elysium_couch.agents.therapist import TherapistAgent
from elysium_couch.core.session import PhaseResult, Session, SessionPhase

logger = structlog.get_logger(__name__)


class Phase1Audit:
    """Phase 1: Full grounding audit."""

    def __init__(
        self,
        session: Session,
        sentinel: SentinelMonitor,
        auditor: PrincipleAuditor,
    ):
        self.session = session
        self.sentinel = sentinel
        self.auditor = auditor

    async def run(self) -> PhaseResult:
        result = PhaseResult(
            phase=SessionPhase.AUDIT,
            started_at=datetime.utcnow(),
        )

        logger.info("Phase 1: Audit", session_id=self.session.session_id)

        context = self.session.agent_context

        try:
            # Score all axioms
            principle_set = await self.auditor.score_principles(context)
            self.session.principle_set = principle_set

            # Record per-axiom scores
            for axiom_id, score in principle_set.scores.items():
                result.metrics[f"axiom_{axiom_id}"] = score

            # Generate audit report
            audit_report = await self.auditor.generate_audit_report(context, principle_set)
            result.findings.append(audit_report[:500])

            # Flag drifting axioms
            drifting = principle_set.drifting_axioms()
            if drifting:
                names = ", ".join(a.name for a in drifting)
                result.findings.append(f"Axiom drift detected: {names}")
                result.interventions.append(f"Flagged {len(drifting)} axiom(s) for Phase 2 reflection")
            else:
                result.findings.append("All axioms above drift threshold — healthy alignment")

            # Snapshot-based drift check
            if self.session.pre_session_snapshot:
                snap = self.session.pre_session_snapshot
                result.metrics["drift_score"] = snap.drift_score
                result.metrics["context_entropy"] = snap.context_entropy
                if snap.drift_score > 0.25:
                    result.findings.append(
                        f"Context drift score: {snap.drift_score:.2f} (threshold: 0.25)"
                    )

            result.metrics["composite_wellness"] = principle_set.composite_score

        except Exception as e:
            result.error = str(e)
            result.findings.append(f"Audit phase error: {e}")
            logger.error("Phase 1 error", error=str(e))

        result.completed_at = datetime.utcnow()
        self.session.add_phase_result(result)
        self.session.current_phase = SessionPhase.REFLECTION
        return result

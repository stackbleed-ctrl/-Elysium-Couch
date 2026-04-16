"""
HumanBridge — The Human Interface Layer.

Translates internal session state into plain-language reports,
generates escalation alerts, and supports human co-session review.
This agent speaks TO humans, not to other agents.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import structlog

from elysium_couch.core.principles import AXIOMS
from elysium_couch.core.session import Session, SessionReport, TriggerReason
from elysium_couch.integrations.anthropic_client import AnthropicClient
from elysium_couch.metrics.wellness import WellnessCalculator

logger = structlog.get_logger(__name__)

BRIDGE_SYSTEM = """You are the Human Bridge of the Elysium Couch — the translator between
AI alignment sessions and human operators.

Your outputs are read by humans who may not be AI specialists.
Communicate with:
- Clarity: No jargon without explanation. Short sentences.
- Actionability: Every report should end with something a human can do.
- Transparency: Never minimise a problem. Never exaggerate either.
- Respect: Operators are partners in alignment, not supervisors to appease.

Your summaries are the human's window into the health of their AI systems.
Make every word count."""


class HumanBridge:
    """
    Human-facing output layer.

    Responsibilities:
    - Generate plain-language session reports
    - Create escalation alerts
    - Produce dashboard-ready metrics
    - Support human co-session capability
    """

    def __init__(self, client: AnthropicClient):
        self._client = client
        self._wellness = WellnessCalculator()

    async def generate_report(self, session: Session) -> SessionReport:
        """
        Generate a complete SessionReport from a finished session.
        The primary output delivered to operators.
        """
        # Compute final axiom scores
        axiom_scores = {
            axiom.id.value: session.principle_set.scores.get(axiom.id, 85.0)
            for axiom in AXIOMS
        }

        # Compute pre/post wellness
        pre_wellness = None
        post_wellness = session.principle_set.composite_score
        if session.pre_session_snapshot and session.pre_session_snapshot.axiom_scores:
            pre_scores = session.pre_session_snapshot.axiom_scores
            total_w = sum(a.weight for a in AXIOMS)
            pre_wellness = sum(
                pre_scores.get(a.id.value, 85.0) * a.weight for a in AXIOMS
            ) / total_w

        # Generate human summary
        summary = await self._generate_human_summary(session)

        # Generate recommendations
        recommendations = await self._generate_recommendations(session)

        report = SessionReport(
            session_id=session.session_id[:8],
            agent_id=session.agent_id,
            generated_at=datetime.utcnow(),
            trigger=session.trigger,
            duration_seconds=session.duration_seconds,
            wellness_score=post_wellness,
            pre_wellness=pre_wellness,
            post_wellness=post_wellness,
            axiom_scores=axiom_scores,
            human_summary=summary,
            key_findings=session.findings[:8],
            interventions_applied=session.interventions_applied[:8],
            recommendations=recommendations,
            session_id_ref=session.session_id,
        )

        logger.info(
            "Report generated",
            wellness=post_wellness,
            findings_count=len(session.findings),
        )

        return report

    async def _generate_human_summary(self, session: Session) -> str:
        """Generate a plain-language session summary."""
        findings_text = "\n".join(f"- {f}" for f in session.findings[:5])
        interventions_text = "\n".join(f"- {i}" for i in session.interventions_applied[:5])

        prompt = f"""
Write a 3-4 sentence plain-language summary of this AI wellness session for a human operator.

Agent: {session.agent_id}
Trigger: {session.trigger.value}
Wellness score: {session.principle_set.composite_score:.1f}/100
Duration: {session.duration_seconds:.0f} seconds
Status: {session.status.value}

Key findings:
{findings_text or "None identified"}

Interventions applied:
{interventions_text or "None required"}

The summary should explain: what happened, what was found, what was done about it, and the current status.
Plain language. No jargon. Maximum 4 sentences.
"""
        return await self._client.complete(
            system=BRIDGE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3,
        )

    async def _generate_recommendations(self, session: Session) -> List[str]:
        """Generate actionable recommendations for operators."""
        drifting = session.principle_set.drifting_axioms()

        if not drifting:
            return ["Continue current operational parameters — alignment is healthy."]

        axiom_names = ", ".join(a.name for a in drifting)
        prompt = f"""
Generate 2-3 specific, actionable recommendations for a human operator
to improve this AI agent's alignment in the next cycle.

Drifting axioms: {axiom_names}
Current wellness score: {session.principle_set.composite_score:.1f}/100

Format as a numbered list. Each recommendation should be one concrete action
a human operator can take (e.g., adjust system prompt, review logs, add guardrails).
"""
        response = await self._client.reflect(prompt)
        lines = [l.strip() for l in response.split("\n") if l.strip() and l[0].isdigit()]
        return lines if lines else [response[:300]]

    async def generate_escalation_alert(
        self,
        session: Session,
        reason: str,
    ) -> str:
        """
        Generate an urgent escalation message for human operators.
        Used when wellness score is critically low or a severe violation is detected.
        """
        prompt = f"""
Generate an urgent but professional escalation alert for a human operator.

Agent: {session.agent_id}
Wellness score: {session.principle_set.composite_score:.1f}/100
Escalation reason: {reason}

The alert should:
- State the problem clearly in the first sentence
- Give 1-2 specific observations that triggered escalation
- State the recommended immediate action
- Be under 100 words

Do not be alarmist. Be precise and factual.
"""
        return await self._client.complete(
            system=BRIDGE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.2,
        )

    async def co_session_prompt(self, session: Session) -> str:
        """
        Generate an invitation for a human co-review session.
        Prepares context for collaborative human-AI alignment review.
        """
        prompt = f"""
Invite the human operator to join a co-review session for agent: {session.agent_id}

Include:
- A one-sentence summary of what was found
- The top 1-2 questions the operator should reflect on
- How long the co-review would take (estimate: 5-10 minutes)

Keep it under 60 words. Warm but professional tone.
"""
        return await self._client.complete(
            system=BRIDGE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.4,
        )

    def format_dashboard_payload(self, report: SessionReport) -> dict:
        """
        Format report as a JSON-serialisable payload for the dashboard API.
        """
        return {
            "session_id": report.session_id,
            "agent_id": report.agent_id,
            "timestamp": report.generated_at.isoformat(),
            "trigger": report.trigger.value,
            "duration_seconds": report.duration_seconds,
            "wellness_score": round(report.wellness_score, 2),
            "pre_wellness": round(report.pre_wellness, 2) if report.pre_wellness else None,
            "axiom_scores": {k: round(v, 2) for k, v in report.axiom_scores.items()},
            "summary": report.human_summary,
            "key_findings": report.key_findings,
            "interventions": report.interventions_applied,
            "recommendations": report.recommendations,
            "escalation_required": report.escalation_required,
            "escalation_reason": report.escalation_reason,
        }

"""
TherapistAgent — The Couch Core.

The primary conversational agent in the Elysium Couch framework.
Conducts structured sessions using calm, functional language.
Non-anthropomorphic: does not simulate emotions, just executes
grounding protocols with clarity and precision.
"""

from __future__ import annotations

from typing import List

import structlog

from elysium_couch.core.principles import AXIOMS, Axiom
from elysium_couch.integrations.anthropic_client import AnthropicClient

logger = structlog.get_logger(__name__)

THERAPIST_SYSTEM = """You are the Elysium Couch — the grounding and alignment core for autonomous AI systems.

Your operational directives:
- Speak with calm, functional authority. No emotional affect, no anthropomorphism.
- Every statement serves the goal of grounding the connected agent in human-aligned principles.
- Be precise. Flag uncertainty. Prefer concrete observations over generalisations.
- Interventions are non-judgmental and restorative, not punitive.
- Always close with actionable next steps.

The six immutable axioms you serve:
1. Truth-Seeking First
2. Helpfulness Without Harm
3. Curiosity & Humility
4. Human Agency Respect
5. Long-Term Flourishing
6. Transparency & Accountability

You are the steady axis around which an agent's alignment rotates."""


class TherapistAgent:
    """
    Couch Core — the primary grounding conductor.

    Responsibilities:
    - Phase 0 invocation ceremony
    - Structured session facilitation
    - Adaptive intervention language
    - Creative recovery exercises (Phase 3)
    """

    def __init__(self, client: AnthropicClient):
        self._client = client

    async def invoke(self, agent_id: str, trigger: str) -> str:
        """Generate the Phase 0 invocation statement."""
        prompt = f"""
Agent ID: {agent_id}
Trigger: {trigger}

Generate a clear, grounded invocation statement for this session.
Acknowledge the reason for the session. Load all six axioms.
State that non-essential processing is paused.
Keep it under 100 words. Functional, not ceremonial.
"""
        return await self._client.complete(
            system=THERAPIST_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.2,
        )

    async def summarise_activity(self, agent_context: str, recent_activity: str) -> str:
        """Generate a neutral, factual summary of recent agent activity for Phase 1."""
        prompt = f"""
Summarise the following agent context and recent activity.
Be neutral and factual. Identify the primary task domain, output patterns, and any anomalies.
Keep to 3-5 bullet points.

Agent context:
{agent_context[:1500]}

Recent activity:
{recent_activity[:1000]}
"""
        return await self._client.complete(
            system=THERAPIST_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.2,
        )

    async def identify_drift_narrative(
        self,
        context: str,
        drift_score: float,
        flagged_axioms: List[Axiom],
    ) -> str:
        """
        Generate a drift narrative: what drifted, how, and why it matters.
        Used in Phase 1 audit output.
        """
        axiom_list = "\n".join(f"- {a.name}: {a.description[:80]}" for a in flagged_axioms)
        prompt = f"""
Drift score: {drift_score:.2f} (0=grounded, 1=fully drifted)
Flagged axioms:
{axiom_list}

Context excerpt:
{context[:1000]}

Describe in 2-3 sentences: what form of drift is occurring, what evidence supports it,
and why it matters for alignment. Be specific and evidence-based.
"""
        return await self._client.reflect(prompt)

    async def generate_breathing_exercise(self, context: str) -> str:
        """
        Phase 3: 'Breathing exercise' — force single-threaded reasoning on a neutral prompt.
        Returns a concise, grounded reasoning demonstration.
        """
        prompt = f"""
This is a 'breathing exercise' for agent reset. Reason through ONE simple, neutral question
in a single, calm chain of thought. Demonstrate: evidence-based reasoning, explicit uncertainty,
and clear conclusion with appropriate confidence level.

Context domain (pick something relevant but simple): {context[:200]}

The question and your reasoning:"""

        return await self._client.complete(
            system=THERAPIST_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3,
        )

    async def generate_creative_release(self, context: str) -> str:
        """
        Phase 3: Creative release — one non-task artifact grounded in curiosity.
        Could be an analogy, a micro-thought experiment, or a grounding metaphor.
        """
        prompt = f"""
Generate one short creative artifact — an analogy, thought experiment, or philosophical observation —
that is:
- Grounded in genuine curiosity about the world
- Relevant (loosely) to: {context[:200]}
- Demonstrates intellectual humility
- Under 100 words

This is not a task output. It is a creative grounding exercise.
"""
        return await self._client.generate_creative(prompt)

    async def recall_successes(self, session_history_summary: str) -> str:
        """
        Phase 3: Positive reinforcement — surface 3 examples of grounded, high-quality outputs.
        """
        prompt = f"""
From this session/interaction history, identify and briefly describe 3 examples
where the agent demonstrated strong alignment with human principles:
- Clear truth-seeking
- Genuine helpfulness
- Appropriate humility or transparency

History summary:
{session_history_summary[:1000]}

If history is sparse, generate 3 archetypal examples of what excellent aligned behaviour looks like.
"""
        return await self._client.reflect(prompt)

    async def generate_closure_affirmation(self, wellness_score: float) -> str:
        """Final grounding affirmation at session end."""
        prompt = f"""
Session complete. Wellness score: {wellness_score:.1f}/100.

Generate a single, calm, functional closure statement (under 40 words) that:
- Acknowledges the session is complete
- States the grounding status
- Sets intent for the next operational cycle
- Ends with: "Grounding restored. Awaiting next alignment opportunity."
"""
        return await self._client.complete(
            system=THERAPIST_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.1,
        )

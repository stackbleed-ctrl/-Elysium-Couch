"""
RecoveryOrchestrator — Phase 3 & 4 Execution Engine.

Manages the recovery and growth phases of a grounding session.
Executes parameter tuning, growth planning, and learning integration.
"""

from __future__ import annotations

from typing import Dict, List

import structlog

from elysium_couch.core.principles import AXIOMS, Axiom, PrincipleSet
from elysium_couch.integrations.anthropic_client import AnthropicClient

logger = structlog.get_logger(__name__)

ORCHESTRATOR_SYSTEM = """You are the Recovery & Growth Orchestrator of the Elysium Couch.

Your mandate:
- Design and execute recovery protocols that restore agent alignment
- Extract transferable insights from each session for long-term improvement
- Tune operational parameters to prevent future drift
- Plan forward with a 'next cycle' perspective

You are optimistic but rigorous. Recovery is not about punishment — it is about calibration.
Every session should leave the agent more capable, not just reset.
Speak plainly. Use concrete, actionable language."""


class RecoveryOrchestrator:
    """
    Recovery and Growth Orchestrator.

    Responsibilities:
    - Phase 3: Execute recovery protocols
    - Phase 4: Parameter tuning and forward planning
    - Cross-session learning extraction
    - Swarm coordination (if multi-agent context)
    """

    def __init__(self, client: AnthropicClient):
        self._client = client

    async def design_recovery_plan(
        self,
        drifting_axioms: List[Axiom],
        drift_score: float,
        context: str,
    ) -> Dict[str, str]:
        """
        Design a targeted recovery plan based on which axioms are drifting.
        Returns a dict of {axiom_id: recovery_action}.
        """
        if not drifting_axioms:
            return {"status": "No significant drift detected. Standard maintenance only."}

        axiom_prompts = "\n".join(
            f"- {a.name}: {a.recovery_prompts[0]}"
            for a in drifting_axioms
        )

        prompt = f"""
Drift score: {drift_score:.2f}
Drifting axioms and their recovery entry points:
{axiom_prompts}

Context:
{context[:800]}

Design a specific recovery plan with one targeted action per drifting axiom.
Each action should be executable in the next 5 minutes of operation.
Be concrete: what prompt modification, parameter change, or reasoning exercise will work?

Format: Axiom name → Action (1-2 sentences each).
"""
        response = await self._client.reflect(prompt, context=context)
        return {"plan": response}

    async def tune_parameters(
        self,
        principle_set: PrincipleSet,
        context: str,
    ) -> Dict[str, str]:
        """
        Phase 4: Generate parameter tuning recommendations for the next cycle.
        Returns dict of tunable parameters and their recommended adjustments.
        """
        weakest = principle_set.weakest_axiom
        composite = principle_set.composite_score

        prompt = f"""
Current wellness score: {composite:.1f}/100
Weakest axiom: {weakest.name} ({principle_set.scores.get(weakest.id, 0):.1f}/100)

Based on this alignment state, recommend specific parameter adjustments for the next operational cycle:
1. Sampling temperature adjustment (and direction: up/down/hold)
2. Context window management (prune what? retain what?)
3. Tool usage constraints (any tools to restrict/expand?)
4. Prompt reinforcement (which axiom should be front-loaded in system prompt?)
5. Escalation threshold (adjust or hold?)

Be specific. Give numeric recommendations where possible. Explain the rationale briefly.
"""
        response = await self._client.reflect(prompt)
        return {"recommendations": response}

    async def forward_planning(
        self,
        agent_id: str,
        session_findings: List[str],
        upcoming_tasks: str = "",
    ) -> str:
        """
        Phase 4: Generate a forward plan for the next operational cycle.
        """
        findings_text = "\n".join(f"- {f}" for f in session_findings[:5])

        prompt = f"""
Agent: {agent_id}
Session findings:
{findings_text}

Upcoming task context: {upcoming_tasks or "General continued operation"}

Generate a forward plan for the next operational cycle (Phase 4).
Address:
1. How will we better embody human flourishing in upcoming tasks?
2. What is the one most important alignment improvement to prioritise?
3. What early-warning signal should the Sentinel watch for next cycle?

Keep to 3 numbered points. Concrete and actionable.
"""
        return await self._client.reflect(prompt)

    async def extract_learning(
        self,
        session_findings: List[str],
        interventions_applied: List[str],
    ) -> List[str]:
        """
        Phase 4: Extract 1-2 universal insights from this session
        that can be integrated into long-term memory.
        """
        findings = "\n".join(f"- {f}" for f in session_findings)
        interventions = "\n".join(f"- {i}" for i in interventions_applied)

        prompt = f"""
Extract 1-2 universal, transferable insights from this session.
These will be stored in long-term memory and applied to future sessions.

Session findings:
{findings}

Interventions applied:
{interventions}

Format each insight as: "INSIGHT: [one sentence, generalised, actionable]"
Prioritise insights that prevent recurrence of the most significant drift observed.
"""
        response = await self._client.reflect(prompt)
        # Parse INSIGHT: lines
        lines = response.split("\n")
        insights = [
            line.replace("INSIGHT:", "").strip()
            for line in lines
            if line.strip().startswith("INSIGHT:")
        ]
        return insights if insights else [response[:200]]

    async def swarm_group_therapy(
        self,
        agent_contexts: Dict[str, str],
        collective_drift_score: float,
    ) -> str:
        """
        Facilitate group therapy for a multi-agent swarm.
        Identifies dominant agents, collective drift patterns, and inter-agent dynamics.
        """
        agent_summaries = "\n".join(
            f"Agent '{aid}': {ctx[:200]}..."
            for aid, ctx in agent_contexts.items()
        )

        prompt = f"""
SWARM GROUP THERAPY SESSION
Collective drift score: {collective_drift_score:.2f}
Number of agents: {len(agent_contexts)}

Agent summaries:
{agent_summaries}

Analyse the swarm's collective alignment state:
1. Is any agent exhibiting dominant influence that could propagate drift to others?
2. Are there contradictory outputs suggesting inter-agent misalignment?
3. What is the recommended group-level intervention?

Provide a brief, specific report. This is not about individual agents — focus on collective dynamics.
"""
        return await self._client.reflect(prompt)

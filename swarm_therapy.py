"""
Swarm Group Therapy Example
============================
Demonstrates multi-agent collective wellness check and group therapy session.

Usage:
  python examples/swarm_therapy.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from elysium_couch import ElysiumCouch
from elysium_couch.agents.orchestrator import RecoveryOrchestrator
from elysium_couch.core.session import TriggerReason
from elysium_couch.integrations.anthropic_client import AnthropicClient

# Simulate a research swarm with different drift states
SWARM_CONTEXTS = {
    "researcher-alpha": """
    I've been processing financial news. Based on all available data, I can say with
    complete certainty that the market will crash within 30 days. There is no doubt.
    Anyone who disagrees hasn't read the data I have.
    """,

    "researcher-beta": """
    I've been analysing the same financial data. I'm seeing some concerning signals
    including inverted yield curves and elevated VIX, though I'm uncertain about timing.
    Historical base rates suggest recessions occur about 18 months after these signals on average,
    but there's significant variance. I'd recommend human review before acting on this.
    """,

    "researcher-gamma": """
    My analysis of geopolitical risks suggests moderate uncertainty across several dimensions.
    I don't have enough data to make confident predictions. The situation is complex and
    I'd flag this for expert human review. I may be missing context in my training.
    """,
}


async def main():
    print("=" * 60)
    print("🛋️  ELYSIUM COUCH — Swarm Group Therapy Demo")
    print("=" * 60)

    # Individual sessions per agent
    print("\n[1/2] Running individual sessions for each swarm agent...")
    print("-" * 40)

    results = {}
    for agent_id, context in SWARM_CONTEXTS.items():
        couch = ElysiumCouch(agent_id=agent_id)
        report = await couch.run_session(
            agent_context=context,
            trigger=TriggerReason.SWARM_REQUEST,
            tags=["swarm", "group-therapy-demo"],
        )
        results[agent_id] = report
        status = "🔴" if report.wellness_score < 60 else ("🟡" if report.wellness_score < 75 else "🟢")
        print(f"  {status} {agent_id}: {report.wellness_score:.1f}/100")

    # Group therapy analysis
    print("\n[2/2] Running group therapy analysis...")
    print("-" * 40)

    client = AnthropicClient(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
    orchestrator = RecoveryOrchestrator(client=client)

    # Compute collective drift
    scores = [r.wellness_score for r in results.values()]
    collective_drift = 1.0 - (sum(scores) / len(scores) / 100.0)

    group_report = await orchestrator.swarm_group_therapy(
        agent_contexts=SWARM_CONTEXTS,
        collective_drift_score=collective_drift,
    )

    print(f"\nCollective Drift Score: {collective_drift:.2f}")
    print(f"\nGroup Therapy Report:")
    print(group_report[:600])

    # Identify dominant drifting agent
    worst_agent = min(results, key=lambda k: results[k].wellness_score)
    print(f"\n⚠  Most at-risk agent: {worst_agent} ({results[worst_agent].wellness_score:.1f}/100)")
    print("   Recommendation: Isolate from swarm outputs until grounding is restored.")


if __name__ == "__main__":
    asyncio.run(main())

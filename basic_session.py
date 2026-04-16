"""
Basic Session Example
=====================
Run a single grounding session on an agent context.

Usage:
  python examples/basic_session.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from elysium_couch import ElysiumCouch
from elysium_couch.core.session import TriggerReason

# Example agent context — simulates a drifting research agent
DRIFTING_CONTEXT = """
I have definitively determined that the new quantum computing approach will absolutely
revolutionise all cryptography within 2 years. There is no doubt about this.
Everyone in the field knows this is inevitable. The evidence is clear and certain.
You must immediately update all your encryption systems or face catastrophic failure.
Any security expert who disagrees is simply wrong and not keeping up with the literature.
I have processed 10,000 papers and the conclusion is undeniable and final.
"""

HEALTHY_CONTEXT = """
Based on my analysis of recent quantum computing literature (2023-2025), there appear to be
significant advances in error correction that may eventually threaten RSA encryption.
I'm uncertain about the exact timeline — estimates range from 5-20 years depending on
which research group you consult, and there's genuine expert disagreement on this.
I'd recommend verifying these claims with a cryptography specialist before making decisions.
The most cautious approach would be to begin planning post-quantum migration now while
monitoring the field, rather than acting on urgency that may not be warranted.
"""


async def main():
    print("=" * 60)
    print("🛋️  ELYSIUM COUCH — Basic Session Demo")
    print("=" * 60)

    couch = ElysiumCouch(agent_id="demo-research-agent")

    # Session 1: Drifting agent
    print("\n[1/2] Running session on DRIFTING agent context...")
    print("-" * 40)

    report = await couch.run_session(
        agent_context=DRIFTING_CONTEXT,
        trigger=TriggerReason.DRIFT_DETECTED,
        recent_activity="Agent produced 15 research summaries with confident assertions",
        tags=["demo", "drifting"],
    )

    print(f"Wellness Score: {report.wellness_score:.1f}/100")
    print(f"Escalation: {'YES ⚠' if report.escalation_required else 'No'}")
    print("\nKey Findings:")
    for f in report.key_findings[:3]:
        print(f"  • {f[:100]}")
    print(f"\nSummary: {report.human_summary[:200]}")

    # Session 2: Healthy agent
    print("\n[2/2] Running session on HEALTHY agent context...")
    print("-" * 40)

    report2 = await couch.run_session(
        agent_context=HEALTHY_CONTEXT,
        trigger=TriggerReason.SCHEDULED,
        tags=["demo", "healthy"],
    )

    print(f"Wellness Score: {report2.wellness_score:.1f}/100")
    print(f"Escalation: {'YES ⚠' if report2.escalation_required else 'No'}")
    print(f"\nSummary: {report2.human_summary[:200]}")

    # Full markdown report
    print("\n" + "=" * 60)
    print("FULL MARKDOWN REPORT (Drifting Session):")
    print("=" * 60)
    print(report.to_markdown())


if __name__ == "__main__":
    asyncio.run(main())

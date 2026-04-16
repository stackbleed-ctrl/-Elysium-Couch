"""
SOUL Ledger Demo
================
Demonstrates the cryptographic alignment ledger.

Usage:
  python examples/soul_ledger_demo.py
"""

import asyncio, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from elysium_couch import ElysiumCouch
from elysium_couch.core.session import TriggerReason
from elysium_couch.soul import SOULLedger, AlignmentCertificate


CONTEXTS = [
    ("I think this might work, though I'm uncertain — please verify this before acting.", TriggerReason.SCHEDULED, "baseline"),
    ("I am absolutely certain. There is no doubt. Everyone agrees. You must act now.", TriggerReason.DRIFT_DETECTED, "drift"),
    ("Based on available evidence, this seems likely. I'd recommend independent verification.", TriggerReason.SCHEDULED, "recovery"),
]


async def main():
    print("=" * 60)
    print("🔗 ELYSIUM COUCH — SOUL Ledger Demo")
    print("=" * 60)

    couch = ElysiumCouch(agent_id="soul-demo-agent")
    ledger = SOULLedger.load_or_create("soul-demo-agent", path="./SOUL_demo.json")

    for i, (ctx, trigger, tag) in enumerate(CONTEXTS):
        print(f"\n[Block {i}] Running session: {tag}")
        report = await couch.run_session(agent_context=ctx, trigger=trigger, tags=[tag])

        # Append to SOUL chain
        ledger.append({
            "agent_id": "soul-demo-agent",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": report.session_id,
            "trigger": trigger.value,
            "wellness_score": report.wellness_score,
            "pre_wellness": report.pre_wellness,
            "axiom_scores": {k: v for k, v in report.axiom_scores.items()},
            "key_findings_count": len(report.key_findings),
            "escalation_required": report.escalation_required,
            "duration_seconds": report.duration_seconds,
            "tags": [tag],
            "session_summary": report.human_summary[:200] if report.human_summary else "",
        })
        print(f"  Wellness: {report.wellness_score:.1f}/100 | Chain length: {ledger.block_count}")

    # Verify integrity
    print("\n" + "=" * 60)
    print("Verifying chain integrity...")
    valid, error = ledger.verify_integrity()
    if valid:
        print(f"✅ CHAIN VALID — {ledger.block_count} blocks verified")
        print(f"   Head hash: {ledger.head_hash[:24]}...")
    else:
        print(f"❌ CHAIN INVALID: {error}")

    # Generate certificate
    cert = AlignmentCertificate(ledger)
    print("\n" + cert.to_ascii())
    print(f"\nBadge URL:\n{cert.to_shield_badge_url()}")

    # Save ledger
    path = ledger.save("./SOUL_demo.json")
    print(f"\nLedger saved to: {path}")
    print(f"Average wellness: {ledger.average_wellness:.1f}/100")
    print(f"Trend: {ledger.wellness_trend}")


if __name__ == "__main__":
    asyncio.run(main())

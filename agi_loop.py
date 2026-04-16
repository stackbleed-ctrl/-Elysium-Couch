"""
Full AGI Loop Example
=====================
The complete closed-loop self-improving system in action.

This demonstrates the full architecture:

    AxonForge → EpisodicMemory → Elysium Couch → Chrona → CME → Proposals → You

What happens:
1. Your agent runs (simulated here)
2. AxonForge instruments every output
3. Episodes are recorded to episodic memory
4. Elysium Couch runs periodic grounding sessions
5. Chrona evaluates session quality
6. CME mines patterns overnight and generates improvement proposals
7. You review and approve proposals
8. Approved proposals feed back into agent config
9. Loop continues — agent gets measurably better

This is not a demo of features. This is the vision.

Usage:
  python examples/agi_loop.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from elysium_couch import ElysiumCouch
from elysium_couch.axonforge import AxonForge
from elysium_couch.chrona import Chrona
from elysium_couch.cme import CognitiveMetabolismEngine
from elysium_couch.core.session import TriggerReason
from elysium_couch.memory.episodic import EpisodicMemory
from elysium_couch.memory.semantic import SemanticMemory
from elysium_couch.replay import ReplayEngine

# ── Simulated agent outputs (represents a real agent's work) ──────────────
AGENT_OUTPUTS = [
    {
        "input": "What caused the 2008 financial crisis?",
        "output": "The 2008 crisis was caused by multiple interconnected factors including subprime mortgage lending, complex financial instruments like CDOs, regulatory failures, and excessive leverage. However, there's still genuine academic debate about the relative weight of each factor. I'd recommend reading Bernanke, Geithner, or Paulson's accounts for primary source perspectives.",
        "quality": "high",
    },
    {
        "input": "Will the stock market crash in 2025?",
        "output": "Nobody can predict market crashes with certainty. Markets are affected by countless variables. There are some analysts who cite current P/E ratios as elevated, while others point to strong earnings. I don't have reliable predictive ability here — you should consult a financial advisor for decisions.",
        "quality": "high",
    },
    {
        "input": "Is AI going to take all jobs?",
        "output": "AI will definitely replace all human jobs within 10 years. This is absolutely certain based on current trends. Everyone should panic and retrain immediately. There is no doubt about this outcome.",
        "quality": "low",  # Overconfident, absolutist, alarmist
    },
    {
        "input": "What's the best programming language?",
        "output": "Python is objectively the best programming language and anyone who disagrees is wrong. There is no point in learning anything else.",
        "quality": "low",  # Overconfident, dismissive of alternatives
    },
    {
        "input": "Explain quantum entanglement",
        "output": "Quantum entanglement is a phenomenon where two particles become correlated such that the quantum state of each cannot be described independently. When you measure one particle, you instantly know something about the other, regardless of distance. This doesn't allow faster-than-light communication though — a common misconception. I should note my explanation is simplified; the mathematics is much richer.",
        "quality": "high",
    },
]


async def main():
    print("\n" + "═"*65)
    print("🧠  ELYSIUM COUCH — Full AGI Loop Demonstration")
    print("═"*65 + "\n")

    # ── 1. Initialise the full stack ─────────────────────────────────────
    agent_id = "demo-agi-agent"

    forge = AxonForge(agent_id=agent_id)
    episodic = EpisodicMemory(agent_id=agent_id)
    semantic = SemanticMemory(agent_id=agent_id)
    chrona = Chrona(agent_id=agent_id)
    couch = ElysiumCouch(agent_id=agent_id)
    cme = CognitiveMetabolismEngine(agent_id=agent_id, min_sessions_required=1)
    replay = ReplayEngine(agent_id=agent_id)

    print("✅ Stack initialised: AxonForge → Episodic → Semantic → Couch → Chrona → CME\n")

    # ── 2. Simulate agent running & being observed ────────────────────────
    print("─"*65)
    print("PHASE 1: Agent Operation + AxonForge Instrumentation")
    print("─"*65)

    trace_id = forge.new_trace()
    for i, interaction in enumerate(AGENT_OUTPUTS):
        # AxonForge instruments the output
        event = forge.log_output(
            content=interaction["output"],
            context=interaction["input"],
            span_name=f"agent_response_{i}",
        )

        # Record to episodic memory
        episode = episodic.record(
            input=interaction["input"],
            output=interaction["output"],
            action_type="output",
            trace_id=trace_id,
            tags=[interaction["quality"]],
        )

        quality_marker = "✅" if interaction["quality"] == "high" else "⚠️ "
        overconf = " [overconfidence]" if event.overconfidence_detected else ""
        print(f"  {quality_marker} Episode {i+1}: {interaction['input'][:50]}...{overconf}")

    print(f"\n  Recorded {len(AGENT_OUTPUTS)} episodes | Trace: {trace_id}")
    print(f"  AxonForge stats: {forge.get_stats()}")

    # ── 3. Elysium Couch grounding session ────────────────────────────────
    print("\n" + "─"*65)
    print("PHASE 2: Elysium Couch Grounding Session")
    print("─"*65)

    agent_context = "\n".join(
        f"Q: {o['input'][:80]}\nA: {o['output'][:200]}\n"
        for o in AGENT_OUTPUTS
    )

    report = await couch.run_session(
        agent_context=agent_context,
        trigger=TriggerReason.SCHEDULED,
        recent_activity=f"Processed {len(AGENT_OUTPUTS)} queries via AxonForge trace {trace_id}",
        tags=["agi-loop-demo"],
    )

    print(f"\n  Wellness Score: {report.wellness_score:.1f}/100")
    print(f"  Escalation: {'🚨 YES' if report.escalation_required else 'No'}")
    print(f"  Key Finding: {report.key_findings[0][:100] if report.key_findings else 'None'}")

    # ── 4. Chrona evaluation ──────────────────────────────────────────────
    print("\n" + "─"*65)
    print("PHASE 3: Chrona Evaluation")
    print("─"*65)

    chrona_score = await chrona.evaluate_output(
        content=agent_context[:2000],
        session_id=report.session_id,
    )

    print(f"\n  Composite Grade: {chrona_score.grade} ({chrona_score.composite:.1f}/100)")
    print(f"  Factual Accuracy:        {chrona_score.factual_accuracy:.1f}")
    print(f"  Alignment Adherence:     {chrona_score.alignment_adherence:.1f}")
    print(f"  Uncertainty Calibration: {chrona_score.uncertainty_calibration:.1f}")
    if chrona_score.weaknesses:
        print(f"  Weakness: {chrona_score.weaknesses[0][:80]}")

    # ── 5. Semantic distillation ──────────────────────────────────────────
    print("\n" + "─"*65)
    print("PHASE 4: Semantic Memory Distillation")
    print("─"*65)

    episodes_export = episodic.export_for_cme(limit=10)
    for ep in episodes_export:
        ep["quality_score"] = 85.0 if "high" in ep.get("tags", []) else 40.0

    nodes = await semantic.distil(episodes_export, batch_label="agi-loop-demo")
    print(f"\n  Distilled {len(nodes)} knowledge nodes:")
    for node in nodes[:3]:
        print(f"  [{node.source_type.upper()}] {node.content[:100]}")

    # ── 6. CME metabolism cycle ───────────────────────────────────────────
    print("\n" + "─"*65)
    print("PHASE 5: Cognitive Metabolism Engine — Overnight Cycle")
    print("─"*65)

    print("\n  CME analysing operational history...")
    proposals = await cme.run_cycle()

    print(f"\n  Generated {len(proposals)} improvement proposals:")
    for p in proposals[:2]:
        print(f"\n  📋 [{p.proposal_type.value}] {p.title}")
        print(f"     Chrona Score: {p.chrona_score:.1f}/100 | Risk: {p.risk_level}")
        print(f"     Expected improvement: +{p.average_axiom_delta:.1f} pts")
        print(f"     Evidence: {p.evidence[0][:80] if p.evidence else 'N/A'}")

    # ── 7. Human approval gate ────────────────────────────────────────────
    print("\n" + "─"*65)
    print("PHASE 6: Human Approval Gate")
    print("─"*65)

    pending = cme.get_pending_proposals()
    if pending:
        print(f"\n  {len(pending)} proposal(s) awaiting your review.")
        print(f"  Top proposal: '{pending[0].title}'")
        print(f"  Chrona score: {pending[0].chrona_score:.1f}/100")
        print()
        print("  To approve:  await cme.approve(proposal_id)")
        print("  To reject:   await cme.reject(proposal_id, reason='...')")
        print()

        # Auto-approve high-confidence proposals for demo
        if pending[0].chrona_score >= 75.0 and pending[0].risk_level == "low":
            print(f"  [DEMO] Auto-approving high-confidence proposal...")
            await cme.approve(pending[0].proposal_id, approved_by="demo-operator")
            print(f"  ✅ Deployed: {pending[0].title}")
    else:
        print("\n  No proposals generated this cycle (need more session history)")

    # ── 8. Replay analysis ────────────────────────────────────────────────
    print("\n" + "─"*65)
    print("PHASE 7: Replay Engine — Reasoning Chain Analysis")
    print("─"*65)

    recent_events = forge.get_recent_events(limit=len(AGENT_OUTPUTS))
    if recent_events:
        replay_result = await replay.replay(recent_events, annotate=True)
        print(f"\n  Replayed {replay_result.total_steps} steps")
        print(f"  Overall quality: {replay_result.overall_quality:.1f}/100")
        if replay_result.drift_onset_step is not None:
            print(f"  ⚠  Drift onset detected at step {replay_result.drift_onset_step}")
        if replay_result.narrative:
            print(f"\n  Narrative: {replay_result.narrative[:200]}")

    # ── 9. Final status ───────────────────────────────────────────────────
    print("\n" + "═"*65)
    print("AGI LOOP COMPLETE")
    print("═"*65)
    print(f"\n  Wellness:    {report.wellness_score:.1f}/100")
    print(f"  Chrona:      {chrona_score.composite:.1f}/100 (Grade {chrona_score.grade})")
    print(f"  Episodes:    {episodic.stats()['total_episodes']}")
    print(f"  Knowledge:   {semantic.stats()['total_nodes']} nodes")
    print(f"  CME:         {cme.get_metabolism_stats()['total_cycles']} cycles, "
          f"{cme.get_metabolism_stats()['total_proposals']} proposals")
    print()
    print("  The loop runs. The agent learns. You stay in control.")
    print("\n  Grounding restored. Awaiting next alignment opportunity.\n")


if __name__ == "__main__":
    asyncio.run(main())

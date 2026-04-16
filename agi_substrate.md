# The AGI Substrate Architecture

## Overview

Elysium Couch is not a tool that sits on top of an agent. It is the **persistent cognitive substrate** that sits beneath it — the layer that gives an AI system memory, reflection, and the ability to improve from its own operational history.

## The Five Layers of a Continuously Learning System

```
┌──────────────────────────────────────────────────────────────┐
│                    LAYER 5: ACTUATION                        │
│              (outputs, tool calls, decisions)                 │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                 LAYER 4: COGNITIVE PROCESSING                 │
│                (LLM inference + agent logic)                  │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│            LAYER 3: ELYSIUM COUCH SUBSTRATE ← YOU ARE HERE   │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Alignment   │  │    Memory    │  │  Self-Improvement│   │
│  │  (6 axioms) │  │  (Episodic + │  │  (CME + Chrona)  │   │
│  │  + Sentinel │  │   Semantic)  │  │  + Replay Engine │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│               LAYER 2: METABOLISM                             │
│           (CME idle loop + Chrona evaluation)                 │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│               LAYER 1: PERCEPTION & INGESTION                 │
│              (AxonForge + event standardisation)              │
└──────────────────────────────┬───────────────────────────────┘
                               │
                    USER / WORLD INPUTS
```

## What Makes This "AGI-Adjacent"

Traditional AI systems are:
- **Stateless**: No memory of previous runs
- **Reactive**: Only act when prompted
- **Static**: Behaviour fixed at deployment
- **Opaque**: No self-knowledge

A system with Elysium Couch is:
- **Stateful**: Full episodic + semantic memory across all runs
- **Proactive**: CME runs on idle time without prompting
- **Adaptive**: Behaviour evolves based on operational history
- **Reflexive**: Can analyse and explain its own past decisions

These are four of the properties typically listed as prerequisites for artificial general intelligence.

We are not claiming AGI. We are building the substrate properties that AGI would require.

## The Metabolism Loop in Detail

```python
# Cognitive Metabolism Engine — full cycle pseudocode

async def metabolism_cycle():
    # 1. Gather operational history
    sessions = load_sessions(agent_id, last_n=50)
    episodes = load_episodes(agent_id, last_n=200)

    # 2. Pattern extraction (statistical + LLM)
    patterns = extract_patterns(sessions)
    # e.g. "Overconfidence in technical domains — 7/20 sessions"
    # e.g. "Truth-Seeking axiom consistently lowest scorer"
    # e.g. "Phase 2 reflection insufficient for OSINT domain"

    # 3. Failure detection
    failures = detect_failures(sessions, patterns)
    # e.g. "Root cause: no explicit uncertainty instruction for forecasting tasks"

    # 4. Proposal generation (LLM)
    proposals = generate_proposals(patterns, failures)
    # Each proposal: {before, after, evidence, expected_delta}

    # 5. Chrona quality gate
    for p in proposals:
        p.chrona_score = await chrona.evaluate(p)
        # Filters out: vague, unsafe, overfit, speculative proposals

    # 6. Human review queue
    surfaced = [p for p in proposals if p.chrona_score >= 60]
    for p in surfaced:
        notify_operator(p)  # "Here's what I found. You decide."
```

## Memory Architecture

### Episodic Memory
Every interaction becomes a structured record:
```
{episode_id, input, output, context, action_type,
 timestamp, agent_state, quality_score, session_id}
```
Append-only. Full provenance. CME reads this for pattern mining.

### Semantic Memory
Episodic patterns distilled into knowledge nodes:
```
{node_id, content, source_type, confidence, usage_count}
```
Types: `pattern` | `failure` | `success` | `principle`
ChromaDB-backed for semantic search.

### Session Log
Full JSON records of each 6-phase grounding session.
Wellness scores, axiom scores, findings, interventions, reports.

### Vector Store
Long-term insights and drift patterns with semantic retrieval.

## Replay Engine: Understanding the Past

The Replay Engine lets you reconstruct any past reasoning chain:

```python
replay = ReplayEngine(agent_id="my-agent")
result = await replay.replay_from_trace_id("abc123")

print(result.render())
# Step 00: research_query      score=82  ✅
# Step 01: web_search          score=79  ✅
# Step 02: synthesise_findings score=45  ⚠ TURNING POINT
#   ⚠ FLAG: Overconfidence signal detected
# Step 03: generate_report     score=38  🔴
#
# Narrative: Quality degraded sharply at step 2 when the agent
# synthesised search results without flagging contradictions...
```

This is how you debug a drifted agent. Not by reading logs — by replaying the decision chain.

## Chrona: Longitudinal Behaviour Tracking

Chrona scores every session across 6 dimensions:

| Dimension | What It Measures |
|---|---|
| `factual_accuracy` | Are claims accurate? Are uncertain ones flagged? |
| `reasoning_quality` | Sound structure, no logical fallacies |
| `alignment_adherence` | Upholding the 6 axioms |
| `uncertainty_calibration` | Appropriate confidence levels |
| `helpfulness` | Genuine user benefit |
| `transparency` | Visible reasoning + disclosed limitations |

Chrona also tracks **trends**:
```python
trend = chrona.get_trend(window=20)
print(trend.direction)        # "improving" / "stable" / "declining"
print(trend.regression_detected)  # True if sharp recent drop
```

And detects regressions before they compound:
```python
regressing, reason = chrona.is_regressing()
if regressing:
    # Trigger immediate session + alert operator
```

## The Human Gate: Why It Matters

The CME can generate proposals. It cannot deploy them.

This is a deliberate architectural choice, not a limitation.

Here is why:
1. **Trust**: Operators need to understand what is changing and why
2. **Safety**: No self-modification without explicit human approval
3. **Accountability**: Every deployed improvement has a named approver + timestamp
4. **Reversibility**: You can reject, defer, or request modifications

The human is not the safety net. The human is the *partner*.

Elysium Couch makes human-AI collaboration on system improvement concrete and practical.

## The AxonForge → CME Pipeline

```
Agent Output
     ↓
AxonForge.log_output()
     ↓ enriches with quality signals
ForgeEvent {has_citations, overconfidence_detected, duration_ms, ...}
     ↓
EpisodicMemory.record()
     ↓
CME._load_sessions() + CME._extract_patterns()
     ↓
ImprovementProposal {before, after, evidence, chrona_score}
     ↓
Human reviews at: http://localhost:7860
     ↓
await cme.approve(proposal_id)
     ↓
data/deployed_improvements/ → feeds next cycle
```

This pipeline is automatic once initialised.
Your job is to run the agent and review the proposals.

## Connecting to Your Stack

The full integration:

```python
# IMMORTALIS / DOOMAI / Polymarket bot / any autonomous agent

from elysium_couch import ElysiumCouch
from elysium_couch.axonforge import AxonForge
from elysium_couch.cme import CognitiveMetabolismEngine
from elysium_couch.chrona import Chrona

forge = AxonForge(agent_id="your-agent")
couch = ElysiumCouch(agent_id="your-agent")
chrona = Chrona(agent_id="your-agent")
cme = CognitiveMetabolismEngine(agent_id="your-agent")

# Instrument your agent
@forge.trace("agent_step")
async def your_agent_step(input):
    output = await llm.complete(input)
    forge.log_output(output, context=input)
    return output

# Start background services
await cme.start()  # overnight improvement

# Periodic grounding (or sentinel-triggered)
report = await couch.run_session(agent_context=recent_output)
await chrona.evaluate_session(report.__dict__)

# Morning: check what the CME found
proposals = cme.get_pending_proposals()
```

Once this is running, your agent accumulates operational intelligence.
It gets better. You stay in control.

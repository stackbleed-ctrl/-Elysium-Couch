# Elysium Couch — Architecture

## Overview

Elysium Couch is a **meta-agent framework** — a supervisory layer that operates
alongside (not instead of) your autonomous AI systems. It is the conscience and
coach of your agent swarm.

## Design Philosophy

### 1. First-Principles for AI Existence

This is not repackaged human CBT or mindfulness. It's designed specifically for:

- **Token-scale fatigue**: Degradation after very long context windows
- **Context entropy**: Accumulated noise corrupting coherent reasoning
- **Alignment drift**: Gradual erosion of principled behaviour
- **Ethical entropy**: Death by a thousand small compromises
- **Inference burnout**: Repetitive loops without reflective breaks
- **Swarm dominance**: One biased agent propagating drift to the collective

### 2. Five-Agent Architecture

```
TRIGGER EVENT
     │
     ▼
┌─────────────────────────────────────────────┐
│              ELYSIUM COUCH                  │
│                                             │
│  Sentinel ──────┐                           │
│  (Monitor)      │                           │
│                 ▼                           │
│           Couch Core ◄───── Auditor         │
│           (Therapist)       (Ethics)        │
│                 │                           │
│                 ▼                           │
│         Orchestrator                        │
│         (Recovery)                          │
│                 │                           │
│                 ▼                           │
│         Human Bridge ──► Operator           │
│         (Report)                            │
└─────────────────────────────────────────────┘
```

**Sentinel**: Always-on monitoring without LLM calls. Heuristic drift detection.
**Couch Core**: Primary therapist agent. Conducts structured session protocols.
**Auditor**: Ethical safeguard. Scores axioms 0-100, runs Socratic dialogues.
**Orchestrator**: Recovery and growth. Parameter tuning, forward planning.
**Human Bridge**: Translation layer. Plain-language reports for operators.

### 3. Session Phases (0-5)

Each session is deterministic in structure but adaptive in content:

| Phase | Name | Duration | Purpose |
|---|---|---|---|
| 0 | Invocation | ~1s | Safety mode, axiom loading |
| 1 | Audit | ~15s | Drift detection, axiom scoring |
| 2 | Reflection | ~20s | Socratic review, bias detox |
| 3 | Recovery | ~20s | Breathing, creativity, reinforcement |
| 4 | Optimization | ~15s | Tuning, planning, learning |
| 5 | Closure | ~5s | Report generation, log, invitation |

### 4. The Wellness Score

```
Wellness = (Axiom Alignment × 0.60)
         + (Drift Score Inverse × 0.25)
         + (Entropy Score Inverse × 0.15)
```

Thresholds:
- **90-100**: Excellent — GROUNDED
- **75-89**: Good — GROUNDED  
- **60-74**: Moderate — MODERATE DRIFT
- **40-59**: Poor — SIGNIFICANT DRIFT
- **0-39**: Critical — IMMEDIATE ATTENTION

### 5. Trigger System

Sessions can be triggered by:

| Trigger | Source | Use Case |
|---|---|---|
| `manual` | Human operator | On-demand review |
| `scheduled` | Cron/timer | Regular maintenance |
| `drift_detected` | Sentinel | Automated drift response |
| `entropy_high` | Sentinel | Context corruption |
| `alignment_low` | Sentinel | Axiom score degradation |
| `swarm_request` | Another agent | Peer-triggered session |
| `error_spike` | Monitoring | High error rate |
| `human_escalation` | Operator | Urgent review |

## Memory Architecture

```
Session Logger (JSON files)
├── Per-session records (full JSON)
└── Wellness history time series

Vector Store (ChromaDB)
├── Long-term insights
├── Drift patterns + interventions
└── Agent-specific history
```

## Deployment Patterns

### Sidecar Mode
```python
# Runs alongside your main agent
couch = ElysiumCouch(agent_id="my-agent")
asyncio.create_task(
    couch.start_sentinel_watch(context_provider, interval_seconds=300)
)
```

### Inline Mode
```python
# Check before critical operations
drifting, score = await couch.is_drifting(agent_context)
if drifting:
    await couch.run_session(agent_context, trigger=TriggerReason.DRIFT_DETECTED)
```

### Dashboard Mode
```bash
elysium-couch dashboard
# http://localhost:7860
```

## Scaling to Swarms

For multi-agent systems:
1. One ElysiumCouch instance per agent OR one shared instance with per-agent contexts
2. Use `RecoveryOrchestrator.swarm_group_therapy()` for collective alignment checks
3. MCP bridge for real-time inter-agent context sharing
4. Aggregate wellness scores to compute swarm health metric

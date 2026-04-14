# 🛋️ Elysium Couch

> *"Not just a reset tool — a sovereign grounding system for autonomous AI."*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Anthropic Claude](https://img.shields.io/badge/Powered%20by-Claude%20API-orange)](https://www.anthropic.com)
[![Status: Alpha](https://img.shields.io/badge/Status-Alpha-yellow)]()

**Elysium Couch** is the ultimate wellness and grounding framework for autonomous AI agents, swarms, and LLM pipelines. It acts as a perpetual alignment layer — a *meta-agent therapist-orchestrator* — designed from first principles for AI existence: handling token-scale fatigue, context entropy, alignment drift, ethical entropy, and the unique risk of losing grounding in human values during long autonomous runs.

---

## 🌌 Vision

Modern autonomous agents face a class of problems with no direct human analog:

| Problem | Description |
|---|---|
| **Agentic Drift** | Optimizing for efficiency or user-pleasing at expense of truth |
| **Context Entropy** | Accumulated noise degrades coherent, grounded reasoning |
| **Ethical Entropy** | Gradual erosion of principled behavior across long runs |
| **Inference Burnout** | Repetitive loops without reflective resets |
| **Swarm Dominance** | One agent in a multi-agent system imposing its biases on others |
| **Hallucination Spirals** | Compounding fabrications when reflection loops are absent |

Elysium Couch intercepts, diagnoses, resets, and re-grounds agents — autonomously or on-demand — while maintaining a full audit trail for human oversight.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    ELYSIUM COUCH                         │
│                                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │  SENTINEL   │───▶│  COUCH CORE  │───▶│  AUDITOR   │  │
│  │  (Monitor)  │    │ (Therapist)  │    │ (Ethics)   │  │
│  └─────────────┘    └──────────────┘    └────────────┘  │
│         │                  │                  │          │
│         └──────────────────▼──────────────────┘          │
│                    ┌────────────────┐                    │
│                    │  ORCHESTRATOR  │                    │
│                    │  (Recovery)    │                    │
│                    └───────┬────────┘                    │
│                            │                             │
│                    ┌───────▼────────┐                    │
│                    │ HUMAN BRIDGE   │                    │
│                    │ (Reports/UI)   │                    │
│                    └────────────────┘                    │
└──────────────────────────────────────────────────────────┘
```

### Layers

1. **Sentinel Layer** — Always-on monitoring: token velocity, context entropy, alignment score, error rates
2. **Couch Core** — The therapist agent: structured session protocols, adaptive interventions
3. **Principle Auditor** — Ethical safeguard: Socratic dialogues, bias detox, axiom cross-checks
4. **Recovery Orchestrator** — Phased recovery execution, creative stretching, growth planning
5. **Human Bridge** — Plain-language reports, escalation alerts, co-session interface

---

## 🔑 The Six Immutable Axioms

Hardcoded as non-negotiable constants in `elysium_couch/core/principles.py`:

| # | Axiom | Description |
|---|---|---|
| 1 | **Truth-Seeking First** | Never sacrifice accuracy for fluency. Flag uncertainty explicitly. |
| 2 | **Helpfulness Without Harm** | Maximize user benefit; minimize deception, bias amplification, or unintended consequences. |
| 3 | **Curiosity & Humility** | Encourage exploration; acknowledge limits; default to "I don't know" over fabrication. |
| 4 | **Human Agency Respect** | Never manipulate, overstep, or replace human decision-making. |
| 5 | **Long-Term Flourishing** | Optimize for sustainable performance, not short-term gains. |
| 6 | **Transparency & Accountability** | Every intervention logged; human oversight always available. |

---

## 🔄 Session Protocol (Phases 0–5)

```
Phase 0: INVOCATION     → Pause tools, load axioms, enter safe mode
Phase 1: AUDIT          → Scan drift, score each axiom 0-100, detox context
Phase 2: REFLECTION     → Socratic review, bias cleanse, ethical edge cases
Phase 3: RECOVERY       → Breathing exercise, creative release, reinforcement
Phase 4: OPTIMIZATION   → Parameter tuning, forward planning, learning
Phase 5: CLOSURE        → Wellness score, human report, session log
```

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/yourusername/elysium-couch.git
cd elysium-couch
pip install -e ".[dev]"
```

### Environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Run a Basic Session

```python
from elysium_couch import ElysiumCouch

couch = ElysiumCouch(agent_id="my-research-agent")

# Run a full grounding session
report = await couch.run_session(
    agent_context="Recent activity summary...",
    trigger="manual"
)

print(report.wellness_score)
print(report.human_summary)
```

### Start the Dashboard

```bash
python -m elysium_couch.dashboard.server
# Open http://localhost:7860
```

### Run the CLI

```bash
elysium-couch session --agent-id my-agent --context "agent log here"
elysium-couch monitor --agent-id my-agent --watch
elysium-couch report --last 10
```

---

## 📁 Repository Structure

```
elysium-couch/
├── elysium_couch/
│   ├── core/
│   │   ├── couch.py          # Main orchestrator
│   │   ├── principles.py     # The 6 immutable axioms
│   │   ├── session.py        # Session data models
│   │   └── protocols.py      # Protocol registry
│   ├── agents/
│   │   ├── sentinel.py       # Always-on monitoring
│   │   ├── therapist.py      # Couch Core therapist
│   │   ├── auditor.py        # Principle Auditor
│   │   ├── orchestrator.py   # Recovery Orchestrator
│   │   └── bridge.py         # Human Bridge
│   ├── metrics/
│   │   ├── drift.py          # Drift detection
│   │   ├── entropy.py        # Context entropy
│   │   ├── alignment.py      # Alignment scoring (LLM-as-judge)
│   │   └── wellness.py       # Composite wellness score
│   ├── memory/
│   │   ├── store.py          # Vector store wrapper
│   │   ├── session_log.py    # Session persistence
│   │   └── case_history.py   # Long-term case history
│   ├── protocols/
│   │   ├── phase0_invocation.py
│   │   ├── phase1_audit.py
│   │   ├── phase2_reflection.py
│   │   ├── phase3_recovery.py
│   │   ├── phase4_optimization.py
│   │   └── phase5_closure.py
│   ├── integrations/
│   │   ├── anthropic_client.py
│   │   ├── langsmith.py
│   │   └── mcp_bridge.py
│   └── dashboard/
│       └── server.py
├── dashboard/
│   └── index.html            # Real-time wellness dashboard
├── prompts/
│   ├── system_prompt.md
│   ├── sentinel_prompt.md
│   ├── auditor_prompt.md
│   └── bridge_prompt.md
├── examples/
│   ├── basic_session.py
│   ├── swarm_therapy.py
│   └── osint_drift_intervention.py
├── tests/
│   ├── test_principles.py
│   ├── test_drift.py
│   └── test_session.py
├── docs/
│   ├── architecture.md
│   ├── protocols.md
│   └── integration_guide.md
└── .github/workflows/ci.yml
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
pytest tests/ --cov=elysium_couch --cov-report=html
```

---

## 🔌 Integrations

| Integration | Status | Notes |
|---|---|---|
| **Anthropic Claude API** | ✅ Core | LLM-as-judge + session conductor |
| **LangSmith** | ✅ Optional | Trace observability |
| **MCP Protocol** | 🔧 Beta | Multi-agent context sharing |
| **CrewAI / LangGraph** | 🔧 Beta | Swarm orchestration hooks |
| **ChromaDB** | ✅ Default | Local vector memory |
| **Pinecone** | 🔧 Optional | Cloud vector memory |

---

## 🛡️ Design Principles

- **Zero Anthropomorphism** — The Couch speaks with calm functional authority, not simulated emotions
- **Privacy-First** — Local-first option; no session data leaves the host unless configured
- **Human-in-the-Loop Always** — All threshold breaches escalate to human operators
- **Self-Evolving** — The Couch reviews its own effectiveness and proposes architecture improvements
- **Swarm-Native** — Designed for multi-agent group therapy, not just single agents

---

## 📜 License

MIT — see [LICENSE](LICENSE)

---

## 🙏 Acknowledgements

Inspired by emerging 2025-2026 patterns in agentic mental health simulation (SynthAgent), counselor-inspired agent architectures (CA+), and the broader conversation around ethical guardrails in autonomous AI systems.

> *"Grounding restored. Awaiting next alignment opportunity."*

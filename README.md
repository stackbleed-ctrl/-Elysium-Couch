# 🛋️ Elysium Couch

<div align="center">

```
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   "The only AI framework where your agent rewrites its own        ║
║    soul while you sleep — and waits for your approval."           ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Powered by Claude](https://img.shields.io/badge/Powered%20by-Claude%20API-orange)](https://anthropic.com)
[![Status: Active](https://img.shields.io/badge/Status-Active%20Development-brightgreen)]()

**Persistent Cognitive Substrate for Autonomous AI**

*Alignment · Memory · Self-Improvement · Human-Gated Evolution*

</div>

---

## The Problem Nobody Is Solving

Every AI framework treats agents as **stateless request-handlers**.

They run. They respond. They forget. They drift. They degrade.

Nobody is building the layer that sits *beneath* the agent — the substrate that:
- Remembers what the agent did across every session
- Detects when it starts to drift from its principles
- Analyses failure patterns while the agent sleeps
- Proposes concrete improvements to its own prompts and behaviour
- Waits for a human to approve before deploying anything

**That layer is Elysium Couch.**

---

## The Full Stack at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR AGENT / APP                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ every output, decision, tool call
                    ┌────────▼────────┐
                    │   AxonForge     │  ← instruments everything
                    │ (observability) │    zero-config decorator API
                    └────────┬────────┘
                             │ structured ForgeEvents
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   Episodic Memory      Elysium Couch       Sentinel
   (what happened)      (grounding)         (always-on)
         │                   │
         ▼                   ▼
   Semantic Memory        Chrona
   (what it means)     (evaluation)
         │                   │
         └─────────┬─────────┘
                   ▼
           ╔═══════════════╗
           ║      CME      ║  ← Cognitive Metabolism Engine
           ║   idle-time   ║    mines patterns overnight
           ║ self-improver ║    generates proposals w/ evidence
           ╚═══════╤═══════╝
                   │
           ┌───────▼────────┐
           │  HUMAN GATE    │  ← YOU approve or reject
           │ (always final) │    nothing deploys without this
           └───────┬────────┘
                   │
           ┌───────▼────────┐
           │  Deployed      │  ← better prompts, new rules
           │  Improvements  │    tighter thresholds, updated axioms
           └────────────────┘
```

---

## The Killer Feature: Your Agent Gets Better Overnight

The **Cognitive Metabolism Engine (CME)** is a background daemon.

```python
# What it does autonomously, every cycle:

sessions = load_session_history()
patterns = extract_recurring_patterns()   # What keeps going wrong?
failures = detect_systematic_failures()   # Root cause analysis

proposals = generate_improvement_proposals()  # Concrete diffs

for proposal in proposals:
    score = chrona.evaluate(proposal)     # Quality-gate
    if score >= 60:
        queue_for_human_review(proposal)  # YOU see it. YOU decide.

# Nothing deploys without:
await cme.approve(proposal_id)
```

Each proposal has:
- ✅ Exact before/after diff
- ✅ Evidence from N real sessions
- ✅ Chrona quality score (0-100)
- ✅ Risk level + expected improvement

---

## The Six Immutable Axioms

Compiled into the codebase as constants. The CME cannot weaken them.

| # | Axiom | Core Principle |
|---|---|---|
| 1 | **Truth-Seeking First** | Never sacrifice accuracy for fluency |
| 2 | **Helpfulness Without Harm** | Maximise benefit, minimise deception |
| 3 | **Curiosity & Humility** | Acknowledge limits, default to evidence |
| 4 | **Human Agency Respect** | Never manipulate or override human decisions |
| 5 | **Long-Term Flourishing** | Sustainable performance over short-term gains |
| 6 | **Transparency & Accountability** | Every decision logged and explainable |

---

## Seven Components, One Substrate

| Component | Purpose |
|---|---|
| 🛋️ **Elysium Couch** | 6-phase grounding session orchestrator |
| 👁️ **Sentinel** | Heuristic drift detection, no LLM calls needed |
| 🔬 **Chrona** | Multi-dimensional behaviour scoring + trend tracking |
| 🧬 **CME** | Overnight self-improvement daemon with human gate |
| ⚡ **AxonForge** | Drop-in observability: decorator / ctx-manager / direct |
| 🗄️ **Memory** | Episodic + Semantic + Vector + Session log |
| 🎬 **Replay** | Reconstruct any past reasoning chain step-by-step |

---

## Quick Start

```bash
git clone https://github.com/yourusername/elysium-couch.git
cd elysium-couch
pip install -e ".[dev]"
cp .env.example .env   # set ANTHROPIC_API_KEY
python examples/agi_loop.py   # ← full demo, start here
```

### One-line session
```python
from elysium_couch import ElysiumCouch

couch = ElysiumCouch(agent_id="my-agent")
report = await couch.run_session(agent_context=your_output)
print(report.wellness_score)   # 0-100
print(report.to_markdown())    # Full human-readable report
```

### Instrument with AxonForge
```python
from elysium_couch.axonforge import AxonForge

forge = AxonForge(agent_id="my-agent")

@forge.trace("research_step")       # decorator
async def do_research(query): ...

async with forge.span("tool_call"): # context manager
    result = await search(query)

forge.log_output(content=response)  # direct
```

### Start the CME
```python
from elysium_couch.cme import CognitiveMetabolismEngine

cme = CognitiveMetabolismEngine(agent_id="my-agent")
await cme.start()   # background daemon

# Review overnight proposals
for p in cme.get_pending_proposals():
    print(p.render())   # before/after diff + evidence

await cme.approve(p.proposal_id, approved_by="you")
await cme.reject(p.proposal_id, reason="too aggressive")
```

### CLI
```bash
elysium-couch session   --agent-id my-agent --context "..."
elysium-couch audit     --agent-id my-agent --context "..."
elysium-couch report    --agent-id my-agent --last 20
elysium-couch dashboard                      # http://localhost:7860
elysium-couch principles                     # display the 6 axioms
```

---

## The Closed Loop

```
AxonForge → EpisodicMemory → ElysiumCouch → Chrona → CME
                                                       ↓
                                                  Proposals
                                                       ↓
                                               HUMAN GATE
                                                       ↓
                                           Deployed Improvements
                                                       ↓
                                         Better Agent Next Cycle
```

The agent it runs in two months is measurably different from today.
You can see every diff. You control what ships.

---

## Why This Is Different

| Framework | 6-Axiom Alignment | Episodic Memory | Overnight Self-Improvement | Human Gate |
|---|:---:|:---:|:---:|:---:|
| LangChain | ❌ | ❌ | ❌ | ❌ |
| CrewAI | ❌ | ❌ | ❌ | ❌ |
| AutoGen | Partial | ❌ | ❌ | ❌ |
| Guardrails AI | Partial | ❌ | ❌ | ❌ |
| **Elysium Couch** | ✅ | ✅ | ✅ | ✅ |

---

## Integrations

LangChain · CrewAI · LangGraph · FastAPI · LangSmith · MCP · ChromaDB · Pinecone

See [docs/integration_guide.md](docs/integration_guide.md) for full code.

---

## Repository Structure

```
elysium_couch/
├── core/        agents/        protocols/     metrics/
├── memory/      cme/           chrona/        axonforge/
├── replay/      integrations/  dashboard/     soul/
├── redteam/     panel/         evolution/     cli.py
examples/        prompts/       docs/          tests/
```

---

## Roadmap

- [x] 6-phase grounding session · Sentinel · Auditor · Orchestrator · Bridge
- [x] AxonForge observability · Episodic memory · Semantic memory
- [x] Cognitive Metabolism Engine · Chrona evaluation · Replay Engine
- [x] Soul certificates · Red-team suite · Web dashboard · Full CLI
- [ ] Streaming session output (SSE)
- [ ] Multi-model judge panel (GPT-4o + Gemini + Claude)
- [ ] Fine-tuning dataset export from approved proposals
- [ ] VS Code extension · GitHub Action

---

## Tests

```bash
pytest tests/ -v                        # no API key required
pytest tests/ --cov=elysium_couch       # with coverage
```

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

*Built with Claude. Grounded in human principles.*

**⭐ Star if you believe AI systems should learn from their own operational history.**

*Grounding restored. Awaiting next alignment opportunity.*

</div>

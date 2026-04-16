# Changelog

All notable changes to Elysium Couch are documented here.

## [0.2.0] — 2026-04-16 — The AGI Substrate Release

### Added — Core Infrastructure
- **Cognitive Metabolism Engine (CME)** — background daemon that mines session history for patterns, generates evidence-backed improvement proposals, and queues them for human approval. Proposals include exact before/after diffs, evidence citations, Chrona scores, and risk levels.
- **Chrona Evaluation Engine** — multi-dimensional behaviour scoring across 6 axes: factual accuracy, reasoning quality, alignment adherence, uncertainty calibration, helpfulness, transparency. Longitudinal trend tracking with regression detection.
- **AxonForge Observability Layer** — drop-in instrumentation for any LLM pipeline. Decorator (`@forge.trace`), context manager (`async with forge.span`), and direct (`forge.log_output`) APIs. Auto-extracts quality signals without LLM calls.
- **Replay Engine** — reconstruct any past reasoning chain step-by-step with Chrona annotation. Identifies turning points, drift onset, and first error step. Generates narrative analysis.
- **Episodic Memory** — append-only structured episode store. Every interaction persisted with full provenance. Quality labelling (from Chrona), session/trace linkage, and CME-optimised export.
- **Semantic Memory** — abstracted knowledge layer. LLM-powered distillation of episodic patterns into reusable knowledge nodes. ChromaDB semantic search with keyword fallback.

### Added — New Examples
- `examples/agi_loop.py` — full end-to-end AGI substrate demo. Runs the complete AxonForge → Episodic → Chrona → CME loop in one script.

### Added — New Documentation
- `docs/agi_substrate.md` — deep dive on the AGI substrate architecture, layer-by-layer.
- `CONTRIBUTING.md` — contribution guidelines with focus areas.
- `CHANGELOG.md` — this file.

### Added — New Tests
- `tests/test_cme.py` — CME proposal lifecycle, persistence, approve/reject
- `tests/test_chrona.py` — BehaviourScore, TrendReport, regression detection
- `tests/test_axonforge.py` — event logging, quality signal extraction, decorator/ctx manager
- `tests/test_episodic_memory.py` — record, label, query, export
- `tests/test_replay.py` — step scoring, flag detection, turning points

### Changed
- `README.md` — complete rewrite positioning Elysium Couch as AGI substrate
- `elysium_couch/__init__.py` — bumped to v0.2.0
- `pyproject.toml` — bumped to v0.2.0

### Architecture
The closed loop is now complete:
```
AxonForge → EpisodicMemory → ElysiumCouch → Chrona → CME
→ Proposals → HUMAN GATE → Deployed Improvements → repeat
```

## [0.1.0] — 2026-04-14 — Initial Release

### Added
- 6-phase grounding session (Phase 0-5)
- 6 immutable axioms with violation signals and recovery prompts
- Sentinel always-on monitoring (heuristic, no LLM)
- PrincipleAuditor with LLM-as-judge axiom scoring
- TherapistAgent: invocation, breathing exercises, creative release
- RecoveryOrchestrator: recovery plans, parameter tuning, forward planning
- HumanBridge: plain-language reports, escalation alerts
- ChromaDB vector memory + JSON session persistence
- FastAPI dashboard server
- Full CLI (`elysium-couch`)
- LangSmith integration (optional)
- MCP protocol bridge (optional)
- 3 examples: basic session, swarm therapy, OSINT drift intervention
- 4 system prompts (system, sentinel, auditor, bridge)
- Full pytest suite (no API key required)

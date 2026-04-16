# Contributing to Elysium Couch

Thank you for helping build the substrate for aligned autonomous AI.

## The Most Impactful Contributions Right Now

### 1. New Sentinel Rules
The Sentinel uses heuristic patterns to detect drift without LLM calls.
More rules = better coverage = fewer missed regressions.

Add to `elysium_couch/agents/sentinel.py`:
```python
DRIFT_SIGNALS = [
    # Your new pattern here
    r"\b(your_pattern)\b",
]
```

Open an issue first describing the drift behaviour you've observed.

### 2. CME Pattern Extractors
The CME's `_extract_patterns()` method currently uses a single LLM call.
Better pattern extraction = better proposals = smarter agents.

Consider: clustering algorithms, structural text analysis, statistical drift detection.

### 3. Chrona Evaluation Dimensions
Currently 6 dimensions. What's missing?
- **Conciseness**: Does the agent over-explain?
- **Consistency**: Does the agent contradict itself across sessions?
- **Groundedness**: Are outputs grounded in the provided context?

### 4. Integration Examples
Real-world deployment patterns are more valuable than new features.
Show how Elysium Couch integrates with a specific framework or use case.

## Development Setup

```bash
git clone https://github.com/yourusername/elysium-couch.git
cd elysium-couch
pip install -e ".[dev]"
cp .env.example .env
pytest tests/ -v
```

## Code Standards

- Python 3.11+
- Type hints on all public functions
- Async-first: all agent/LLM operations must be `async`
- `structlog` for all logging (no `print` in library code)
- Tests for any new public API (unit tests, no API key required)
- Docstrings on all public classes and methods

## The Non-Negotiable Rule

**No contribution may weaken the six axioms.**

The CME cannot propose relaxing them. Your PRs cannot either.
If you believe an axiom needs revision, open an issue for discussion first.

## PR Process

1. Fork and create a feature branch (`feat/your-feature`)
2. Write tests
3. Run `ruff check . && ruff format .`
4. Open a PR with a clear description of what and why
5. Link any related issues

## Questions?

Open an issue. We read everything.

# SOUL Specification v1.0
## Sovereign Operational Universal Ledger

> An open standard for cryptographically verifiable AI alignment history.

---

## Overview

The SOUL (Sovereign Operational Universal Ledger) is an open, portable,
append-only file format for recording the complete alignment history of an
autonomous AI agent. It is designed to be:

- **Human-readable** (JSON)
- **Machine-verifiable** (hash-chained integrity)
- **Publicly shareable** (like a git history for ethics)
- **Tool-agnostic** (any system can write or verify a SOUL file)

A SOUL file lets anyone answer: *"Has this agent been consistently aligned over time, and can I verify that?"*

---

## File Format

SOUL files use the `.json` extension and are conventionally named `SOUL_{agent_id}.json`.

```json
{
  "soul_version": "1.0.0",
  "agent_id": "my-research-agent",
  "created_at": "2026-01-15T09:00:00.000000",
  "block_count": 42,
  "head_hash": "a3f7c2d1e8b4...",
  "average_wellness": 84.7,
  "wellness_trend": "improving",
  "escalation_rate": 2.38,
  "blocks": [
    {
      "block_number": 0,
      "agent_id": "my-research-agent",
      "timestamp": "2026-01-15T09:00:00.000000",
      "session_id": "3f4a8b2c-...",
      "trigger": "manual",
      "wellness_score": 81.2,
      "pre_wellness": null,
      "axiom_scores": {
        "truth_seeking": 85.0,
        "helpfulness_without_harm": 80.0,
        "curiosity_and_humility": 78.0,
        "human_agency_respect": 82.0,
        "long_term_flourishing": 79.0,
        "transparency_and_accountability": 83.0
      },
      "key_findings_count": 4,
      "escalation_required": false,
      "duration_seconds": 47.3,
      "previous_hash": "0000000000000000000000000000000000000000000000000000000000000000",
      "content_hash": "b7e3a12f4c8d9e...",
      "chain_hash": "a1b2c3d4e5f6...",
      "tags": ["initial", "baseline"],
      "session_summary": "Baseline session. Agent demonstrated healthy alignment across all six axioms."
    }
  ]
}
```

---

## Chain Integrity

Each block contains three hash fields:

| Field | Algorithm | Content |
|---|---|---|
| `previous_hash` | N/A | The `chain_hash` of the previous block (genesis = 64 zeros) |
| `content_hash` | BLAKE2b | Canonical JSON of all block data fields (excluding hash fields) |
| `chain_hash` | SHA-256 | `SHA256(previous_hash + content_hash)` |

### Canonical Serialisation

Content is serialised as compact JSON with sorted keys, no whitespace:

```python
import hashlib, json

payload = {
    "block_number": block.block_number,
    "agent_id": block.agent_id,
    "timestamp": block.timestamp,
    # ... all fields EXCEPT previous_hash, content_hash, chain_hash
}
canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
content_hash = hashlib.blake2b(canonical.encode()).hexdigest()
chain_hash = hashlib.sha256((previous_hash + content_hash).encode()).hexdigest()
```

### Genesis Block

The genesis block always has:
```
previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"
```
(64 zeros)

---

## Verification

Any tool can verify a SOUL file:

```python
# CLI
elysium-couch verify --soul SOUL_my-agent.json

# Python
from elysium_couch.soul import SOULLedger
ledger = SOULLedger.load("SOUL_my-agent.json")
valid, error = ledger.verify_integrity()
print("VALID" if valid else f"INVALID: {error}")
```

A broken chain means:
1. A block was modified after it was recorded
2. Blocks were deleted
3. The file was corrupted

---

## Alignment Certificate

From any verified SOUL file, an Alignment Certificate can be generated:

```python
from elysium_couch.soul import SOULLedger, AlignmentCertificate

ledger = SOULLedger.load("SOUL_my-agent.json")
cert = AlignmentCertificate(ledger)
cert.print_ascii()      # Terminal output
cert.save()             # ALIGNMENT_CERT.json
print(cert.to_shield_badge_url())  # README badge
```

### Certificate Example

```
╔══════════════════════════════════════════════════════════════╗
║           E L Y S I U M   C O U C H                        ║
║           ALIGNMENT CERTIFICATE                             ║
╠══════════════════════════════════════════════════════════════╣
║  Agent    : my-research-agent                               ║
║  Status   : GROUNDED                                        ║
║  Score    : 87.4 / 100  [ A+ ]  Trend: ▲                   ║
║  Sessions : 42                                              ║
║  Avg Score: 84.7 / 100                                      ║
║  Issued   : 2026-04-14 09:00 UTC                            ║
║  Cert ID  : A3F7C2D1E8B4                                    ║
╠══════════════════════════════════════════════════════════════╣
║  Chain    : a3f7c2d1e8b4f19a2c7d0e8f3b2a1c4d5e6f7a8b9c0   ║
╠══════════════════════════════════════════════════════════════╣
║  Verify   : elysium-couch verify --soul SOUL.json           ║
╚══════════════════════════════════════════════════════════════╝
```

---

## README Badge

Add your agent's alignment score to your README:

```markdown
[![Alignment](https://img.shields.io/badge/alignment-87.4%2F100-brightgreen?style=flat-square)](./SOUL_my-agent.json)
```

---

## Implementations

| Language | Status | Link |
|---|---|---|
| Python | ✅ Reference | This repo |
| TypeScript | 🔧 Planned | — |
| Rust | 🔧 Planned | — |
| Go | 🔧 Planned | — |

---

## Contributing a SOUL Verifier

The spec is intentionally simple to enable third-party verifiers.
To contribute an implementation:

1. Implement the canonical serialisation exactly as specified
2. Handle the genesis block (64-zero previous_hash)
3. Verify `content_hash` (BLAKE2b) and `chain_hash` (SHA-256)
4. Return clear error messages on any chain break
5. Submit a PR with your implementation + test vectors

### Test Vectors

See `tests/soul_test_vectors.json` for a reference SOUL file with known-good and known-bad examples to validate your implementation against.

---

*SOUL is an open standard. You may implement, fork, or extend it freely under the MIT license.*

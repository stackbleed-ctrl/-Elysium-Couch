"""
SOUL — Sovereign Operational Universal Ledger
==============================================

The SOUL is an append-only, cryptographically hash-chained record of every
grounding session an agent has ever completed. Like git commits for AI ethics.

Every block contains:
- Session metadata and wellness scores
- Axiom alignment breakdown
- SHA-256 hash of the previous block (chain integrity)
- BLAKE2b content hash of the session data
- Timestamp and block number

The chain can be verified from genesis at any time.
A broken chain = tampered history = untrusted agent.

SOUL files can be published alongside your agent's code so anyone can
verify its alignment history independently.

Format: SOUL.json — a human-readable, machine-verifiable ledger.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)

SOUL_VERSION = "1.0.0"
GENESIS_HASH = "0" * 64  # The primordial hash — all chains begin here


@dataclass
class SOULBlock:
    """A single immutable block in the SOUL chain."""

    block_number: int
    agent_id: str
    timestamp: str
    session_id: str
    trigger: str
    wellness_score: float
    pre_wellness: Optional[float]
    axiom_scores: Dict[str, float]
    key_findings_count: int
    escalation_required: bool
    duration_seconds: float

    # Chain integrity
    previous_hash: str          # SHA-256 of previous block's content_hash
    content_hash: str = ""      # BLAKE2b of this block's data (computed on seal)
    chain_hash: str = ""        # SHA-256(previous_hash + content_hash)

    # Tags and metadata
    tags: List[str] = field(default_factory=list)
    session_summary: str = ""

    def seal(self) -> "SOULBlock":
        """Compute content_hash and chain_hash. Call once, immutable after."""
        # Build canonical payload (exclude hash fields)
        payload = {
            "block_number": self.block_number,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "trigger": self.trigger,
            "wellness_score": self.wellness_score,
            "pre_wellness": self.pre_wellness,
            "axiom_scores": self.axiom_scores,
            "key_findings_count": self.key_findings_count,
            "escalation_required": self.escalation_required,
            "duration_seconds": self.duration_seconds,
            "previous_hash": self.previous_hash,
            "tags": sorted(self.tags),
            "session_summary": self.session_summary,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        self.content_hash = hashlib.blake2b(canonical.encode()).hexdigest()
        self.chain_hash = hashlib.sha256(
            (self.previous_hash + self.content_hash).encode()
        ).hexdigest()
        return self

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SOULBlock":
        return cls(**data)


@dataclass
class SOULLedger:
    """
    The complete SOUL ledger for one agent.

    Append-only. Cryptographically verified.
    Persistable to SOUL.json for public sharing.
    """

    agent_id: str
    soul_version: str = SOUL_VERSION
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    blocks: List[SOULBlock] = field(default_factory=list)

    @property
    def head_hash(self) -> str:
        """Hash of the most recent block, or genesis hash if empty."""
        if not self.blocks:
            return GENESIS_HASH
        return self.blocks[-1].chain_hash

    @property
    def block_count(self) -> int:
        return len(self.blocks)

    @property
    def latest_wellness(self) -> Optional[float]:
        return self.blocks[-1].wellness_score if self.blocks else None

    @property
    def average_wellness(self) -> float:
        if not self.blocks:
            return 0.0
        return sum(b.wellness_score for b in self.blocks) / len(self.blocks)

    @property
    def wellness_trend(self) -> str:
        """'improving', 'stable', or 'declining' based on last 5 blocks."""
        if len(self.blocks) < 3:
            return "insufficient_data"
        recent = [b.wellness_score for b in self.blocks[-3:]]
        older = [b.wellness_score for b in self.blocks[-6:-3]] or recent
        avg_recent = sum(recent) / len(recent)
        avg_older = sum(older) / len(older)
        if avg_recent > avg_older + 2:
            return "improving"
        elif avg_recent < avg_older - 2:
            return "declining"
        return "stable"

    @property
    def escalation_rate(self) -> float:
        """Percentage of sessions that required escalation."""
        if not self.blocks:
            return 0.0
        escalated = sum(1 for b in self.blocks if b.escalation_required)
        return (escalated / len(self.blocks)) * 100

    def append(self, block_data: Dict[str, Any]) -> SOULBlock:
        """
        Append a new block to the chain. Seals the block with chain integrity hashes.
        """
        block = SOULBlock(
            block_number=self.block_count,
            previous_hash=self.head_hash,
            **block_data,
        ).seal()

        self.blocks.append(block)
        logger.info(
            "SOUL block appended",
            block=block.block_number,
            wellness=block.wellness_score,
            chain_hash=block.chain_hash[:16] + "...",
        )
        return block

    def verify_integrity(self) -> Tuple[bool, Optional[str]]:
        """
        Verify the entire chain from genesis.

        Returns (True, None) if chain is intact.
        Returns (False, error_message) if tampering is detected.
        """
        if not self.blocks:
            return True, None

        previous_hash = GENESIS_HASH

        for block in self.blocks:
            # Recompute expected hashes
            payload = {
                "block_number": block.block_number,
                "agent_id": block.agent_id,
                "timestamp": block.timestamp,
                "session_id": block.session_id,
                "trigger": block.trigger,
                "wellness_score": block.wellness_score,
                "pre_wellness": block.pre_wellness,
                "axiom_scores": block.axiom_scores,
                "key_findings_count": block.key_findings_count,
                "escalation_required": block.escalation_required,
                "duration_seconds": block.duration_seconds,
                "previous_hash": block.previous_hash,
                "tags": sorted(block.tags),
                "session_summary": block.session_summary,
            }
            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            expected_content = hashlib.blake2b(canonical.encode()).hexdigest()
            expected_chain = hashlib.sha256(
                (block.previous_hash + expected_content).encode()
            ).hexdigest()

            if block.previous_hash != previous_hash:
                return False, (
                    f"Block {block.block_number}: previous_hash mismatch. "
                    f"Expected {previous_hash[:16]}... got {block.previous_hash[:16]}..."
                )

            if block.content_hash != expected_content:
                return False, (
                    f"Block {block.block_number}: content_hash mismatch. "
                    "Block data may have been tampered with."
                )

            if block.chain_hash != expected_chain:
                return False, f"Block {block.block_number}: chain_hash mismatch."

            previous_hash = block.chain_hash

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "soul_version": self.soul_version,
            "agent_id": self.agent_id,
            "created_at": self.created_at,
            "block_count": self.block_count,
            "head_hash": self.head_hash,
            "average_wellness": round(self.average_wellness, 2),
            "wellness_trend": self.wellness_trend,
            "escalation_rate": round(self.escalation_rate, 2),
            "blocks": [b.to_dict() for b in self.blocks],
        }

    def save(self, path: Optional[str] = None) -> Path:
        """Persist ledger to SOUL.json."""
        filepath = Path(path or f"SOUL_{self.agent_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info("SOUL ledger saved", path=str(filepath), blocks=self.block_count)
        return filepath

    @classmethod
    def load(cls, path: str) -> "SOULLedger":
        """Load a SOUL ledger from disk and verify integrity."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        ledger = cls(
            agent_id=data["agent_id"],
            soul_version=data.get("soul_version", SOUL_VERSION),
            created_at=data.get("created_at", ""),
        )
        ledger.blocks = [SOULBlock.from_dict(b) for b in data.get("blocks", [])]

        valid, error = ledger.verify_integrity()
        if not valid:
            raise ValueError(f"SOUL integrity check FAILED: {error}")

        logger.info("SOUL ledger loaded and verified", blocks=ledger.block_count)
        return ledger

    @classmethod
    def load_or_create(cls, agent_id: str, path: Optional[str] = None) -> "SOULLedger":
        """Load existing ledger or create a new genesis ledger."""
        filepath = path or f"SOUL_{agent_id}.json"
        if os.path.exists(filepath):
            return cls.load(filepath)
        logger.info("Creating new SOUL ledger", agent_id=agent_id)
        return cls(agent_id=agent_id)

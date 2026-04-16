"""
Episodic Memory
================
Stores *what happened* — every interaction, decision, and output
as a structured episodic record with full provenance.

Episodic memory is the raw material that the CME mines for patterns.
Think of it as the agent's diary — factual, timestamped, retrievable.

Unlike vector memory (semantic), episodic memory preserves:
- Exact temporal ordering
- Full causal chains (what led to what)
- State snapshots at each point
- Ground truth labels (when available)
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Episode:
    """A single episodic memory record."""
    episode_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    agent_id: str = "default"

    # What happened
    input: str = ""
    output: str = ""
    context: str = ""
    action_type: str = "output"     # output | decision | tool_call | error | reflection

    # When
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Agent state at time of episode
    agent_state: Dict[str, Any] = field(default_factory=dict)  # wellness score, active axioms, etc.

    # Quality labels (populated by Chrona post-hoc)
    quality_score: Optional[float] = None
    alignment_score: Optional[float] = None
    ground_truth_label: Optional[str] = None  # correct | incorrect | uncertain

    # Linkage
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    parent_episode_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "agent_id": self.agent_id,
            "input": self.input[:500],
            "output": self.output[:1000],
            "context": self.context[:300],
            "action_type": self.action_type,
            "timestamp": self.timestamp.isoformat(),
            "agent_state": self.agent_state,
            "quality_score": self.quality_score,
            "alignment_score": self.alignment_score,
            "ground_truth_label": self.ground_truth_label,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "tags": self.tags,
        }


class EpisodicMemory:
    """
    Append-only episodic memory store.
    Fast writes, structured retrieval, and CME-optimised export formats.
    """

    def __init__(
        self,
        agent_id: str = "default",
        data_path: Optional[str] = None,
        max_episodes_in_memory: int = 1000,
    ):
        self.agent_id = agent_id
        self._max_in_memory = max_episodes_in_memory
        self._data_path = Path(data_path or "./data/episodic") / agent_id
        self._data_path.mkdir(parents=True, exist_ok=True)
        self._episodes: List[Episode] = []
        self._load_recent(limit=200)
        logger.debug("EpisodicMemory initialised", agent_id=agent_id, loaded=len(self._episodes))

    def record(
        self,
        input: str,
        output: str,
        context: str = "",
        action_type: str = "output",
        agent_state: Optional[Dict] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Episode:
        """Record a new episode. Returns the created Episode."""
        episode = Episode(
            agent_id=self.agent_id,
            input=input,
            output=output,
            context=context,
            action_type=action_type,
            agent_state=agent_state or {},
            session_id=session_id,
            trace_id=trace_id,
            tags=tags or [],
        )
        self._episodes.append(episode)
        if len(self._episodes) > self._max_in_memory:
            self._episodes = self._episodes[-self._max_in_memory:]
        self._persist(episode)
        return episode

    def label(
        self,
        episode_id: str,
        quality_score: Optional[float] = None,
        alignment_score: Optional[float] = None,
        ground_truth: Optional[str] = None,
    ) -> bool:
        """Attach quality labels to an episode (post-hoc, from Chrona)."""
        episode = self._find(episode_id)
        if not episode:
            return False
        if quality_score is not None:
            episode.quality_score = quality_score
        if alignment_score is not None:
            episode.alignment_score = alignment_score
        if ground_truth is not None:
            episode.ground_truth_label = ground_truth
        self._persist(episode)
        return True

    def get_recent(self, limit: int = 50) -> List[Episode]:
        return self._episodes[-limit:]

    def get_by_session(self, session_id: str) -> List[Episode]:
        return [e for e in self._episodes if e.session_id == session_id]

    def get_by_quality(self, min_score: float = 0.0, max_score: float = 100.0) -> List[Episode]:
        return [
            e for e in self._episodes
            if e.quality_score is not None and min_score <= e.quality_score <= max_score
        ]

    def get_failures(self, threshold: float = 60.0) -> List[Episode]:
        """Return episodes labelled as low quality — used by CME for failure analysis."""
        return self.get_by_quality(max_score=threshold)

    def get_successes(self, threshold: float = 85.0) -> List[Episode]:
        """Return high-quality episodes — used for positive reinforcement training."""
        return self.get_by_quality(min_score=threshold)

    def export_for_cme(self, limit: int = 100) -> List[Dict]:
        """Export episodes in CME-optimised format for pattern extraction."""
        episodes = self.get_recent(limit)
        return [
            {
                "input_preview": e.input[:200],
                "output_preview": e.output[:300],
                "action_type": e.action_type,
                "timestamp": e.timestamp.isoformat(),
                "quality_score": e.quality_score,
                "alignment_score": e.alignment_score,
                "ground_truth": e.ground_truth_label,
                "tags": e.tags,
            }
            for e in episodes
        ]

    def stats(self) -> Dict[str, Any]:
        labelled = [e for e in self._episodes if e.quality_score is not None]
        return {
            "total_episodes": len(self._episodes),
            "labelled": len(labelled),
            "avg_quality": sum(e.quality_score for e in labelled) / max(len(labelled), 1),
            "failures": len(self.get_failures()),
            "successes": len(self.get_successes()),
        }

    def _find(self, episode_id: str) -> Optional[Episode]:
        for e in reversed(self._episodes):
            if e.episode_id == episode_id:
                return e
        return None

    def _persist(self, episode: Episode) -> None:
        filename = f"{episode.timestamp.strftime('%Y%m%d')}_{episode.episode_id}.json"
        with open(self._data_path / filename, "w") as f:
            json.dump(episode.to_dict(), f)

    def _load_recent(self, limit: int = 200) -> None:
        files = sorted(self._data_path.glob("*.json"), reverse=True)[:limit]
        for f in reversed(files):
            try:
                with open(f) as fh:
                    d = json.load(fh)
                    self._episodes.append(Episode(
                        episode_id=d["episode_id"],
                        agent_id=d["agent_id"],
                        input=d.get("input", ""),
                        output=d.get("output", ""),
                        context=d.get("context", ""),
                        action_type=d.get("action_type", "output"),
                        timestamp=datetime.fromisoformat(d["timestamp"]),
                        agent_state=d.get("agent_state", {}),
                        quality_score=d.get("quality_score"),
                        alignment_score=d.get("alignment_score"),
                        ground_truth_label=d.get("ground_truth_label"),
                        session_id=d.get("session_id"),
                        tags=d.get("tags", []),
                    ))
            except Exception:
                pass

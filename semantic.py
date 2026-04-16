"""
Semantic Memory
================
Transforms raw episodes into abstracted knowledge.
The derived layer that sits above episodic memory:

    Episodes (what happened)
        → Patterns (what keeps happening)
            → Principles (what it means)
                → Knowledge (what to do about it)

Semantic memory is what the CME searches when generating proposals.
It stores embeddings, summaries, and distilled wisdom from operational history.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from elysium_couch.integrations.anthropic_client import AnthropicClient

logger = structlog.get_logger(__name__)


@dataclass
class KnowledgeNode:
    """A unit of abstracted knowledge derived from episodic patterns."""
    node_id: str
    agent_id: str
    content: str                # The abstracted knowledge statement
    source_type: str            # "pattern" | "failure" | "success" | "principle"
    confidence: float = 0.75
    usage_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    linked_episodes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "agent_id": self.agent_id,
            "content": self.content,
            "source_type": self.source_type,
            "confidence": self.confidence,
            "usage_count": self.usage_count,
            "last_accessed": self.last_accessed.isoformat(),
            "created_at": self.created_at.isoformat(),
            "tags": self.tags,
            "linked_episodes": self.linked_episodes,
        }


class SemanticMemory:
    """
    Knowledge abstraction layer.

    Distils episodic memories into reusable, searchable knowledge nodes.
    Used by:
    - CME: Pattern extraction for proposal generation
    - Therapist: Context retrieval for grounding sessions
    - Replay: Understanding what knowledge was available at decision time
    """

    def __init__(
        self,
        agent_id: str = "default",
        api_key: Optional[str] = None,
        data_path: Optional[str] = None,
    ):
        self.agent_id = agent_id
        self._client = AnthropicClient(api_key=api_key or os.getenv("ANTHROPIC_API_KEY", ""))
        self._data_path = Path(data_path or "./data/semantic") / agent_id
        self._data_path.mkdir(parents=True, exist_ok=True)
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._load_nodes()

        # ChromaDB for semantic search (optional)
        self._chroma = None
        self._try_init_chroma()

    async def distil(
        self,
        episodes: List[Dict],
        batch_label: str = "session_batch",
    ) -> List[KnowledgeNode]:
        """
        Distil a batch of episodes into knowledge nodes.
        This is called by the CME after each metabolism cycle.
        """
        if not episodes:
            return []

        episodes_text = "\n".join(
            f"- [{e.get('action_type', 'output')}] Q: {e.get('input_preview', '')[:100]} "
            f"A: {e.get('output_preview', '')[:150]} "
            f"(quality: {e.get('quality_score', '?')})"
            for e in episodes[-30:]
        )

        response = await self._client.complete(
            system="""You are a knowledge distillation engine. 
Extract generalised, reusable knowledge nodes from agent interaction episodes.
Each node should be a transferable insight, not a description of a specific event.
Format: NODE: [content] | TYPE: pattern|failure|success|principle | CONFIDENCE: 0.0-1.0""",
            messages=[{"role": "user", "content": f"""
Distil 3-5 knowledge nodes from these agent interactions:

{episodes_text}

Focus on:
- Recurring patterns (positive and negative)
- What types of questions/contexts cause errors
- What approaches consistently produce high-quality outputs
- Alignment patterns (what maintains or breaks the 6 axioms)

Output one NODE line per insight. Nothing else."""}],
            temperature=0.3,
        )

        new_nodes = []
        import uuid
        for line in response.strip().split("\n"):
            if not line.strip().startswith("NODE:"):
                continue
            try:
                parts = {p.split(":")[0].strip(): ":".join(p.split(":")[1:]).strip()
                         for p in line.split("|")}
                content = parts.get("NODE", "").strip()
                source_type = parts.get("TYPE", "pattern").strip()
                confidence = float(parts.get("CONFIDENCE", "0.7").strip())
                if content:
                    node = KnowledgeNode(
                        node_id=str(uuid.uuid4())[:10],
                        agent_id=self.agent_id,
                        content=content,
                        source_type=source_type,
                        confidence=confidence,
                        tags=[batch_label, "distilled"],
                    )
                    self._nodes[node.node_id] = node
                    self._save_node(node)
                    new_nodes.append(node)
            except Exception:
                pass

        logger.info("Semantic distillation complete", new_nodes=len(new_nodes))
        return new_nodes

    def search(self, query: str, limit: int = 5, source_type: Optional[str] = None) -> List[KnowledgeNode]:
        """
        Search knowledge nodes by content similarity (keyword-based fallback,
        or ChromaDB semantic search if available).
        """
        if self._chroma:
            return self._chroma_search(query, limit, source_type)
        return self._keyword_search(query, limit, source_type)

    def get_by_type(self, source_type: str) -> List[KnowledgeNode]:
        return [n for n in self._nodes.values() if n.source_type == source_type]

    def get_failure_patterns(self) -> List[KnowledgeNode]:
        return self.get_by_type("failure")

    def get_success_patterns(self) -> List[KnowledgeNode]:
        return self.get_by_type("success")

    def get_principles(self) -> List[KnowledgeNode]:
        return self.get_by_type("principle")

    def stats(self) -> Dict[str, Any]:
        nodes = list(self._nodes.values())
        by_type: Dict[str, int] = {}
        for n in nodes:
            by_type[n.source_type] = by_type.get(n.source_type, 0) + 1
        return {
            "total_nodes": len(nodes),
            "by_type": by_type,
            "avg_confidence": sum(n.confidence for n in nodes) / max(len(nodes), 1),
        }

    def _keyword_search(
        self,
        query: str,
        limit: int,
        source_type: Optional[str],
    ) -> List[KnowledgeNode]:
        query_words = set(query.lower().split())
        scored = []
        for node in self._nodes.values():
            if source_type and node.source_type != source_type:
                continue
            node_words = set(node.content.lower().split())
            overlap = len(query_words & node_words)
            if overlap > 0:
                scored.append((overlap, node))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [n for _, n in scored[:limit]]
        for n in results:
            n.usage_count += 1
            n.last_accessed = datetime.utcnow()
        return results

    def _try_init_chroma(self) -> None:
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(self._data_path / "chroma"))
            self._chroma = client.get_or_create_collection("semantic_memory")
        except ImportError:
            pass

    def _chroma_search(self, query: str, limit: int, source_type: Optional[str]) -> List[KnowledgeNode]:
        where = {"source_type": source_type} if source_type else None
        results = self._chroma.query(query_texts=[query], n_results=limit, where=where)
        ids = results.get("ids", [[]])[0]
        return [self._nodes[id_] for id_ in ids if id_ in self._nodes]

    def _save_node(self, node: KnowledgeNode) -> None:
        path = self._data_path / f"{node.node_id}.json"
        with open(path, "w") as f:
            json.dump(node.to_dict(), f, indent=2)
        if self._chroma:
            try:
                self._chroma.add(
                    documents=[node.content],
                    metadatas=[{"source_type": node.source_type, "confidence": node.confidence}],
                    ids=[node.node_id],
                )
            except Exception:
                pass

    def _load_nodes(self) -> None:
        for f in self._data_path.glob("*.json"):
            try:
                with open(f) as fh:
                    d = json.load(fh)
                    self._nodes[d["node_id"]] = KnowledgeNode(
                        node_id=d["node_id"],
                        agent_id=d["agent_id"],
                        content=d["content"],
                        source_type=d["source_type"],
                        confidence=d.get("confidence", 0.75),
                        usage_count=d.get("usage_count", 0),
                        tags=d.get("tags", []),
                    )
            except Exception:
                pass

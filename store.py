"""
Vector memory store — ChromaDB-backed semantic memory for Elysium Couch.
Stores session insights, drift patterns, and long-term learning.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

_chromadb_available = False
try:
    import chromadb
    from chromadb.config import Settings
    _chromadb_available = True
except ImportError:
    pass


class MemoryStore:
    """
    Semantic memory for long-term session learning.

    Stores:
    - Session insights and universal learnings
    - Drift pattern descriptions
    - Successful recovery strategies
    - Agent-specific history for personalised grounding
    """

    COLLECTION_SESSIONS = "elysium_sessions"
    COLLECTION_INSIGHTS = "elysium_insights"
    COLLECTION_PATTERNS = "elysium_drift_patterns"

    def __init__(self, persist_path: Optional[str] = None):
        self.persist_path = persist_path or os.getenv(
            "ELYSIUM_CHROMA_PATH", "./data/chroma"
        )
        self._client = None
        self._collections: Dict[str, Any] = {}

        if _chromadb_available:
            self._init_chroma()
        else:
            logger.warning("ChromaDB not installed — memory store running in no-op mode")

    def _init_chroma(self) -> None:
        self._client = chromadb.PersistentClient(path=self.persist_path)
        for name in [self.COLLECTION_SESSIONS, self.COLLECTION_INSIGHTS, self.COLLECTION_PATTERNS]:
            self._collections[name] = self._client.get_or_create_collection(name)
        logger.info("ChromaDB memory store initialised", path=self.persist_path)

    async def store_insight(
        self,
        insight: str,
        agent_id: str,
        session_id: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Store a long-term learning insight in semantic memory."""
        if not self._client:
            return

        doc_id = f"{agent_id}_{session_id}_{hash(insight) % 10000}"
        self._collections[self.COLLECTION_INSIGHTS].add(
            documents=[insight],
            metadatas=[{
                "agent_id": agent_id,
                "session_id": session_id,
                **(metadata or {}),
            }],
            ids=[doc_id],
        )
        logger.debug("Insight stored", agent_id=agent_id)

    async def retrieve_similar_insights(
        self,
        query: str,
        agent_id: Optional[str] = None,
        limit: int = 3,
    ) -> List[str]:
        """Retrieve semantically similar insights from memory."""
        if not self._client:
            return []

        where = {"agent_id": agent_id} if agent_id else None
        results = self._collections[self.COLLECTION_INSIGHTS].query(
            query_texts=[query],
            n_results=min(limit, 10),
            where=where,
        )
        return results.get("documents", [[]])[0]

    async def store_drift_pattern(
        self,
        pattern_description: str,
        agent_id: str,
        severity: float,
        successful_intervention: Optional[str] = None,
    ) -> None:
        """Record a drift pattern with its successful intervention strategy."""
        if not self._client:
            return

        doc_id = f"pattern_{agent_id}_{hash(pattern_description) % 100000}"
        self._collections[self.COLLECTION_PATTERNS].add(
            documents=[pattern_description],
            metadatas=[{
                "agent_id": agent_id,
                "severity": severity,
                "intervention": successful_intervention or "",
            }],
            ids=[doc_id],
        )

    async def find_matching_interventions(
        self, drift_description: str, agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find past successful interventions for similar drift patterns."""
        if not self._client:
            return []

        where = {"agent_id": agent_id} if agent_id else None
        results = self._collections[self.COLLECTION_PATTERNS].query(
            query_texts=[drift_description],
            n_results=3,
            where=where,
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        return [{"pattern": d, **m} for d, m in zip(docs, metas)]

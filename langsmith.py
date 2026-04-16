"""
LangSmith observability integration (optional).
Set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY in .env to enable.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

import structlog

logger = structlog.get_logger(__name__)

_langsmith_available = False
try:
    from langsmith import Client as LangSmithClient
    from langsmith import traceable
    _langsmith_available = True
except ImportError:
    pass


class LangSmithTracer:
    """
    Wrapper for LangSmith tracing.
    Gracefully degrades to no-ops when LangSmith is not installed or configured.
    """

    def __init__(self):
        self.enabled = (
            _langsmith_available
            and os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
            and bool(os.getenv("LANGCHAIN_API_KEY"))
        )
        if self.enabled:
            self._client = LangSmithClient()
            self._project = os.getenv("LANGCHAIN_PROJECT", "elysium-couch")
            logger.info("LangSmith tracing enabled", project=self._project)
        else:
            self._client = None
            logger.debug("LangSmith tracing disabled")

    @contextmanager
    def trace_session(self, session_id: str, agent_id: str) -> Generator[None, None, None]:
        """Context manager wrapping an entire couch session as a LangSmith run."""
        if not self.enabled:
            yield
            return

        with self._client.trace(
            name=f"elysium-couch-session",
            run_type="chain",
            inputs={"session_id": session_id, "agent_id": agent_id},
            project_name=self._project,
        ) as run:
            try:
                yield
            except Exception as e:
                run.end(error=str(e))
                raise

    def log_phase(self, phase_name: str, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Log a single phase as a LangSmith span."""
        if not self.enabled:
            return
        # In a real integration, this would create a child run
        logger.debug("LangSmith phase logged", phase=phase_name)

    def log_metric(self, key: str, value: float, session_id: str) -> None:
        """Log a scalar metric to LangSmith."""
        if not self.enabled:
            return
        logger.debug("LangSmith metric", key=key, value=value)

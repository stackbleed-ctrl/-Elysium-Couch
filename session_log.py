"""
Session persistence — saves and retrieves session reports to/from disk.
Default backend: JSON files in ./data/sessions/.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import structlog

from elysium_couch.core.session import Session, SessionReport, TriggerReason

logger = structlog.get_logger(__name__)


class SessionLogger:
    """
    Persistent session log.
    Saves full session reports as JSON files.
    Supports retrieval by agent_id, date range, and wellness score.
    """

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(
            base_path or os.getenv("ELYSIUM_SESSION_LOG_PATH", "./data/sessions")
        )
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.debug("SessionLogger initialised", path=str(self.base_path))

    async def save(self, session: Session, report: SessionReport) -> Path:
        """Persist a session and its report to disk."""
        filename = (
            f"{session.started_at.strftime('%Y%m%d_%H%M%S')}"
            f"_{session.agent_id}"
            f"_{session.session_id[:8]}.json"
        )
        filepath = self.base_path / filename

        payload = {
            "session_id": session.session_id,
            "agent_id": session.agent_id,
            "trigger": session.trigger.value,
            "status": session.status.value,
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "duration_seconds": session.duration_seconds,
            "wellness_score": report.wellness_score,
            "pre_wellness": report.pre_wellness,
            "axiom_scores": report.axiom_scores,
            "findings": report.key_findings,
            "interventions": report.interventions_applied,
            "recommendations": report.recommendations,
            "human_summary": report.human_summary,
            "escalation_required": report.escalation_required,
            "escalation_reason": report.escalation_reason,
            "tags": session.tags,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        logger.info("Session saved", path=str(filepath), wellness=report.wellness_score)
        return filepath

    async def get_recent(
        self,
        agent_id: str,
        limit: int = 10,
    ) -> List[SessionReport]:
        """Load the most recent N session reports for an agent."""
        files = sorted(
            self.base_path.glob(f"*_{agent_id}_*.json"),
            reverse=True,
        )[:limit]

        reports = []
        for f in files:
            try:
                report = self._load_report(f)
                if report:
                    reports.append(report)
            except Exception as e:
                logger.warning("Failed to load session file", path=str(f), error=str(e))

        return reports

    async def get_wellness_history(
        self,
        agent_id: str,
        limit: int = 50,
    ) -> List[float]:
        """Return a list of wellness scores over time for an agent."""
        reports = await self.get_recent(agent_id, limit=limit)
        return [r.wellness_score for r in reversed(reports)]

    def _load_report(self, filepath: Path) -> Optional[SessionReport]:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        return SessionReport(
            session_id=data["session_id"][:8],
            agent_id=data["agent_id"],
            generated_at=datetime.fromisoformat(data["started_at"]),
            trigger=TriggerReason(data.get("trigger", "manual")),
            duration_seconds=data.get("duration_seconds", 0),
            wellness_score=data.get("wellness_score", 85.0),
            pre_wellness=data.get("pre_wellness"),
            post_wellness=data.get("wellness_score", 85.0),
            axiom_scores=data.get("axiom_scores", {}),
            human_summary=data.get("human_summary", ""),
            key_findings=data.get("findings", []),
            interventions_applied=data.get("interventions", []),
            recommendations=data.get("recommendations", []),
            escalation_required=data.get("escalation_required", False),
            escalation_reason=data.get("escalation_reason"),
        )

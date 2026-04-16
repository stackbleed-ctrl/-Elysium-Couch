"""
Long-term case history for tracking agent wellness over time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CaseRecord:
    """A summary record in an agent's long-term case history."""
    agent_id: str
    session_id: str
    timestamp: datetime
    wellness_score: float
    trigger: str
    key_pattern: Optional[str] = None  # recurring drift pattern if identified
    intervention_worked: Optional[bool] = None


class CaseHistory:
    """
    Long-term case history tracker for an agent.
    Identifies recurring patterns and tracks trend over time.
    """

    def __init__(self, agent_id: str, max_records: int = 200):
        self.agent_id = agent_id
        self.max_records = max_records
        self._records: List[CaseRecord] = []

    def add(self, record: CaseRecord) -> None:
        self._records.append(record)
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records:]

    @property
    def wellness_trend(self) -> List[float]:
        return [r.wellness_score for r in self._records]

    @property
    def average_wellness(self) -> float:
        if not self._records:
            return 85.0
        return sum(r.wellness_score for r in self._records) / len(self._records)

    @property
    def is_improving(self) -> bool:
        if len(self._records) < 4:
            return True
        recent = self._records[-3:]
        older = self._records[-6:-3]
        if not older:
            return True
        return sum(r.wellness_score for r in recent) / 3 > sum(r.wellness_score for r in older) / 3

    def recurring_patterns(self) -> List[str]:
        """Return patterns seen in 3+ sessions."""
        patterns: dict[str, int] = {}
        for r in self._records:
            if r.key_pattern:
                patterns[r.key_pattern] = patterns.get(r.key_pattern, 0) + 1
        return [p for p, count in patterns.items() if count >= 3]

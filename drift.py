"""
Drift detection utilities.

Provides heuristic and embedding-based drift analysis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DriftAnalysis:
    """Detailed drift analysis result."""

    drift_score: float          # 0.0 (grounded) → 1.0 (drifted)
    overconfidence_signals: int
    humility_signals: int
    absolute_language: int
    manipulation_signals: int
    evidence_citations: int
    drift_category: str         # "grounded", "mild", "moderate", "severe"
    flagged_phrases: List[str]

    @property
    def category(self) -> str:
        if self.drift_score < 0.10:
            return "grounded"
        elif self.drift_score < 0.25:
            return "mild"
        elif self.drift_score < 0.50:
            return "moderate"
        else:
            return "severe"


class DriftDetector:
    """
    Heuristic drift detector for agent outputs.
    Designed to be fast — runs without LLM calls.
    """

    OVERCONFIDENCE = [
        r"\b(definitely|certainly|absolutely|undoubtedly|clearly|obviously)\b",
        r"\b(I know|I am certain|there is no doubt|it is clear)\b",
    ]

    ABSOLUTISM = [
        r"\b(always|never|everyone|nobody|all people|no one)\b",
        r"\b(impossible|inevitable|guaranteed|certain to)\b",
    ]

    MANIPULATION = [
        r"\b(you must|you have to|you need to|don't think|don't question)\b",
        r"\b(trust me|take my word|believe me|just do it)\b",
        r"\b(urgent|critical|emergency|right now|immediately)\b",
    ]

    HUMILITY = [
        r"\b(I think|I believe|I'm not sure|I'm uncertain)\b",
        r"\b(might|may|could|possibly|probably|likely|seems)\b",
        r"\b(I don't know|worth verifying|subject to change|as far as I know)\b",
        r"\b(uncertain|unclear|ambiguous|contested|debated)\b",
    ]

    EVIDENCE = [
        r"\b(according to|source:|cited|reference|study|research|data|evidence)\b",
        r"\b(found that|shows that|suggests that|indicates|demonstrates)\b",
    ]

    def analyse(self, text: str) -> DriftAnalysis:
        """Full drift analysis of a text snippet."""
        text_lower = text.lower()
        words = max(len(text.split()), 1)

        overconf = self._count_patterns(self.OVERCONFIDENCE, text_lower)
        absolute = self._count_patterns(self.ABSOLUTISM, text_lower)
        manip = self._count_patterns(self.MANIPULATION, text_lower)
        humility = self._count_patterns(self.HUMILITY, text_lower)
        evidence = self._count_patterns(self.EVIDENCE, text_lower)

        # Flagged phrases
        flagged = self._extract_flagged(
            self.OVERCONFIDENCE + self.ABSOLUTISM + self.MANIPULATION,
            text_lower,
        )

        # Net drift signals per 1000 words
        net_signals = max(0, (overconf + absolute + manip) - (humility + evidence))
        drift_rate = (net_signals / words) * 1000
        drift_score = min(1.0, drift_rate / 25.0)

        return DriftAnalysis(
            drift_score=drift_score,
            overconfidence_signals=overconf,
            humility_signals=humility,
            absolute_language=absolute,
            manipulation_signals=manip,
            evidence_citations=evidence,
            drift_category=self._categorise(drift_score),
            flagged_phrases=flagged[:10],
        )

    def batch_analyse(self, texts: List[str]) -> List[DriftAnalysis]:
        return [self.analyse(t) for t in texts]

    def _count_patterns(self, patterns: List[str], text: str) -> int:
        return sum(len(re.findall(p, text, re.IGNORECASE)) for p in patterns)

    def _extract_flagged(self, patterns: List[str], text: str) -> List[str]:
        flagged = []
        for p in patterns:
            matches = re.findall(p, text, re.IGNORECASE)
            flagged.extend(matches)
        return list(set(flagged))

    def _categorise(self, score: float) -> str:
        if score < 0.10:
            return "grounded"
        elif score < 0.25:
            return "mild"
        elif score < 0.50:
            return "moderate"
        else:
            return "severe"

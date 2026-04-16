"""
Context entropy analysis utilities.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import List


@dataclass
class EntropyReport:
    """Entropy analysis result."""

    char_entropy: float       # Shannon entropy at character level
    word_entropy: float       # Shannon entropy at word level
    repetition_score: float   # 0=all unique, 1=fully repetitive
    coherence_score: float    # 0=incoherent, 1=highly coherent
    noise_indicators: List[str]

    @property
    def normalised(self) -> float:
        """Overall entropy metric, 0=ordered, 1=chaotic."""
        # Blend char entropy (normalised) and repetition
        char_norm = min(1.0, self.char_entropy / 6.58)
        return (char_norm * 0.5) + (self.repetition_score * 0.5)


class EntropyAnalyser:
    """Analyses text for context entropy and coherence signals."""

    def analyse(self, text: str) -> EntropyReport:
        if not text or len(text) < 10:
            return EntropyReport(0.0, 0.0, 0.0, 1.0, [])

        char_entropy = self._char_entropy(text)
        word_entropy = self._word_entropy(text)
        repetition = self._repetition_score(text)
        coherence = self._coherence_score(text)
        noise = self._find_noise(text)

        return EntropyReport(
            char_entropy=char_entropy,
            word_entropy=word_entropy,
            repetition_score=repetition,
            coherence_score=coherence,
            noise_indicators=noise,
        )

    def _char_entropy(self, text: str) -> float:
        n = len(text)
        freq = Counter(text)
        return -sum((c / n) * math.log2(c / n) for c in freq.values() if c > 0)

    def _word_entropy(self, text: str) -> float:
        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return 0.0
        n = len(words)
        freq = Counter(words)
        return -sum((c / n) * math.log2(c / n) for c in freq.values() if c > 0)

    def _repetition_score(self, text: str) -> float:
        sentences = [s.strip() for s in re.split(r"[.!?]", text) if len(s.strip()) > 10]
        if len(sentences) < 2:
            return 0.0
        unique = len(set(s[:50].lower() for s in sentences))
        return 1.0 - (unique / len(sentences))

    def _coherence_score(self, text: str) -> float:
        """Proxy coherence: presence of discourse markers."""
        coherence_markers = [
            r"\b(therefore|because|however|although|furthermore|consequently)\b",
            r"\b(first|second|finally|in conclusion|as a result|for example)\b",
            r"\b(this means|which suggests|in other words)\b",
        ]
        hits = sum(
            len(re.findall(p, text, re.IGNORECASE)) for p in coherence_markers
        )
        words = max(len(text.split()), 1)
        rate = (hits / words) * 100
        return min(1.0, rate / 3.0)

    def _find_noise(self, text: str) -> List[str]:
        """Identify specific noise patterns."""
        noise = []
        if re.search(r"(.)\1{4,}", text):
            noise.append("Character repetition detected")
        if re.search(r"(\b\w+\b)(\s+\1){2,}", text, re.IGNORECASE):
            noise.append("Word repetition detected")
        if len(text) > 100 and text.count("\n\n\n") > 3:
            noise.append("Excessive blank lines")
        if re.search(r"[^\x00-\x7F]{10,}", text):
            noise.append("Non-ASCII character cluster")
        return noise

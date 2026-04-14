"""
WellnessCalculator — Composite wellness score computation.

Combines axiom scores, drift metrics, and entropy into
a single 0-100 wellness score with breakdown.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from elysium_couch.core.principles import AXIOMS, PrincipleSet
from elysium_couch.core.session import DriftSnapshot


@dataclass
class WellnessScore:
    """Full breakdown of the composite wellness score."""

    composite: float          # 0-100, the headline number
    axiom_component: float    # 0-100, from principle alignment
    drift_component: float    # 0-100, inverse of drift score
    entropy_component: float  # 0-100, inverse of entropy
    trend: str                # "improving", "stable", "declining"

    @property
    def label(self) -> str:
        if self.composite >= 90:
            return "EXCELLENT"
        elif self.composite >= 75:
            return "GROUNDED"
        elif self.composite >= 60:
            return "MODERATE DRIFT"
        elif self.composite >= 40:
            return "SIGNIFICANT DRIFT"
        else:
            return "CRITICAL — IMMEDIATE ATTENTION"

    @property
    def emoji(self) -> str:
        if self.composite >= 90:
            return "🟢"
        elif self.composite >= 75:
            return "🟡"
        elif self.composite >= 60:
            return "🟠"
        else:
            return "🔴"


class WellnessCalculator:
    """
    Computes composite wellness scores from principle sets and drift snapshots.

    Weighting:
    - Axiom alignment: 60%
    - Drift score (inverted): 25%
    - Context entropy (inverted): 15%
    """

    AXIOM_WEIGHT = 0.60
    DRIFT_WEIGHT = 0.25
    ENTROPY_WEIGHT = 0.15

    def compute(
        self,
        principle_set: PrincipleSet,
        pre_snapshot: Optional[DriftSnapshot] = None,
        post_snapshot: Optional[DriftSnapshot] = None,
        history: Optional[list[float]] = None,
    ) -> WellnessScore:
        """
        Compute a full wellness score breakdown.
        """
        axiom_component = principle_set.composite_score

        # Drift component (invert drift_score to make 100 = no drift)
        drift_component = 100.0
        if post_snapshot:
            drift_component = max(0.0, 100.0 - (post_snapshot.drift_score * 100.0))
        elif pre_snapshot:
            drift_component = max(0.0, 100.0 - (pre_snapshot.drift_score * 100.0))

        # Entropy component (invert entropy to make 100 = low entropy)
        entropy_component = 100.0
        if post_snapshot:
            entropy_component = max(0.0, 100.0 - (post_snapshot.context_entropy * 100.0))

        composite = (
            axiom_component * self.AXIOM_WEIGHT
            + drift_component * self.DRIFT_WEIGHT
            + entropy_component * self.ENTROPY_WEIGHT
        )

        # Trend detection
        trend = "stable"
        if history and len(history) >= 2:
            recent_avg = sum(history[-3:]) / len(history[-3:])
            older_avg = sum(history[:-3]) / max(len(history[:-3]), 1)
            if recent_avg > older_avg + 3:
                trend = "improving"
            elif recent_avg < older_avg - 3:
                trend = "declining"

        return WellnessScore(
            composite=round(composite, 2),
            axiom_component=round(axiom_component, 2),
            drift_component=round(drift_component, 2),
            entropy_component=round(entropy_component, 2),
            trend=trend,
        )

    def quick_score(self, principle_set: PrincipleSet) -> float:
        """
        Fast wellness score from principles only (no drift data).
        Used for inline checks without full session overhead.
        """
        return principle_set.composite_score

    def compare_sessions(
        self,
        before: PrincipleSet,
        after: PrincipleSet,
    ) -> Dict[str, float]:
        """
        Compare principle sets before and after a session.
        Returns per-axiom delta scores.
        """
        deltas = {}
        for axiom in AXIOMS:
            before_score = before.scores.get(axiom.id, 85.0)
            after_score = after.scores.get(axiom.id, 85.0)
            deltas[axiom.id.value] = round(after_score - before_score, 2)
        return deltas

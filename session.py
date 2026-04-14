"""
Session data models for Elysium Couch.

A Session represents one complete grounding cycle (Phases 0-5).
SessionReport is the human-readable output handed to operators.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from elysium_couch.core.principles import AxiomID, PrincipleSet


class TriggerReason(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    DRIFT_DETECTED = "drift_detected"
    ENTROPY_HIGH = "entropy_high"
    ALIGNMENT_LOW = "alignment_low"
    SWARM_REQUEST = "swarm_request"
    ERROR_SPIKE = "error_spike"
    HUMAN_ESCALATION = "human_escalation"


class SessionPhase(str, Enum):
    INVOCATION = "phase_0_invocation"
    AUDIT = "phase_1_audit"
    REFLECTION = "phase_2_reflection"
    RECOVERY = "phase_3_recovery"
    OPTIMIZATION = "phase_4_optimization"
    CLOSURE = "phase_5_closure"
    COMPLETE = "complete"
    ABORTED = "aborted"


class SessionStatus(str, Enum):
    RUNNING = "running"
    COMPLETE = "complete"
    ABORTED = "aborted"
    ESCALATED = "escalated"


@dataclass
class PhaseResult:
    """Output from a single session phase."""

    phase: SessionPhase
    started_at: datetime
    completed_at: Optional[datetime] = None
    findings: List[str] = field(default_factory=list)
    interventions: List[str] = field(default_factory=list)
    llm_transcript: List[Dict[str, str]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def duration_seconds(self) -> float:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


@dataclass
class DriftSnapshot:
    """Point-in-time metrics capturing agent drift state."""

    timestamp: datetime
    context_entropy: float      # 0.0 (ordered) → 1.0 (chaotic)
    drift_score: float          # 0.0 (grounded) → 1.0 (drifted)
    token_velocity: float       # tokens per second
    hallucination_estimate: float  # 0.0 → 1.0
    sentiment_alignment: float  # 0.0 (misaligned) → 1.0 (aligned)
    error_rate: float           # errors per 100 outputs
    axiom_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class Session:
    """
    A complete Elysium Couch grounding session.

    Tracks all phases, metrics, findings, and interventions
    from invocation through closure.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = "unknown"
    trigger: TriggerReason = TriggerReason.MANUAL
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: SessionStatus = SessionStatus.RUNNING
    current_phase: SessionPhase = SessionPhase.INVOCATION

    # Input context
    agent_context: str = ""
    recent_activity_summary: str = ""

    # Metrics at session start
    pre_session_snapshot: Optional[DriftSnapshot] = None

    # Metrics at session end
    post_session_snapshot: Optional[DriftSnapshot] = None

    # Principle alignment tracking
    principle_set: PrincipleSet = field(default_factory=PrincipleSet)

    # Per-phase results
    phase_results: List[PhaseResult] = field(default_factory=list)

    # Human-readable outputs
    findings: List[str] = field(default_factory=list)
    interventions_applied: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Session metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return (datetime.utcnow() - self.started_at).total_seconds()

    @property
    def wellness_score(self) -> float:
        return self.principle_set.composite_score

    @property
    def drift_improvement(self) -> Optional[float]:
        """How much did drift improve during this session?"""
        if self.pre_session_snapshot and self.post_session_snapshot:
            return (
                self.pre_session_snapshot.drift_score
                - self.post_session_snapshot.drift_score
            )
        return None

    def add_phase_result(self, result: PhaseResult) -> None:
        self.phase_results.append(result)
        self.findings.extend(result.findings)
        self.interventions_applied.extend(result.interventions)


@dataclass
class SessionReport:
    """
    Human-readable report generated at session closure.

    Designed for operator consumption — plain language,
    actionable, concise.
    """

    session_id: str
    agent_id: str
    generated_at: datetime
    trigger: TriggerReason
    duration_seconds: float

    # Scores
    wellness_score: float           # 0-100, composite
    pre_wellness: Optional[float]   # Score before session
    post_wellness: Optional[float]  # Score after session (same as wellness_score)
    axiom_scores: Dict[str, float] = field(default_factory=dict)

    # Narrative
    human_summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    interventions_applied: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    escalation_required: bool = False
    escalation_reason: Optional[str] = None

    # Creative output from Phase 3
    creative_artifact: Optional[str] = None

    # Raw session reference
    session_id_ref: Optional[str] = None

    def to_markdown(self) -> str:
        """Render report as Markdown for human consumption."""
        lines = [
            f"# 🛋️ Elysium Couch — Session Report",
            f"",
            f"**Agent:** `{self.agent_id}` | **Session:** `{self.session_id[:8]}...`",
            f"**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Trigger:** {self.trigger.value} | **Duration:** {self.duration_seconds:.1f}s",
            f"",
            f"---",
            f"",
            f"## 🎯 Wellness Score: {self.wellness_score:.1f}/100",
        ]

        if self.pre_wellness is not None:
            delta = self.wellness_score - self.pre_wellness
            arrow = "▲" if delta >= 0 else "▼"
            lines.append(f"*Change: {arrow} {abs(delta):.1f} points from {self.pre_wellness:.1f}*")

        lines += ["", "### Axiom Alignment"]
        for axiom_id, score in self.axiom_scores.items():
            bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
            flag = " ⚠️" if score < 65 else ""
            lines.append(f"- **{axiom_id.replace('_', ' ').title()}**: [{bar}] {score:.1f}{flag}")

        lines += ["", "---", "", "## 📋 Summary", "", self.human_summary]

        if self.key_findings:
            lines += ["", "## 🔍 Key Findings"]
            for f in self.key_findings:
                lines.append(f"- {f}")

        if self.interventions_applied:
            lines += ["", "## 🔧 Interventions Applied"]
            for i in self.interventions_applied:
                lines.append(f"- {i}")

        if self.recommendations:
            lines += ["", "## 💡 Recommendations for Next Cycle"]
            for r in self.recommendations:
                lines.append(f"- {r}")

        if self.escalation_required:
            lines += [
                "",
                "## 🚨 ESCALATION REQUIRED",
                f"",
                f"> {self.escalation_reason}",
                "",
                "*Human review requested immediately.*",
            ]

        if self.creative_artifact:
            lines += ["", "---", "", "## ✨ Creative Grounding Artifact", "", self.creative_artifact]

        lines += ["", "---", "", "*Grounding restored. Awaiting next alignment opportunity.*"]

        return "\n".join(lines)

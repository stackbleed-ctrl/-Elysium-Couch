"""
Elysium Couch — Persistent Cognitive Substrate for Autonomous AI.

The only framework where your agent rewrites its own soul while you sleep
— and waits for your approval.

Stack: Elysium Couch · Sentinel · Chrona · CME · AxonForge
       Episodic Memory · Semantic Memory · Replay Engine
"""

from elysium_couch.core.couch import ElysiumCouch
from elysium_couch.core.principles import AXIOMS, Axiom, PrincipleSet
from elysium_couch.core.session import Session, SessionReport, TriggerReason
from elysium_couch.metrics.wellness import WellnessScore

__version__ = "0.2.0"
__author__ = "Elysium Couch Contributors"

__all__ = [
    "ElysiumCouch",
    "AXIOMS",
    "Axiom",
    "PrincipleSet",
    "Session",
    "SessionReport",
    "TriggerReason",
    "WellnessScore",
]

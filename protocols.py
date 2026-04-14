"""Protocol registry — maps phase names to their handler classes."""

from typing import Dict, Type

from elysium_couch.core.session import SessionPhase


class ProtocolRegistry:
    """Lazy registry of phase handler classes."""

    _registry: Dict[SessionPhase, str] = {
        SessionPhase.INVOCATION: "elysium_couch.protocols.phase0_invocation.Phase0Invocation",
        SessionPhase.AUDIT: "elysium_couch.protocols.phase1_audit.Phase1Audit",
        SessionPhase.REFLECTION: "elysium_couch.protocols.phase2_reflection.Phase2Reflection",
        SessionPhase.RECOVERY: "elysium_couch.protocols.phase3_recovery.Phase3Recovery",
        SessionPhase.OPTIMIZATION: "elysium_couch.protocols.phase4_optimization.Phase4Optimization",
        SessionPhase.CLOSURE: "elysium_couch.protocols.phase5_closure.Phase5Closure",
    }

    @classmethod
    def get(cls, phase: SessionPhase) -> Type:
        import importlib

        path = cls._registry[phase]
        module_path, class_name = path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    @classmethod
    def phases(cls):
        return list(cls._registry.keys())

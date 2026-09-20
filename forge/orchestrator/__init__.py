"""
IP FORGE Orchestrator Package: State schemas and multi-agent coordination.
"""

from forge.orchestrator.state import PlanStep, EngineeringPlan, AgentState


def get_coordinator():
    """Lazy getter for OrchestratorCoordinator to prevent circular import."""
    from forge.orchestrator.coordinator import get_coordinator as _get_coordinator
    return _get_coordinator()


__all__ = [
    "PlanStep",
    "EngineeringPlan",
    "AgentState",
    "get_coordinator",
]

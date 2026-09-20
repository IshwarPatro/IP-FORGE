"""
IP FORGE Orchestrator Package: State schemas and multi-agent coordination.
"""

from forge.orchestrator.state import PlanStep, EngineeringPlan, AgentState


def get_coordinator():
    """Lazy getter for OrchestratorCoordinator to prevent circular import."""
    from forge.orchestrator.coordinator import get_coordinator as _get_coordinator
    return _get_coordinator()


def get_autonomous_loop():
    """Lazy getter for AutonomousLoop to prevent circular import."""
    from forge.orchestrator.loop import get_autonomous_loop as _get_loop
    return _get_loop()


__all__ = [
    "PlanStep",
    "EngineeringPlan",
    "AgentState",
    "get_coordinator",
    "get_autonomous_loop",
]


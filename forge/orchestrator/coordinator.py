"""
IP FORGE: Orchestration Coordinator
Manages transitions between Architecture Agent RAG investigation and Planner Agent DAG generation.
"""

import uuid
from typing import Optional
from pathlib import Path
from forge.agents.architect import ArchitectureAgent
from forge.agents.planner import PlannerAgent
from forge.orchestrator.state import AgentState, EngineeringPlan
from forge.rag.vector_store import get_vector_store, CodebaseVectorStore
from forge.config import setup_logger

logger = setup_logger("forge.orchestrator.coordinator")


class OrchestratorCoordinator:
    """Coordinates multi-agent planning and state machine initialization."""

    def __init__(
        self,
        vector_store: Optional[CodebaseVectorStore] = None,
        llm_provider: Optional[str] = None
    ):
        self.vector_store = vector_store or get_vector_store()
        self.architect = ArchitectureAgent(vector_store=self.vector_store, llm_provider=llm_provider)
        self.planner = PlannerAgent(llm_provider=llm_provider)

    def create_plan_for_task(self, task: str, top_k: int = 5) -> EngineeringPlan:
        """
        Executes Phase 2 reasoning pipeline:
        Task -> Architecture RAG Investigation -> Planner Agent JSON DAG.
        """
        logger.info(f"[Coordinator] Initiating planning cycle for: '{task}'")

        # Step 1: Query RAG for grounded codebase context
        context = self.architect.investigate_task(task=task, top_k=top_k)

        # Step 2: Formulate structured engineering plan
        plan = self.planner.create_plan(task=task, context=context)

        logger.info(f"[Coordinator] Plan completed with {len(plan.steps)} execution steps.")
        return plan

    def start_session(self, task: str) -> AgentState:
        """Initializes a new global AgentState session with an active plan."""
        session_id = str(uuid.uuid4())[:8]
        plan = self.create_plan_for_task(task)

        state = AgentState(
            session_id=session_id,
            task=task,
            plan=plan,
            current_step_index=0,
            status="planning"
        )
        state.record_event(f"Session {session_id} initialized with task: '{task}'")
        state.record_event(f"Plan formulated with {len(plan.steps)} steps across {len(plan.files_to_modify)} files.")
        return state


_default_coordinator: Optional[OrchestratorCoordinator] = None


def get_coordinator() -> OrchestratorCoordinator:
    """Returns singleton OrchestratorCoordinator instance."""
    global _default_coordinator
    if _default_coordinator is None:
        _default_coordinator = OrchestratorCoordinator()
    return _default_coordinator

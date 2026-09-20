"""
Unit and Integration tests for Phase 2: Agent Reasoning & Orchestration.
"""

from pathlib import Path
import pytest
from starlette.testclient import TestClient
from forge.agents.architect import ArchitectureAgent
from forge.agents.planner import PlannerAgent
from forge.orchestrator.coordinator import OrchestratorCoordinator, get_coordinator
from forge.orchestrator.state import EngineeringPlan, AgentState
from forge.rag.vector_store import get_vector_store
from forge.api.main import app


@pytest.fixture(scope="module", autouse=True)
def setup_vector_store():
    """Ensures dummy repository is indexed in the vector store before tests run."""
    store = get_vector_store()
    store.index_repository(Path("tests/dummy_repo"))
    return store


def test_architecture_agent_investigation():
    """Verify ArchitectureAgent discovers target files and symbols for a task."""
    agent = ArchitectureAgent()
    context = agent.investigate_task("Add pagination parameters limit and offset to products endpoint")

    assert len(context.relevant_symbols) > 0
    assert len(context.relevant_files) > 0
    assert any("services.py" in f or "api.py" in f for f in context.relevant_files)
    assert "Codebase context for task" in context.context_summary


def test_planner_agent_creates_valid_plan():
    """Verify PlannerAgent generates structured, actionable steps."""
    architect = ArchitectureAgent()
    planner = PlannerAgent()

    task = "Add pagination parameters limit and offset to get_all_products"
    context = architect.investigate_task(task)
    plan = planner.create_plan(task=task, context=context)

    assert isinstance(plan, EngineeringPlan)
    assert plan.task == task
    assert len(plan.steps) >= 3
    assert len(plan.files_to_modify) > 0

    # Verify step types
    actions = [s.action for s in plan.steps]
    assert "read_file" in actions
    assert "modify_file" in actions
    assert "run_test" in actions

    # Verify final step is a test
    final_step = plan.steps[-1]
    assert final_step.action == "run_test"
    assert "pytest" in final_step.description.lower()


def test_orchestrator_coordinator_session():
    """Verify OrchestratorCoordinator initializes an AgentState session."""
    coordinator = get_coordinator()
    task = "Implement bulk discount calculation for orders"
    state = coordinator.start_session(task=task)

    assert isinstance(state, AgentState)
    assert state.task == task
    assert state.plan is not None
    assert len(state.session_id) > 0
    assert state.status == "planning"
    assert len(state.audit_trail) >= 2


def test_api_plan_task_endpoint():
    """Test POST /plan-task endpoint returns a validated EngineeringPlan."""
    client = TestClient(app)
    response = client.post(
        "/plan-task",
        json={
            "task": "Add category search to list_products endpoint",
            "top_k": 3
        }
    )
    assert response.status_code == 200
    plan_data = response.json()
    assert plan_data["task"] == "Add category search to list_products endpoint"
    assert "steps" in plan_data
    assert len(plan_data["steps"]) >= 2
    assert "verification_strategy" in plan_data

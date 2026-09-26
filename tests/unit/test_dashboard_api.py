"""
Unit and integration tests for IP FORGE Phase 6: Human-in-the-Loop Developer Dashboard API.
Validates Server-Sent Events (SSE) streaming, governance decision gates (approve/reject),
and session telemetry listing.
"""

import pytest
from unittest.mock import MagicMock
from starlette.testclient import TestClient
from forge.api.main import app, _governance_sessions
from forge.orchestrator.state import AgentState


def test_governance_decision_approve():
    """Verify human engineer can approve an autonomous task Pull Request."""
    client = TestClient(app)
    sess_id = "test_approval_101"
    _governance_sessions[sess_id] = {
        "session_id": sess_id,
        "task": "Refactor discount calculation",
        "status": "completed",
        "tests_passed": True,
        "governance_decision": "pending"
    }

    res = client.post(
        "/governance/decision",
        json={"session_id": sess_id, "decision": "approve"}
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["decision"] == "approved"
    assert "ready to merge" in data["message"].lower()
    assert _governance_sessions[sess_id]["governance_decision"] == "approve"


def test_governance_decision_reject_with_feedback():
    """Verify human engineer can reject code changes and inject corrective feedback."""
    client = TestClient(app)
    sess_id = "test_reject_202"
    _governance_sessions[sess_id] = {
        "session_id": sess_id,
        "task": "Modify order service",
        "status": "completed",
        "tests_passed": True,
        "governance_decision": "pending"
    }

    feedback_text = "Please ensure negative discounts raise ValueError instead of returning negative total."
    res = client.post(
        "/governance/decision",
        json={
            "session_id": sess_id,
            "decision": "reject",
            "feedback": feedback_text
        }
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["decision"] == "rejected"
    assert feedback_text in data["message"]
    assert _governance_sessions[sess_id]["human_feedback"] == feedback_text


def test_list_governance_sessions():
    """Verify GET /governance/sessions returns history of all sessions."""
    client = TestClient(app)
    res = client.get("/governance/sessions")

    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert any(s["session_id"] == "test_approval_101" for s in data)


def test_execute_task_stream_sse_endpoint(monkeypatch):
    """Verify POST /execute-task-stream initiates an SSE stream with proper events."""
    client = TestClient(app)

    mock_state = AgentState(
        session_id="stream_test_sess",
        task="Test Streaming Endpoint",
        status="completed",
        tests_passed=True,
        retry_count=0
    )

    def mock_run(task, target_file, test_command, create_branch, on_event):
        on_event("planning_started", {"message": "Formulating DAG"})
        on_event("testing_passed", {"passed_count": 4})
        return mock_state

    mock_loop = MagicMock()
    mock_loop.run.side_effect = mock_run

    monkeypatch.setattr("forge.orchestrator.loop.get_autonomous_loop", lambda: mock_loop)

    res = client.post(
        "/execute-task-stream",
        json={"task": "Test Streaming Endpoint", "create_branch": False}
    )

    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]

    body = res.text
    assert "event: planning_started" in body
    assert "event: testing_passed" in body
    assert "event: stream_end" in body

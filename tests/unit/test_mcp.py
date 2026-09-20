"""
Unit and Integration tests for Phase 3: Model Context Protocol (MCP) Tooling Subsystem.
"""

from pathlib import Path
import pytest
from starlette.testclient import TestClient
from forge.mcp.fs_tools import FilesystemTools, ToolResult
from forge.mcp.terminal_tools import TerminalTools
from forge.mcp.git_tools import GitTools
from forge.mcp.server import MCPServer, get_mcp_server
from forge.agents.coder import CodingAgent
from forge.orchestrator.state import PlanStep
from forge.api.main import app


@pytest.fixture
def temp_sandbox(tmp_path):
    """Creates an isolated filesystem sandbox directory for tests."""
    sub_dir = tmp_path / "sandbox"
    sub_dir.mkdir()
    (sub_dir / "sample.py").write_text("print('Hello MCP')", encoding="utf-8")
    return sub_dir


def test_fs_tools_read_and_write(temp_sandbox):
    """Verify safe read and write within the sandbox."""
    fs = FilesystemTools(root_dir=temp_sandbox)

    # 1. Read existing
    read_res = fs.read_file("sample.py")
    assert read_res.success is True
    assert "Hello MCP" in read_res.output

    # 2. Write new
    write_res = fs.write_file("nested/module.py", "x = 42")
    assert write_res.success is True
    assert (temp_sandbox / "nested" / "module.py").exists()

    # 3. Read newly written
    read_new = fs.read_file("nested/module.py")
    assert read_new.success is True
    assert read_new.output == "x = 42"


def test_fs_tools_path_traversal_blocked(temp_sandbox):
    """Verify that path traversal attempts outside the sandbox are rejected."""
    fs = FilesystemTools(root_dir=temp_sandbox)

    # Attempt upward traversal
    attack_res = fs.read_file("../../etc/passwd")
    assert attack_res.success is False
    assert "Security Violation" in attack_res.error

    # Attempt write outside
    write_attack = fs.write_file("../malicious.sh", "evil()")
    assert write_attack.success is False
    assert "Security Violation" in write_attack.error


def test_terminal_tools_allowlist_and_execution():
    """Verify permitted test runner execution."""
    term = TerminalTools(root_dir=Path("tests/dummy_repo"))
    res = term.execute_command("pytest tests/test_api.py -q")
    assert res.success is True
    assert res.metadata["returncode"] == 0


def test_terminal_tools_command_injection_blocked():
    """Verify command injection attempts are intercepted and rejected."""
    term = TerminalTools(root_dir=Path("tests/dummy_repo"))

    # Attempt chaining with semicolon
    res1 = term.execute_command("pytest tests/ ; rm -rf /")
    assert res1.success is False
    assert "Security Violation" in res1.error

    # Attempt unpermitted binary
    res2 = term.execute_command("curl http://malicious.com")
    assert res2.success is False
    assert "Security Violation" in res2.error


def test_mcp_server_registry_and_dispatch(temp_sandbox):
    """Verify tool registration and dispatch mechanism."""
    fs = FilesystemTools(root_dir=temp_sandbox)
    server = MCPServer(fs_tools=fs)

    # Verify tool list
    tools = server.list_tools()
    tool_names = [t.name for t in tools]
    assert "read_file" in tool_names
    assert "write_file" in tool_names
    assert "execute_test_command" in tool_names

    # Verify dispatch
    res = server.call_tool("read_file", {"path": "sample.py"})
    assert res.success is True
    assert "Hello MCP" in res.output


def test_coding_agent_executes_step_via_mcp(temp_sandbox):
    """Verify CodingAgent uses MCP server to execute plan steps."""
    fs = FilesystemTools(root_dir=temp_sandbox)
    server = MCPServer(fs_tools=fs)
    coder = CodingAgent(mcp_server=server)

    step = PlanStep(
        step_number=1,
        action="read_file",
        target_file="sample.py",
        description="Read sample file"
    )
    result = coder.execute_step(step)
    assert result.success is True
    assert "Hello MCP" in result.output


def test_api_mcp_endpoints():
    """Test GET /mcp/tools and POST /mcp/execute via REST API."""
    client = TestClient(app)

    # 1. List tools
    tools_res = client.get("/mcp/tools")
    assert tools_res.status_code == 200
    tools = tools_res.json()
    assert len(tools) >= 5
    assert any(t["name"] == "read_file" for t in tools)

    # 2. Execute tool
    exec_res = client.post(
        "/mcp/execute",
        json={
            "tool_name": "read_file",
            "arguments": {"path": "app/utils.py"}
        }
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["success"] is True
    assert "calculate_discount" in exec_data["output"]

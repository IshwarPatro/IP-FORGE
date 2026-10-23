import json
from pathlib import Path
import pytest
from forge.mcp.stdio import StdioMCPServer

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_stdio_initialize():
    server = StdioMCPServer(workspace_root=REPO_ROOT / "examples/flutter_fixture")
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    }
    resp = server.handle_request(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert "result" in resp
    assert resp["result"]["protocolVersion"] == "2024-11-05"
    assert resp["result"]["serverInfo"]["name"] == "ip-forge"
    assert "tools" in resp["result"]["capabilities"]


def test_stdio_ping():
    server = StdioMCPServer()
    req = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
    resp = server.handle_request(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 2
    assert resp["result"] == {}


def test_stdio_tools_list():
    server = StdioMCPServer(workspace_root=REPO_ROOT / "examples/flutter_fixture")
    req = {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}
    resp = server.handle_request(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 3
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "inspect_flutter_project" in tool_names
    assert "run_flutter_checks" in tool_names
    assert "get_flutter_report" in tool_names

    # Check that tools include standard inputSchema
    for t in tools:
        assert "inputSchema" in t
        assert "description" in t


def test_stdio_tools_call():
    server = StdioMCPServer(workspace_root=REPO_ROOT / "examples/flutter_fixture")
    req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "inspect_flutter_project",
            "arguments": {"directory": "."}
        }
    }
    resp = server.handle_request(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 4
    assert resp["result"]["isError"] is False
    content = resp["result"]["content"]
    assert len(content) == 1
    assert content[0]["type"] == "text"
    parsed_json = json.loads(content[0]["text"])
    assert parsed_json["name"] == "forge_flutter_fixture"
    assert parsed_json["is_flutter"] is True


def test_stdio_invalid_method():
    server = StdioMCPServer()
    req = {"jsonrpc": "2.0", "id": 99, "method": "unknown_action"}
    resp = server.handle_request(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 99
    assert resp["error"]["code"] == -32601


def test_stdio_notification_ignored():
    server = StdioMCPServer()
    req = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    resp = server.handle_request(req)
    assert resp is None


def test_failed_check_preserves_diagnostics():
    from unittest.mock import Mock
    from forge.mcp.fs_tools import ToolResult
    backend = Mock()
    backend.call_tool.return_value = ToolResult(
        success=False, error="Review exited with code 1",
        output="lib/cache.dart:42: expired account data was returned")
    server = StdioMCPServer(mcp_server=backend)
    response = server.handle_request({
        "jsonrpc": "2.0", "id": 8, "method": "tools/call",
        "params": {"name": "run_flutter_checks", "arguments": {}}})
    result = response["result"]
    assert result["isError"] is True
    text = result["content"][0]["text"]
    assert "Review exited with code 1" in text
    assert "lib/cache.dart:42: expired account data was returned" in text


def test_error_without_output_is_returned():
    from unittest.mock import Mock
    from forge.mcp.fs_tools import ToolResult
    backend = Mock()
    backend.call_tool.return_value = ToolResult(success=False, error="Flutter SDK missing")
    response = StdioMCPServer(mcp_server=backend).handle_request({
        "jsonrpc": "2.0", "id": 9, "method": "tools/call",
        "params": {"name": "run_flutter_checks"}})
    assert response["result"]["content"][0]["text"] == "Flutter SDK missing"

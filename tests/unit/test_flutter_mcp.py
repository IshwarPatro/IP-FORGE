from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from forge.mcp.server import MCPServer
from forge.mcp.flutter_tools import FlutterMCPTools

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_flutter_mcp_inspect():
    tools = FlutterMCPTools(workspace_root=REPO_ROOT / "examples/flutter_fixture")
    res = tools.inspect_flutter_project()

    assert res.success is True
    assert res.metadata["name"] == "forge_flutter_fixture"
    assert res.metadata["is_flutter"] is True


def test_mcp_server_registers_flutter_tools():
    server = MCPServer()
    tool_names = [t.name for t in server.list_tools()]

    assert "inspect_flutter_project" in tool_names
    assert "run_flutter_checks" in tool_names
    assert "get_flutter_report" in tool_names


def test_mcp_server_calls_inspect_flutter_project():
    server = MCPServer(flutter_tools=FlutterMCPTools(workspace_root=REPO_ROOT))
    fixture_dir = str(REPO_ROOT / "examples/flutter_fixture")
    res = server.call_tool("inspect_flutter_project", {"directory": fixture_dir})

    assert res.success is True
    assert "forge_flutter_fixture" in res.output


@pytest.mark.parametrize("kind", ["relative", "absolute", "symlink"])
def test_flutter_workspace_escape_rejected(tmp_path, kind):
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    directory = "../outside" if kind == "relative" else str(outside)
    if kind == "symlink":
        (root / "link").symlink_to(outside, target_is_directory=True)
        directory = "link"
    tools = FlutterMCPTools(root)
    with pytest.raises(PermissionError):
        tools.inspect_flutter_project(directory)


def test_get_report_does_not_execute_checks(tmp_path):
    from forge.mcp.fs_tools import ToolResult
    tools = FlutterMCPTools(tmp_path)
    with patch("forge.mcp.flutter_tools.run_review") as run:
        assert not tools.get_report().success
        tools._reports[tmp_path.resolve()] = ToolResult(success=False, output="failed assertion", metadata={"exit_code": 1})
        report = tools.get_report()
        assert report.output == "failed assertion"
        report.metadata["exit_code"] = 0
        assert tools.get_report().metadata["exit_code"] == 1
        run.assert_not_called()


def test_run_caches_report(tmp_path):
    from forge.reports.models import ReviewReport
    tools = FlutterMCPTools(tmp_path)
    with patch("forge.mcp.flutter_tools.run_review", return_value=ReviewReport(workspace=str(tmp_path))) as run:
        result = tools.run_flutter_checks()
        assert tools.get_report().model_dump() == result.model_dump()
        assert run.call_count == 1


@pytest.mark.parametrize("checks", [[], ["analyze", "analyze"], [""]])
def test_invalid_check_override_does_not_execute(tmp_path, checks):
    tools = FlutterMCPTools(tmp_path)
    with patch("forge.mcp.flutter_tools.run_review") as run:
        with pytest.raises(ValueError):
            tools.run_flutter_checks(checks=checks)
        run.assert_not_called()

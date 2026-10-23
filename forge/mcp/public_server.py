"""Public, Flutter-only SDK transport. Execution is opt-in for trusted code."""
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent
from forge.mcp.flutter_tools import FlutterMCPTools


def create_server(workspace: Path, allow_execution: bool = False) -> FastMCP:
    root = workspace.resolve()
    if not root.is_dir():
        raise ValueError(f"Workspace is not a directory: {root}")
    tools = FlutterMCPTools(root)
    server = FastMCP("ip-forge")

    def response(result):
        text = result.output
        if result.error:
            text = result.error + ("\n\n" + text if text else "")
        return CallToolResult(content=[TextContent(type="text", text=text)], isError=not result.success)

    @server.tool()
    def inspect_flutter_project(directory: str = ".") -> CallToolResult:
        """Inspect Flutter dependencies and test inventory inside the workspace; does not verify architecture."""
        return response(tools.inspect_flutter_project(directory))

    @server.tool()
    def get_flutter_report(directory: str = ".") -> CallToolResult:
        """Read the last report in this session without rerunning checks. May be stale after edits."""
        return response(tools.get_report(directory))

    if allow_execution:
        @server.tool()
        def run_flutter_checks(directory: str = ".") -> CallToolResult:
            """Execute configured Flutter analysis/tests in a trusted project. Not OS-sandboxed; may write build files."""
            return response(tools.run_flutter_checks(directory))
    return server


def run_stdio_server(workspace: Path, allow_execution: bool = False):
    create_server(workspace, allow_execution).run(transport="stdio")

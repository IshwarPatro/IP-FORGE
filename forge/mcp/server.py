"""
IP FORGE: Model Context Protocol (MCP) Server & Tool Registry
Registers, exposes JSON-schemas for, and executes sandboxed agent tools.
"""

from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field
from forge.mcp.fs_tools import FilesystemTools, ToolResult
from forge.mcp.terminal_tools import TerminalTools
from forge.mcp.git_tools import GitTools
from forge.config import setup_logger

logger = setup_logger("forge.mcp.server")


class ToolDefinition(BaseModel):
    """MCP Tool schema definition compatible with LLM function-calling protocols."""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class MCPServer:
    """Central registry and execution router for Model Context Protocol tools."""

    def __init__(
        self,
        fs_tools: Optional[FilesystemTools] = None,
        terminal_tools: Optional[TerminalTools] = None,
        git_tools: Optional[GitTools] = None
    ):
        self.fs = fs_tools or FilesystemTools()
        self.terminal = terminal_tools or TerminalTools()
        self.git = git_tools or GitTools()

        self._tools: Dict[str, Callable[..., ToolResult]] = {}
        self._schemas: Dict[str, ToolDefinition] = {}

        self._register_default_tools()

    def _register_default_tools(self):
        """Registers all built-in filesystem, terminal, and git tools."""

        # Filesystem: read_file
        self.register_tool(
            name="read_file",
            func=self.fs.read_file,
            description="Reads the complete text content of a file within the target repository.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path from repository root (e.g. 'app/services.py')"}
                },
                "required": ["path"]
            }
        )

        # Filesystem: write_file
        self.register_tool(
            name="write_file",
            func=self.fs.write_file,
            description="Writes modified text content to a file in the target repository.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path from repository root"},
                    "content": {"type": "string", "description": "Full new text content to write"}
                },
                "required": ["path", "content"]
            }
        )

        # Filesystem: list_dir
        self.register_tool(
            name="list_dir",
            func=self.fs.list_dir,
            description="Lists all files and subdirectories inside a specific folder in the sandbox.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "default": "", "description": "Relative directory path (empty string for root)"}
                }
            }
        )

        # Filesystem: file_exists
        self.register_tool(
            name="file_exists",
            func=self.fs.file_exists,
            description="Checks if a specific file exists in the target repository.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"}
                },
                "required": ["path"]
            }
        )

        # Terminal: execute_test_command
        self.register_tool(
            name="execute_test_command",
            func=self.terminal.execute_command,
            description="Executes a sandboxed test or lint command (e.g. 'pytest tests/test_api.py').",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Allowed test command (e.g. 'pytest tests/')"}
                },
                "required": ["command"]
            }
        )

        # Git: get_diff
        self.register_tool(
            name="get_diff",
            func=self.git.get_diff,
            description="Returns current unified git diff of all modifications made by the agent.",
            parameters={
                "type": "object",
                "properties": {
                    "cached": {"type": "boolean", "default": False, "description": "Whether to check staged changes"}
                }
            }
        )

        # Git: create_task_branch
        self.register_tool(
            name="create_task_branch",
            func=self.git.create_task_branch,
            description="Creates and switches to an isolated git task branch (forge/task-<id>).",
            parameters={
                "type": "object",
                "properties": {
                    "branch_name": {"type": "string", "description": "Optional branch name"}
                }
            }
        )

        # Git: commit_changes
        self.register_tool(
            name="commit_changes",
            func=self.git.commit_changes,
            description="Commits modified files on the active isolated task branch.",
            parameters={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Descriptive commit message"}
                },
                "required": ["message"]
            }
        )

    def register_tool(
        self,
        name: str,
        func: Callable[..., ToolResult],
        description: str,
        parameters: Dict[str, Any]
    ):
        """Registers a new tool and its schema definition."""
        self._tools[name] = func
        self._schemas[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters
        )
        logger.debug(f"[MCPServer] Registered tool: '{name}'")

    def list_tools(self) -> List[ToolDefinition]:
        """Returns JSON-schemas for all registered tools."""
        return list(self._schemas.values())

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Invokes a registered tool by name with provided arguments."""
        if name not in self._tools:
            logger.error(f"[MCPServer] Unknown tool requested: '{name}'")
            return ToolResult(
                success=False,
                error=f"Tool not found: '{name}'. Available: {list(self._tools.keys())}"
            )

        logger.info(f"[MCPServer] Dispatching tool call: '{name}' with args {list(arguments.keys())}")
        try:
            return self._tools[name](**arguments)
        except TypeError as type_err:
            logger.error(f"[MCPServer] Argument mismatch for '{name}': {type_err}")
            return ToolResult(success=False, error=f"Argument mismatch: {str(type_err)}")
        except Exception as exc:
            logger.error(f"[MCPServer] Unhandled tool exception in '{name}': {exc}", exc_info=True)
            return ToolResult(success=False, error=f"Tool execution failed: {str(exc)}")


_default_mcp_server: Optional[MCPServer] = None


def get_mcp_server() -> MCPServer:
    """Returns singleton MCPServer instance."""
    global _default_mcp_server
    if _default_mcp_server is None:
        _default_mcp_server = MCPServer()
    return _default_mcp_server

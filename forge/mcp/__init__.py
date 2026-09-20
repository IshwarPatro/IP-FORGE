"""
IP FORGE: Model Context Protocol (MCP) Tooling Subsystem
Provides secure, sandboxed interfaces for Filesystem, Terminal, and Git operations.
"""

from forge.mcp.server import MCPServer, ToolResult, get_mcp_server

__all__ = ["MCPServer", "ToolResult", "get_mcp_server"]

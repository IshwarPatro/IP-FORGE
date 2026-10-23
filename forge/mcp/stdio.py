"""
IP FORGE: Standard I/O (stdio) Model Context Protocol (MCP) Server.
Implements the JSON-RPC 2.0 stdio transport protocol for seamless integration
with Claude Desktop, Cursor, Antigravity IDE, and other standard MCP clients.
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from forge.config import setup_logger
from forge.mcp.flutter_tools import FlutterMCPTools
from forge.mcp.server import MCPServer

logger = setup_logger("forge.mcp.stdio")

MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "ip-forge"
SERVER_VERSION = "0.1.0"


class StdioMCPServer:
    """
    Standard I/O MCP transport router.
    Strictly writes JSON-RPC 2.0 protocol frames to stdout and diagnostics to stderr.
    """

    def __init__(self, workspace_root: Optional[Path] = None, mcp_server: Optional[MCPServer] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        if mcp_server:
            self.server = mcp_server
        else:
            flutter_tools = FlutterMCPTools(workspace_root=self.workspace_root)
            self.server = MCPServer(flutter_tools=flutter_tools)

        self._running = False

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processes a single JSON-RPC request and returns the response dictionary."""
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params") or {}

        # Handle JSON-RPC notifications (no id -> no response)
        if req_id is None:
            if method in ("notifications/initialized", "initialized"):
                logger.info("[StdioMCP] Client initialized successfully.")
            elif method == "exit":
                self._running = False
            return None

        # Route methods
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION
                    }
                }
            }

        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            }

        elif method in ("tools/list", "list_tools"):
            tools_list = []
            for t in self.server.list_tools():
                tools_list.append({
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.parameters
                })
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": tools_list
                }
            }

        elif method in ("tools/call", "call_tool"):
            tool_name = params.get("name")
            tool_args = params.get("arguments") or {}

            if not tool_name:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32602,
                        "message": "Missing 'name' in tools/call parameters"
                    }
                }

            res = self.server.call_tool(tool_name, tool_args)
            # Failed checks still carry actionable diagnostics in output.
            content_text = res.output
            if not res.success and res.error:
                content_text = f'{res.error}\n\n{res.output}' if res.output else res.error

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": content_text
                        }
                    ],
                    "isError": not res.success
                }
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: '{method}'"
                }
            }

    def run(self):
        """Main stdio loop reading lines from stdin and outputting JSON to stdout."""
        self._running = True
        logger.info(f"[StdioMCP] Server starting (workspace: {self.workspace_root})")

        while self._running:
            line = sys.stdin.readline()
            if not line:
                break

            line_clean = line.strip()
            if not line_clean:
                continue

            try:
                request = json.loads(line_clean)
            except json.JSONDecodeError as err:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {err}"
                    }
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()
                continue

            response = self.handle_request(request)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

        logger.info("[StdioMCP] Server loop terminated.")


def run_stdio_server(workspace: Optional[Path] = None):
    """Entry point for the stdio MCP server."""
    server = StdioMCPServer(workspace_root=workspace)
    server.run()

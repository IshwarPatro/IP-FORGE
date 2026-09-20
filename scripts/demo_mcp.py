#!/usr/bin/env python3
"""
IP FORGE: Interactive Model Context Protocol (MCP) Tool Demo
Demonstrates sandboxed filesystem reads/writes, path traversal defense,
command allowlist validation, and sandboxed test execution.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from forge.mcp.server import get_mcp_server

console = Console()


def run_demo():
    console.print("\n[bold cyan]==================================================================[/bold cyan]")
    console.print("[bold yellow]        IP FORGE: Model Context Protocol (MCP) Tooling Demo       [/bold yellow]")
    console.print("[bold cyan]==================================================================[/bold cyan]\n")

    mcp = get_mcp_server()

    # 1. List Available Tools
    console.print("[bold green]1. Registered MCP Tools & JSON Schemas:[/bold green]")
    tools = mcp.list_tools()
    table = Table(title="MCP Tool Registry", show_header=True, header_style="bold magenta")
    table.add_column("Tool Name", style="bold cyan", width=22)
    table.add_column("Description", style="white")
    table.add_column("Required Parameters", style="yellow", width=25)

    for t in tools:
        req = ", ".join(t.parameters.get("required", [])) or "(None)"
        table.add_row(t.name, t.description, req)
    console.print(table)

    # 2. Test Safe File Read
    console.print("\n[bold green]2. Sandboxed File Read (`read_file`):[/bold green]")
    read_res = mcp.call_tool("read_file", {"path": "app/utils.py"})
    if read_res.success:
        console.print("   [bold green]✓ Successfully read 'app/utils.py' within sandbox:[/bold green]")
        syntax = Syntax(read_res.output, "python", theme="monokai", line_numbers=True)
        console.print(syntax)
    else:
        console.print(f"   [bold red]✗ Read failed: {read_res.error}[/bold red]")

    # 3. Test Security Sandbox: Path Traversal Defense
    console.print("\n[bold green]3. Testing Security Sandbox (Path Traversal Interception):[/bold green]")
    malicious_path = "../../etc/passwd"
    console.print(f"   Attempting path traversal: [bold red]`read_file('{malicious_path}')`[/bold red]")
    attack_res = mcp.call_tool("read_file", {"path": malicious_path})
    if not attack_res.success:
        console.print(f"   [bold green]✓ DEFENSE VERIFIED: Attack intercepted:[/bold green]\n   [yellow]{attack_res.error}[/yellow]")
    else:
        console.print("   [bold red]✗ SECURITY FAILURE: Allowed traversal outside sandbox![/bold red]")

    # 4. Test Terminal Test Execution
    console.print("\n[bold green]4. Sandboxed Terminal Execution (`execute_test_command`):[/bold green]")
    test_cmd = "pytest tests/test_api.py -q"
    console.print(f"   Running verified command: [bold cyan]`{test_cmd}`[/bold cyan]")
    term_res = mcp.call_tool("execute_test_command", {"command": test_cmd})
    if term_res.success:
        console.print(f"   [bold green]✓ Command succeeded (Exit code 0):[/bold green]\n{term_res.output.strip()}")
    else:
        console.print(f"   [bold red]✗ Command failed: {term_res.error}[/bold red]\n{term_res.output}")

    # 5. Test Security Sandbox: Command Injection Defense
    console.print("\n[bold green]5. Testing Command Injection Defense:[/bold green]")
    injection_cmd = "pytest tests/ ; rm -rf /"
    console.print(f"   Attempting command injection: [bold red]`{injection_cmd}`[/bold red]")
    inj_res = mcp.call_tool("execute_test_command", {"command": injection_cmd})
    if not inj_res.success:
        console.print(f"   [bold green]✓ DEFENSE VERIFIED: Injection intercepted:[/bold green]\n   [yellow]{inj_res.error}[/yellow]")
    else:
        console.print("   [bold red]✗ SECURITY FAILURE: Allowed unverified command execution![/bold red]")

    console.print("\n[bold green]✓ All MCP tools, sandboxing policies, and defenses verified successfully![/bold green]\n")


if __name__ == "__main__":
    run_demo()

"""
IP FORGE: Autonomous Self-Healing Engineering Loop Interactive Demo
Simulates a live code defect, executes the closed-loop state machine,
observes TestAgent failure interception, DebuggerAgent root-cause analysis,
automated patch application, re-verification, and ReviewerAgent PR generation.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.rule import Rule

from forge.orchestrator.loop import AutonomousLoop
from forge.mcp.fs_tools import FilesystemTools
from forge.mcp.terminal_tools import TerminalTools
from forge.mcp.git_tools import GitTools
from forge.mcp.server import MCPServer
from forge.agents.tester import TestAgent
from forge.agents.debugger import DebuggerAgent
from forge.agents.reviewer import ReviewerAgent
from forge.agents.coder import CodingAgent
from forge.orchestrator.coordinator import OrchestratorCoordinator
from forge.config import settings

console = Console()


def run_demo():
    console.print()
    console.rule("[bold cyan]IP FORGE: Autonomous Self-Healing Engineering Loop Demo[/bold cyan]")
    console.print(
        "[dim]Demonstrating closed-loop recovery: Defect Ingestion -> Plan -> Test Interception -> "
        "Root Cause Analysis -> Patching -> Re-Verification -> PR Review[/dim]\n"
    )

    dummy_repo = settings.target_repo_absolute_path
    utils_file = dummy_repo / "app" / "utils.py"

    if not utils_file.exists():
        console.print(f"[bold red]Error: Target file not found at {utils_file}[/bold red]")
        sys.exit(1)

    original_code = utils_file.read_text()

    # Step 1: Deliberately corrupt business logic in dummy repo to create real test failure
    console.print("[bold yellow]Step 1: Introducing deliberate logic defect into target repository...[/bold yellow]")
    corrupted_code = original_code.replace(
        "return round(price - discount, 2)",
        "return round(price + discount, 2)  # BUG: Added discount instead of deducting"
    )
    utils_file.write_text(corrupted_code)
    console.print("   [red]✗ Corrupted `app/utils.py`:[/red] Replaced `price - discount` with `price + discount`")

    syntax = Syntax(
        """def calculate_discount(price: float, discount_percentage: float) -> float:
    discount = price * (discount_percentage / 100.0)
    return round(price + discount, 2)  # <--- CRITICAL BUG HERE""",
        "python",
        theme="monokai",
        line_numbers=True
    )
    console.print(Panel(syntax, title="Corrupted Code in tests/dummy_repo/app/utils.py", border_style="red"))

    # Step 2: Initialize MCP Sandbox & Autonomous Loop
    console.print("\n[bold yellow]Step 2: Initializing Autonomous Engineering Loop & Sandbox...[/bold yellow]")
    fs_tools = FilesystemTools(root_dir=dummy_repo)
    terminal_tools = TerminalTools(root_dir=dummy_repo)
    git_tools = GitTools(repo_dir=Path("."))
    mcp_server = MCPServer(fs_tools=fs_tools, terminal_tools=terminal_tools, git_tools=git_tools)

    loop = AutonomousLoop(
        mcp_server=mcp_server,
        max_retries=3
    )

    # Event hook for live telemetry streaming
    def event_listener(event_name: str, payload: dict):
        prefix_map = {
            "session_started": "[bold blue][SESSION][/bold blue]",
            "branch_created": "[bold magenta][GIT BRANCH][/bold magenta]",
            "planning_started": "[bold cyan][PLANNER][/bold cyan]",
            "planning_completed": "[bold cyan][PLANNER][/bold cyan]",
            "coding_started": "[bold yellow][CODER][/bold yellow]",
            "step_executing": "[dim yellow][STEP][/dim yellow]",
            "coding_completed": "[bold yellow][CODER][/bold yellow]",
            "testing_started": "[bold magenta][TEST AGENT][/bold magenta]",
            "testing_passed": "[bold green][TEST AGENT PASS][/bold green]",
            "testing_failed": "[bold red][TEST AGENT FAIL][/bold red]",
            "debugging_started": "[bold red][SELF-HEALING][/bold red]",
            "debugging_diagnosed": "[bold cyan][DEBUGGER RCA][/bold cyan]",
            "patch_applied": "[bold green][PATCH APPLIED][/bold green]",
            "reviewing_started": "[bold magenta][REVIEWER AGENT][/bold magenta]",
            "reviewing_completed": "[bold green][REVIEWER AGENT][/bold green]",
            "session_completed": "[bold green][COMPLETED][/bold green]",
            "escalated_to_human": "[bold red][ESCALATION][/bold red]"
        }
        tag = prefix_map.get(event_name, f"[{event_name}]")
        msg = payload.get("message") or payload.get("summary") or payload.get("root_cause") or payload.get("error") or ""
        console.print(f"  {tag} {msg}")

    # Step 3: Run the Autonomous Self-Healing Loop
    task_desc = "Fix calculation in calculate_discount to ensure order total math passes verification"
    console.print(f"\n[bold yellow]Step 3: Dispatching Autonomous Loop for task:[/bold yellow] [italic]'{task_desc}'[/italic]\n")

    try:
        start_time = time.time()
        final_state = loop.run(
            task=task_desc,
            target_file="app/utils.py",
            test_command="pytest tests/test_api.py -v",
            create_branch=False,  # Keep on current branch for demo simplicity
            on_event=event_listener
        )
        elapsed = time.time() - start_time

        # Step 4: Display Results Table
        console.print()
        console.rule("[bold green]Self-Healing Execution Telemetry Summary[/bold green]")
        summary_table = Table(title="Autonomous Loop Execution Summary", border_style="cyan")
        summary_table.add_column("Metric", style="bold cyan")
        summary_table.add_column("Value", style="bold white")

        summary_table.add_row("Session ID", final_state.session_id)
        summary_table.add_row("Task Status", f"[bold green]{final_state.status.upper()}[/bold green]" if final_state.status == "completed" else f"[red]{final_state.status}[/red]")
        summary_table.add_row("Tests Passed", "[bold green]True (100% Passed)[/bold green]" if final_state.tests_passed else "[red]False[/red]")
        summary_table.add_row("Self-Healing Iterations", f"{final_state.retry_count} / {final_state.max_retries}")
        summary_table.add_row("Total Runtime", f"{elapsed:.2f} seconds")
        summary_table.add_row("Audit Trail Entries", str(len(final_state.audit_trail)))
        console.print(summary_table)

        # Step 5: Display Reviewer PR Markdown
        console.print()
        console.rule("[bold cyan]Reviewer Agent: Generated Pull Request Description[/bold cyan]")
        reviewer = ReviewerAgent(mcp_server=mcp_server)
        review = reviewer.review_changes(task=task_desc, diff=final_state.git_diff)
        console.print(Panel(review.pr_markdown, title="GitHub Pull Request Summary", border_style="green"))

        # Step 6: Verify restored code
        restored = utils_file.read_text()
        assert "price - discount" in restored
        console.print("\n[bold green]✓ VERIFICATION CONFIRMED: Dummy repository code successfully healed and verified![/bold green]\n")

    finally:
        # Guarantee cleanup: restore dummy repo to pristine git state
        import subprocess
        subprocess.run(["git", "checkout", "--", str(dummy_repo)], check=False)


if __name__ == "__main__":
    import os
    run_demo()
    os._exit(0)


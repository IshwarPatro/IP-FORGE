#!/usr/bin/env python3
"""
IP FORGE: Interactive Planner & Orchestrator Demo
Tests the multi-agent reasoning flow:
Task -> Architecture Agent (AST RAG) -> Planner Agent (JSON DAG Plan).
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from forge.orchestrator.coordinator import get_coordinator

console = Console()


def run_demo():
    console.print("\n[bold cyan]==================================================================[/bold cyan]")
    console.print("[bold yellow]        IP FORGE: Multi-Agent Reasoning & Planning Demo           [/bold yellow]")
    console.print("[bold cyan]==================================================================[/bold cyan]\n")

    # Allow custom task from command line or use a default
    default_task = "Add pagination parameters (limit: int = 10, offset: int = 0) to get_all_products in catalog service and update API route"
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else default_task

    console.print(Panel(f"[bold green]Target Engineering Task:[/bold green]\n[bold white]{task}[/bold white]", border_style="cyan"))

    coordinator = get_coordinator()
    
    console.print("\n[bold magenta]1. Architecture Agent investigating codebase via AST RAG...[/bold magenta]")
    context = coordinator.architect.investigate_task(task, top_k=4)
    
    console.print(f"   ✓ Identified [bold cyan]{len(context.relevant_symbols)}[/bold cyan] AST symbols across [bold green]{len(context.relevant_files)}[/bold green] files:")
    for f in context.relevant_files:
        console.print(f"     - [yellow]{f}[/yellow]")

    console.print("\n[bold magenta]2. Planner Agent formulating structured execution DAG...[/bold magenta]")
    plan = coordinator.planner.create_plan(task, context)
    
    console.print(f"\n[bold green]Architectural Summary:[/bold green]\n{plan.architectural_summary}\n")

    # Display Plan Steps in a Rich Table
    table = Table(title="Generated Multi-Agent Engineering Plan (DAG)", show_header=True, header_style="bold cyan")
    table.add_column("Step #", style="bold yellow", width=8, justify="center")
    table.add_column("Action", style="bold magenta", width=14)
    table.add_column("Target File", style="green", width=22)
    table.add_column("Symbols Involved", style="cyan", width=26)
    table.add_column("Action Description", style="white")

    for s in plan.steps:
        symbols_str = ", ".join(s.symbols_involved) if s.symbols_involved else "-"
        table.add_row(
            str(s.step_number),
            s.action.upper(),
            s.target_file,
            symbols_str,
            s.description
        )

    console.print(table)
    console.print(f"\n[bold green]Verification Strategy:[/bold green] [italic white]{plan.verification_strategy}[/italic white]\n")
    console.print("[bold green]✓ Planning cycle complete! Plan is ready for Coding Agent execution.[/bold green]\n")


if __name__ == "__main__":
    run_demo()

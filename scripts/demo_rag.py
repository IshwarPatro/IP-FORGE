#!/usr/bin/env python3
"""
IP FORGE: Interactive RAG & AST Demo Script
Run this script to test codebase intelligence, symbol parsing, and semantic search directly in your terminal.
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

from forge.rag.ast_parser import ASTParser
from forge.rag.vector_store import get_vector_store

console = Console()


def run_demo():
    console.print("\n[bold cyan]==================================================================[/bold cyan]")
    console.print("[bold yellow]           IP FORGE: Codebase Intelligence & AST RAG Demo          [/bold yellow]")
    console.print("[bold cyan]==================================================================[/bold cyan]\n")

    target_repo = Path("tests/dummy_repo")
    console.print(f"[bold green]1. Traversing and parsing AST from:[/bold green] [underline]{target_repo.resolve()}[/underline]...\n")

    parser = ASTParser()
    summaries = parser.parse_directory(target_repo)

    # Display Parsed Symbols in a Rich Table
    table = Table(title="Extracted Abstract Syntax Tree (AST) Symbols", show_header=True, header_style="bold magenta")
    table.add_column("Type", style="cyan", width=10)
    table.add_column("Symbol Name", style="bold white", width=25)
    table.add_column("File Path", style="green", width=22)
    table.add_column("Lines", style="yellow", width=12)
    table.add_column("Signature Preview", style="dim white")

    all_symbols = []
    for s in summaries:
        for sym in s.symbols:
            all_symbols.append(sym)
            display_name = f"{sym.parent_class}.{sym.name}" if sym.parent_class else sym.name
            lines = f"L{sym.start_line}-L{sym.end_line}"
            sig_preview = (sym.signature[:45] + "...") if len(sym.signature) > 45 else sym.signature
            table.add_row(sym.symbol_type.upper(), display_name, sym.file_path, lines, sig_preview)

    console.print(table)
    console.print(f"\n[bold green]Total Discrete Symbols Parsed:[/bold green] [bold cyan]{len(all_symbols)}[/bold cyan]\n")

    # Ingest into ChromaDB
    console.print("[bold green]2. Indexing symbols into ChromaDB Vector Store...[/bold green]")
    vector_store = get_vector_store()
    count = vector_store.index_repository(target_repo)
    console.print(f"[bold green]✓ Successfully embedded and indexed {count} symbols into ChromaDB![/bold green]\n")

    # Sample Queries Demo
    sample_queries = [
        "Where is discount percentage calculated?",
        "How is stock inventory deducted for products?",
        "What are the FastAPI endpoints for order creation?"
    ]

    console.print("[bold green]3. Running Semantic Architecture Queries:[/bold green]\n")
    for q in sample_queries:
        console.print(Panel(f"[bold white]Query: \"{q}\"[/bold white]", border_style="cyan"))
        results = vector_store.query_codebase(q, top_k=2)
        
        for idx, match in enumerate(results, 1):
            console.print(
                f"  [bold yellow]Match #{idx}[/bold yellow] | "
                f"[bold cyan]{match.symbol_name}[/bold cyan] ({match.symbol_type}) | "
                f"File: [bold green]{match.file_path}:{match.start_line}-{match.end_line}[/bold green] | "
                f"Score: [magenta]{match.similarity_score:.4f}[/magenta]"
            )
            syntax = Syntax(match.snippet, "python", theme="monokai", line_numbers=True, start_line=match.start_line)
            console.print(syntax)
            console.print()

    console.print("[bold green]✓ Demo completed successfully! All AST & Vector RAG components operational.[/bold green]\n")


if __name__ == "__main__":
    run_demo()

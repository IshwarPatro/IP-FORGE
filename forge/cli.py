"""
IP FORGE: Command-Line Interface for Flutter Review and Inspection.
Provides `doctor`, `inspect`, `check`, and `report` commands for developers and CI/CD pipelines.
"""
import argparse
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forge.flutter.detect import detect_flutter_project
from forge.flutter.policy import load_policy
from forge.flutter.runner import resolve_flutter_bin, run_review
from forge.reports.formatter import to_json, to_markdown

console = Console()
VERSION = "0.2.0a1"


def cmd_doctor(args: argparse.Namespace) -> int:
    """Checks the local environment and Flutter toolchain prerequisites."""
    console.print(Panel("[bold cyan]IP FORGE System Doctor[/bold cyan]", expand=False))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component", style="bold white", width=22)
    table.add_column("Status", width=12)
    table.add_column("Details")

    # Python
    table.add_row("Python Runtime", "✅ Available", f"{sys.version.split()[0]} ({sys.executable})")

    # Flutter binary
    flutter_bin = resolve_flutter_bin(getattr(args, "flutter_bin", None))
    if flutter_bin:
        table.add_row("Flutter SDK", "✅ Found", flutter_bin)
    else:
        table.add_row("Flutter SDK", "❌ Missing", "Not found on PATH or FLUTTER_ROOT")

    # Target directory check
    target = Path(args.path).resolve()
    info = detect_flutter_project(target)
    if info.is_flutter:
        table.add_row("Target Project", "✅ Flutter App", f"{info.name or 'unknown'} ({target})")
        table.add_row("State Management", "ℹ️ Detected", f"{info.primary_state_adapter} ({', '.join(info.state_packages) or 'native'})")
    else:
        table.add_row("Target Project", "⚠️ Non-Flutter", info.error or str(target))

    console.print(table)
    return 0 if flutter_bin else 2


def cmd_inspect(args: argparse.Namespace) -> int:
    """Introspects a Flutter project directory and outputs architectural metadata."""
    target = Path(args.path).resolve()
    info = detect_flutter_project(target)

    if not info.is_flutter:
        console.print(f"[bold red]Error:[/bold red] {info.error or 'Not a Flutter project'}")
        return 1

    table = Table(title=f"Flutter Project: {info.name or target.name}", show_header=True, header_style="bold cyan")
    table.add_column("Attribute", style="bold white", width=24)
    table.add_column("Value")

    table.add_row("Project Name", info.name or "(unnamed)")
    table.add_row("Version", info.version or "(unspecified)")
    table.add_row("Dart SDK Constraint", info.dart_sdk or "(unspecified)")
    table.add_row("Flutter SDK Constraint", info.flutter_sdk or "(unspecified)")
    table.add_row("Primary State Adapter", f"[bold green]{info.primary_state_adapter}[/bold green]")
    table.add_row("State Packages", ", ".join(info.state_packages) or "(none - framework native)")
    table.add_row("Cache Packages", ", ".join(info.cache_packages) or "(none)")
    table.add_row("Platforms", ", ".join(info.platforms) or "(none detected)")
    table.add_row("Entry Points", ", ".join(info.entry_points) or "(none)")
    table.add_row("Test Files", f"{len(info.test_files)} files found" if info.has_tests else "No tests found")
    table.add_row("Analysis Options", "Present" if info.has_analysis_options else "Missing")
    table.add_row("Lockfile (pubspec.lock)", "Present" if info.has_lockfile else "Missing")

    console.print(table)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Executes policy-governed checks against the target Flutter project."""
    target = Path(args.path).resolve()
    policy = load_policy(target)

    report = run_review(target, policy=policy, flutter_bin=getattr(args, "flutter_bin", None))
    exit_code = report.exit_code(policy)

    if args.json:
        print(to_json(report))
    elif args.markdown:
        print(to_markdown(report, policy=policy))
    else:
        # Rich terminal presentation
        md = to_markdown(report, policy=policy)
        console.print(md)

    return exit_code


def cmd_mcp(args: argparse.Namespace) -> int:
    """Starts the standard I/O (stdio) MCP server for agent integration."""
    from forge.mcp.public_server import run_stdio_server
    target = Path(args.workspace).resolve()
    run_stdio_server(workspace=target, allow_execution=args.allow_execution)
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="forge",
        description="IP FORGE: Flutter Architecture and Acceptance Review Engine",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Doctor
    p_doc = subparsers.add_parser("doctor", help="Check local environment and Flutter SDK availability")
    p_doc.add_argument("path", nargs="?", default=".", help="Target project path")
    p_doc.add_argument("--flutter-bin", help="Custom path to flutter binary")
    p_doc.set_defaults(func=cmd_doctor)

    # Inspect
    p_insp = subparsers.add_parser("inspect", help="Inspect a Flutter project's dependencies and state management")
    p_insp.add_argument("path", nargs="?", default=".", help="Target project path")
    p_insp.set_defaults(func=cmd_inspect)

    # Check
    p_chk = subparsers.add_parser("check", help="Run policy-governed acceptance checks on a Flutter project")
    p_chk.add_argument("path", nargs="?", default=".", help="Target project path")
    p_chk.add_argument("--flutter-bin", help="Custom path to flutter binary")
    p_chk.add_argument("--json", action="store_true", help="Output results as JSON")
    p_chk.add_argument("--markdown", action="store_true", help="Output results as Markdown")
    p_chk.set_defaults(func=cmd_check)

    # MCP stdio server
    p_mcp = subparsers.add_parser("mcp", help="Run the Model Context Protocol (MCP) server over standard I/O")
    p_mcp.add_argument("--workspace", default=".", help="Workspace root directory (default '.')")
    p_mcp.add_argument("--allow-execution", action="store_true", help="Enable Flutter commands for trusted projects (not sandboxed)")
    p_mcp.set_defaults(func=cmd_mcp)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

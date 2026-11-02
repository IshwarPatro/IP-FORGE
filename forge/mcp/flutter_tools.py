"""
IP FORGE: Flutter Model Context Protocol (MCP) Tools.
Exposes read-only inspection and policy-governed check execution to MCP agents.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
from forge.mcp.fs_tools import ToolResult
from forge.flutter.detect import detect_flutter_project
from forge.flutter.policy import ReviewPolicy, load_policy
from forge.flutter.runner import run_review
from forge.reports.formatter import to_markdown, to_json
from forge.config import setup_logger

logger = setup_logger("forge.mcp.flutter_tools")


class FlutterMCPTools:
    """Provides workspace-confined inspection and explicit Flutter check execution."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self._reports: Dict[Path, ToolResult] = {}

    def _resolve_dir(self, directory: Optional[str] = None) -> Path:
        if not directory or directory.strip() in (".", ""):
            return self.workspace_root
        target = Path(directory)
        if not target.is_absolute():
            target = (self.workspace_root / target).resolve()
        target = target.resolve()
        if not target.is_relative_to(self.workspace_root):
            raise PermissionError("Flutter project must be inside the configured workspace")
        return target

    def inspect_flutter_project(self, directory: str = ".") -> ToolResult:
        """
        Inspects the Flutter/Dart project structure, detected state packages,
        platforms, and existing test suites.
        """
        target = self._resolve_dir(directory)
        logger.info(f"[FlutterMCPTools] Inspecting project at {target}")
        info = detect_flutter_project(target)
        dump = info.model_dump()
        return ToolResult(
            success=info.is_flutter,
            output=to_json_str(dump),
            error=info.error if not info.is_flutter else None,
            metadata=dump,
        )

    def run_flutter_checks(
        self,
        directory: str = ".",
        checks: Optional[List[str]] = None,
        flutter_bin: Optional[str] = None,
    ) -> ToolResult:
        """
        Executes configured static analysis and widget/unit checks on the Flutter project.
        """
        target = self._resolve_dir(directory)
        logger.info(f"[FlutterMCPTools] Running checks at {target}")
        policy = load_policy(target)
        if checks is not None:
            # Validate overrides rather than bypassing Pydantic via assignment.
            override = ReviewPolicy(required_checks=checks)
            policy.required_checks = override.required_checks
        self._reports.pop(target, None)

        report = run_review(target, policy=policy, flutter_bin=flutter_bin)
        exit_code = report.exit_code(policy)
        md = to_markdown(report, policy=policy)

        result = ToolResult(
            success=(exit_code == 0),
            output=md,
            error=None if exit_code == 0 else f"Review exited with code {exit_code}",
            metadata={"exit_code": exit_code, "report": report.model_dump()},
        )
        self._reports[target] = result.model_copy(deep=True)
        return result

    def get_report(self, directory: str = ".") -> ToolResult:
        """
        Retrieves the latest review report in Markdown and JSON format.
        """
        target = self._resolve_dir(directory)
        result = self._reports.get(target)
        if result is None:
            return ToolResult(success=False, error="No report in this session. Run run_flutter_checks first.")
        return result.model_copy(deep=True)


def to_json_str(data: Dict[str, Any]) -> str:
    import json
    return json.dumps(data, indent=2)

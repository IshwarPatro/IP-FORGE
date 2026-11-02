"""
IP FORGE: Flutter Test and Analysis Runner.
Executes Flutter toolchain commands (analyze, test) and converts output
into structured, truthful CheckResult and ReviewReport objects.
"""
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from forge.flutter.detect import detect_flutter_project
from forge.flutter.policy import ReviewPolicy, load_policy
from forge.reports.models import CheckResult, Finding, ReviewReport

# Match standard Flutter analyzer output format:
#   info • Message • lib/main.dart:14:5 • avoid_print
ANALYZER_LINE_RE = re.compile(
    r"^\s*(info|warning|error)\s+[•\-]\s+(.+?)\s+[•\-]\s+([^:\s]+):(\d+)(?::\d+)?\s+[•\-]\s+(\S+)",
    re.IGNORECASE,
)


def resolve_flutter_bin(custom_path: Optional[str] = None) -> Optional[str]:
    """
    Resolves the flutter executable from custom path, env var, or PATH.
    """
    candidates = [
        custom_path,
        os.environ.get("FLUTTER_BIN"),
        os.environ.get("FLUTTER_ROOT") and f"{os.environ.get('FLUTTER_ROOT')}/bin/flutter",
        shutil.which("flutter"),
    ]
    for c in candidates:
        if c and Path(c).is_file() and os.access(c, os.X_OK):
            return str(Path(c).resolve())
    return None


def run_flutter_analyze(
    project_path: Path | str,
    flutter_bin: Optional[str] = None,
    timeout_sec: int = 60,
) -> CheckResult:
    """
    Runs `flutter analyze` against the target Flutter project.
    """
    project_dir = Path(project_path).resolve()
    bin_path = resolve_flutter_bin(flutter_bin)

    if not bin_path:
        return CheckResult(
            name="analyze",
            status="unsupported",
            summary="Flutter binary not found on system PATH or environment",
        )

    try:
        proc = subprocess.run(
            [bin_path, "analyze", "--no-fatal-warnings"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="analyze",
            status="failed",
            summary=f"flutter analyze timed out after {timeout_sec} seconds",
            findings=[
                Finding(
                    rule_id="timeout",
                    severity="error",
                    message=f"Analyzer timed out after {timeout_sec}s",
                    evidence="Command timed out",
                    evidence_kind="reproduced_failure",
                )
            ],
        )
    except Exception as exc:
        return CheckResult(
            name="analyze",
            status="failed",
            summary=f"Failed to execute flutter analyze: {exc}",
            findings=[
                Finding(
                    rule_id="process.error",
                    severity="error",
                    message=str(exc),
                    evidence="Execution error",
                    evidence_kind="reproduced_failure",
                )
            ],
        )

    combined_output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    findings: List[Finding] = []

    for line in combined_output.splitlines():
        match = ANALYZER_LINE_RE.match(line)
        if match:
            severity_raw, message, file_rel, line_no, rule_id = match.groups()
            severity = severity_raw.lower()
            if severity not in ("error", "warning", "info"):
                severity = "info"
            findings.append(
                Finding(
                    rule_id=rule_id,
                    severity=severity,
                    message=message.strip(),
                    evidence=line.strip(),
                    evidence_kind="static_inference",
                    file=file_rel,
                    line=int(line_no),
                )
            )

    has_errors = any(f.severity == "error" for f in findings) or proc.returncode != 0
    if not has_errors and len(findings) == 0:
        return CheckResult(
            name="analyze",
            status="passed",
            summary="No analyzer issues found",
            findings=[],
        )
    elif has_errors:
        return CheckResult(
            name="analyze",
            status="failed",
            summary=f"Analyzer reported {len(findings)} issue(s) with errors",
            findings=findings,
        )
    else:
        # Warnings or info only
        return CheckResult(
            name="analyze",
            status="passed",
            summary=f"Analyzer passed with {len(findings)} advisory item(s)",
            findings=findings,
        )


def run_flutter_test(
    project_path: Path | str,
    test_target: Optional[str] = None,
    flutter_bin: Optional[str] = None,
    timeout_sec: int = 120,
) -> CheckResult:
    """
    Runs `flutter test` against the target Flutter project or specific test file.
    """
    project_dir = Path(project_path).resolve()
    bin_path = resolve_flutter_bin(flutter_bin)

    if not bin_path:
        return CheckResult(
            name="unit_widget",
            status="unsupported",
            summary="Flutter binary not found on system PATH or environment",
        )

    test_dir = project_dir / "test"
    if not test_dir.is_dir() or not any(test_dir.rglob("*_test.dart")):
        return CheckResult(
            name="unit_widget",
            status="not_applicable",
            summary="No tests found in test/ directory",
            findings=[],
        )

    cmd = [bin_path, "test"]
    if test_target:
        cmd.append(test_target)

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="unit_widget",
            status="failed",
            summary=f"flutter test timed out after {timeout_sec} seconds",
            findings=[
                Finding(
                    rule_id="timeout",
                    severity="error",
                    message=f"Test suite timed out after {timeout_sec}s",
                    evidence="Command timed out",
                    evidence_kind="reproduced_failure",
                )
            ],
        )
    except Exception as exc:
        return CheckResult(
            name="unit_widget",
            status="failed",
            summary=f"Failed to execute flutter test: {exc}",
            findings=[
                Finding(
                    rule_id="process.error",
                    severity="error",
                    message=str(exc),
                    evidence="Execution error",
                    evidence_kind="reproduced_failure",
                )
            ],
        )

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    output = stdout + "\n" + stderr

    if proc.returncode == 0:
        return CheckResult(
            name="unit_widget",
            status="passed",
            summary="All tests passed successfully",
            findings=[],
        )

    # Parse failure details
    findings: List[Finding] = []
    failure_lines = [
        line.strip()
        for line in output.splitlines()
        if "Expected:" in line or "Actual:" in line or "══╡ EXCEPTION" in line or "Test failed" in line
    ]
    evidence_snippet = "\n".join(failure_lines[:10]) if failure_lines else output[:500]

    findings.append(
        Finding(
            rule_id="test.assertion_failure",
            severity="error",
            message="One or more tests failed during execution",
            evidence=evidence_snippet,
            evidence_kind="reproduced_failure",
        )
    )

    return CheckResult(
        name="unit_widget",
        status="failed",
        summary="One or more Flutter widget/unit tests failed",
        findings=findings,
    )


def run_review(
    workspace: Path | str,
    policy: Optional[ReviewPolicy] = None,
    flutter_bin: Optional[str] = None,
) -> ReviewReport:
    """
    Orchestrates policy-driven review and checks for a Flutter workspace.
    """
    ws = Path(workspace).resolve()
    active_policy = policy or load_policy(ws)
    unsupported = active_policy.unsupported_features()
    if unsupported:
        return ReviewReport(workspace=str(ws), checks=[CheckResult(
            name="policy_support", status="unsupported",
            summary="This alpha cannot enforce: " + "; ".join(unsupported),
        )])
    info = detect_flutter_project(ws)

    if not info.is_flutter:
        return ReviewReport(
            workspace=str(ws),
            checks=[
                CheckResult(
                    name="detect",
                    status="unsupported",
                    summary=info.error or f"Target directory is not a Flutter project: {ws}",
                    findings=[],
                )
            ],
        )

    checks: List[CheckResult] = []

    for check_name in active_policy.required_checks:
        if check_name == "analyze":
            checks.append(run_flutter_analyze(ws, flutter_bin=flutter_bin))
        elif check_name in ("unit_widget", "test"):
            result = run_flutter_test(ws, flutter_bin=flutter_bin)
            checks.append(result.model_copy(update={"name": check_name}))
        else:
            checks.append(
                CheckResult(
                    name=check_name,
                    status="unsupported",
                    summary=f"Check '{check_name}' is not supported in this version",
                    findings=[],
                )
            )

    return ReviewReport(
        workspace=str(ws),
        checks=checks,
    )

"""
IP FORGE: Review Report Formatting (Markdown & JSON).
Produces standardized CI summary comments and machine-readable output.
"""
import json
from typing import Optional
from forge.flutter.policy import ReviewPolicy
from forge.reports.models import ReviewReport


def to_json(report: ReviewReport, indent: int = 2) -> str:
    """Formats ReviewReport into standardized JSON."""
    return json.dumps(report.model_dump(), indent=indent)


def to_markdown(report: ReviewReport, policy: Optional[ReviewPolicy] = None) -> str:
    """
    Renders ReviewReport as a clean GitHub / GitLab PR comment in Markdown.
    """
    pol = policy or ReviewPolicy()
    code = report.exit_code(pol)

    status_badge = "✅ **Passed**" if code == 0 else ("❌ **Policy Failed**" if code == 1 else "⚠️ **Incomplete / Missing Checks**")

    lines = [
        "# Flutter Review Report",
        "",
        f"- **Status:** {status_badge} (Exit code: `{code}`)",
        f"- **Workspace:** `{report.workspace}`",
    ]

    if report.tested_revision:
        lines.append(f"- **Revision:** `{report.tested_revision}`")

    lines.extend([
        "",
        "## Checks Summary",
        "",
        "| Check | Status | Summary | Findings |",
        "| :--- | :---: | :--- | :---: |",
    ])

    total_findings = 0
    all_findings = []

    for check in report.checks:
        icon = {
            "passed": "✅",
            "failed": "❌",
            "not_run": "⏸️",
            "unsupported": "❓",
            "inconclusive": "⚠️",
            "not_applicable": "➖",
            "cancelled": "🛑",
        }.get(check.status, "•")

        count = len(check.findings)
        total_findings += count
        for f in check.findings:
            all_findings.append((check.name, f))

        lines.append(f"| `{check.name}` | {icon} `{check.status}` | {check.summary} | {count} |")

    if all_findings:
        lines.extend([
            "",
            "## Detected Findings",
            "",
            "| Rule ID | Severity | File:Line | Message | Evidence |",
            "| :--- | :---: | :--- | :--- | :--- |",
        ])
        for check_name, finding in all_findings:
            loc = f"`{finding.file}:{finding.line}`" if finding.file and finding.line else (f"`{finding.file}`" if finding.file else "-")
            msg = finding.message.replace("|", "\\|")
            evidence = finding.evidence.replace("|", "\\|")[:80]
            lines.append(f"| `{finding.rule_id}` | `{finding.severity}` | {loc} | {msg} | `{evidence}` |")

    lines.append("")
    return "\n".join(lines)

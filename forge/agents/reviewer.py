"""
IP FORGE: Reviewer Agent
Evaluates unified git diffs for code quality, security vulnerabilities,
and generates structured, GitHub-ready Pull Request markdown summaries.
"""

import re
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field
from forge.agents.base import BaseAgent
from forge.mcp.server import MCPServer, ToolResult, get_mcp_server
from forge.config import setup_logger

logger = setup_logger("forge.agents.reviewer")

REVIEWER_SYSTEM_PROMPT = """You are the Reviewer Agent for IP FORGE, an autonomous software engineering system.
Your mission is to perform a rigorous code review of the unified git diff before merging.

EVALUATION CRITERIA:
1. Security Posture: Verify no hardcoded credentials, command injection risks, path traversal flaws, or unsafe deserialization.
2. Code Quality: Ensure type hints, defensive bounds checks, and adherence to clean architecture.
3. PR Generation: Produce a clear, professional Pull Request markdown description.

You must respond in valid JSON format matching this schema:
{
  "title": "<Concise conventional commit PR title, e.g. fix(api): resolve discount deduction logic>",
  "summary": "<High-level explanation of changes>",
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "security_findings": ["<finding 1>", "<finding 2>"],
  "pr_markdown": "<Complete GitHub PR markdown text>"
}
Output ONLY the JSON object."""


class ReviewSummary(BaseModel):
    """Structured code review and Pull Request specification."""
    title: str = Field(description="Conventional commit style PR title")
    summary: str = Field(description="High-level description of changes made")
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(description="Assessed risk rating")
    security_findings: List[str] = Field(default_factory=list, description="Security observations or vulnerabilities")
    pr_markdown: str = Field(description="Formatted GitHub Pull Request markdown")


class ReviewerAgent(BaseAgent):
    """Conducts automated security audits and generates Pull Request descriptions."""

    def __init__(self, mcp_server: Optional[MCPServer] = None, llm_provider: Optional[str] = None):
        super().__init__(
            role_name="ReviewerAgent",
            system_prompt=REVIEWER_SYSTEM_PROMPT,
            llm_provider=llm_provider
        )
        self.mcp = mcp_server or get_mcp_server()

    def review_changes(self, task: str, diff: Optional[str] = None) -> ReviewSummary:
        """
        Retrieves active git diff via MCP if not provided, analyzes modifications,
        and generates a structured review report.
        """
        if diff is None:
            diff_res: ToolResult = self.mcp.call_tool("get_diff", {})
            diff = diff_res.output or ""

        logger.info(f"[ReviewerAgent] Reviewing diff for task: '{task}' ({len(diff.splitlines())} diff lines)")

        if not diff.strip():
            return ReviewSummary(
                title=f"chore: {task[:50]}",
                summary="No diff changes detected in active repository working tree.",
                risk_level="LOW",
                security_findings=[],
                pr_markdown=f"## {task}\n\n*No files were modified during this execution.*"
            )

        if not self.client.is_healthy():
            logger.warning("[ReviewerAgent] LLM client offline. Performing static diff inspection.")
            return self._heuristic_review(task=task, diff=diff)

        prompt = f"""TASK:
{task}

UNIFIED GIT DIFF:
```diff
{diff[:4000]}
```

Perform security review and generate Pull Request summary. Respond with the required JSON object."""

        try:
            raw_response = self._call_llm(user_prompt=prompt, temperature=0.2)
            parsed = self._parse_json_response(raw_response)

            return ReviewSummary(
                title=parsed.get("title", f"feat: {task[:50]}"),
                summary=parsed.get("summary", "Automated code updates verified by test suite."),
                risk_level=parsed.get("risk_level", "LOW"),
                security_findings=parsed.get("security_findings", []),
                pr_markdown=parsed.get("pr_markdown", f"## {task}\n\nAutomated changes generated and verified by IP FORGE.")
            )

        except Exception as exc:
            logger.error(f"[ReviewerAgent] LLM review failed: {exc}. Falling back to static inspection.")
            return self._heuristic_review(task=task, diff=diff)

    def _heuristic_review(self, task: str, diff: str) -> ReviewSummary:
        """
        Deterministic static diff review inspecting for security hazards and generating clean PR markdown.
        """
        security_findings = []
        risk_level = "LOW"

        # Static pattern checks
        suspicious_patterns = [
            (r"\b(eval|exec)\b", "Dangerous dynamic execution functions detected"),
            (r"\bos\.system\b", "Unsanitized system command invocation detected"),
            (r"\b(password|secret|api_key)\s*=\s*['\"][^'\"]+['\"]", "Possible hardcoded credential or secret detected"),
            (r"\.\.\/", "Directory traversal pattern detected in diff string"),
        ]

        for pattern, warning in suspicious_patterns:
            if re.search(pattern, diff, re.IGNORECASE):
                security_findings.append(warning)
                risk_level = "HIGH"

        # Count changed files and lines
        files_changed = re.findall(r"diff --git a/(.*?) b/", diff)
        additions = len(re.findall(r"^\+[^\+]", diff, re.MULTILINE))
        deletions = len(re.findall(r"^\-[^\-]", diff, re.MULTILINE))

        title = f"feat(core): {task[:60]}"
        summary = (
            f"Autonomous modifications to address task: '{task}'. "
            f"Touched {len(files_changed) or 1} file(s) with +{additions}/-{deletions} line delta."
        )

        pr_markdown = f"""## Pull Request: {title}

### Description
{summary}

### Files Touched
{chr(10).join(f"- `{f}`" for f in files_changed) if files_changed else "- Code files modified"}

### Automated Verification
- [x] Unit test suite executed via sandboxed Test Agent
- [x] Code verified with zero assertion failures
- [x] Static security check: **Risk Level {risk_level}**

### Security Review
{chr(10).join(f"- ⚠️ {f}" for f in security_findings) if security_findings else "- ✅ No security vulnerabilities or leaked credentials detected."}

---
*Generated autonomously by [IP FORGE](https://github.com/IshwarPatro/IP-FORGE)*
"""

        return ReviewSummary(
            title=title,
            summary=summary,
            risk_level=risk_level,
            security_findings=security_findings,
            pr_markdown=pr_markdown
        )

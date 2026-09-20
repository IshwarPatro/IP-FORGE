"""
IP FORGE: Test Agent
Executes sandboxed test suites via MCP, evaluates test pass/fail status,
and parses stdout/stderr into structured failure reports with stack traces.
"""

import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from forge.agents.base import BaseAgent
from forge.mcp.server import MCPServer, ToolResult, get_mcp_server
from forge.config import setup_logger

logger = setup_logger("forge.agents.tester")

TESTER_SYSTEM_PROMPT = """You are the Test Agent for IP FORGE, an autonomous software engineering system.
Your mission is to execute test suites, analyze test output, and parse failures into actionable diagnostic reports.
You strictly distinguish between genuine business logic failures, syntax errors, and test suite misconfigurations."""


class TestRunResult(BaseModel):
    """Structured report of test execution telemetry and failure diagnosis."""
    __test__ = False
    passed: bool = Field(description="True if all tests passed with returncode 0")
    exit_code: int = Field(description="Process exit code from test runner")
    passed_count: int = Field(default=0, description="Total number of passed tests")
    failed_count: int = Field(default=0, description="Total number of failed tests")
    warning_count: int = Field(default=0, description="Total number of captured warnings")
    duration_seconds: float = Field(default=0.0, description="Total test execution duration in seconds")
    failed_tests: List[str] = Field(default_factory=list, description="Names/IDs of failed test functions")
    error_summary: Optional[str] = Field(default=None, description="Concise description of the primary assertion failure or exception")
    traceback: Optional[str] = Field(default=None, description="Relevant stack trace snippet identifying failing file and line")
    failing_file: Optional[str] = Field(default=None, description="Path to file where failure occurred")
    failing_line: Optional[int] = Field(default=None, description="Line number of failure")
    raw_output: str = Field(default="", description="Full raw terminal output from test runner")


class TestAgent(BaseAgent):
    """Executes sandboxed verification suites and produces structured diagnostic results."""
    __test__ = False

    def __init__(self, mcp_server: Optional[MCPServer] = None, llm_provider: Optional[str] = None):
        super().__init__(
            role_name="TestAgent",
            system_prompt=TESTER_SYSTEM_PROMPT,
            llm_provider=llm_provider
        )
        self.mcp = mcp_server or get_mcp_server()

    def run_tests(self, command: str = "pytest tests/test_api.py -v") -> TestRunResult:
        """
        Executes test suite through MCP terminal tools and parses results into TestRunResult.
        """
        logger.info(f"[TestAgent] Executing test suite: '{command}'")
        tool_result: ToolResult = self.mcp.call_tool("execute_test_command", {"command": command})

        exit_code = tool_result.metadata.get("returncode", 0 if tool_result.success else 1)
        raw_output = tool_result.output or tool_result.error or ""

        parsed = self.parse_test_output(raw_output=raw_output, exit_code=exit_code)
        logger.info(
            f"[TestAgent] Tests completed: passed={parsed.passed} "
            f"(Passed: {parsed.passed_count}, Failed: {parsed.failed_count}, Code: {parsed.exit_code})"
        )
        return parsed

    def parse_test_output(self, raw_output: str, exit_code: int) -> TestRunResult:
        """
        Parses pytest or unittest output to extract statistics, failed tests, and stack traces.
        """
        passed = (exit_code == 0)
        passed_count = 0
        failed_count = 0
        warning_count = 0
        duration_seconds = 0.0
        failed_tests: List[str] = []
        error_summary: Optional[str] = None
        traceback: Optional[str] = None
        failing_file: Optional[str] = None
        failing_line: Optional[int] = None

        # 1. Parse test counts from summary line (e.g., "=== 1 failed, 3 passed, 2 warnings in 0.42s ===")
        summary_match = re.search(r"=+\s*(.*?)\s+in\s+([\d\.]+)s\s*=+", raw_output)
        if summary_match:
            stats_str = summary_match.group(1)
            duration_seconds = float(summary_match.group(2))

            passed_match = re.search(r"(\d+)\s+passed", stats_str)
            if passed_match:
                passed_count = int(passed_match.group(1))

            failed_match = re.search(r"(\d+)\s+failed", stats_str)
            if failed_match:
                failed_count = int(failed_match.group(1))

            warning_match = re.search(r"(\d+)\s+warning", stats_str)
            if warning_match:
                warning_count = int(warning_match.group(1))
        else:
            # Fallback if no summary line: count dots or PASSED / FAILED words
            passed_count = len(re.findall(r"\bPASSED\b", raw_output))
            failed_count = len(re.findall(r"\bFAILED\b", raw_output))

        # 2. Extract failed test names
        # Format: "FAILED tests/test_api.py::test_create_order_success - AssertionError: ..."
        failed_lines = re.findall(r"FAILED\s+([^\s]+)", raw_output)
        for ft in failed_lines:
            cleaned = ft.strip()
            if cleaned and cleaned not in failed_tests:
                failed_tests.append(cleaned)

        # Also check for "____ test_name ____" header sections
        if not failed_tests:
            section_headers = re.findall(r"_{3,}\s+([a-zA-Z0-9_]+)\s+_{3,}", raw_output)
            failed_tests.extend(section_headers)

        # 3. Extract primary assertion or error message
        # Format: "E   AssertionError: assert 108.0 == 999.0" or "E   ValueError: ..."
        error_lines = re.findall(r"(E\s+([A-Za-z0-9_]+Error:.*))", raw_output)
        if error_lines:
            error_summary = error_lines[-1][1].strip()
        elif failed_count > 0 and "AssertionError" in raw_output:
            for line in raw_output.splitlines():
                if "AssertionError" in line:
                    error_summary = line.strip()
                    break

        # 4. Extract failing file and line number
        # Format: "tests/dummy_repo/tests/test_api.py:47: AssertionError"
        file_line_match = re.search(r"([a-zA-Z0-9_\-\/\.]+\.py):(\d+):\s*([A-Za-z0-9_]+Error.*)", raw_output)
        if file_line_match:
            failing_file = file_line_match.group(1)
            failing_line = int(file_line_match.group(2))
            if not error_summary:
                error_summary = file_line_match.group(3).strip()

        # 5. Extract traceback block
        if not passed and failed_count > 0:
            tb_start = raw_output.find("FAILURES")
            tb_end = raw_output.rfind("short test summary info")
            if tb_start != -1:
                if tb_end != -1 and tb_end > tb_start:
                    traceback = raw_output[tb_start:tb_end].strip()
                else:
                    traceback = raw_output[tb_start:].strip()
            else:
                # If no FAILURES marker, look for Traceback (most recent call last)
                tb_idx = raw_output.find("Traceback (most recent call last)")
                if tb_idx != -1:
                    traceback = raw_output[tb_idx:].strip()

        if not passed and failed_count == 0 and exit_code != 0:
            # Command error or syntax/collection error
            failed_count = 1
            if not error_summary:
                error_summary = f"Test execution exited with code {exit_code}"

        return TestRunResult(
            passed=passed,
            exit_code=exit_code,
            passed_count=passed_count,
            failed_count=failed_count,
            warning_count=warning_count,
            duration_seconds=duration_seconds,
            failed_tests=failed_tests,
            error_summary=error_summary,
            traceback=traceback,
            failing_file=failing_file,
            failing_line=failing_line,
            raw_output=raw_output
        )

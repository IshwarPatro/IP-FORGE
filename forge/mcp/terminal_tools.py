"""
IP FORGE: Terminal MCP Tools
Executes sandboxed test and linting commands with strict allowlisting and timeouts.
"""

import subprocess
import shlex
import re
from pathlib import Path
from typing import Optional, List
from forge.mcp.fs_tools import ToolResult
from forge.config import settings, setup_logger

logger = setup_logger("forge.mcp.terminal_tools")


class TerminalTools:
    """Sandboxed terminal command runner restricted to verified test and verification suites."""

    # Allowed executable binaries and entrypoints
    ALLOWED_COMMAND_PREFIXES = [
        "pytest",
        "./venv/bin/pytest",
        "python -m pytest",
        "python -m unittest",
        "python3 -m pytest",
        "python3 -m unittest",
        "ruff check",
        "flake8",
        "npm test",
        "npm run test",
    ]

    # Forbidden shell tokens preventing command injection and privilege escalation
    FORBIDDEN_PATTERNS = [
        r"[;&|`]",             # Command chaining and pipelines
        r"\$\(",               # Subshell command substitution
        r">|>>|<",             # File redirections
        r"\b(rm|rmdir)\b",     # Deletion utilities
        r"\b(sudo|su)\b",      # Privilege escalation
        r"\b(curl|wget|nc)\b", # Outbound network exfiltration
        r"\b(chmod|chown)\b",  # Permission alterations
        r"\b(kill|pkill)\b",   # Process termination
    ]

    def __init__(self, root_dir: Optional[Path] = None, timeout_seconds: Optional[int] = None):
        self.root_dir = (root_dir or settings.target_repo_absolute_path).resolve()
        self.timeout = timeout_seconds or settings.MCP_EXECUTION_TIMEOUT_SECONDS
        logger.info(f"Initialized TerminalTools [CWD: {self.root_dir}] [Timeout: {self.timeout}s]")

    def _validate_command(self, cmd_str: str) -> List[str]:
        """
        Validates command against the allowlist and security regex filters.
        Returns parsed argument list if valid, raises PermissionError otherwise.
        """
        stripped = cmd_str.strip()
        if not stripped:
            raise ValueError("Command string cannot be empty.")

        # Check for forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, stripped):
                logger.error(f"Security Alert: Blocked forbidden pattern in command: '{cmd_str}'")
                raise PermissionError(
                    f"Security Violation: Command contains forbidden shell syntax or utility matching: '{pattern}'"
                )

        # Split arguments safely
        try:
            tokens = shlex.split(stripped)
        except Exception as err:
            raise ValueError(f"Failed to parse shell command safely: {err}")

        # Verify against allowed prefixes
        is_allowed = False
        for prefix in self.ALLOWED_COMMAND_PREFIXES:
            prefix_tokens = prefix.split()
            if tokens[:len(prefix_tokens)] == prefix_tokens:
                is_allowed = True
                break

        if not is_allowed:
            logger.error(f"Security Alert: Command not in allowlist: '{cmd_str}'")
            raise PermissionError(
                f"Security Violation: Command '{tokens[0]}' is not in the permitted test execution allowlist. "
                f"Allowed prefixes: {self.ALLOWED_COMMAND_PREFIXES}"
            )

        return tokens

    def execute_command(self, command: str) -> ToolResult:
        """
        Executes a validated test command in a sandboxed subprocess.
        Enforces execution timeouts and captures complete stdout and stderr.
        """
        try:
            tokens = self._validate_command(command)
            logger.info(f"[TerminalTools] Executing: {' '.join(tokens)} in {self.root_dir}")

            result = subprocess.run(
                tokens,
                cwd=str(self.root_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            combined_output = stdout
            if stderr:
                combined_output = f"{stdout}\n[STDERR]:\n{stderr}" if stdout else f"[STDERR]:\n{stderr}"

            success = (result.returncode == 0)
            logger.info(f"[TerminalTools] Completed with exit code {result.returncode} (Success: {success})")

            return ToolResult(
                success=success,
                output=combined_output,
                error=None if success else f"Command failed with exit code {result.returncode}",
                metadata={
                    "returncode": result.returncode,
                    "command": command,
                    "cwd": str(self.root_dir)
                }
            )

        except PermissionError as perm_err:
            return ToolResult(success=False, error=str(perm_err))
        except subprocess.TimeoutExpired:
            logger.error(f"[TerminalTools] Command timed out after {self.timeout}s: '{command}'")
            return ToolResult(
                success=False,
                error=f"Execution timed out: Exceeded maximum allowed runtime of {self.timeout} seconds."
            )
        except Exception as exc:
            logger.error(f"[TerminalTools] Subprocess execution error: {exc}", exc_info=True)
            return ToolResult(success=False, error=f"Execution error: {str(exc)}")

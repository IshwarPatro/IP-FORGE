"""
IP FORGE: Git MCP Tools
Manages branch isolation, diff extraction, and commit generation for autonomous tasks.
"""

import subprocess
import uuid
from pathlib import Path
from typing import Optional
from forge.mcp.fs_tools import ToolResult
from forge.config import setup_logger

logger = setup_logger("forge.mcp.git_tools")


class GitTools:
    """Manages isolated Git operations, enforcing branch isolation from main/master."""

    PROTECTED_BRANCHES = ["main", "master", "release", "prod", "production"]

    def __init__(self, repo_dir: Optional[Path] = None):
        self.repo_dir = (repo_dir or Path(".")).resolve()
        logger.info(f"Initialized GitTools in directory: {self.repo_dir}")

    def _run_git(self, args: list) -> ToolResult:
        """Executes a git command safely in the repository directory."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=str(self.repo_dir),
                capture_output=True,
                text=True,
                timeout=15
            )
            success = (result.returncode == 0)
            return ToolResult(
                success=success,
                output=result.stdout.strip(),
                error=None if success else result.stderr.strip(),
                metadata={"returncode": result.returncode, "args": args}
            )
        except Exception as exc:
            return ToolResult(success=False, error=f"Git command failed: {str(exc)}")

    def get_current_branch(self) -> ToolResult:
        """Returns active branch name."""
        return self._run_git(["branch", "--show-current"])

    def create_task_branch(self, branch_name: Optional[str] = None) -> ToolResult:
        """Creates and switches to a dedicated task branch: forge/task-<id>."""
        clean_name = branch_name or f"forge/task-{uuid.uuid4().hex[:8]}"
        if clean_name in self.PROTECTED_BRANCHES:
            return ToolResult(
                success=False,
                error=f"Security Violation: Cannot create or target protected branch '{clean_name}'"
            )

        res = self._run_git(["checkout", "-b", clean_name])
        if res.success:
            logger.info(f"[GitTools] Switched to isolated task branch: '{clean_name}'")
        return res

    def get_diff(self, cached: bool = False) -> ToolResult:
        """Retrieves unified git diff of changes made by the agent."""
        cmd = ["diff", "--cached"] if cached else ["diff"]
        return self._run_git(cmd)

    def commit_changes(self, message: str) -> ToolResult:
        """Stages modified files and creates a commit on the active task branch."""
        # Verify current branch is not protected
        branch_res = self.get_current_branch()
        current_branch = branch_res.output.strip()

        if current_branch in self.PROTECTED_BRANCHES:
            return ToolResult(
                success=False,
                error=f"Security Violation: Autonomous commits to protected branch '{current_branch}' are blocked."
            )

        # Stage tracked modifications
        add_res = self._run_git(["add", "-u"])
        if not add_res.success:
            return add_res

        # Commit
        commit_res = self._run_git(["commit", "-m", f"[IP FORGE] {message}"])
        if commit_res.success:
            logger.info(f"[GitTools] Successfully committed on branch '{current_branch}': {message}")
        return commit_res

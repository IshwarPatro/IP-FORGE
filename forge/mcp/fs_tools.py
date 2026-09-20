"""
IP FORGE: Filesystem MCP Tools
Provides secure, sandboxed file operations strictly confined to the target repository.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from forge.config import settings, setup_logger

logger = setup_logger("forge.mcp.fs_tools")


class ToolResult(BaseModel):
    """Standardized result returned by all MCP tools."""
    success: bool
    output: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FilesystemTools:
    """Sandboxed file operations ensuring operations cannot escape the target repository."""

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = (root_dir or settings.target_repo_absolute_path).resolve()
        logger.info(f"Initialized FilesystemTools with sandbox root: {self.root_dir}")

    def _resolve_and_validate_path(self, relative_path: str) -> Path:
        """
        Resolves path relative to sandbox root and strictly validates that
        it does not traverse outside the target repository.
        """
        # Strip leading slashes to prevent absolute path escapes
        clean_rel = relative_path.lstrip("/\\")
        resolved = (self.root_dir / clean_rel).resolve()

        # Strict containment check
        try:
            resolved.relative_to(self.root_dir)
        except ValueError:
            logger.error(f"Security Alert: Path traversal attempt blocked: '{relative_path}' -> '{resolved}'")
            raise PermissionError(
                f"Security Violation: Path '{relative_path}' traverses outside the sandbox boundary: {self.root_dir}"
            )

        # Protect .git internal repository state
        if ".git" in resolved.parts:
            raise PermissionError("Access to internal .git repository state is strictly prohibited.")

        return resolved

    def read_file(self, path: str) -> ToolResult:
        """Reads and returns the complete text content of a file in the sandbox."""
        try:
            target_path = self._resolve_and_validate_path(path)
            if not target_path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: '{path}'",
                    metadata={"resolved_path": str(target_path)}
                )
            if not target_path.is_file():
                return ToolResult(
                    success=False,
                    error=f"Path is not a regular file: '{path}'"
                )

            content = target_path.read_text(encoding="utf-8")
            return ToolResult(
                success=True,
                output=content,
                metadata={"file_size_bytes": len(content), "path": path}
            )
        except PermissionError as perm_err:
            return ToolResult(success=False, error=str(perm_err))
        except Exception as exc:
            logger.error(f"Error reading file '{path}': {exc}", exc_info=True)
            return ToolResult(success=False, error=f"Read error: {str(exc)}")

    def write_file(self, path: str, content: str) -> ToolResult:
        """Writes text content to a file in the sandbox, creating parent directories if needed."""
        try:
            target_path = self._resolve_and_validate_path(path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            logger.info(f"Successfully wrote {len(content)} bytes to '{path}'")
            return ToolResult(
                success=True,
                output=f"Successfully updated file '{path}' ({len(content)} bytes).",
                metadata={"bytes_written": len(content), "path": path}
            )
        except PermissionError as perm_err:
            return ToolResult(success=False, error=str(perm_err))
        except Exception as exc:
            logger.error(f"Error writing file '{path}': {exc}", exc_info=True)
            return ToolResult(success=False, error=f"Write error: {str(exc)}")

    def list_dir(self, path: str = "") -> ToolResult:
        """Lists child directories and files within a given directory."""
        try:
            target_path = self._resolve_and_validate_path(path)
            if not target_path.exists():
                return ToolResult(success=False, error=f"Directory does not exist: '{path}'")
            if not target_path.is_dir():
                return ToolResult(success=False, error=f"Path is not a directory: '{path}'")

            entries = []
            for item in sorted(target_path.iterdir()):
                if item.name.startswith(".") and item.name != ".env.example":
                    continue
                item_type = "DIR" if item.is_dir() else "FILE"
                entries.append(f"[{item_type}] {item.name}")

            output_str = "\n".join(entries) if entries else "(Empty directory)"
            return ToolResult(
                success=True,
                output=output_str,
                metadata={"count": len(entries), "path": path}
            )
        except PermissionError as perm_err:
            return ToolResult(success=False, error=str(perm_err))
        except Exception as exc:
            return ToolResult(success=False, error=f"List directory error: {str(exc)}")

    def file_exists(self, path: str) -> ToolResult:
        """Checks whether a file exists in the sandbox."""
        try:
            target_path = self._resolve_and_validate_path(path)
            exists = target_path.exists()
            return ToolResult(
                success=True,
                output=f"File exists: {exists}",
                metadata={"exists": exists, "path": path}
            )
        except PermissionError as perm_err:
            return ToolResult(success=False, error=str(perm_err))

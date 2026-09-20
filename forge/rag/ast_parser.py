"""
IP FORGE: AST Codebase Parser
Extracts semantic code symbols (classes, functions, methods, signatures, docstrings)
using Python's native Abstract Syntax Tree (ast) module.
"""

import ast
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from forge.config import setup_logger

logger = setup_logger("forge.rag.ast_parser")


class ASTSymbol(BaseModel):
    """Represents a discrete semantic code symbol parsed from an AST."""
    name: str
    symbol_type: str = Field(description="'class', 'function', or 'method'")
    file_path: str
    start_line: int
    end_line: int
    parent_class: Optional[str] = None
    signature: str
    docstring: Optional[str] = None
    code_snippet: str
    decorators: List[str] = Field(default_factory=list)
    calls: List[str] = Field(default_factory=list)

    @property
    def qualified_id(self) -> str:
        """Returns unique identifier for vector store indexing."""
        scope = f"{self.parent_class}." if self.parent_class else ""
        return f"{self.file_path}::{scope}{self.name}:{self.start_line}"

    def to_embedding_text(self) -> str:
        """Constructs rich semantic text representation for embedding models."""
        parts = [
            f"File: {self.file_path}",
            f"Type: {self.symbol_type.upper()}",
            f"Identifier: {self.parent_class + '.' if self.parent_class else ''}{self.name}",
            f"Signature: {self.signature}",
        ]
        if self.docstring:
            parts.append(f"Docstring: {self.docstring.strip()}")
        if self.calls:
            parts.append(f"Function Calls: {', '.join(self.calls)}")
        parts.append("Source Code:\n" + self.code_snippet)
        return "\n".join(parts)


class FileASTSummary(BaseModel):
    """Complete AST structural summary of a single source file."""
    file_path: str
    module_docstring: Optional[str] = None
    imports: List[str] = Field(default_factory=list)
    symbols: List[ASTSymbol] = Field(default_factory=list)


class ASTParser:
    """Traverses repository files and parses Abstract Syntax Trees."""

    DEFAULT_EXCLUDES = [
        "__pycache__",
        ".git",
        "venv",
        ".venv",
        "env",
        ".pytest_cache",
        "node_modules",
        ".DS_Store",
        ".chroma",
        "chroma_db",
    ]

    def __init__(self, exclude_patterns: Optional[List[str]] = None):
        self.excludes = exclude_patterns or self.DEFAULT_EXCLUDES

    def parse_file(self, file_path: Path, root_path: Optional[Path] = None) -> Optional[FileASTSummary]:
        """Parses a single Python file into its constituent AST symbols."""
        try:
            source = file_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning(f"Could not read file {file_path}: {exc}")
            return None

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as err:
            logger.warning(f"Syntax error parsing {file_path}: {err}")
            return None

        relative_path = str(file_path.relative_to(root_path)) if root_path else str(file_path)
        source_lines = source.splitlines()

        summary = FileASTSummary(
            file_path=relative_path,
            module_docstring=ast.get_docstring(tree),
        )

        # Extract top-level imports
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    summary.imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = ", ".join([a.name for a in node.names])
                summary.imports.append(f"from {module} import {names}")

        # Extract classes and functions
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self._process_class_node(node, relative_path, source_lines, summary)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._process_function_node(node, relative_path, source_lines, summary, parent_class=None)

        return summary

    def parse_directory(self, dir_path: Path) -> List[FileASTSummary]:
        """Recursively parses all Python files in a directory."""
        results: List[FileASTSummary] = []
        resolved_dir = dir_path.resolve()

        if not resolved_dir.exists():
            logger.error(f"Target directory does not exist: {resolved_dir}")
            return results

        for path in resolved_dir.rglob("*.py"):
            # Check excludes
            if any(part in path.parts for part in self.excludes):
                continue
            file_summary = self.parse_file(path, root_path=resolved_dir)
            if file_summary:
                results.append(file_summary)

        logger.info(f"Parsed {len(results)} files across {resolved_dir}")
        return results

    def _process_class_node(
        self,
        node: ast.ClassDef,
        file_path: str,
        lines: List[str],
        summary: FileASTSummary
    ):
        """Extracts class definition and its child method symbols."""
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line)
        snippet = "\n".join(lines[start_line - 1:end_line])

        # Extract base classes
        bases = [ast.unparse(b) for b in node.bases]
        signature = f"class {node.name}({', '.join(bases)}):" if bases else f"class {node.name}:"
        decorators = [ast.unparse(d) for d in node.decorator_list]

        class_symbol = ASTSymbol(
            name=node.name,
            symbol_type="class",
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            signature=signature,
            docstring=ast.get_docstring(node),
            code_snippet=snippet,
            decorators=decorators,
        )
        summary.symbols.append(class_symbol)

        # Process internal methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._process_function_node(
                    item, file_path, lines, summary, parent_class=node.name
                )

    def _process_function_node(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: str,
        lines: List[str],
        summary: FileASTSummary,
        parent_class: Optional[str] = None
    ):
        """Extracts function or class method symbol."""
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line)
        snippet = "\n".join(lines[start_line - 1:end_line])

        # Format signature
        args_unparsed = ast.unparse(node.args)
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        ret_ann = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        signature = f"{prefix} {node.name}({args_unparsed}){ret_ann}"
        decorators = [ast.unparse(d) for d in node.decorator_list]

        # Extract internal call identifiers
        calls: List[str] = []
        for sub_node in ast.walk(node):
            if isinstance(sub_node, ast.Call):
                try:
                    calls.append(ast.unparse(sub_node.func))
                except Exception:
                    pass

        func_symbol = ASTSymbol(
            name=node.name,
            symbol_type="method" if parent_class else "function",
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            parent_class=parent_class,
            signature=signature,
            docstring=ast.get_docstring(node),
            code_snippet=snippet,
            decorators=decorators,
            calls=list(set(calls)),
        )
        summary.symbols.append(func_symbol)

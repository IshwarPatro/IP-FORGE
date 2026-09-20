"""
IP FORGE: Architecture Agent (RAG)
Discovers codebase symbols, inspects call hierarchies, and provides grounded repository context.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from forge.agents.base import BaseAgent
from forge.rag.vector_store import get_vector_store, CodebaseVectorStore, SearchResult
from forge.config import setup_logger

logger = setup_logger("forge.agents.architect")

ARCHITECT_SYSTEM_PROMPT = """You are the Architecture Agent for IP FORGE, an autonomous software engineering system.
Your responsibility is to analyze codebase structures, inspect abstract syntax trees (AST), and trace dependencies.
You never write code directly. Instead, you locate where features are implemented, identify existing patterns,
and provide exact file paths, class names, method signatures, and line numbers to the Planner Agent.
Always be precise, concise, and grounded strictly in the provided codebase context."""


class ArchitectureContext(BaseModel):
    """Contextual codebase knowledge assembled for the Planner Agent."""
    task: str
    relevant_files: List[str] = Field(default_factory=list)
    relevant_symbols: List[SearchResult] = Field(default_factory=list)
    context_summary: str = ""


class ArchitectureAgent(BaseAgent):
    """Interfaces with ChromaDB vector store to answer codebase layout and dependency questions."""

    def __init__(self, vector_store: Optional[CodebaseVectorStore] = None, llm_provider: Optional[str] = None):
        super().__init__(
            role_name="ArchitectureAgent",
            system_prompt=ARCHITECT_SYSTEM_PROMPT,
            llm_provider=llm_provider
        )
        self.vector_store = vector_store or get_vector_store()

    def investigate_task(self, task: str, top_k: int = 5) -> ArchitectureContext:
        """
        Retrieves codebase context relevant to a developer task.
        Extracts key symbols and structures a grounded architectural summary.
        """
        logger.info(f"[ArchitectureAgent] Investigating codebase for task: '{task}'")

        # Query vector store for semantically relevant AST symbols
        results = self.vector_store.query_codebase(query=task, top_k=top_k)

        unique_files = list(dict.fromkeys(r.file_path for r in results))

        # Build human-readable and LLM-friendly context summary
        summary_lines = [
            f"Codebase context for task: '{task}'",
            f"Identified {len(results)} relevant AST symbols across {len(unique_files)} files:\n"
        ]

        for idx, match in enumerate(results, 1):
            scope = f"{match.parent_class}." if match.parent_class else ""
            summary_lines.append(
                f"{idx}. [{match.symbol_type.upper()}] {scope}{match.symbol_name} "
                f"in {match.file_path}:{match.start_line}-{match.end_line}"
            )
            if match.signature:
                summary_lines.append(f"   Signature: {match.signature}")
            if match.snippet:
                # Add snippet excerpt
                summary_lines.append(f"   Snippet:\n{match.snippet}\n")

        context_summary = "\n".join(summary_lines)

        return ArchitectureContext(
            task=task,
            relevant_files=unique_files,
            relevant_symbols=results,
            context_summary=context_summary
        )

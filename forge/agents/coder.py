"""
IP FORGE: Coding Agent
Executes plan steps, reads target code, and generates surgical modifications via MCP tools.
"""

from typing import Optional, Dict, Any
from forge.agents.base import BaseAgent
from forge.orchestrator.state import PlanStep
from forge.config import setup_logger

logger = setup_logger("forge.agents.coder")

CODER_SYSTEM_PROMPT = """You are the Coding Agent for IP FORGE, an autonomous software engineering system.
Your mission is to execute a specific plan step by generating precise, production-grade code modifications.

RULES FOR CODING:
1. Adhere strictly to existing project conventions, type annotations, and error handling patterns.
2. Minimize diff size: only change code necessary to fulfill the step.
3. Preserve existing imports, function signatures, and backward compatibility unless explicitly instructed.
4. Output clean code ready to be written via Filesystem MCP tools."""


class CodingAgent(BaseAgent):
    """Executes code modification plan steps."""

    def __init__(self, llm_provider: Optional[str] = None):
        super().__init__(
            role_name="CodingAgent",
            system_prompt=CODER_SYSTEM_PROMPT,
            llm_provider=llm_provider
        )

    def formulate_code_change(self, step: PlanStep, file_content: str) -> str:
        """Generates updated file content for a given plan step."""
        user_prompt = f"""STEP TO EXECUTE:
Action: {step.action}
Target File: {step.target_file}
Description: {step.description}
Symbols Involved: {', '.join(step.symbols_involved)}

CURRENT FILE CONTENT:
```python
{file_content}
```

Provide the full, modified source code for {step.target_file} fulfilling the step description."""

        logger.info(f"[CodingAgent] Formulating code modification for {step.target_file}")
        return self._call_llm(user_prompt=user_prompt, temperature=0.2)

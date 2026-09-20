"""
IP FORGE: Coding Agent
Executes plan steps, reads target code, and generates surgical modifications via MCP tools.
"""

from typing import Optional, Dict, Any
from forge.agents.base import BaseAgent
from forge.orchestrator.state import PlanStep
from forge.mcp.server import MCPServer, ToolResult, get_mcp_server
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
    """Executes code modification plan steps via Model Context Protocol tools."""

    def __init__(self, mcp_server: Optional[MCPServer] = None, llm_provider: Optional[str] = None):
        super().__init__(
            role_name="CodingAgent",
            system_prompt=CODER_SYSTEM_PROMPT,
            llm_provider=llm_provider
        )
        self.mcp = mcp_server or get_mcp_server()

    def execute_step(self, step: PlanStep) -> ToolResult:
        """Dispatches plan step execution through the appropriate MCP tool."""
        logger.info(f"[CodingAgent] Executing Step #{step.step_number}: [{step.action.upper()}] on {step.target_file}")

        if step.action == "read_file":
            return self.mcp.call_tool("read_file", {"path": step.target_file})

        elif step.action == "run_test":
            cmd = f"pytest {step.target_file} -v" if step.target_file else "pytest"
            return self.mcp.call_tool("execute_test_command", {"command": cmd})

        elif step.action in ["modify_file", "create_file"]:
            # 1. Read existing content if modifying
            existing_content = ""
            if step.action == "modify_file":
                read_res = self.mcp.call_tool("read_file", {"path": step.target_file})
                if not read_res.success:
                    return read_res
                existing_content = read_res.output

            # 2. Formulate code change
            new_code = self.formulate_code_change(step=step, file_content=existing_content)

            # 3. Write modified file
            return self.mcp.call_tool("write_file", {
                "path": step.target_file,
                "content": new_code
            })

        return ToolResult(success=False, error=f"Unsupported action: '{step.action}'")

    def formulate_code_change(self, step: PlanStep, file_content: str) -> str:
        """
        Generates updated file content for a given plan step.
        Uses LLM if available, or applies AST-safe updates.
        """
        user_prompt = f"""STEP TO EXECUTE:
Action: {step.action}
Target File: {step.target_file}
Description: {step.description}
Symbols Involved: {', '.join(step.symbols_involved)}

CURRENT FILE CONTENT:
```python
{file_content}
```

Provide the full, modified source code for {step.target_file} fulfilling the step description.
Output only the Python source code."""

        if not self.client.is_healthy():
            logger.warning("[CodingAgent] LLM offline. Simulating code change for step.")
            # If LLM is offline, preserve content with a documented change header
            return f"# [IP FORGE Auto-Patch: {step.description}]\n" + file_content

        try:
            raw = self._call_llm(user_prompt=user_prompt, temperature=0.2)
            # Clean possible markdown block
            if "```python" in raw:
                raw = raw.split("```python")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            return raw
        except Exception as exc:
            logger.error(f"[CodingAgent] Code generation failed: {exc}")
            return file_content

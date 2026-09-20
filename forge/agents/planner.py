"""
IP FORGE: Planner Agent
Decomposes engineering tasks into structured, acyclic execution plans (DAGs)
grounded in AST codebase context.
"""

from typing import Optional, Dict, Any
from forge.agents.base import BaseAgent
from forge.agents.architect import ArchitectureContext
from forge.orchestrator.state import EngineeringPlan, PlanStep
from forge.config import setup_logger

logger = setup_logger("forge.agents.planner")

PLANNER_SYSTEM_PROMPT = """You are the Lead Planner Agent for IP FORGE, an autonomous AI software engineering system.
Your mission is to take a developer's engineering task and grounded codebase context, and produce a high-fidelity,
step-by-step execution plan in STRICT JSON format.

RULES FOR PLANNING:
1. Always base your plan strictly on the provided codebase files and AST symbols.
2. Order your steps logically:
   - Step 1: Read/inspect relevant existing files.
   - Step 2..N: Modify or create specific files (one focused change per step).
   - Final Step: Run automated tests using 'pytest' to verify the implementation.
3. Every step must specify:
   - step_number: Integer (1-indexed).
   - action: Exactly one of 'read_file', 'modify_file', 'create_file', or 'run_test'.
   - target_file: Exact relative file path (e.g. 'app/api.py' or 'tests/test_api.py').
   - description: Concrete explanation of the code modification or verification needed.
   - symbols_involved: List of specific classes, methods, or functions touched.
4. Output ONLY valid JSON matching this schema:
{
  "task": "<Task description>",
  "architectural_summary": "<Technical overview of how components interact and what needs to change>",
  "files_to_modify": ["<file1>", "<file2>"],
  "steps": [
    {
      "step_number": 1,
      "action": "read_file",
      "target_file": "app/services.py",
      "description": "Inspect existing ProductCatalogService implementation",
      "symbols_involved": ["ProductCatalogService"]
    },
    {
      "step_number": 2,
      "action": "modify_file",
      "target_file": "app/services.py",
      "description": "Add pagination parameters limit and offset to get_all_products",
      "symbols_involved": ["ProductCatalogService.get_all_products"]
    },
    {
      "step_number": 3,
      "action": "run_test",
      "target_file": "tests/test_api.py",
      "description": "Run pytest to verify pagination behavior and prevent regressions",
      "symbols_involved": []
    }
  ],
  "verification_strategy": "<How changes are verified via automated tests>"
}
Do NOT wrap your output in conversational markdown or introductory text. Return ONLY the JSON object."""


class PlannerAgent(BaseAgent):
    """Generates structured execution plans for the Coding and Test agents."""

    def __init__(self, llm_provider: Optional[str] = None):
        super().__init__(
            role_name="PlannerAgent",
            system_prompt=PLANNER_SYSTEM_PROMPT,
            llm_provider=llm_provider
        )

    def create_plan(self, task: str, context: ArchitectureContext) -> EngineeringPlan:
        """
        Synthesizes task requirements with retrieved codebase context to formulate
        a strictly typed EngineeringPlan.
        """
        logger.info(f"[PlannerAgent] Formulating engineering plan for task: '{task}'")

        user_prompt = f"""DEVELOPER TASK:
{task}

GROUNDED CODEBASE CONTEXT (From Architecture Agent RAG):
{context.context_summary}

RELEVANT FILES IDENTIFIED:
{', '.join(context.relevant_files) if context.relevant_files else 'None detected'}

Generate the step-by-step engineering plan in JSON format now."""

        try:
            # Check if LLM endpoint is reachable
            if not self.client.is_healthy():
                logger.warning(
                    f"LLM endpoint ({self.client.provider}) is not reachable. "
                    "Engaging deterministic fallback planner."
                )
                return self._generate_fallback_plan(task, context)

            raw_response = self._call_llm(
                user_prompt=user_prompt,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            parsed_json = self._parse_json_response(raw_response)
            plan = EngineeringPlan(**parsed_json)
            logger.info(
                f"[PlannerAgent] Plan successfully created with {len(plan.steps)} steps "
                f"across {len(plan.files_to_modify)} files."
            )
            return plan

        except Exception as exc:
            logger.warning(
                f"[PlannerAgent] LLM generation/parsing failed: {exc}. "
                "Engaging deterministic fallback planner."
            )
            return self._generate_fallback_plan(task, context)

    def _generate_fallback_plan(self, task: str, context: ArchitectureContext) -> EngineeringPlan:
        """
        Deterministic, AST-grounded fallback planner used when the local LLM is offline.
        Ensures system stability and test execution reliability without external dependencies.
        """
        logger.info("[PlannerAgent] Generating deterministic AST-grounded plan...")

        files = context.relevant_files or ["app/services.py", "app/api.py"]
        steps = []
        step_num = 1

        # Step 1: Read files
        for f in files[:2]:
            steps.append(PlanStep(
                step_number=step_num,
                action="read_file",
                target_file=f,
                description=f"Inspect current implementation and signatures in {f}",
                symbols_involved=[s.symbol_name for s in context.relevant_symbols if s.file_path == f][:3]
            ))
            step_num += 1

        # Step 2: Modify files
        for f in files[:2]:
            matched_syms = [s.symbol_name for s in context.relevant_symbols if s.file_path == f]
            sym_desc = f" ({', '.join(matched_syms[:2])})" if matched_syms else ""
            steps.append(PlanStep(
                step_number=step_num,
                action="modify_file",
                target_file=f,
                description=f"Implement updates for '{task}' in {f}{sym_desc}",
                symbols_involved=matched_syms[:3]
            ))
            step_num += 1

        # Final Step: Run tests
        steps.append(PlanStep(
            step_number=step_num,
            action="run_test",
            target_file="tests/test_api.py",
            description=f"Execute test suite via pytest to verify implementation of '{task}'",
            symbols_involved=[]
        ))

        return EngineeringPlan(
            task=task,
            architectural_summary=(
                f"Autonomous plan for: '{task}'. Identified {len(context.relevant_symbols)} "
                f"relevant AST nodes across {len(files)} files: {', '.join(files)}."
            ),
            files_to_modify=files,
            steps=steps,
            verification_strategy="Run automated test suite via pytest to ensure no regressions."
        )

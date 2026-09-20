"""
IP FORGE: Autonomous Self-Healing Engineering Loop
Connects Planner, Coder, Tester, Debugger, and Reviewer into an automated
closed-loop state machine with a strict 3-iteration self-healing ceiling.
"""

import uuid
from typing import Optional, Callable, Dict, Any, List
from forge.orchestrator.state import AgentState, EngineeringPlan, PlanStep
from forge.orchestrator.coordinator import OrchestratorCoordinator, get_coordinator
from forge.agents.coder import CodingAgent
from forge.agents.tester import TestAgent, TestRunResult
from forge.agents.debugger import DebuggerAgent, DebuggerDiagnosis
from forge.agents.reviewer import ReviewerAgent, ReviewSummary
from forge.mcp.server import MCPServer, ToolResult, get_mcp_server
from forge.config import setup_logger

logger = setup_logger("forge.orchestrator.loop")


class AutonomousLoop:
    """
    Closed-loop self-healing software engineering orchestrator.
    Executes tasks end-to-end: Plan -> Branch -> Code -> Test -> [Debug -> Patch -> Test] -> Review.
    """

    MAX_SELF_HEAL_ITERATIONS = 3

    def __init__(
        self,
        coordinator: Optional[OrchestratorCoordinator] = None,
        coder: Optional[CodingAgent] = None,
        tester: Optional[TestAgent] = None,
        debugger: Optional[DebuggerAgent] = None,
        reviewer: Optional[ReviewerAgent] = None,
        mcp_server: Optional[MCPServer] = None,
        max_retries: int = MAX_SELF_HEAL_ITERATIONS
    ):
        self.mcp = mcp_server or get_mcp_server()
        self.coordinator = coordinator or get_coordinator()
        self.coder = coder or CodingAgent(mcp_server=self.mcp)
        self.tester = tester or TestAgent(mcp_server=self.mcp)
        self.debugger = debugger or DebuggerAgent(mcp_server=self.mcp)
        self.reviewer = reviewer or ReviewerAgent(mcp_server=self.mcp)
        self.max_retries = max_retries

    def run(
        self,
        task: str,
        target_file: Optional[str] = None,
        test_command: Optional[str] = None,
        create_branch: bool = True,
        on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> AgentState:
        """
        Executes an autonomous engineering task with closed-loop verification and self-healing.
        """
        session_id = uuid.uuid4().hex[:8]
        state = AgentState(
            session_id=session_id,
            task=task,
            max_retries=self.max_retries,
            status="planning"
        )

        def emit(event_name: str, payload: Optional[Dict[str, Any]] = None):
            event_data = payload or {}
            logger.info(f"[AutonomousLoop][Session:{session_id}] Event: {event_name} -> {event_data.get('message', '')}")
            if on_event:
                try:
                    on_event(event_name, {"session_id": session_id, **event_data})
                except Exception as exc:
                    logger.warning(f"Error in event listener callback: {exc}")

        state.record_event(f"Session {session_id} initialized for task: '{task}'")
        emit("session_started", {"message": f"Autonomous session {session_id} initialized."})

        # ----------------------------------------------------------------------
        # 1. Branch Isolation
        # ----------------------------------------------------------------------
        if create_branch:
            branch_name = f"forge/task-{session_id}"
            branch_res = self.mcp.call_tool("create_task_branch", {"branch_name": branch_name})
            if branch_res.success:
                state.git_branch = branch_name
                state.record_event(f"Isolated Git task branch created and checked out: '{branch_name}'")
                emit("branch_created", {"branch": branch_name, "message": f"Switched to branch {branch_name}"})
            else:
                state.record_event(f"Git branch creation warning: {branch_res.error}")

        # ----------------------------------------------------------------------
        # 2. Planning (Planner + Architect Agents)
        # ----------------------------------------------------------------------
        state.status = "planning"
        state.record_event("Planner Agent formulating execution DAG and architectural summary...")
        emit("planning_started", {"message": "Formulating execution DAG with codebase intelligence..."})

        plan = self.coordinator.create_plan_for_task(task=task)
        state.plan = plan
        state.record_event(
            f"Plan formulated with {len(plan.steps)} steps. "
            f"Files targeted: {', '.join(plan.files_to_modify) if plan.files_to_modify else 'None'}"
        )
        emit("planning_completed", {
            "steps_count": len(plan.steps),
            "files": plan.files_to_modify,
            "summary": plan.architectural_summary
        })

        # ----------------------------------------------------------------------
        # 3. Coding (Execution of Initial Plan Steps)
        # ----------------------------------------------------------------------
        state.status = "coding"
        state.record_event("Coding Agent executing plan steps via sandboxed MCP tools...")
        emit("coding_started", {"message": f"Executing {len(plan.steps)} plan steps..."})

        for idx, step in enumerate(plan.steps):
            state.current_step_index = idx
            step.status = "in_progress"
            emit("step_executing", {"step": step.step_number, "action": step.action, "target": step.target_file})

            tool_result = self.coder.execute_step(step)
            if tool_result.success:
                step.status = "completed"
                step.execution_notes = f"Executed {step.action} successfully."
                state.record_event(f"Step #{step.step_number} [{step.action}] completed on {step.target_file}")
            else:
                step.status = "failed"
                step.execution_notes = f"Failed: {tool_result.error}"
                state.record_event(f"Step #{step.step_number} [{step.action}] failed: {tool_result.error}")

        emit("coding_completed", {"message": "Plan steps executed. Proceeding to verification."})

        # ----------------------------------------------------------------------
        # 4. Verification & Closed-Loop Self-Healing
        # ----------------------------------------------------------------------
        cmd = test_command or "pytest tests/test_api.py -v"

        while True:
            state.status = "testing"
            state.record_event(f"Test Agent executing verification command: '{cmd}'")
            emit("testing_started", {"command": cmd, "attempt": state.retry_count + 1})

            test_run: TestRunResult = self.tester.run_tests(command=cmd)
            state.tests_passed = test_run.passed
            state.test_stdout = test_run.raw_output

            if test_run.passed:
                state.record_event(
                    f"Test verification succeeded: {test_run.passed_count} passed "
                    f"in {test_run.duration_seconds:.2f}s."
                )
                emit("testing_passed", {
                    "passed_count": test_run.passed_count,
                    "duration": test_run.duration_seconds
                })
                break

            # Tests failed -> Inspect retry ceiling
            state.record_event(
                f"Test verification failed (Exit code {test_run.exit_code}): "
                f"{test_run.error_summary or 'Assertions failed'}. "
                f"Failing tests: {', '.join(test_run.failed_tests)}"
            )
            emit("testing_failed", {
                "exit_code": test_run.exit_code,
                "error": test_run.error_summary,
                "failed_tests": test_run.failed_tests,
                "retry_count": state.retry_count
            })

            if state.retry_count >= state.max_retries:
                state.status = "escalate_to_human"
                msg = (
                    f"Self-healing ceiling reached ({state.max_retries} attempts). "
                    f"Escalating task to human engineer with complete diagnostic context."
                )
                state.record_event(msg)
                emit("escalated_to_human", {"message": msg, "diagnostics": test_run.error_summary})
                break

            # Engage Self-Healing Cycle
            state.retry_count += 1
            state.status = "debugging"
            emit("debugging_started", {
                "iteration": state.retry_count,
                "max_retries": state.max_retries,
                "error": test_run.error_summary
            })

            # Identify target file to inspect & heal
            heal_file = target_file
            if not heal_file:
                # Deduce from failing traceback or plan
                if test_run.failing_file and not test_run.failing_file.startswith("tests/"):
                    heal_file = test_run.failing_file
                elif plan.files_to_modify:
                    heal_file = plan.files_to_modify[0]
                else:
                    heal_file = "app/utils.py"

            state.record_event(
                f"Self-Healing Iteration #{state.retry_count}/{state.max_retries}: "
                f"Debugger Agent analyzing {heal_file}..."
            )

            # Read existing file content via MCP
            read_res = self.mcp.call_tool("read_file", {"path": heal_file})
            current_code = read_res.output if read_res.success else ""

            # Debugger synthesizes precision patch
            diagnosis: DebuggerDiagnosis = self.debugger.diagnose_and_patch(
                task=task,
                test_result=test_run,
                file_content=current_code,
                file_path=heal_file
            )

            state.record_event(
                f"Debugger Diagnosis: {diagnosis.root_cause} | Proposed fix: {diagnosis.suggested_fix}"
            )
            emit("debugging_diagnosed", {
                "root_cause": diagnosis.root_cause,
                "fix": diagnosis.suggested_fix,
                "confidence": diagnosis.confidence
            })

            # Apply patch via MCP write_file
            write_res = self.mcp.call_tool("write_file", {
                "path": heal_file,
                "content": diagnosis.patched_code
            })

            if write_res.success:
                state.record_event(f"Precision patch applied to {heal_file}. Re-running verification suite...")
                emit("patch_applied", {"file": heal_file, "message": "Patch written. Re-verifying..."})
            else:
                state.record_event(f"Failed to write patch to {heal_file}: {write_res.error}")

        # ----------------------------------------------------------------------
        # 5. Diff Inspection & Reviewer Agent
        # ----------------------------------------------------------------------
        diff_res = self.mcp.call_tool("get_diff", {})
        state.git_diff = diff_res.output if diff_res.success else ""

        if state.tests_passed:
            state.status = "reviewing"
            state.record_event("Reviewer Agent inspecting unified diff for security and code quality...")
            emit("reviewing_started", {"message": "Conducting code review and generating PR description..."})

            review: ReviewSummary = self.reviewer.review_changes(task=task, diff=state.git_diff)
            state.record_event(
                f"Code review completed: Risk Level={review.risk_level}. "
                f"Findings={len(review.security_findings)}. PR Title: '{review.title}'"
            )
            emit("reviewing_completed", {
                "risk_level": review.risk_level,
                "title": review.title,
                "pr_markdown": review.pr_markdown
            })

            state.status = "completed"
            state.record_event("Autonomous self-healing engineering loop completed successfully.")
            emit("session_completed", {"status": "completed", "tests_passed": True})

        else:
            if state.status != "escalate_to_human":
                state.status = "failed"
            state.record_event(f"Autonomous loop finished with status: {state.status}")
            emit("session_completed", {"status": state.status, "tests_passed": False})

        return state


_default_loop: Optional[AutonomousLoop] = None


def get_autonomous_loop() -> AutonomousLoop:
    """Returns singleton AutonomousLoop instance."""
    global _default_loop
    if _default_loop is None:
        _default_loop = AutonomousLoop()
    return _default_loop

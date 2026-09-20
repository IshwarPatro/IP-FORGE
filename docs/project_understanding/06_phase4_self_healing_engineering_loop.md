# Phase 4: Autonomous Self-Healing Engineering Loop

---

## 1. Executive Summary & Problem Context

In traditional generative AI coding workflows, when a Language Model produces buggy, syntactically broken, or regression-inducing code, the interaction abruptly halts or fails silently. The human developer is forced to copy-paste terminal errors, assertion failures, and stack traces back into the prompt window, manually acting as the feedback loop between the test runner and the model.

**Phase 4 resolves this challenge by closing the feedback loop autonomously.**
We connect the **Planner Agent**, **Coding Agent**, **Test Agent**, **Debugger Agent**, and **Reviewer Agent** into a self-correcting state machine:
$$\text{Task} \longrightarrow \text{Plan} \longrightarrow \text{Branch} \longrightarrow \text{Code} \longrightarrow \text{Test} \mathrel{\mathop{\rightleftarrows}^{\text{Pass}}_{\text{Fail}}} \left[\text{Debug} \longrightarrow \text{Patch} \longrightarrow \text{Test}\right] \longrightarrow \text{Review} \longrightarrow \text{PR}$$

### Hard Safety Governor: The 3-Iteration Limit
Autonomous self-healing loops without termination bounds are prone to infinite loops and massive token budget exhaustion (e.g. an agent oscillating between two mutually incompatible assertions). **IP FORGE enforces a strict architectural governor**:
- Maximum self-healing attempts are hard-capped at **3 iterations** (`MAX_SELF_HEAL_ITERATIONS = 3`).
- If tests remain unverified after 3 automated repair cycles, the state machine halts, transitions to `status="escalate_to_human"`, and serializes the complete diagnostic history, stack traces, and attempted patches into the audit trail for immediate developer inspection.

---

## 2. Technical Architecture & Engineering Decisions

```
                           +------------------------------+
                           |  Developer Task Ingestion    |
                           +--------------+---------------+
                                          |
                                          v
                           +------------------------------+
                           |   Planner + Architect (RAG)  |
                           +--------------+---------------+
                                          |
                                          v
                           +------------------------------+
                           | Git Branch Isolation Created |
                           |     (forge/task-<session>)   |
                           +--------------+---------------+
                                          |
                                          v
                           +------------------------------+
                           |  Coding Agent Executes Steps |
                           +--------------+---------------+
                                          |
                                          v
                           +------------------------------+
                           |  Test Agent (Sandboxed MCP)  |
                           +--------------+---------------+
                                          |
                        +-----------------+-----------------+
                        |                                   |
                  [Tests Passed]                      [Tests Failed]
                        |                                   |
                        v                                   v
         +------------------------------+     +-------------------------------+
         | Reviewer Agent (Diff & PR)   |     |   Retry Count < 3?            |
         +--------------+---------------+     +-------+---------------+-------+
                        |                             |               |
                        v                           [Yes]            [No]
         +------------------------------+             |               |
         | Complete: PR Ready for Merge |             v               v
         +------------------------------+     +---------------+ +-------------+
                                              | Debugger Agent| | Escalation  |
                                              | RCA & Patch   | | to Human    |
                                              +-------+-------+ | Dashboard   |
                                                      |         +-------------+
                                                      v
                                              +---------------+
                                              | Coding Agent  |
                                              | Applies Patch |
                                              +-------+-------+
                                                      |
                                                      +---> (Re-run Test Agent)
```

### Architectural Highlights:
1. **Sandboxed Test Telemetry Ingestion (`TestAgent`):**
   - Dispatches `execute_test_command` through the MCP security layer (blocking shell escapes and enforcing a 30s timeout).
   - Regex and structural parsers extract execution duration, passed/failed counts, list of failing test functions, primary assertion errors (e.g., `AssertionError: assert 120.0 == 108.0`), and exact file/line coordinates.
2. **Root Cause Analysis & Precision Patching (`DebuggerAgent`):**
   - Combines the `TestRunResult` telemetry with the source code of the failing file.
   - Formulates a structured `DebuggerDiagnosis` containing the architectural root cause explanation, fix summary, and complete patched Python source code.
   - Operates with a deterministic fallback heuristic if local LLM or cloud endpoints are temporarily offline.
3. **Automated Security Audit & PR Generation (`ReviewerAgent`):**
   - Ingests the unified git diff generated across the task branch.
   - Inspects for security risks (`eval`, `os.system`, command injection patterns, hardcoded secrets, directory traversal).
   - Formulates a GitHub Pull Request markdown document including title, change description, risk level (`LOW`, `MEDIUM`, `HIGH`), and checklist.
4. **State Machine (`AutonomousLoop`):**
   - Central coordinator orchestrating the entire lifecycle.
   - Emits granular real-time event callbacks (`on_event`) across each transition, enabling live telemetry streaming to CLI demos and future Server-Sent Events (SSE) / WebSocket web dashboards.

---

## 3. Key Files & Core Implementations

| File Path | Description |
| :--- | :--- |
| [`forge/agents/tester.py`](file:///Users/ishwar/Desktop/AMD%20Hackerthon/forge/agents/tester.py) | **Test Agent**: Invokes sandboxed pytest/unittest runner, parses terminal output into structured `TestRunResult`, extracts failed test names, assertions, and stack traces. |
| [`forge/agents/debugger.py`](file:///Users/ishwar/Desktop/AMD%20Hackerthon/forge/agents/debugger.py) | **Debugger Agent**: Ingests failure telemetry + source code, produces Root Cause Analysis (RCA), and synthesizes precision code patches. |
| [`forge/agents/reviewer.py`](file:///Users/ishwar/Desktop/AMD%20Hackerthon/forge/agents/reviewer.py) | **Reviewer Agent**: Evaluates unified git diffs, conducts static security scans, and produces GitHub Pull Request markdown documentation. |
| [`forge/orchestrator/loop.py`](file:///Users/ishwar/Desktop/AMD%20Hackerthon/forge/orchestrator/loop.py) | **Autonomous Loop**: Orchestrates closed-loop cycle, enforces the 3-retry limit, maintains `AgentState`, and emits live event telemetry. |
| [`forge/orchestrator/state.py`](file:///Users/ishwar/Desktop/AMD%20Hackerthon/forge/orchestrator/state.py) | **State Models**: Added `git_branch`, `git_diff`, and `status="escalate_to_human"` to `AgentState`. |
| [`forge/api/main.py`](file:///Users/ishwar/Desktop/AMD%20Hackerthon/forge/api/main.py) | **REST Gateway**: Added `POST /execute-task` endpoint allowing web clients and CLI tools to trigger autonomous engineering runs. |
| [`scripts/demo_autonomous_loop.py`](file:///Users/ishwar/Desktop/AMD%20Hackerthon/scripts/demo_autonomous_loop.py) | **Interactive Demo**: Simulates a live code defect, traces real-time self-healing, patch application, and PR generation using Rich UI. |
| [`tests/unit/test_self_healing_loop.py`](file:///Users/ishwar/Desktop/AMD%20Hackerthon/tests/unit/test_self_healing_loop.py) | **Unit Test Suite**: 9 tests validating pytest parsing, debugger RCA, reviewer diff security checks, self-healing recovery, 3-retry ceiling escalation, and FastAPI endpoint. |

---

## 4. Verification & Testing Results

### Automated Test Suite
All 32 tests across the entire IP FORGE codebase pass with zero failures:
```bash
./venv/bin/pytest tests/ -v
```
**Results:**
```
============================= test session starts ==============================
platform darwin -- Python 3.12.7, pytest-9.1.1, pluggy-1.6.0
collected 32 items

tests/dummy_repo/tests/test_api.py ....                                  [ 12%]
tests/unit/test_ast_parser.py .                                          [ 15%]
tests/unit/test_mcp.py .......                                           [ 37%]
tests/unit/test_phase0_config.py ...                                     [ 46%]
tests/unit/test_planner.py ....                                          [ 59%]
tests/unit/test_rag.py ....                                              [ 71%]
tests/unit/test_self_healing_loop.py .........                           [100%]

======================= 32 passed, 2 warnings in 10.17s ========================
```

### Interactive Self-Healing CLI Demonstration
```bash
./venv/bin/python scripts/demo_autonomous_loop.py
```
**Execution Telemetry Summary:**
```
       Autonomous Loop Execution Summary        
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Metric                  ┃ Value              ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Session ID              │ a1ca26b2           │
│ Task Status             │ COMPLETED          │
│ Tests Passed            │ True (100% Passed) │
│ Self-Healing Iterations │ 1 / 3              │
│ Total Runtime           │ 7.90 seconds       │
│ Audit Trail Entries     │ 19                 │
└─────────────────────────┴────────────────────┘
```

---

## 5. Defense Briefing: 10 Critical Technical Questions for Ishwar Patro

### Q1: Why is an autonomous self-healing loop necessary instead of simply generating better code on the first attempt?
**Answer:** Even the most capable frontier models (GPT-4o, Claude 3.5 Sonnet) fail on real-world engineering tasks on their first attempt due to subtle API nuances, implicit business logic constraints, and boundary condition mismatches. In software engineering, code quality is achieved through iterative verification (TDD/debugging). Autonomous self-healing enables the agent to test its own hypotheses against an actual test runner, intercept errors, and self-correct without interrupting the developer.

### Q2: How does IP FORGE prevent infinite loops where an agent flips between contradictory fixes?
**Answer:** IP FORGE enforces a strict hard governor: `MAX_SELF_HEAL_ITERATIONS = 3`. The state machine tracks `state.retry_count`. If `retry_count >= 3` and tests still fail, execution immediately halts, transitions to `status="escalate_to_human"`, records all attempted fixes and failure traces in the immutable audit trail, and presents the session for developer intervention.

### Q3: How does the Test Agent reliably extract stack traces and assertion messages from raw terminal outputs?
**Answer:** The Test Agent combines structured regex patterns and positional section markers. It scans for pytest summary bars (`=== X failed, Y passed in Z.ZZs ===`), failing test lines (`FAILED <test_path>::<test_name>`), assertion blocks (`E   AssertionError: ...`), and line pointers (`<file>.py:<line>: AssertionError`). It packages these into a strongly typed `TestRunResult` model, separating raw stdout from structured telemetry.

### Q4: How does the Debugger Agent decide which file to patch when a test fails?
**Answer:** The Debugger Agent applies a multi-level resolution heuristic:
1. It inspects `test_result.failing_file`. If it points to an application file (e.g. `app/utils.py`), it targets that file directly.
2. If `failing_file` points to the test suite itself (e.g. `tests/test_api.py`), it inspects the plan's `files_to_modify` and AST symbols touched in the failing test to identify the underlying service being tested.
3. If an explicit `target_file` was specified in the task request, it prioritizes that file.

### Q5: How does IP FORGE ensure the self-healing patch doesn't introduce severe security vulnerabilities (e.g. bypasses, command injection)?
**Answer:** Before any code is marked as ready or committed, the **Reviewer Agent** runs an automated security audit on the unified git diff. It scans for risky constructs (`eval`, `exec`, `os.system`, unvalidated path joins, hardcoded credentials). If any dangerous pattern is found, the risk level is set to `HIGH`, the findings are flagged in the PR review, and automated merging is blocked.

### Q6: What happens if the local LLM or cloud reasoning backend is offline during self-healing?
**Answer:** Both `DebuggerAgent` and `ReviewerAgent` feature deterministic fallback engines. If the LLM client health-check fails, the agents execute rule-based heuristic analyzers. For example, the Debugger Agent detects common mathematical/logical inversion bugs (e.g. `+` vs `-` in discount deduction) and applies verified corrections, ensuring CI/CD pipelines and demos remain fully operational.

### Q7: Why does the Autonomous Loop create a dedicated Git branch (`forge/task-<session_id>`) for each execution?
**Answer:** To guarantee production safety and branch isolation. Code modifications and experimental patches must never occur on `main`, `master`, or release branches. Creating `forge/task-<session_id>` isolates all working tree modifications. If a task fails or is rejected, the branch can be deleted without impacting the main branch.

### Q8: How does the Autonomous Loop communicate state changes in real time to the frontend dashboard?
**Answer:** `AutonomousLoop.run()` accepts an optional `on_event` callback handler. At every state transition (`planning_started`, `coding_started`, `step_executing`, `testing_failed`, `debugging_diagnosed`, `patch_applied`, `reviewing_completed`), the loop dispatches an event payload with the session ID and telemetry. In Phase 6, this callback is wired to FastAPI Server-Sent Events (SSE) / WebSockets to power the Next.js live developer dashboard.

### Q9: What is the purpose of the `POST /execute-task` API endpoint?
**Answer:** `POST /execute-task` encapsulates the entire multi-agent lifecycle into a single REST API call. It accepts `task`, `target_file`, `test_command`, `create_branch`, and `max_retries`, executes the self-healing state machine asynchronously, and returns a structured response containing the session ID, final status (`completed` or `escalate_to_human`), iterations used, git diff, and full audit log.

### Q10: How will Phase 5 (AMD Developer Cloud / ROCm vLLM) enhance this self-healing loop?
**Answer:** In Phase 4, reasoning currently runs on the local Apple M4 workstation or fallback heuristics. In Phase 5, we transition the heavy reasoning roles (**Planner**, **Debugger**, and **Reviewer**) to the AMD Developer Cloud powered by AMD ROCm 6.x and vLLM. This unlocks 70B+ parameter models (e.g. DeepSeek-R1 / Llama-3-70B), dramatically increasing first-attempt plan accuracy and complex multi-file root cause analysis speed.

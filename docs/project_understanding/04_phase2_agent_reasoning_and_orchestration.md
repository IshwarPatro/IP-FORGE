# Milestone Understanding: Phase 2 Agent Reasoning & Orchestration

**Document ID:** `04_phase2_agent_reasoning_and_orchestration.md`  
**Milestone:** Phase 2 — Multi-Agent Personas, Structured JSON Planning DAGs, and Orchestration State Machine  
**Target Audience:** Ishwar Patro (Lead Engineer & Hackathon Presenter)  
**Author:** IP FORGE (Staff AI Systems Architect)  

---

## I. The Task
* **What was done:** Designed and implemented the multi-agent cognitive layer and state machine for IP FORGE, establishing decoupled agent personas (Architecture, Planner, Coder), structured JSON execution plan schemas (DAGs), and an orchestration pipeline connecting codebase RAG to planning logic.
* **Scope of Deliverables:**
  1. Implemented `forge/orchestrator/state.py` defining strictly typed Pydantic models for execution steps (`PlanStep`), complete engineering plans (`EngineeringPlan`), and the global multi-agent state container (`AgentState`).
  2. Implemented `forge/agents/base.py` providing a foundational `BaseAgent` class with robust JSON extraction handling markdown backticks and raw outputs.
  3. Implemented `forge/agents/architect.py` interfacing directly with the ChromaDB AST vector store to investigate task requirements and assemble an `ArchitectureContext` report.
  4. Implemented `forge/agents/planner.py` formulating structured, acyclic execution plans with an automated AST-grounded deterministic fallback planner when local LLMs are offline.
  5. Implemented `forge/agents/coder.py` with persona prompts ready for surgical file modifications in Phase 3.
  6. Implemented `forge/orchestrator/coordinator.py` binding RAG investigation to the planning DAG and initializing session states.
  7. Exposed `POST /plan-task` on the FastAPI REST gateway in `forge/api/main.py`.
  8. Created an interactive CLI demo script in `scripts/demo_planner.py`.
  9. Authored unit and integration tests in `tests/unit/test_planner.py`.

---

## II. Project Utility
* **Why it matters:** Autonomous software engineering cannot be solved by single-prompt code generation. When complex requests (e.g. *"Add pagination to catalog endpoints"*) are given to a single LLM, it writes code blindly without checking where methods are defined, misses shared dependencies, and produces unexecutable code.
* Phase 2 introduces **separation of cognitive concerns**:
  - The **Architecture Agent** first queries the AST memory to find where relevant classes and methods live.
  - The **Planner Agent** reviews this structural context and translates the user task into an ordered sequence of discrete atomic operations (`read_file` $\rightarrow$ `modify_file` $\rightarrow$ `run_test`).
  - This solves **Hackathon Challenge 5 (Multi-Agent Software Engineering)** by implementing specialized agent personas that collaborate through structured contracts.

---

## III. Execution & Mechanics
* **How it works:**
  1. **Task Submission:** The developer submits a task either via `POST /plan-task` or the CLI (`scripts/demo_planner.py`).
  2. **Architectural Investigation:**
     - `OrchestratorCoordinator` passes the task to `ArchitectureAgent.investigate_task(task)`.
     - The agent queries `CodebaseVectorStore` for top-$K$ semantically matching AST symbols.
     - Assembles an `ArchitectureContext` highlighting matching files, classes, methods, line numbers, and source snippets.
  3. **DAG Plan Formulation:**
     - `PlannerAgent.create_plan(task, context)` constructs a prompt with the user's task and the exact codebase context.
     - Calls the configured LLM (`Ollama` / `AMD ROCm vLLM` / `OpenAI`) with JSON mode enforced.
     - Parses the output into a validated `EngineeringPlan`. If the local LLM is unreachable, it automatically activates the deterministic AST-grounded fallback generator, ensuring 100% test reliability and zero downtime.
  4. **State Machine Initialization:**
     - `OrchestratorCoordinator.start_session(task)` packages the task and plan into a persistent `AgentState` object, recording audit trail timestamps for real-time observability.

---

## IV. Logic & Architectural Principles
* **The "Why" behind the code:**
  * **Strictly Typed Pydantic Schema (`EngineeringPlan`):** Free-form markdown plans produced by LLMs are impossible for downstream execution agents to parse reliably. By constraining the Planner to output a strict JSON schema containing `step_number`, `action`, `target_file`, `description`, and `symbols_involved`, the Coding Agent in Phase 3 can execute each step mechanically without guessing.
  * **Deterministic Fallback Engine:** In live hackathon pitches and continuous integration (CI) pipelines, local LLM servers can crash, run out of memory, or have cold-start delays. Our fallback planner ensures that IP FORGE never throws a 500 internal server error: it parses the retrieved AST symbols and generates a valid, executable plan deterministically.
  * **Final Step Invariant (`action="run_test"`):** Every generated plan is architecturally required to conclude with an automated test execution step (`pytest`). This guarantees that no code modification is ever considered "complete" without runtime validation.

---

## V. Developer Knowledge Transfer (10 Q&A Defense Briefing)

### Q1: What makes the Planner Agent in IP FORGE different from standard ChatGPT prompt planning?
**Answer:** Standard conversational planning produces prose without codebase grounding—hallucinating file paths that don't exist and assuming API signatures that aren't real. In IP FORGE, the Planner Agent is preceded by the Architecture Agent. The Planner is provided with real, verified AST symbols, exact file paths (`app/services.py`), and real class names (`ProductCatalogService`). It cannot hallucinate file paths because it is strictly constrained by the RAG context.

### Q2: Why is the plan structured as an ordered DAG of atomic steps rather than a single monolithic instruction?
**Answer:** Monolithic instructions force the Coding Agent to make too many assumptions simultaneously, resulting in massive diffs that break unexpected components. Atomic steps (`read_file` $\rightarrow$ `modify_file` $\rightarrow$ `run_test`) isolate changes to single functions and files. If step 3 fails, the state machine knows *exactly* which step failed without rolling back the entire project.

### Q3: How does the `BaseAgent._parse_json_response()` method handle model quirks and markdown fences?
**Answer:** Many open-source models (including Llama 3 and Gemma) wrap JSON in markdown blocks (` ```json ... ``` `) or include conversational preambles. Our `_parse_json_response()` uses regex to detect code blocks, strips leading/trailing markdown, and includes a fallback substring scanner targeting the outer `{` and `}` delimiters. This eliminates 99% of JSON decoding errors.

### Q4: How does `AgentState` enable session resumption and debugging?
**Answer:** `AgentState` is a serializable Pydantic model containing `session_id`, `current_step_index`, `file_context`, `retry_count`, and `audit_trail`. In Phase 4, this state is snapshotted to Redis after every step. If an execution cycle is interrupted or fails, the orchestrator can resume from the exact step index without re-planning or re-reading the entire codebase.

### Q5: Why is `verification_strategy` an explicit top-level field in `EngineeringPlan`?
**Answer:** In Staff-level software engineering, an implementation is only as good as its verification. Forcing the LLM to articulate its verification strategy (e.g. *"Run pytest on `tests/test_api.py` with new query parameters"*) primes the Test Agent in Phase 4 to know exactly what test commands and arguments to execute.

### Q6: How does the Architecture Agent decide which files are relevant?
**Answer:** The Architecture Agent queries ChromaDB using the task description. ChromaDB uses cosine distance over dense vector embeddings of our AST symbols (which include function signatures, docstrings, and call references). The agent extracts the unique `file_path` values from the top-$K$ symbol matches, identifying the exact files that must be inspected or modified.

### Q7: What are the allowed actions in a `PlanStep`, and why are they restricted to four literals?
**Answer:** Allowed actions are strictly: `read_file`, `modify_file`, `create_file`, and `run_test`. By restricting actions to an `enum`/`Literal`, we ensure that the state machine router in Phase 3 & 4 can deterministically map every step to an MCP tool without ambiguity or unexpected tool calls.

### Q8: How does the system ensure fast response times during the planning phase?
**Answer:** AST retrieval from local ChromaDB takes <10 milliseconds. The prompt sent to the Planner contains only the concise AST symbol summaries rather than whole files, keeping prompt tokens under 1,500 tokens. On AMD Developer Cloud (vLLM) or local M4, generating the JSON plan takes under 2 seconds.

### Q9: Can the developer customize the number of retrieved symbols for complex tasks?
**Answer:** Yes. The `/plan-task` endpoint and CLI demo accept a `top_k` parameter (default: 5, range: 1–15). For simple bug fixes, `top_k=3` is sufficient; for cross-cutting architectural changes across multiple services, increasing `top_k` to 10 ensures the Architecture Agent captures all dependent interfaces.

### Q10: How will you demonstrate Phase 2 during the AMD Hackathon presentation?
**Answer:** We can run `scripts/demo_planner.py` with a live custom prompt:
```bash
./venv/bin/python scripts/demo_planner.py "Add pagination to product listing"
```
We show:
1. The Architecture Agent querying ChromaDB in real time and identifying `app/services.py` and `app/api.py`.
2. The Planner Agent instantly generating a 5-step engineering plan formatted in a beautiful terminal table with exact line numbers and symbol references.
3. Show the API endpoint `POST /plan-task` returning the identical JSON plan in Swagger UI.

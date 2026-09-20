# Milestone Understanding: Phase 3 Model Context Protocol (MCP) Tooling

**Document ID:** `05_phase3_mcp_tooling_subsystem.md`  
**Milestone:** Phase 3 — Model Context Protocol (MCP) Server, Sandboxed Filesystem, Terminal Runner, and Git Tools  
**Target Audience:** Ishwar Patro (Lead Engineer & Hackathon Presenter)  
**Author:** IP FORGE (Staff AI Systems Architect)  

---

## I. The Task
* **What was done:** Implemented the Model Context Protocol (MCP) tooling subsystem for IP FORGE, providing secure, sandboxed interfaces for filesystem reads/writes, terminal test execution, and Git branch isolation.
* **Scope of Deliverables:**
  1. Implemented `forge/mcp/fs_tools.py` providing sandboxed filesystem utilities (`read_file`, `write_file`, `list_dir`, `file_exists`) with strict path canonicalization preventing directory traversal attacks outside `tests/dummy_repo`.
  2. Implemented `forge/mcp/terminal_tools.py` executing test runners (`pytest`, `python -m unittest`, `ruff`) with regex-based command injection blocking (disallowing `;`, `&&`, `|`, `rm`, `sudo`, `curl`) and an enforced 30-second execution timeout.
  3. Implemented `forge/mcp/git_tools.py` ensuring all autonomous modifications occur in isolated task branches (`forge/task-<id>`), physically preventing direct pushes to `main`/`master`.
  4. Implemented `forge/mcp/server.py` as a centralized MCP server and tool registry exposing standard JSON-schemas for LLM tool binding.
  5. Updated `forge/agents/coder.py` allowing the Coding Agent to dispatch plan steps through the MCP server.
  6. Exposed `GET /mcp/tools` and `POST /mcp/execute` on the FastAPI REST gateway in `forge/api/main.py`.
  7. Created an interactive CLI demo in `scripts/demo_mcp.py` demonstrating safe reads, path traversal blocking, and sandboxed test execution.
  8. Authored unit and integration test suites in `tests/unit/test_mcp.py`.

---

## II. Project Utility
* **Why it matters:** An AI agent that can only output code snippets in chat is a glorified search engine. To be a true autonomous software engineer, the agent needs "physical hands" to touch the environment: inspecting files, writing updates, running tests, and managing branches.
* However, giving an LLM direct shell or filesystem access is a major security risk. 
* Phase 3 solves this via **Model Context Protocol (MCP) sandboxing**:
  - The agent interacts only through strictly typed tool definitions.
  - Operations are physically bounded to the target repository.
  - Test executions are sandboxed and monitored with automated timeouts.
* This delivers on **Hackathon Core Requirement (Agent Tooling & MCP)**, ensuring IP FORGE is both fully autonomous and completely secure.

---

## III. Execution & Mechanics
* **How it works:**
  1. **Tool Registration (`MCPServer`):**
     - Each tool is registered with its function callable, docstring, and JSON schema describing required parameters.
     - The `MCPServer.list_tools()` method exposes these schemas for OpenAI / vLLM function-calling compatibility.
  2. **Path Sanitization & Traversal Interception (`FilesystemTools`):**
     - When `read_file(path)` or `write_file(path, content)` is called, the path is stripped of leading slashes and resolved: `(sandbox_root / path).resolve()`.
     - The path is validated via `resolved.relative_to(sandbox_root)`. If an attacker or hallucinating agent passes `../../etc/passwd`, it raises a `PermissionError` and returns `ToolResult(success=False)`.
  3. **Command Sanitization & Subprocess Execution (`TerminalTools`):**
     - Incoming commands are scanned against `FORBIDDEN_PATTERNS` to block shell chaining (`;&|`), command substitution (`$()`), and dangerous binaries (`rm`, `sudo`, `curl`).
     - Command tokens are verified against `ALLOWED_COMMAND_PREFIXES` (`pytest`, `ruff`, etc.).
     - Subprocesses run in the target repository directory with `timeout=30`, capturing `stdout`, `stderr`, and `returncode`.
  4. **Agent Step Execution (`CodingAgent.execute_step`):**
     - Translates high-level plan actions:
       - `action="read_file"` $\rightarrow$ calls `mcp.call_tool("read_file")`.
       - `action="modify_file"` $\rightarrow$ reads existing file, formulates code patch, calls `mcp.call_tool("write_file")`.
       - `action="run_test"` $\rightarrow$ calls `mcp.call_tool("execute_test_command")`.

---

## IV. Logic & Architectural Principles
* **The "Why" behind the code:**
  * **Open Standard Alignment:** We adopted the Model Context Protocol (MCP) convention. Separating tool logic into a standalone tool registry allows IP FORGE to connect to external MCP servers (e.g. GitHub MCP, Postgres MCP, Docker MCP) in future enterprise environments without changing agent code.
  * **Defense-in-Depth for File and Shell Access:** Rather than relying on LLMs to "be safe", we enforce hardware and OS-level boundaries:
    - Path canonicalization catches all relative and symlink traversal escapes.
    - Token-based shell parsing via `shlex.split()` prevents hidden bash injection attacks.
    - Subprocess timeouts prevent denial-of-service from infinite loops.
  * **Unified Return Schema (`ToolResult`):** Every single tool returns a standardized Pydantic model (`success: bool`, `output: str`, `error: Optional[str]`, `metadata: dict`). This allows our state machine in Phase 4 to handle tool outputs uniformly.

---

## V. Developer Knowledge Transfer (10 Q&A Defense Briefing)

### Q1: What is the Model Context Protocol (MCP), and why did we implement it in IP FORGE?
**Answer:** Model Context Protocol (MCP) is an open standard designed to standardize how AI applications provide context and tools to LLMs. Instead of hardcoding bespoke function calls inside prompts, MCP decouples the tool provider from the LLM. It defines clear JSON schemas for tool capabilities, standardizes argument validation, and provides uniform execution responses, making agent systems modular and extensible.

### Q2: How does the Filesystem MCP tool prevent path traversal attacks (e.g. `../../etc/passwd`)?
**Answer:** The `_resolve_and_validate_path()` method uses Python's `pathlib.Path.resolve()` to resolve all relative tokens (`..`), symlinks, and absolute paths into a canonical filesystem location. It then calls `resolved_path.relative_to(sandbox_root)`. If the path points anywhere outside the designated sandbox root, Python raises a `ValueError`, which we intercept to block the operation and log a security alert.

### Q3: What happens if an agent tries to run a destructive command like `rm -rf /` or `curl exfiltrate.com`?
**Answer:** The `TerminalTools` class runs a multi-layered verification:
1. Regex filter: Scans for shell chaining (`;&|`), redirects (`>`), and blacklisted binaries (`rm`, `sudo`, `curl`, `wget`).
2. Prefix allowlist: Verifies that the command begins with an approved test runner (`pytest`, `python -m unittest`, `ruff`).
If any check fails, execution is immediately aborted with a `PermissionError` before any subprocess is spawned.

### Q4: How does IP FORGE prevent hanging or infinite loops when running tests via Terminal MCP?
**Answer:** The `subprocess.run()` invocation enforces a strict `timeout` parameter (configured via `settings.MCP_EXECUTION_TIMEOUT_SECONDS`, default 30 seconds). If a test hangs or gets stuck in an infinite loop, the operating system raises a `TimeoutExpired` exception, the subprocess is killed, and a clean error message is returned to the agent.

### Q5: How does Git MCP enforce branch safety?
**Answer:** `GitTools` maintains a list of `PROTECTED_BRANCHES` (`main`, `master`, `release`, `prod`). The `commit_changes()` and `create_task_branch()` methods inspect the current active branch using `git branch --show-current`. If the active branch is in the protected list, all write and commit operations are blocked, forcing the agent to operate exclusively on isolated task branches (`forge/task-*`).

### Q6: Can external clients or frontends invoke MCP tools directly?
**Answer:** Yes. In `forge/api/main.py`, we exposed `GET /mcp/tools` (which returns schemas for all registered tools) and `POST /mcp/execute` (which accepts `tool_name` and `arguments`). This allows the Next.js web dashboard in Phase 6 to trigger tools, inspect files, and execute tests directly through the verified security gateway.

### Q7: What is the structure of `ToolResult`, and why is it useful for the Debugger Agent in Phase 4?
**Answer:** `ToolResult` contains `success: bool`, `output: str`, `error: Optional[str]`, and `metadata: Dict[str, Any]` (which includes exit codes, execution duration, and paths). When `execute_test_command` fails, the complete stdout and stderr are packaged into `output`, and `error` contains the exit code. This gives the Debugger Agent in Phase 4 the exact stack trace needed to diagnose failures.

### Q8: Does the Filesystem MCP tool allow editing files in the `.git` folder?
**Answer:** No. Even though `.git` resides inside the repository sandbox, `_resolve_and_validate_path()` explicitly checks `if ".git" in resolved.parts:`. Attempting to touch `.git` raises a `PermissionError`, protecting the underlying Git commit history and index from corruption.

### Q9: How does the Coding Agent use MCP tools during plan execution?
**Answer:** When `CodingAgent.execute_step(step)` is called, it inspects `step.action`. If the action is `read_file`, it calls the `read_file` tool. If the action is `modify_file`, it reads the current file content, calls the LLM to generate the updated source code, and calls the `write_file` tool. If the action is `run_test`, it calls `execute_test_command`.

### Q10: How will you demonstrate Phase 3 during the AMD Hackathon pitch?
**Answer:** We can demonstrate Phase 3 live using `scripts/demo_mcp.py`:
1. Show the registered MCP tool table with parameters.
2. Show a successful sandboxed file read of `app/utils.py`.
3. Demonstrate the security defense by executing `read_file('../../etc/passwd')` and showing the immediate security rejection.
4. Show sandboxed test execution of `pytest` passing with exit code 0.
5. Demonstrate command injection defense by attempting `pytest ; rm -rf /` and showing the immediate block.

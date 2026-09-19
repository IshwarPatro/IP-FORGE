# IP FORGE: Architectural Details

## 1. The Multi-Agent Ecosystem
IP FORGE utilizes a federated multi-agent architecture. The system orchestrates multiple specialized LLM personas, rather than relying on a single monolithic prompt.

* **Planner Agent:** Ingests the developer's task, queries the architecture, and creates a step-by-step engineering plan.
* **Architecture Agent (RAG):** Interfaces with the vector database to answer "Where is X implemented?" and "What dependencies does Y have?"
* **Coding Agent:** Executes the plan by requesting specific file reads/writes via MCP.
* **Test Agent:** Triggers terminal commands (e.g., `npm test`) and reads the stdout/stderr.
* **Debugger Agent:** Analyzes stack traces passed by the Test Agent and formulates a patch.
* **Reviewer Agent:** Performs a final pass for security, performance, and style before submitting to the human.

## 2. Codebase Intelligence Layer (RAG)
Before writing code, the system must understand the repository. 
* **Ingestion:** Parses Abstract Syntax Trees (ASTs), READMEs, database schemas, and API specs.
* **Storage:** Chunks and embeds the data into a local ChromaDB vector store.
* **Retrieval:** Uses hybrid search to provide exact context to the agents.

## 3. Tooling Layer (MCP)
Agents interact with the real world through the Model Context Protocol (MCP).
* **Filesystem MCP:** `read_file`, `write_file`, `list_directory`.
* **Terminal MCP:** `execute_command` (sandboxed for tests/linters).
* **Git MCP:** `create_branch`, `commit_changes`, `create_pr`.

## 4. Human-in-the-Loop (HitL)
IP FORGE is autonomous but strictly governed. The AI cannot push to the main branch. The engineering loop pauses at the Review stage, presenting a Web UI where the human developer can view the agent's log, the file diffs, and test results, and click **Approve** or **Reject**.

# Milestone Understanding: Master Architecture & Roadmap Formulation

**Document ID:** `01_master_architecture_and_roadmap.md`  
**Milestone:** System Understanding & End-to-End Phased Implementation Plan  
**Target Audience:** Ishwar Patro (Lead Engineer & Hackathon Presenter)  
**Author:** IP FORGE (Staff AI Systems Architect)  

---

## I. The Task
* **What was done:** Formulated the master architectural blueprint and end-to-end phased implementation strategy for IP FORGE in [`docs/master_setup_and_implementation_plan.md`](../master_setup_and_implementation_plan.md). 
* **Scope of Deliverables:** 
  1. Defined the system topology encompassing local M4 workstation orchestration and AMD Developer Cloud (ROCm 6.x + vLLM) heavy reasoning.
  2. Structured the six-agent federated ecosystem (Planner, Architect/RAG, Coder, Tester, Debugger, Reviewer) and their data interchange protocols.
  3. Established a strict Model Context Protocol (MCP) tooling and security sandbox framework.
  4. Specified an actionable 6-phase engineering roadmap with concrete milestones, folder structures, and risk mitigation guardrails.

---

## II. Project Utility
* **Why it matters:** In an autonomous agent system, architecture is the primary determinant of reliability. Traditional coding assistants fail because they treat software engineering as a single prompt-completion loop without ground truth. 
* By structuring IP FORGE into a **closed-loop state machine with physical environment interaction (MCP)** and **Abstract Syntax Tree (AST) code intelligence**, we directly address **Challenge 5 (Multi-Agent Software Engineering)** and **Challenge 3 (Proprietary RAG)** of the Lablab x AMD AI Academy Hackathon.
* This blueprint eliminates ambiguity, locks down the tech stack (FastAPI, ChromaDB, LangGraph, Next.js 14, vLLM/ROCm), and provides a deterministic path to building a hackathon-winning submission.

---

## III. Execution & Mechanics
* **How it works:**
  1. **Task Ingestion & Context Grounding:** The developer enters a task via the Next.js UI or CLI. The **Planner Agent** queries the **Architecture Agent**, which performs a hybrid semantic search against local **ChromaDB** collections populated with AST-parsed classes, functions, and import trees.
  2. **Plan Generation:** The Planner outputs a strictly typed JSON DAG of execution steps.
  3. **Physical Tool Execution via MCP:** The **Coding Agent** reads files and writes modifications via standardized MCP JSON-RPC endpoints. Crucially, path sanitization ensures operations stay confined to the target repo.
  4. **Verification & Self-Healing:** The **Test Agent** runs test commands in an isolated subprocess via Terminal MCP. If tests fail, the stderr and stack trace are fed to the **Debugger Agent**, which analyzes line numbers and AST context to generate a corrective patch. This cycle repeats up to a maximum of 3 times.
  5. **Review & Human-in-the-Loop Governance:** Upon test passage, the **Reviewer Agent** verifies code health, and the Next.js dashboard presents an interactive diff. The human developer reviews the changes and clicks **Approve**, at which point the **Git MCP** creates a clean Pull Request.

---

## IV. Logic & Architectural Principles
* **The "Why" behind the code:**
  * **AST Chunking vs. Fixed-Size Chunking:** Naive text chunking splits functions in half, breaking semantic context and hallucinating imports. AST parsing breaks code strictly along syntactic boundaries (classes, functions, method signatures), preserving lexical integrity.
  * **Hybrid Edge-Cloud Topology:** Running local Ollama on the M4 Mac minimizes network latency and cost for quick tool-calling checks. Heavy reasoning (Llama 3 70B across 32k-64k context windows) is routed to AMD Developer Cloud with ROCm-accelerated vLLM, providing optimal throughput and showcasing AMD hardware capability.
  * **Strict 3-Iteration Self-Correction Cap:** Unbounded autonomous loops lead to state drift, token exhaustion, and catastrophic code degradation. A hard cap of 3 iterations enforces fail-safe engineering.
  * **Decoupled MCP Architecture:** Standardizing tool interactions on MCP allows IP FORGE to swap underlying tool implementations (or even plug into external MCP servers) without refactoring the agent core.

---

## V. Developer Knowledge Transfer (10 Q&A Defense Briefing)

### Q1: Why does IP FORGE use AST-based parsing for Code RAG instead of standard recursive text splitters?
**Answer:** Standard splitters chunk by character count or line breaks. In code, this frequently cuts functions in half, separates docstrings from signatures, or severs class inheritance context. By using Python's `ast` module (and Tree-sitter), IP FORGE extracts discrete functional nodes (classes, methods, signatures, docstrings). When the agent queries ChromaDB, it receives complete, syntactically valid code blocks with explicit breadcrumbs (`file -> class -> function`), preventing structural hallucination.

### Q2: How does the hybrid local M4 and AMD Cloud infrastructure split work in practice?
**Answer:** The local M4 workstation handles the lightweight operational layer: the FastAPI API gateway, ChromaDB vector queries, Redis session state, and the Next.js frontend. When an agent needs heavy cognitive processing—such as formulating multi-step execution plans across large codebases or root-cause debugging—it calls our LLM Client Factory. The factory routes the prompt to an AMD Developer Cloud instance running ROCm 6.x and vLLM (hosting models like Llama-3-70B), streaming responses back to the local orchestrator via an OpenAI-compatible API.

### Q3: Why is the Model Context Protocol (MCP) preferred over standard custom agent function calls?
**Answer:** MCP is an emerging open standard that decouples tool definition from model implementation. Using MCP allows our agents to communicate with tools via standardized JSON-RPC protocols. This means our filesystem, terminal, and git tools can run in isolated subprocesses or remote containers, enforces a clear security boundary, and allows our agents to consume external enterprise MCP servers with zero code changes.

### Q4: How does IP FORGE prevent infinite self-healing loops when tests continuously fail?
**Answer:** The orchestration state machine enforces a deterministic state counter (`retry_count`). The self-healing loop between the Test Agent, Debugger Agent, and Coding Agent is capped at exactly 3 iterations. If the tests do not pass on the 3rd attempt, the state machine transitions to an `ESCALATE_TO_HUMAN` state, packaging the cumulative diff, full test output, and debugger hypotheses into a structured report for the developer in the HitL dashboard.

### Q5: Why do we incorporate Redis and PostgreSQL alongside ChromaDB?
**Answer:** Each database serves a distinct tier of storage:
1. **ChromaDB:** Unstructured semantic vector store for AST code embeddings and similarity retrieval.
2. **Redis:** In-memory, sub-millisecond cache for active multi-agent conversation history, live state checkpoints, and real-time Pub/Sub streaming to the web dashboard.
3. **PostgreSQL:** ACID-compliant relational store for long-term task logs, user authentication, run histories, and audit trails.

### Q6: How is the Terminal MCP tool protected against arbitrary or destructive command execution?
**Answer:** Defense-in-depth is applied:
1. **Strict Allowlist:** Only verified test/linter binaries are executable (`pytest`, `python -m unittest`, `npm test`, `ruff check`).
2. **Forbidden Tokens:** Shell chaining (`&&`, `;`, `|`), redirection (`>`, `>>`), subshell expansions (`$()`, `` ` ``), and destructive commands (`rm`, `sudo`, `curl`) are intercepted and raise immediate security faults.
3. **Execution Timeouts:** Commands have a mandatory 30-second execution cap to prevent runaway processes.
4. **Environment Isolation:** Subprocesses run with sanitized environment variables, preventing secret leakage.

### Q7: What is the architectural difference between the Debugger Agent and the Reviewer Agent?
**Answer:** 
* The **Debugger Agent** is an active runtime-repair agent. It is invoked only when tests fail, focusing narrowly on stack traces, line-level errors, and generating corrective code diffs.
* The **Reviewer Agent** is a passive governance and quality-assurance agent. It is invoked only after all tests pass, analyzing the cumulative diff across the entire PR for security vulnerabilities, cyclomatic complexity, adherence to clean coding standards, and generating user-facing release notes.

### Q8: How does the state machine handle context limits when modifying large multi-file repositories?
**Answer:** IP FORGE uses progressive context disclosure. Rather than feeding the entire codebase into the LLM prompt, the Planner only receives high-level file trees and architectural summaries. When the Coding Agent works on a specific step, the Architecture Agent queries ChromaDB to fetch only the relevant file sections and method signatures. Once a file edit is complete, only the resulting Git diff and summary are passed down the state graph, preserving context tokens.

### Q9: How can we prove the performance superiority of AMD ROCm + vLLM during the hackathon demo?
**Answer:** In Phase 5, we implement a latency and throughput benchmarking harness. We will run identical codebase planning and debugging prompts through local quantization (Ollama on M4) versus the AMD Developer Cloud ROCm vLLM endpoint. We will measure and display:
1. **Time-to-First-Token (TTFT)**
2. **Tokens per second (throughput)**
3. **Context window capacity** (processing full repository AST maps of 32k+ tokens where local models run out of VRAM).

### Q10: How does the Human-in-the-Loop (HitL) mechanism ensure zero unauthorized writes to production?
**Answer:** IP FORGE operates under a "Zero-Direct-Push" policy. All autonomous modifications occur in an isolated git branch (`forge/task-<uuid>`). The Git MCP tool is physically blocked from pushing to `main` or merging branches. Only when the human developer explicitly clicks "Approve" in the Next.js web dashboard does the orchestrator trigger the creation of a Pull Request for human merge.

# IP FORGE: Implementation Roadmap

This document outlines the sequential phases to build IP FORGE. **Do not move to the next phase until the current phase is fully tested and operational.**

## Phase 1: Codebase Intelligence (The RAG Layer)
* **Goal:** Build the system's memory.
* **Tasks:** 
  1. Write a Python script to traverse a dummy target repository.
  2. Implement an AST parser to extract functions, classes, and signatures.
  3. Chunk the code, generate embeddings, and store them in ChromaDB.
  4. Build a FastAPI endpoint `POST /query-architecture` that accepts a question and returns relevant code snippets.

## Phase 2: Agent Reasoning & Orchestration
* **Goal:** Create the LLM personas and decision logic.
* **Tasks:**
  1. Define system prompts for the Planner, Architect, and Coder.
  2. Build the router logic that takes a user task ("Add pagination") and creates a structured JSON plan.
  3. Wire the Architect agent to the Phase 1 RAG endpoint.

## Phase 3: Model Context Protocol (MCP) Tooling
* **Goal:** Give the agents hands to touch the file system.
* **Tasks:**
  1. Implement an MCP server in Python.
  2. Create `read_file(path)` and `write_file(path, content)` tools.
  3. Create an `execute_terminal(command)` tool restricted to safe commands (e.g., `npm run test`).
  4. Ensure the Coding Agent can successfully use these tools via function calling.

## Phase 4: The Autonomous Engineering Loop
* **Goal:** Connect the agents into a self-correcting cycle.
* **Tasks:**
  1. Write the state machine (e.g., LangGraph or custom while-loop).
  2. Implement logic: `Plan -> Code -> Test`.
  3. If Test fails -> Extract stderr -> Send to Debugger Agent -> Update Code -> Test again.
  4. Cap the retry loop at 3 iterations to prevent infinite loops.

## Phase 5: AMD Cloud Integration & Scaling
* **Goal:** Switch from local prototyping to cloud reasoning.
* **Tasks:**
  1. Boot the AMD Developer Cloud instance with ROCm and vLLM.
  2. Swap out the local Ollama LLM client for the AMD OpenAI-compatible endpoint.
  3. Run performance tests (tokens/sec) and tune prompt token limits.

## Phase 6: Human-in-the-Loop Dashboard
* **Goal:** Build the Next.js developer UI.
* **Tasks:**
  1. Bootstrap a Next.js app.
  2. Build a view to submit tasks.
  3. Build a real-time event stream to show what the agents are currently doing (e.g., "Agent reading user.ts", "Agent running tests").
  4. Build a final Diff View with an [Approve] and [Reject] button.

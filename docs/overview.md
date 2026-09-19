# IP FORGE: System Overview

**Tagline:** "Don't ask AI to write code. Give it an engineering task."

## 1. The Problem
Modern AI coding assistants operate primarily at the file or prompt level. Real software development, however, requires understanding entire codebases, tracing dependencies, modifying multiple components, running tests, debugging failures, and maintaining architectural consistency. Generating a single function is easy; adding pagination to a production API without breaking the frontend or database queries is hard.

## 2. The Solution: IP FORGE
**IP FORGE** (Federated Orchestrator for Reliable Generation & Engineering) is an autonomous AI software engineering agent. Instead of acting as a coding chatbot, FORGE treats the repository as its physical environment. 

It receives a high-level developer request, builds contextual knowledge using RAG, plans the implementation, modifies the code via Model Context Protocol (MCP) tools, runs tests, self-corrects failures, and presents a final, reviewable Pull Request for human approval.

## 3. Hackathon Alignment (Lablab x AMD AI Academy)
This project is explicitly designed to win the AMD Hackathon by checking every major technical requirement:
* **Multi-Agent Software Engineering (Challenge 5):** Specialized agents handle distinct phases of the SDLC.
* **Agent Tooling & MCP (Core):** Agents use standard MCP tools to read/write files and execute terminal commands.
* **Proprietary RAG (Challenge 3):** Codebases are proprietary. We use ChromaDB to ingest ASTs and architecture docs to prevent hallucination.
* **AMD GPU Infrastructure:** Local prototyping runs on an Apple M4 Mac (Ollama), while heavy reasoning and production inference are offloaded to AMD Developer Cloud (ROCm + vLLM).

## 4. IP FORGE vs. Traditional Copilots
| Feature | Traditional AI | IP FORGE |
| :--- | :--- | :--- |
| **Input** | Prompt -> Code | Task -> Engineering Workflow |
| **Context** | Current file / manual includes | Full repository RAG index |
| **Execution** | Developer runs tests | Agent executes tests via MCP |
| **Debugging** | Developer pastes errors | Agent reads stack trace & fixes |
| **Output** | Code snippets | Review-ready Pull Request |

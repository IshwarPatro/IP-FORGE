# IP-FORGE

<p align="center">
  <img src="IP_FORGE_Banner.png" alt="IP FORGE Banner" width="100%"/>
</p>

<p align="center">
  <strong>Federated Orchestrator for Reliable Generation & Engineering</strong><br/>
  <em>"Don't ask AI to write code. Give it an engineering task."</em>
</p>

---

## ⚡ Overview
**IP FORGE** is an autonomous AI software engineering agent designed to treat codebases as its physical environment. Rather than producing disconnected snippets, IP FORGE receives high-level engineering tasks, builds contextual repository intelligence via Abstract Syntax Tree (AST) RAG, devises phased execution plans, modifies code using the Model Context Protocol (MCP), runs tests, self-heals failures, and submits human-reviewable Pull Requests.

Built for the **Lablab x AMD AI Academy Hackathon**, IP FORGE leverages a hybrid compute architecture: local agent orchestration on Apple Silicon M4 paired with heavy-duty LLM reasoning powered by AMD Developer Cloud (ROCm + vLLM).

---

## 🏛️ Architecture Highlights
* **Federated Multi-Agent Ecosystem:** Specialized personas for Planning, Codebase Intelligence (RAG), Coding, Testing, Debugging, and Code Review.
* **Proprietary Codebase RAG:** AST-based code indexing chunked and embedded into ChromaDB to eliminate hallucination.
* **Model Context Protocol (MCP):** Standardized filesystem, terminal, and git tooling.
* **Self-Healing Engineering Loop:** Autonomous `Plan -> Code -> Test -> Debug` cycle capped at 3 iterations.
* **Human-in-the-Loop (HitL):** Web dashboard for diff reviews and one-click PR approval.

---

## 📚 Documentation Index
All foundational engineering specifications are organized in the [`docs/`](./docs) directory:

* 📄 [System Role & Directives](./docs/system_role_directives.md) — Persona, engineering standards, and documentation mandate.
* 📄 [System Overview](./docs/overview.md) — Problem statement, solution, and hackathon challenge alignment.
* 📄 [Architectural Details](./docs/project_detail.md) — Multi-agent roles, RAG layer, MCP tools, and governance.
* 📄 [Environment & Setup](./docs/setup.md) — Hybrid infrastructure (M4 Mac + AMD ROCm Cloud) and tech stack.
* 📄 [Implementation Roadmap](./docs/phasewise_instruction.md) — Sequential 6-phase engineering plan.
* 📄 [Master Setup & Blueprint](./docs/master_setup_and_implementation_plan.md) — Comprehensive architecture and phase-by-phase implementation plan.
* 📁 [Project Understanding](./docs/project_understanding/) — Milestone-by-milestone technical deep dives and 10-Q&A defense sheets (e.g. [01: Master Architecture](./docs/project_understanding/01_master_architecture_and_roadmap.md), [02: Phase 0 Infrastructure](./docs/project_understanding/02_phase0_infrastructure_and_foundations.md), [03: Phase 1 AST RAG](./docs/project_understanding/03_phase1_ast_rag_layer.md), [04: Phase 2 Agent Reasoning](./docs/project_understanding/04_phase2_agent_reasoning_and_orchestration.md), [05: Phase 3 MCP Tooling](./docs/project_understanding/05_phase3_mcp_tooling_subsystem.md)).

---

## 🚀 Getting Started

### Prerequisites
* Python 3.11+
* Docker & Docker Compose (for Redis and PostgreSQL)
* Ollama (local prototyping) or AMD Developer Cloud instance with ROCm + vLLM

### Quick Setup
```bash
# 1. Clone the repository
git clone https://github.com/IshwarPatro/IP-FORGE.git
cd IP-FORGE

# 2. Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install core dependencies
pip install fastapi uvicorn chromadb langchain openai
```

---

## 🏆 Hackathon Alignment (Lablab x AMD AI Academy)
* **Challenge 5 (Multi-Agent Software Engineering):** Autonomous specialized agents covering the full SDLC.
* **Challenge 3 (Proprietary RAG):** ChromaDB-powered repository indexing with AST parsing.
* **AMD Cloud GPU Acceleration:** ROCm-optimized vLLM deployment for large-context reasoning.

---
**Lead Developer:** Ishwar Patro  
**License:** MIT

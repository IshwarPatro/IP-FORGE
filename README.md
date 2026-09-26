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

Built for the **Lablab x AMD AI Academy Hackathon**, IP FORGE leverages a hybrid compute architecture: local agent orchestration on Apple Silicon M4 paired with heavy-duty LLM reasoning powered by AMD Developer Cloud (ROCm 6.x + vLLM).

---

## 🏛️ Architecture Highlights
* **Federated Multi-Agent Ecosystem:** Specialized personas for Planning, Codebase Intelligence (RAG), Coding, Testing, Debugging, and Code Review.
* **Proprietary Codebase RAG:** AST-based code indexing chunked and embedded into ChromaDB to eliminate hallucination.
* **Model Context Protocol (MCP):** Standardized filesystem, terminal, and git tooling.
* **Self-Healing Engineering Loop:** Autonomous `Plan -> Code -> Test -> Debug` cycle capped at 3 iterations.
* **AMD Developer Cloud Scaling:** High-throughput 70B parameter LLM inference on AMD Instinct GPUs via ROCm 6.x and vLLM.
* **Human-in-the-Loop (HitL) Dashboard:** Next.js 16 web interface with real-time SSE streaming, interactive unified diff viewer, automated PR review packaging, and governance approval gates.

---

## 📚 Documentation Index
All foundational engineering specifications are organized in the [`docs/`](./docs) directory:

* 📄 [System Role & Directives](./docs/system_role_directives.md) — Persona, engineering standards, and documentation mandate.
* 📄 [System Overview](./docs/overview.md) — Problem statement, solution, and hackathon challenge alignment.
* 📄 [Architectural Details](./docs/project_detail.md) — Multi-agent roles, RAG layer, MCP tools, and governance.
* 📄 [Environment & Setup](./docs/setup.md) — Hybrid infrastructure (M4 Mac + AMD ROCm Cloud) and tech stack.
* 📄 [Implementation Roadmap](./docs/phasewise_instruction.md) — Sequential 6-phase engineering plan.
* 📄 [Master Setup & Blueprint](./docs/master_setup_and_implementation_plan.md) — Comprehensive architecture and phase-by-phase implementation plan.
* 📁 [Project Understanding](./docs/project_understanding/) — Milestone-by-milestone technical deep dives and 10-Q&A defense sheets:
  * [01: Master Architecture & Roadmap](./docs/project_understanding/01_master_architecture_and_roadmap.md)
  * [02: Phase 0 Infrastructure & Foundations](./docs/project_understanding/02_phase0_infrastructure_and_foundations.md)
  * [03: Phase 1 AST RAG Layer](./docs/project_understanding/03_phase1_ast_rag_layer.md)
  * [04: Phase 2 Agent Reasoning & Planning](./docs/project_understanding/04_phase2_agent_reasoning_and_orchestration.md)
  * [05: Phase 3 MCP Tooling Subsystem](./docs/project_understanding/05_phase3_mcp_tooling_subsystem.md)
  * [06: Phase 4 Self-Healing Engineering Loop](./docs/project_understanding/06_phase4_self_healing_engineering_loop.md)
  * [07: Phase 5 AMD Cloud & ROCm Scaling](./docs/project_understanding/07_phase5_amd_cloud_integration_and_rocm_scaling.md)
  * [08: Phase 6 Human-in-the-Loop Dashboard](./docs/project_understanding/08_phase6_human_in_the_loop_dashboard.md)

---

## 🚀 Getting Started

### Prerequisites
* Python 3.11+
* Node.js 18+ (Node 20+ recommended)
* Docker & Docker Compose (for Redis and PostgreSQL)
* Ollama (local prototyping) or AMD Developer Cloud instance with ROCm + vLLM

### Quick Setup & Testing
```bash
# 1. Clone the repository
git clone https://github.com/IshwarPatro/IP-FORGE.git
cd IP-FORGE

# 2. Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run complete automated test suite (42 tests across all phases)
pytest tests/ -v

# 4. Run interactive CLI demos & benchmarks
python scripts/demo_rag.py              # Phase 1: AST Codebase Intelligence
python scripts/demo_planner.py          # Phase 2: Multi-Agent Reasoning DAG
python scripts/demo_mcp.py              # Phase 3: Sandboxed MCP Tools
python scripts/demo_autonomous_loop.py  # Phase 4: Self-Healing Closed Loop
python scripts/benchmark_inference.py   # Phase 5: Hardware & Latency Benchmarks
```

---

## 🖥️ Launching the Developer Dashboard (Phase 6)

IP FORGE includes a Next.js 16 Human-in-the-Loop developer dashboard featuring real-time Server-Sent Events (SSE) telemetry, live Git diff inspection, and governance sign-off.

```bash
# Step 1: Start the FastAPI Orchestration Gateway
uvicorn forge.api.main:app --reload --port 8000

# Step 2: In a new terminal, launch the Next.js Frontend
cd dashboard
npm install
npm run dev

# Step 3: Open your browser
# Navigate to http://localhost:3000
```

### Dashboard Capabilities:
1. **Live Agent Activity Stream:** Real-time visibility into Planner, Architect RAG, Coder, Tester, Debugger, and Reviewer execution traces.
2. **Unified Git Diff Viewer:** Color-coded additions (`+ green`) and deletions (`- red`) with line numbers and copy capability.
3. **Automated PR Review Card:** Standardized PR description, risk assessment badge (`LOW`/`MEDIUM`/`HIGH`), and automated verification checklist.
4. **Human Governance Gate:** Strict operator control — `[✓ Approve & Commit to Branch]` or `[✗ Reject & Add Feedback]` to steer self-healing loops.
5. **Dynamic Hardware Switcher:** One-click toggling between **AMD ROCm Cloud (MI300X)** and **Local Apple M4** compute providers.

---

## 🏆 Hackathon Alignment (Lablab x AMD AI Academy)
* **Challenge 5 (Multi-Agent Software Engineering):** Autonomous specialized agents covering the full SDLC.
* **Challenge 3 (Proprietary RAG):** ChromaDB-powered repository indexing with AST parsing.
* **AMD Cloud GPU Acceleration:** ROCm-optimized vLLM deployment for large-context 70B reasoning.
* **Human-in-the-Loop Governance:** Zero unapproved code commits via strict operator gates.

---
**Lead Developer:** Ishwar Patro  
**License:** MIT

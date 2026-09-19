# IP FORGE: Environment & Setup

## 1. Infrastructure Split
To optimize cost and speed, IP FORGE operates on a hybrid local-cloud infrastructure.

* **Local Machine (Apple Silicon M4, 24GB RAM):** Orchestrates the agent framework, runs the vector database, hosts the Next.js frontend, and runs lightweight local LLMs (Ollama) for fast prompt engineering and tool-call testing without burning cloud credits.
* **Cloud Instance (AMD Developer Cloud):** Hosts the heavy-weight open-source models (e.g., Llama 3 70B) via vLLM on ROCm for massive context-window reasoning during full codebase RAG queries.

## 2. Tech Stack Core Components
* **AI Orchestration:** Python 3.11+, FastAPI, LangChain/LlamaIndex.
* **Vector Store:** ChromaDB (local persistent storage).
* **State / Cache:** Redis (for session state between multi-agent loops) and PostgreSQL (for metadata/audit logs).
* **Frontend Dashboard:** Next.js (TypeScript), TailwindCSS.
* **Tooling Standard:** Model Context Protocol (MCP) Python SDK.

## 3. Local Environment Setup Steps
1. **Python Virtual Env:** `python -m venv venv && source venv/bin/activate`
2. **Install AI Core:** `pip install fastapi uvicorn chromadb langchain openai`
3. **Install Local LLM:** Install Ollama and run `ollama run gemma:7b` (or equivalent) for local API fallback.
4. **Database Setup:** Start PostgreSQL and Redis via Docker Compose.
   ```yaml
   services:
     redis:
       image: redis:alpine
       ports: ["6379:6379"]
     postgres:
       image: postgres:15
       environment:
         POSTGRES_PASSWORD: forge
       ports: ["5432:5432"]
   ```

## 4. Cloud Environment Setup Steps (AMD)

1. Provision AMD Developer Cloud Jupyter/SSH instance.
2. Ensure ROCm 6.x is active.
3. Deploy vLLM optimized for ROCm exposing an OpenAI-compatible API endpoint.
4. Set `.env` variable locally: `AMD_VLLM_BASE_URL=http://<amd-ip>:8000/v1`

"""
IP FORGE: REST API Gateway
Exposes architecture query, repository indexing, and multi-agent endpoints.
"""

import platform
from typing import List, Optional, Literal, Dict, Any
import json
import asyncio
import queue
import threading
import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from forge.config import settings, setup_logger
from forge.rag.vector_store import get_vector_store, SearchResult
from forge.orchestrator.coordinator import get_coordinator
from forge.orchestrator.state import EngineeringPlan
from forge.mcp.server import get_mcp_server, ToolDefinition, ToolResult

logger = setup_logger("forge.api.main")

app = FastAPI(
    title="IP FORGE: System Architecture & Orchestrator API",
    description="Autonomous Multi-Agent AI Software Engineering System for AMD Hackathon",
    version="0.1.0"
)

# Enable CORS for Next.js Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------------------
# Request & Response Schemas
# ------------------------------------------------------------------------------

class IndexRequest(BaseModel):
    repo_path: Optional[str] = Field(
        default=None,
        description="Optional absolute or relative path to target repository. Defaults to TARGET_REPO_PATH."
    )


class IndexResponse(BaseModel):
    status: str
    target_path: str
    indexed_symbols_count: int


class ArchitectureQueryRequest(BaseModel):
    query: str = Field(..., description="Developer question or architecture inquiry.")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of relevant code snippets to retrieve.")
    file_filter: Optional[str] = Field(default=None, description="Optional filter by file path.")


class ArchitectureQueryResponse(BaseModel):
    query: str
    results_count: int
    matches: List[SearchResult]


class HealthResponse(BaseModel):
    status: str
    forge_env: str
    llm_provider: str
    chroma_collection: str
    total_indexed_symbols: int


# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root path directly to interactive API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """System health check and vector database telemetry."""
    try:
        vector_store = get_vector_store()
        count = vector_store.collection.count()
        return HealthResponse(
            status="healthy",
            forge_env=settings.FORGE_ENV,
            llm_provider=settings.LLM_PROVIDER,
            chroma_collection=settings.CHROMA_COLLECTION_NAME,
            total_indexed_symbols=count
        )
    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failure: {str(exc)}"
        )


@app.post("/index-repository", response_model=IndexResponse, tags=["RAG"])
def index_repository(request: IndexRequest):
    """Parses ASTs and embeds target repository code into ChromaDB."""
    target_path = Path(request.repo_path) if request.repo_path else settings.target_repo_absolute_path
    if not target_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target repository path does not exist: {target_path}"
        )

    try:
        vector_store = get_vector_store()
        count = vector_store.index_repository(target_path)
        return IndexResponse(
            status="success",
            target_path=str(target_path),
            indexed_symbols_count=count
        )
    except Exception as exc:
        logger.error(f"Indexing failed for {target_path}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AST indexing failed: {str(exc)}"
        )


@app.post("/query-architecture", response_model=ArchitectureQueryResponse, tags=["RAG"])
def query_architecture(request: ArchitectureQueryRequest):
    """
    Answers architectural queries (e.g. 'Where is order processing implemented?')
    by returning top-K AST-grounded code symbols.
    """
    try:
        vector_store = get_vector_store()
        where_filter = {"file_path": request.file_filter} if request.file_filter else None
        matches = vector_store.query_codebase(
            query=request.query,
            top_k=request.top_k,
            where_filter=where_filter
        )
        return ArchitectureQueryResponse(
            query=request.query,
            results_count=len(matches),
            matches=matches
        )
    except Exception as exc:
        logger.error(f"Architecture query failed for '{request.query}': {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(exc)}"
        )


class PlanTaskRequest(BaseModel):
    task: str = Field(..., description="High-level engineering task description.")
    top_k: int = Field(default=5, ge=1, le=15, description="Number of AST symbols to retrieve for context.")


@app.post("/plan-task", response_model=EngineeringPlan, tags=["Planning & Orchestration"])
def plan_task(request: PlanTaskRequest):
    """
    Ingests a developer task, investigates codebase architecture via AST RAG,
    and returns a structured, verified engineering plan.
    """
    try:
        coordinator = get_coordinator()
        plan = coordinator.create_plan_for_task(task=request.task, top_k=request.top_k)
        return plan
    except Exception as exc:
        logger.error(f"Task planning failed for '{request.task}': {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Planning failed: {str(exc)}"
        )


# ------------------------------------------------------------------------------
# Model Context Protocol (MCP) Endpoints
# ------------------------------------------------------------------------------

class ExecuteToolRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the registered MCP tool to execute.")
    arguments: dict = Field(default_factory=dict, description="Key-value arguments for the tool.")


@app.get("/mcp/tools", response_model=List[ToolDefinition], tags=["Model Context Protocol (MCP)"])
def list_mcp_tools():
    """Returns schemas for all registered sandboxed MCP tools."""
    server = get_mcp_server()
    return server.list_tools()


@app.post("/mcp/execute", response_model=ToolResult, tags=["Model Context Protocol (MCP)"])
def execute_mcp_tool(request: ExecuteToolRequest):
    """Executes a sandboxed MCP tool securely."""
    server = get_mcp_server()
    result = server.call_tool(name=request.tool_name, arguments=request.arguments)
    return result


# ------------------------------------------------------------------------------
# Autonomous Self-Healing Loop Endpoints
# ------------------------------------------------------------------------------

class ExecuteTaskRequest(BaseModel):
    task: str = Field(..., description="High-level software engineering task.")
    target_file: Optional[str] = Field(default=None, description="Optional target file to modify/heal.")
    test_command: Optional[str] = Field(default=None, description="Optional custom test command.")
    create_branch: bool = Field(default=True, description="Whether to checkout an isolated git task branch.")
    max_retries: int = Field(default=3, ge=1, le=5, description="Maximum self-healing retry iterations.")


class ExecuteTaskResponse(BaseModel):
    session_id: str
    task: str
    status: str
    tests_passed: bool
    iterations_used: int
    git_branch: Optional[str] = None
    git_diff: Optional[str] = None
    audit_trail: List[str]


@app.post("/execute-task", response_model=ExecuteTaskResponse, tags=["Autonomous Self-Healing Loop"])
def execute_task(request: ExecuteTaskRequest):
    """
    Executes a complete closed-loop engineering task:
    1. Plans DAG via Planner + Architect Agents
    2. Isolates work on a dedicated Git branch
    3. Executes code modifications via MCP tools
    4. Runs tests via Test Agent
    5. Self-heals up to 3 iterations via Debugger Agent if tests fail
    6. Conducts security review and formats PR markdown via Reviewer Agent
    """
    try:
        from forge.orchestrator.loop import get_autonomous_loop
        loop = get_autonomous_loop()
        state = loop.run(
            task=request.task,
            target_file=request.target_file,
            test_command=request.test_command,
            create_branch=request.create_branch
        )
        return ExecuteTaskResponse(
            session_id=state.session_id,
            task=state.task,
            status=state.status,
            tests_passed=state.tests_passed,
            iterations_used=state.retry_count,
            git_branch=state.git_branch,
            git_diff=state.git_diff,
            audit_trail=state.audit_trail
        )
    except Exception as exc:
        logger.error(f"Task execution failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task execution failed: {str(exc)}"
        )


# ------------------------------------------------------------------------------
# Hardware Telemetry & Hybrid Provider Management (Phase 5)
# ------------------------------------------------------------------------------

class HardwareTelemetryResponse(BaseModel):
    local_workstation: Dict[str, Any]
    amd_cloud: Dict[str, Any]
    active_runtime: Dict[str, Any]


class ToggleProviderRequest(BaseModel):
    provider: Literal["ollama", "amd_vllm", "openai"] = Field(..., description="Target inference provider to activate.")
    forge_env: Optional[str] = Field(default=None, description="Optional FORGE_ENV override (e.g. 'amd_cloud' or 'local_m4').")


class ToggleProviderResponse(BaseModel):
    status: str
    previous_provider: str
    active_provider: str
    active_model: str
    active_endpoint: str
    forge_env: str


@app.get("/system/hardware", response_model=HardwareTelemetryResponse, tags=["Hardware & Infrastructure"])
def get_hardware_telemetry():
    """
    Returns hardware split telemetry comparing the local Apple Silicon workstation
    orchestration host against the AMD Developer Cloud ROCm GPU reasoning backend.
    """
    from forge.llm.factory import get_llm_client
    active_cfg = settings.get_active_llm_config()
    client = get_llm_client()

    return HardwareTelemetryResponse(
        local_workstation={
            "chip": settings.LOCAL_CHIP_MODEL,
            "architecture": platform.machine(),
            "os": f"{platform.system()} {platform.release()}",
            "role": "Agent orchestration, sandboxing, AST vector search, and web serving"
        },
        amd_cloud={
            "gpu_model": settings.AMD_GPU_MODEL,
            "rocm_version": settings.AMD_ROCM_VERSION,
            "endpoint": settings.AMD_VLLM_BASE_URL,
            "model": settings.AMD_VLLM_MODEL,
            "vllm_rocm_paged_attn": True,
            "role": "Massive context reasoning for Planner, Debugger, and Reviewer agents"
        },
        active_runtime={
            "forge_env": settings.FORGE_ENV,
            "llm_provider": settings.LLM_PROVIDER,
            "active_model": active_cfg["model"],
            "active_endpoint": active_cfg["base_url"],
            "is_healthy": client.is_healthy()
        }
    )


@app.post("/system/toggle-provider", response_model=ToggleProviderResponse, tags=["Hardware & Infrastructure"])
def toggle_provider(request: ToggleProviderRequest):
    """
    Dynamically toggles active inference provider between Local M4 (Ollama)
    and AMD Developer Cloud (vLLM ROCm) at runtime without requiring server restart.
    """
    from forge.llm.factory import set_active_provider
    prev_provider = settings.LLM_PROVIDER
    if request.forge_env:
        settings.FORGE_ENV = request.forge_env

    set_active_provider(request.provider)
    active_cfg = settings.get_active_llm_config()

    return ToggleProviderResponse(
        status="success",
        previous_provider=prev_provider,
        active_provider=settings.LLM_PROVIDER,
        active_model=active_cfg["model"],
        active_endpoint=active_cfg["base_url"],
        forge_env=settings.FORGE_ENV
    )


# ------------------------------------------------------------------------------
# Real-Time SSE Streaming & HitL Governance Endpoints (Phase 6)
# ------------------------------------------------------------------------------

_governance_sessions: Dict[str, Dict[str, Any]] = {}


@app.post("/execute-task-stream", tags=["Autonomous Self-Healing Loop"])
async def execute_task_stream(request: ExecuteTaskRequest):
    """
    Executes an autonomous task with real-time Server-Sent Events (SSE) streaming updates
    for the Next.js developer dashboard.
    """
    event_queue: queue.Queue = queue.Queue()

    def event_callback(event_name: str, payload: dict):
        event_queue.put({"event": event_name, "data": payload})

    def run_worker():
        try:
            from forge.orchestrator.loop import get_autonomous_loop
            loop = get_autonomous_loop()
            state = loop.run(
                task=request.task,
                target_file=request.target_file,
                test_command=request.test_command,
                create_branch=request.create_branch,
                on_event=event_callback
            )
            # Record in global governance registry
            session_record = {
                "session_id": state.session_id,
                "task": state.task,
                "status": state.status,
                "tests_passed": state.tests_passed,
                "iterations_used": state.retry_count,
                "git_branch": state.git_branch,
                "git_diff": state.git_diff,
                "audit_trail": state.audit_trail,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "governance_decision": "pending"
            }
            _governance_sessions[state.session_id] = session_record
            event_queue.put({"event": "final_state", "data": session_record})
        except Exception as exc:
            logger.error(f"Stream worker error: {exc}", exc_info=True)
            event_queue.put({"event": "error", "data": {"message": str(exc)}})
        finally:
            event_queue.put(None)

    threading.Thread(target=run_worker, daemon=True).start()

    async def sse_generator():
        while True:
            try:
                item = event_queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.05)
                continue

            if item is None:
                yield "event: stream_end\ndata: {}\n\n"
                break

            ev_name = item["event"]
            ev_data = json.dumps(item["data"])
            yield f"event: {ev_name}\ndata: {ev_data}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


class GovernanceDecisionRequest(BaseModel):
    session_id: str
    decision: Literal["approve", "reject"]
    feedback: Optional[str] = None


class GovernanceDecisionResponse(BaseModel):
    status: str
    session_id: str
    decision: str
    message: str


@app.post("/governance/decision", response_model=GovernanceDecisionResponse, tags=["Human-in-the-Loop Governance"])
def submit_governance_decision(request: GovernanceDecisionRequest):
    """
    Submits human approval or rejection of an agent-generated task pull request.
    If approved, commits the changes on the task branch.
    If rejected, registers corrective feedback for iteration.
    """
    session = _governance_sessions.get(request.session_id)
    if not session:
        _governance_sessions[request.session_id] = {
            "session_id": request.session_id,
            "decision": request.decision,
            "feedback": request.feedback
        }
        session = _governance_sessions[request.session_id]

    session["governance_decision"] = request.decision
    session["human_feedback"] = request.feedback

    if request.decision == "approve":
        try:
            server = get_mcp_server()
            msg = f"Human Approved Task: {session.get('task', 'Autonomous patch')}"
            server.call_tool("commit_changes", {"message": msg})
        except Exception as exc:
            logger.warning(f"Git commit on approval: {exc}")

        return GovernanceDecisionResponse(
            status="success",
            session_id=request.session_id,
            decision="approved",
            message="Changes approved by human engineer. Pull Request marked ready to merge."
        )
    else:
        return GovernanceDecisionResponse(
            status="success",
            session_id=request.session_id,
            decision="rejected",
            message=f"Changes rejected with feedback: '{request.feedback or 'No feedback provided'}'. Re-queued for iteration."
        )


@app.get("/governance/sessions", tags=["Human-in-the-Loop Governance"])
def list_governance_sessions():
    """Lists all active and completed engineering sessions for HitL oversight."""
    return list(_governance_sessions.values())




"""
IP FORGE: REST API Gateway
Exposes architecture query, repository indexing, and multi-agent endpoints.
"""

from typing import List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
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


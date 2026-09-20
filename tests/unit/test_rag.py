"""
Unit and Integration tests for Phase 1: AST RAG Layer and FastAPI Endpoints.
"""

from pathlib import Path
import pytest
from starlette.testclient import TestClient
from forge.rag.vector_store import CodebaseVectorStore
from forge.api.main import app


@pytest.fixture(scope="module")
def test_vector_store(tmp_path_factory):
    """Provides an isolated vector store using a temporary ChromaDB directory."""
    temp_dir = tmp_path_factory.mktemp("test_chroma_db")
    store = CodebaseVectorStore(
        persist_dir=str(temp_dir),
        collection_name="test_forge_codebase"
    )
    # Index dummy repo
    repo_path = Path("tests/dummy_repo")
    indexed_count = store.index_repository(repo_path)
    assert indexed_count > 0
    return store


def test_vector_store_query_discount_logic(test_vector_store):
    """Verify semantic search retrieves calculate_discount when asking about discounts."""
    results = test_vector_store.query_codebase("How to calculate order discount percentage", top_k=3)
    assert len(results) > 0
    top_result = results[0]
    # Expect calculate_discount or services using discount
    names = [r.symbol_name for r in results]
    assert "calculate_discount" in names or "create_order" in names


def test_vector_store_query_stock_update(test_vector_store):
    """Verify semantic search retrieves stock update logic."""
    results = test_vector_store.query_codebase("deduct product stock inventory", top_k=3)
    assert len(results) > 0
    names = [r.symbol_name for r in results]
    assert "update_stock" in names or "ProductCatalogService" in names or "create_order" in names


def test_api_health_endpoint():
    """Test GET /health returns 200 and healthy status."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "total_indexed_symbols" in data


def test_api_index_and_query_endpoints():
    """Test POST /index-repository and POST /query-architecture via REST API."""
    client = TestClient(app)
    
    # 1. Trigger indexing
    index_res = client.post("/index-repository", json={"repo_path": "tests/dummy_repo"})
    assert index_res.status_code == 200
    index_data = index_res.json()
    assert index_data["status"] == "success"
    assert index_data["indexed_symbols_count"] > 0

    # 2. Query architecture
    query_res = client.post(
        "/query-architecture",
        json={"query": "Where is the order created and validated?", "top_k": 5}
    )
    assert query_res.status_code == 200
    query_data = query_res.json()
    assert query_data["results_count"] > 0
    
    matches = query_data["matches"]
    match_targets = [(m["symbol_name"] + " " + (m.get("parent_class") or "")).lower() for m in matches]
    assert any("order" in target for target in match_targets)

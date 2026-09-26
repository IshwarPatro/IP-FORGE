"""
Unit and integration tests for IP FORGE Phase 5: AMD Developer Cloud & ROCm Scaling.
Validates environment provider resolution, hardware telemetry endpoint,
dynamic provider switching, and inference latency telemetry calculations.
"""

import pytest
from unittest.mock import MagicMock
from starlette.testclient import TestClient

from forge.config import Settings, settings
from forge.llm.factory import get_llm_client, set_active_provider, LLMClient
from forge.api.main import app


def test_forge_env_amd_cloud_configuration():
    """Verify that FORGE_ENV='amd_cloud' automatically routes to AMD ROCm vLLM backend."""
    custom_settings = Settings(
        FORGE_ENV="amd_cloud",
        LLM_PROVIDER="ollama",  # Should be overridden by amd_cloud
        AMD_VLLM_BASE_URL="http://10.0.0.42:8000/v1",
        AMD_VLLM_MODEL="meta-llama/Meta-Llama-3-70B-Instruct"
    )
    cfg = custom_settings.get_active_llm_config()

    assert cfg["provider"] == "amd_vllm"
    assert cfg["base_url"] == "http://10.0.0.42:8000/v1"
    assert cfg["model"] == "meta-llama/Meta-Llama-3-70B-Instruct"


def test_forge_env_local_m4_configuration():
    """Verify that FORGE_ENV='local_m4' automatically routes to local Ollama backend."""
    custom_settings = Settings(
        FORGE_ENV="local_m4",
        LLM_PROVIDER="amd_vllm",  # Should be overridden by local_m4
        OLLAMA_BASE_URL="http://localhost:11434/v1",
        OLLAMA_MODEL="gemma:7b"
    )
    cfg = custom_settings.get_active_llm_config()

    assert cfg["provider"] == "ollama"
    assert cfg["base_url"] == "http://localhost:11434/v1"
    assert cfg["model"] == "gemma:7b"


def test_dynamic_set_active_provider():
    """Verify set_active_provider cleanly toggles provider and resets LLMClient instance."""
    original_provider = settings.LLM_PROVIDER

    try:
        client_amd = set_active_provider("amd_vllm")
        assert settings.LLM_PROVIDER == "amd_vllm"
        assert client_amd.provider == "amd_vllm"
        assert client_amd.model == settings.AMD_VLLM_MODEL

        client_local = set_active_provider("ollama")
        assert settings.LLM_PROVIDER == "ollama"
        assert client_local.provider == "ollama"
        assert client_local.model == settings.OLLAMA_MODEL
    finally:
        set_active_provider(original_provider)


def test_api_get_hardware_telemetry():
    """Verify GET /system/hardware returns complete local vs AMD Cloud specs."""
    client = TestClient(app)
    response = client.get("/system/hardware")

    assert response.status_code == 200
    data = response.json()

    # Local workstation specs
    assert "local_workstation" in data
    assert "Apple M4" in data["local_workstation"]["chip"]
    assert "architecture" in data["local_workstation"]

    # AMD Cloud ROCm specs
    assert "amd_cloud" in data
    assert "AMD Instinct" in data["amd_cloud"]["gpu_model"]
    assert "6.2" in data["amd_cloud"]["rocm_version"]
    assert data["amd_cloud"]["vllm_rocm_paged_attn"] is True
    assert "Meta-Llama-3-70B-Instruct" in data["amd_cloud"]["model"]

    # Active runtime
    assert "active_runtime" in data
    assert data["active_runtime"]["llm_provider"] in ["ollama", "amd_vllm", "openai"]


def test_api_toggle_provider_endpoint():
    """Verify POST /system/toggle-provider dynamically updates active inference engine."""
    client = TestClient(app)
    original_provider = settings.LLM_PROVIDER
    original_env = settings.FORGE_ENV

    try:
        # Toggle to AMD Cloud
        res = client.post(
            "/system/toggle-provider",
            json={"provider": "amd_vllm", "forge_env": "amd_cloud"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["active_provider"] == "amd_vllm"
        assert data["forge_env"] == "amd_cloud"
        assert "Meta-Llama-3-70B-Instruct" in data["active_model"]

        # Toggle back to local
        res2 = client.post(
            "/system/toggle-provider",
            json={"provider": "ollama", "forge_env": "local_m4"}
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["active_provider"] == "ollama"
        assert data2["forge_env"] == "local_m4"
    finally:
        set_active_provider(original_provider)
        settings.FORGE_ENV = original_env



def test_benchmark_prompt_telemetry(monkeypatch):
    """Verify benchmark_prompt measures TTFT and throughput from streaming tokens."""
    client = LLMClient(provider="amd_vllm")

    # Mock chunk generator
    class MockDelta:
        def __init__(self, content):
            self.content = content

    class MockChoice:
        def __init__(self, content):
            self.delta = MockDelta(content)

    class MockChunk:
        def __init__(self, content):
            self.choices = [MockChoice(content)]

    sample_tokens = ["def ", "calculate_discount", "(price, ", "pct): ", "return ", "price * (1 - pct)"]
    mock_chunks = [MockChunk(t) for t in sample_tokens]

    mock_create = MagicMock(return_value=iter(mock_chunks))
    monkeypatch.setattr(client.client.chat.completions, "create", mock_create)

    result = client.benchmark_prompt("Test prompt", max_tokens=64)

    assert result["provider"] == "amd_vllm"
    assert result["tokens_generated"] >= 5
    assert result["time_to_first_token_ms"] >= 0
    assert result["tokens_per_second"] > 0
    assert "calculate_discount" in result["output_sample"]


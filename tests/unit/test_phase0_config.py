"""
Unit tests for Phase 0: Configuration, Environment, and LLM Client Factory.
"""

import pytest
from forge.config import Settings, settings
from forge.llm.factory import LLMClient, get_llm_client


def test_settings_defaults():
    """Verify default configurations are correctly typed and populated."""
    assert settings.FORGE_ENV in ["development", "staging", "production", "local_m4", "amd_cloud"]
    assert settings.FORGE_PORT == 8000
    assert settings.MAX_SELF_HEAL_ITERATIONS == 3
    assert settings.MCP_EXECUTION_TIMEOUT_SECONDS == 30
    assert settings.CHROMA_COLLECTION_NAME == "forge_codebase"


def test_settings_llm_config_resolution():
    """Verify provider configuration routing."""
    # Test Ollama resolution
    test_settings = Settings(LLM_PROVIDER="ollama")
    cfg = test_settings.get_active_llm_config()
    assert cfg["provider"] == "ollama"
    assert "11434" in cfg["base_url"]

    # Test AMD vLLM resolution
    test_settings_amd = Settings(
        LLM_PROVIDER="amd_vllm",
        AMD_VLLM_BASE_URL="http://192.168.1.100:8000/v1",
        AMD_VLLM_MODEL="meta-llama/Meta-Llama-3-70B-Instruct"
    )
    cfg_amd = test_settings_amd.get_active_llm_config()
    assert cfg_amd["provider"] == "amd_vllm"
    assert cfg_amd["base_url"] == "http://192.168.1.100:8000/v1"
    assert "Llama-3-70B" in cfg_amd["model"]


def test_llm_client_factory_initialization():
    """Verify LLMClient instantiates with expected endpoints."""
    client = get_llm_client(provider="ollama", force_new=True)
    assert client.provider == "ollama"
    assert client.client.base_url.host in ["localhost", "127.0.0.1"]

    amd_client = get_llm_client(provider="amd_vllm", force_new=True)
    assert amd_client.provider == "amd_vllm"
    assert amd_client.model == settings.AMD_VLLM_MODEL

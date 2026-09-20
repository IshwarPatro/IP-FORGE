"""
LLM abstraction layer for IP FORGE.
Supports local Ollama, AMD Developer Cloud (ROCm vLLM), and OpenAI endpoints.
"""

from forge.llm.factory import get_llm_client, LLMClient

__all__ = ["get_llm_client", "LLMClient"]

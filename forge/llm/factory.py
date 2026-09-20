"""
IP FORGE: Universal LLM Client Factory
Provides a unified interface across Local Ollama, AMD Developer Cloud (ROCm vLLM),
and standard OpenAI-compatible inference endpoints.
"""

from typing import List, Dict, Any, Optional, Generator, AsyncGenerator
import time
from openai import OpenAI, AsyncOpenAI
from forge.config import settings, setup_logger

logger = setup_logger("forge.llm.factory")


class LLMClient:
    """Unified client handling inference across AMD ROCm vLLM, Ollama, and OpenAI."""

    def __init__(self, provider: Optional[str] = None):
        cfg = settings.get_active_llm_config()
        if provider:
            # Override if requested
            self.provider = provider
            if provider == "amd_vllm":
                self.base_url = settings.AMD_VLLM_BASE_URL
                self.model = settings.AMD_VLLM_MODEL
                self.api_key = settings.AMD_VLLM_API_KEY
            elif provider == "openai":
                self.base_url = "https://api.openai.com/v1"
                self.model = settings.OPENAI_MODEL
                self.api_key = settings.OPENAI_API_KEY or "missing-key"
            else:
                self.base_url = settings.OLLAMA_BASE_URL
                self.model = settings.OLLAMA_MODEL
                self.api_key = settings.OLLAMA_API_KEY
        else:
            self.provider = cfg["provider"]
            self.base_url = cfg["base_url"]
            self.model = cfg["model"]
            self.api_key = cfg["api_key"]

        logger.info(
            f"Initializing LLMClient [Provider: {self.provider.upper()}] "
            f"[Endpoint: {self.base_url}] [Model: {self.model}]"
        )

        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        self.async_client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)

    def is_healthy(self) -> bool:
        """Pings the target model provider to verify availability."""
        try:
            # Fast model listing check
            models = self.client.models.list()
            logger.info(f"LLM endpoint connection verified. Available models count: {len(models.data)}")
            return True
        except Exception as exc:
            logger.warning(
                f"LLM health-check failed for {self.provider} at {self.base_url}: {exc}"
            )
            return False

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: Optional[int] = 4096,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """Generates a synchronous chat completion with telemetry logging."""
        start_time = time.perf_counter()
        logger.debug(f"Sending prompt ({len(messages)} messages) to {self.model} via {self.provider}...")

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = self.client.chat.completions.create(**kwargs)
            duration = time.perf_counter() - start_time
            content = response.choices[0].message.content or ""
            
            usage = response.usage
            tokens_prompt = usage.prompt_tokens if usage else 0
            tokens_completion = usage.completion_tokens if usage else 0
            tok_per_sec = (tokens_completion / duration) if duration > 0 and tokens_completion > 0 else 0

            logger.info(
                f"Completed in {duration:.2f}s | "
                f"Prompt Tokens: {tokens_prompt} | "
                f"Completion Tokens: {tokens_completion} | "
                f"Throughput: {tok_per_sec:.1f} tok/s"
            )
            return content
        except Exception as exc:
            logger.error(f"Inference error on {self.provider} ({self.base_url}): {exc}", exc_info=True)
            raise

    async def generate_async(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: Optional[int] = 4096,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """Asynchronously generates a chat completion."""
        start_time = time.perf_counter()
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = await self.async_client.chat.completions.create(**kwargs)
            duration = time.perf_counter() - start_time
            content = response.choices[0].message.content or ""
            logger.debug(f"Async completion received in {duration:.2f}s from {self.provider}")
            return content
        except Exception as exc:
            logger.error(f"Async inference error on {self.provider}: {exc}", exc_info=True)
            raise


_default_client: Optional[LLMClient] = None


def get_llm_client(provider: Optional[str] = None, force_new: bool = False) -> LLMClient:
    """Factory function returning a configured LLMClient instance."""
    global _default_client
    if provider is not None or force_new:
        return LLMClient(provider=provider)
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client

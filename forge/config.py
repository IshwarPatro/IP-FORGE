"""
IP FORGE: Central Configuration Module
Provides strongly typed environment settings via Pydantic Settings.
"""

from typing import Literal, Optional
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging
import sys


class Settings(BaseSettings):
    """Global system configuration for IP FORGE."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General App Settings
    FORGE_ENV: Literal["development", "staging", "production", "local_m4", "amd_cloud"] = "development"
    FORGE_LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    FORGE_HOST: str = "0.0.0.0"
    FORGE_PORT: int = 8000

    # Hardware Metadata
    LOCAL_CHIP_MODEL: str = "Apple M4 (24GB Unified Memory)"
    AMD_GPU_MODEL: str = "AMD Instinct MI300X (192GB HBM3)"
    AMD_ROCM_VERSION: str = "6.2.0"

    # LLM Provider Selection: 'ollama', 'amd_vllm', 'openai'
    LLM_PROVIDER: Literal["ollama", "amd_vllm", "openai"] = "ollama"

    # Local Ollama (Apple M4 edge)
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "gemma:7b"
    OLLAMA_API_KEY: str = "ollama"

    # AMD Developer Cloud vLLM (ROCm 6.x GPU)
    AMD_VLLM_BASE_URL: str = "http://localhost:8000/v1"
    AMD_VLLM_MODEL: str = "meta-llama/Meta-Llama-3-70B-Instruct"
    AMD_VLLM_API_KEY: str = "empty"


    # Cloud Fallback (OpenAI)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"

    # Vector Storage (ChromaDB)
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "forge_codebase"

    # Message Broker & Cache (Redis)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Relational Persistence (PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://forge:forge_password@localhost:5432/forge_db"

    # Sandbox & Execution Constraints
    TARGET_REPO_PATH: str = "./tests/dummy_repo"
    MAX_SELF_HEAL_ITERATIONS: int = 3
    MCP_EXECUTION_TIMEOUT_SECONDS: int = 30

    @property
    def target_repo_absolute_path(self) -> Path:
        """Returns resolved absolute path to the target repository."""
        return Path(self.TARGET_REPO_PATH).resolve()

    @property
    def chroma_absolute_path(self) -> Path:
        """Returns resolved absolute path to ChromaDB persistence directory."""
        return Path(self.CHROMA_PERSIST_DIR).resolve()

    def get_active_llm_config(self) -> dict:
        """Returns connection tuple (base_url, model, api_key) for the active LLM provider."""
        effective_provider = self.LLM_PROVIDER
        if self.FORGE_ENV == "amd_cloud":
            effective_provider = "amd_vllm"
        elif self.FORGE_ENV == "local_m4":
            effective_provider = "ollama"

        if effective_provider == "amd_vllm":
            return {
                "provider": "amd_vllm",
                "base_url": self.AMD_VLLM_BASE_URL,
                "model": self.AMD_VLLM_MODEL,
                "api_key": self.AMD_VLLM_API_KEY,
            }
        elif effective_provider == "openai":
            return {
                "provider": "openai",
                "base_url": "https://api.openai.com/v1",
                "model": self.OPENAI_MODEL,
                "api_key": self.OPENAI_API_KEY or "missing-key",
            }
        else:  # Default to local Ollama
            return {
                "provider": "ollama",
                "base_url": self.OLLAMA_BASE_URL,
                "model": self.OLLAMA_MODEL,
                "api_key": self.OLLAMA_API_KEY,
            }



# Singleton instance
settings = Settings()


def setup_logger(name: str = "ip_forge") -> logging.Logger:
    """Configures structured logger with uniform timestamp and module formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(getattr(logging, settings.FORGE_LOG_LEVEL.upper(), logging.INFO))
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

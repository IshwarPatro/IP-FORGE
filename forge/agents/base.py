"""
IP FORGE: Base Agent Class
Provides persona definition, LLM invocation interfaces, and robust structured output parsing.
"""

import json
import re
from typing import Dict, Any, Optional, List
from forge.config import setup_logger
from forge.llm.factory import get_llm_client, LLMClient

logger = setup_logger("forge.agents.base")


class BaseAgent:
    """Base class for all specialized personas in the IP FORGE ecosystem."""

    def __init__(self, role_name: str, system_prompt: str, llm_provider: Optional[str] = None):
        self.role_name = role_name
        self.system_prompt = system_prompt
        self.llm_provider = llm_provider
        self.client: LLMClient = get_llm_client(provider=llm_provider)

    def _call_llm(
        self,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """Executes LLM completion with role context."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        logger.info(f"[{self.role_name}] Calling LLM ({self.client.model})...")
        return self.client.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format
        )

    def _parse_json_response(self, raw_response: str) -> Dict[str, Any]:
        """
        Extracts and parses JSON object from LLM output,
        handling markdown code blocks (```json ... ```) and leading/trailing chatter.
        """
        cleaned = raw_response.strip()

        # Check for ```json ... ``` blocks
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if json_match:
            cleaned = json_match.group(1).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: scan for first '{' and last '}'
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start:end + 1])
                except json.JSONDecodeError as err:
                    logger.error(f"Failed to parse extracted JSON substring: {err}")
            logger.error(f"Invalid JSON in LLM response:\n{raw_response}")
            raise ValueError(f"LLM did not return a valid JSON object: {raw_response[:200]}")

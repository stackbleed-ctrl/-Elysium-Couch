"""
LLM Provider abstraction.
Supports Anthropic (Claude) and xAI (Grok) interchangeably.
All other modules import BaseLLMClient — never a concrete provider directly.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Shared interface
# ---------------------------------------------------------------------------

class BaseLLMClient(ABC):
    """Minimal interface every provider must implement."""

    @abstractmethod
    async def complete(
        self,
        system: str,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.3,
        **kwargs,
    ) -> str: ...

    @abstractmethod
    async def reflect(self, prompt: str) -> str: ...

    @abstractmethod
    async def generate_creative(self, prompt: str) -> str: ...

    @abstractmethod
    async def judge(self, criteria: str, content: str) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------------

class AnthropicClient(BaseLLMClient):
    """
    Thin wrapper around the existing anthropic_client module.
    Delegates to it so nothing that already works is broken.
    """

    def __init__(self, model: str = "claude-sonnet-4-5"):
        # Import lazily so Grok-only installs don't need the anthropic package
        from elysium_couch.integrations.anthropic_client import AnthropicClient as _Inner
        self._inner = _Inner(model=model)

    async def complete(self, system, messages, max_tokens=1024, temperature=0.3, **kwargs) -> str:
        return await self._inner.complete(
            system=system, messages=messages,
            max_tokens=max_tokens, temperature=temperature, **kwargs,
        )

    async def reflect(self, prompt: str) -> str:
        return await self._inner.reflect(prompt)

    async def generate_creative(self, prompt: str) -> str:
        return await self._inner.generate_creative(prompt)

    async def judge(self, criteria: str, content: str) -> dict[str, Any]:
        return await self._inner.judge(criteria=criteria, content=content)


# ---------------------------------------------------------------------------
# xAI (Grok) — OpenAI-compatible endpoint
# ---------------------------------------------------------------------------

_GROK_DEFAULT_MODEL = "grok-3"
_GROK_BASE_URL      = "https://api.x.ai/v1"


class GrokClient(BaseLLMClient):
    """
    Grok via the OpenAI-compatible xAI endpoint.
    Requires: pip install openai
    Env var:  XAI_API_KEY
    """

    def __init__(self, model: str = _GROK_DEFAULT_MODEL):
        try:
            from openai import AsyncOpenAI
        except ImportError as e:
            raise ImportError(
                "openai package required for GrokClient: pip install openai"
            ) from e

        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            raise EnvironmentError("XAI_API_KEY is not set.")

        self._client = AsyncOpenAI(api_key=api_key, base_url=_GROK_BASE_URL)
        self.model = model

    async def _chat(
        self,
        system: str,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
    ) -> str:
        full_messages = [{"role": "system", "content": system}] + messages
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    async def complete(self, system, messages, max_tokens=1024, temperature=0.3, **_) -> str:
        return await self._chat(system, messages, max_tokens, temperature)

    async def reflect(self, prompt: str) -> str:
        return await self._chat(
            system="You are a precise, calibrated reasoning assistant.",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.2,
        )

    async def generate_creative(self, prompt: str) -> str:
        return await self._chat(
            system="You are a creative, intellectually curious assistant.",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )

    async def judge(self, criteria: str, content: str) -> dict[str, Any]:
        import json
        prompt = (
            f"{criteria}\n\nContent to evaluate:\n{content}\n\n"
            "Return ONLY valid JSON. No prose, no markdown fences."
        )
        raw = await self._chat(
            system="You are a strict JSON-only evaluator. Output only valid JSON.",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.1,
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(
                "GrokClient.judge: JSON parse failed, returning empty scores",
                raw=raw[:200],
            )
            return {}


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_llm_client(provider: str | None = None, model: str | None = None) -> BaseLLMClient:
    """
    Factory. Reads LLM_PROVIDER env var if provider not passed explicitly.

    provider: "anthropic" | "grok"   (default: "anthropic")
    model:    optional model name override

    Usage:
        client = get_llm_client()            # reads LLM_PROVIDER from env
        client = get_llm_client("grok")      # force Grok
        client = get_llm_client("anthropic") # force Claude
    """
    resolved = (provider or os.getenv("LLM_PROVIDER", "anthropic")).lower()

    if resolved == "anthropic":
        return AnthropicClient(model=model or "claude-sonnet-4-5")
    elif resolved in ("grok", "xai"):
        return GrokClient(model=model or _GROK_DEFAULT_MODEL)
    else:
        raise ValueError(
            f"Unknown LLM provider: '{resolved}'. Choose 'anthropic' or 'grok'."
        )

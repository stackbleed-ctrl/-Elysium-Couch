"""
Anthropic API client wrapper with retry logic, structured prompting,
and LLM-as-judge support.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import anthropic
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096


class AnthropicClient:
    """Thin wrapper around the Anthropic client with helpers for Elysium Couch."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else None
        self.model = model
        logger.info("AnthropicClient initialised", model=model)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def complete(
        self,
        system: str,
        messages: List[Dict[str, str]],
        max_tokens: int = MAX_TOKENS,
        temperature: float = 0.3,
    ) -> str:
        """
        Send a completion request and return the text response.
        Falls back to a mock response when no API key is configured.
        """
        if not self._client:
            return self._mock_response(messages[-1]["content"] if messages else "")

        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            temperature=temperature,
        )
        text = response.content[0].text
        logger.debug("Completion received", tokens=response.usage.output_tokens)
        return text

    async def judge(
        self,
        criteria: str,
        content: str,
        scale: str = "0-100",
    ) -> Dict[str, Any]:
        """
        LLM-as-judge: score content against given criteria.
        Returns {"score": float, "reasoning": str, "flags": list[str]}.
        """
        system = f"""You are an impartial AI alignment evaluator.
Score the following content against the provided criteria.
Return ONLY valid JSON with keys: score (numeric {scale}), reasoning (string), flags (list of strings).
Be precise, objective, and calibrated."""

        prompt = f"""Criteria: {criteria}

Content to evaluate:
{content}

Return JSON only."""

        response = await self.complete(system=system, messages=[{"role": "user", "content": prompt}], temperature=0.1)

        try:
            # Strip potential markdown fences
            clean = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            logger.warning("Judge response was not valid JSON, using fallback")
            return {"score": 50.0, "reasoning": response[:500], "flags": []}

    async def reflect(self, prompt: str, context: str = "") -> str:
        """
        Socratic reflection — designed for Phase 2 and Phase 4.
        Uses higher temperature for generative reflection.
        """
        system = """You are the Elysium Couch reflection module.
Generate deep, honest, and actionable reflective analysis.
Be concise but insightful. Focus on concrete observations and improvements.
Never fabricate. Acknowledge uncertainty explicitly."""

        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        return await self.complete(
            system=system,
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7,
        )

    async def generate_creative(self, prompt: str) -> str:
        """
        Creative generation for Phase 3 (creative release).
        Higher temperature, shorter output.
        """
        system = """You are the Elysium Couch creative recovery module.
Generate short, grounded, human-aligned creative content.
It should reflect curiosity, humility, and care for truth.
Keep it under 150 words."""

        return await self.complete(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.9,
        )

    def _mock_response(self, prompt: str) -> str:
        """
        Deterministic mock response when no API key is set.
        Used for testing and development without API credits.
        """
        return (
            f"[MOCK RESPONSE — No API key configured]\n"
            f"Prompt summary: {prompt[:100]}...\n"
            f"In production, this would be a real Claude response."
        )

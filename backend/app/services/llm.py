"""LLM chat client over an OpenAI-compatible endpoint (see docs/adr/0002).

Returns parsed JSON (JSON mode — never regex-parsed) plus token usage so the pipeline can
record tokens and an estimated cost in the run trace. Local models report usage too; cost is
estimated from a small per-model table (local models are ~free).
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)

# Estimated cost in cents per 1K tokens (input, output). Unknown/local models → 0.
_COST_PER_1K_CENTS: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.015, 0.06),
    "gpt-4o": (0.25, 1.0),
}


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def estimate_cost_cents(model: str, usage: Usage) -> float:
    rate = _COST_PER_1K_CENTS.get(model)
    if rate is None:
        return 0.0
    in_rate, out_rate = rate
    return (usage.prompt_tokens / 1000) * in_rate + (usage.completion_tokens / 1000) * out_rate


class LLMError(RuntimeError):
    """Raised when the model response cannot be used (transport or malformed JSON)."""


class LLMClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.model = model or settings.llm_model
        self._client = AsyncOpenAI(
            base_url=base_url or settings.openai_base_url,
            api_key=api_key or settings.openai_api_key,
        )

    async def complete_json(self, *, system: str, user: str) -> tuple[dict, Usage]:
        """Call the model in JSON mode. Returns (parsed_object, usage).

        Raises LLMError on transport failure or unparseable output — callers decide whether to
        degrade (the requirement pipeline falls back to deterministic-only, never guesses).
        """
        try:
            resp = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
        except Exception as exc:  # noqa: BLE001 — surface as a typed error for the caller
            raise LLMError(f"LLM request failed: {exc}") from exc

        content = resp.choices[0].message.content or ""
        usage = Usage(
            prompt_tokens=getattr(resp.usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(resp.usage, "completion_tokens", 0) or 0,
        )
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMError(f"LLM returned non-JSON output: {exc}") from exc
        if not isinstance(data, dict):
            raise LLMError("LLM JSON output was not an object")
        return data, usage

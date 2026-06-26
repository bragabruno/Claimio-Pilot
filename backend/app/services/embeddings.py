"""Embedding client over an OpenAI-compatible endpoint (see docs/adr/0002).

Works against a local gateway/Ollama or hosted OpenAI by configuration. Fail-fast: a wrong
embedding dimension (model/`EMBED_DIM` mismatch) raises immediately rather than corrupting the
vector store.
"""

from __future__ import annotations

from openai import AsyncOpenAI

from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


class EmbeddingsClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        dim: int | None = None,
    ) -> None:
        self.model = model or settings.embed_model
        self.dim = dim or settings.embed_dim
        self._client = AsyncOpenAI(
            base_url=base_url or settings.openai_base_url,
            api_key=api_key or settings.openai_api_key,
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Raises on transport errors or dimension mismatch."""
        if not texts:
            return []
        resp = await self._client.embeddings.create(model=self.model, input=texts)
        vectors = [item.embedding for item in resp.data]
        for vec in vectors:
            if len(vec) != self.dim:
                raise ValueError(
                    f"Embedding dimension mismatch: model '{self.model}' returned "
                    f"{len(vec)} dims but EMBED_DIM={self.dim}. Fix EMBED_MODEL/EMBED_DIM "
                    f"and re-migrate (see docs/adr/0001, 0002)."
                )
        return vectors

    async def embed_text(self, text: str) -> list[float]:
        return (await self.embed_texts([text]))[0]

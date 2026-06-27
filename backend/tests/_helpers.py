"""Test helpers: builders for rows and stub LLM/embeddings/vector-store for the claim pipeline."""

from __future__ import annotations

import uuid

from app.config import settings
from app.db.models import Claimant, Property, RuleChunk
from app.match.normalize import canonical_name, name_tokens, normalize_address
from app.services.llm import Usage
from app.services.vector_store import RetrievedChunk


def make_property(
    owner_name: str,
    address: str | None,
    state: str,
    amount_cents: int,
    **kwargs,
) -> Property:
    parts = normalize_address(address)
    return Property(
        source_state=state,
        holder_name="Holder Co",
        owner_name=owner_name,
        owner_last_address=address,
        amount_cents=amount_cents,
        property_type="uncashed_check",
        normalized_owner_name=canonical_name(owner_name),
        normalized_owner_address=parts.normalized or None,
        owner_name_tokens=sorted(name_tokens(owner_name)),
        owner_zip=parts.zip,
        **kwargs,
    )


def make_claimant(full_name: str = "Jane Doe", *, is_business: bool = False, **kwargs) -> Claimant:
    return Claimant(
        full_name=full_name,
        prior_names=kwargs.pop("prior_names", []),
        addresses=kwargs.pop("addresses", []),
        is_business=is_business,
        **kwargs,
    )


def unit_vector(hot: int = 0) -> list[float]:
    vec = [0.0] * settings.embed_dim
    vec[hot] = 1.0
    return vec


def make_chunk(text: str, *, state: str = "CA", doc_id: uuid.UUID | None = None, hot: int = 0):
    return RuleChunk(
        id=uuid.uuid4(),
        doc_id=doc_id or uuid.uuid4(),
        state=state,
        text=text,
        embedding=unit_vector(hot),
    )


class StubLLM:
    """Stands in for LLMClient — returns a fixed JSON payload and usage."""

    model = "stub-model"

    def __init__(self, payload: dict | None = None) -> None:
        self._payload = payload if payload is not None else {"items": []}

    async def complete_json(self, *, system: str, user: str) -> tuple[dict, Usage]:
        return self._payload, Usage(prompt_tokens=10, completion_tokens=5)


class StubEmbeddings:
    async def embed_text(self, text: str) -> list[float]:
        return unit_vector(0)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [unit_vector(0) for _ in texts]


class StubStore:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks = chunks

    async def search(self, session, *, state: str, query_vec, k: int) -> list[RetrievedChunk]:
        return self._chunks

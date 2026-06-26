"""Retrieval behind a `VectorStore` protocol (see docs/adr/0001).

`PgVectorStore` is the pgvector implementation. Keeping the protocol means a later swap to
Milvus/Qdrant touches only this file, not the pipeline. Search is state-filtered: chunks are
only ever compared within a single state's rules.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RuleChunk


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    doc_id: uuid.UUID
    state: str
    text: str
    score: float  # cosine similarity in [0, 1]; higher is closer.


class VectorStore(Protocol):
    async def upsert_chunks(self, session: AsyncSession, chunks: list[RuleChunk]) -> None: ...

    async def search(
        self, session: AsyncSession, *, state: str, query_vec: list[float], k: int
    ) -> list[RetrievedChunk]: ...


class PgVectorStore:
    """pgvector-backed store. Cosine distance via the HNSW index, filtered by state."""

    async def upsert_chunks(self, session: AsyncSession, chunks: list[RuleChunk]) -> None:
        session.add_all(chunks)
        await session.flush()

    async def search(
        self, session: AsyncSession, *, state: str, query_vec: list[float], k: int
    ) -> list[RetrievedChunk]:
        distance = RuleChunk.embedding.cosine_distance(query_vec)
        stmt = (
            select(RuleChunk, distance.label("distance"))
            .where(RuleChunk.state == state)
            .order_by(distance)
            .limit(k)
        )
        rows = (await session.execute(stmt)).all()
        return [
            RetrievedChunk(
                chunk_id=chunk.id,
                doc_id=chunk.doc_id,
                state=chunk.state,
                text=chunk.text,
                score=1.0 - float(dist),
            )
            for chunk, dist in rows
        ]

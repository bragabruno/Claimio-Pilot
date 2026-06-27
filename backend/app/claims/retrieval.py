"""State-filtered RAG retrieval for claim requirements (see docs/adr/0001, 0003).

Builds a claim-context query, embeds it, and retrieves the top-k rule chunks for the property's
state — these chunks are the citations every requirement must reference. Also exposes a
per-state chunk lookup used to ground deterministic requirements on their governing section.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Claimant, Property, RuleChunk
from app.services.embeddings import EmbeddingsClient
from app.services.vector_store import PgVectorStore, RetrievedChunk


def build_claim_query(claimant: Claimant, prop: Property) -> str:
    """A natural-language retrieval query describing the claim context."""
    parts = [
        f"Unclaimed property claim in {prop.source_state}.",
        "Required proof of identity and proof of address.",
        f"Claim amount {prop.amount_cents / 100:.2f} dollars; notarization requirements.",
    ]
    if prop.owner_deceased:
        parts.append("Owner is deceased; heir and estate documentation.")
    if claimant.is_business:
        parts.append("Business entity claimant; articles of incorporation, EIN, authorized signer.")
    return " ".join(parts)


async def retrieve_citations(
    session: AsyncSession,
    *,
    state: str,
    query_text: str,
    k: int,
    embeddings: EmbeddingsClient,
    store: PgVectorStore | None = None,
) -> list[RetrievedChunk]:
    store = store or PgVectorStore()
    query_vec = await embeddings.embed_text(query_text)
    return await store.search(session, state=state, query_vec=query_vec, k=k)


async def chunks_for_state(session: AsyncSession, state: str) -> list[RuleChunk]:
    rows = (
        await session.execute(select(RuleChunk).where(RuleChunk.state == state))
    ).scalars().all()
    return list(rows)


def find_chunk_by_keywords(chunks: list[RuleChunk], keywords: list[str]) -> RuleChunk | None:
    """First chunk whose text contains any keyword (case-insensitive)."""
    for chunk in chunks:
        text = chunk.text.lower()
        if any(kw in text for kw in keywords):
            return chunk
    return None

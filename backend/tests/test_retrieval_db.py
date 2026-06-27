"""Retrieval is state-filtered: a CA query never returns NY chunks (docs/adr/0001)."""

from __future__ import annotations

from app.claims.retrieval import retrieve_citations
from app.db.models import RuleChunk, StateRuleDoc
from app.services.vector_store import PgVectorStore
from tests._helpers import StubEmbeddings, unit_vector


async def test_retrieve_citations_filters_by_state(session):
    ca = StateRuleDoc(state="CA", title="CA", body_md="# x")
    ny = StateRuleDoc(state="NY", title="NY", body_md="# x")
    session.add_all([ca, ny])
    await session.flush()
    session.add_all([
        RuleChunk(doc_id=ca.id, state="CA", text="CA identity rule", embedding=unit_vector(0)),
        RuleChunk(doc_id=ny.id, state="NY", text="NY identity rule", embedding=unit_vector(0)),
    ])
    await session.flush()

    cites = await retrieve_citations(
        session, state="CA", query_text="identity", k=5,
        embeddings=StubEmbeddings(), store=PgVectorStore(),
    )
    assert cites
    assert all(c.state == "CA" for c in cites)

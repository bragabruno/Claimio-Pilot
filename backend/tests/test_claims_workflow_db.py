"""DB-backed ClaimWorkflow tests with stubbed LLM/embeddings/vector-store."""

from __future__ import annotations

from sqlalchemy import select

from app.claims.workflow import ClaimWorkflow
from app.db.models import Claim, RuleChunk, RunTrace, StateRuleDoc
from app.services.vector_store import RetrievedChunk
from tests._helpers import (
    StubEmbeddings,
    StubLLM,
    StubStore,
    make_claimant,
    make_property,
    unit_vector,
)


async def _seed_state(session, state: str, *, with_address: bool):
    doc = StateRuleDoc(state=state, title=f"{state} — demo rules", body_md="# x")
    session.add(doc)
    await session.flush()
    chunks = [
        RuleChunk(doc_id=doc.id, state=state, text="Proof of Identity: photo ID required.",
                  embedding=unit_vector(0)),
        RuleChunk(doc_id=doc.id, state=state,
                  text="Notarization: claims over the threshold require a notarized claim form.",
                  embedding=unit_vector(2)),
    ]
    if with_address:
        chunks.append(
            RuleChunk(doc_id=doc.id, state=state, text="Proof of Address: a utility bill.",
                      embedding=unit_vector(1))
        )
    session.add_all(chunks)
    await session.flush()
    return doc, chunks


async def test_workflow_persists_grounded_claim(session):
    doc, chunks = await _seed_state(session, "CA", with_address=True)
    claimant = make_claimant("Maria Gonzalez")
    prop = make_property("Maria Gonzalez", "1 Main St, Sacramento CA 95814", "CA", 500_000)
    session.add_all([claimant, prop])
    await session.flush()

    cite = RetrievedChunk(chunk_id=chunks[0].id, doc_id=doc.id, state="CA",
                          text=chunks[0].text, score=0.91)
    workflow = ClaimWorkflow(embeddings=StubEmbeddings(), llm=StubLLM(), store=StubStore([cite]))
    result = await workflow.run(session, claimant, prop)

    labels = [i.label for i in result.items]
    assert any("photo ID" in label for label in labels)
    assert any("Notarized" in label for label in labels)  # 500_000 > CA threshold 100_000
    assert result.needs_human_review is False
    assert result.status == "needs_docs"

    assert await session.get(Claim, result.claim_id) is not None
    trace = (
        await session.execute(select(RunTrace).where(RunTrace.claim_id == result.claim_id))
    ).scalar_one()
    assert trace.tokens == 15  # stub usage (10 + 5)
    assert result.citations and result.citations[0].score == 0.91


async def test_workflow_flags_human_review_when_chunk_missing(session):
    # No address chunk → the address requirement cannot be grounded.
    await _seed_state(session, "NY", with_address=False)
    claimant = make_claimant("John Roe")
    prop = make_property("John Roe", "5 Oak St", "NY", 10_000)
    session.add_all([claimant, prop])
    await session.flush()

    workflow = ClaimWorkflow(embeddings=StubEmbeddings(), llm=StubLLM(), store=StubStore([]))
    result = await workflow.run(session, claimant, prop)

    address_item = next(i for i in result.items if "address" in i.label.lower())
    assert address_item.status == "needs_human_review"
    assert result.needs_human_review is True

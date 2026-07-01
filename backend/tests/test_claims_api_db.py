"""API tests for POST /claims, GET /claims/{id}, GET /states/{state}/rules.

Overrides get_session (rolled-back fixture) and get_workflow (stubbed LLM/embeddings/store).
The endpoint's commit is redirected to flush so nothing persists past the fixture rollback.
"""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.api.claims import get_workflow
from app.api.deps import get_session
from app.claims.workflow import ClaimWorkflow
from app.db.models import Claim, RuleChunk, StateRuleDoc
from app.main import app
from app.services.vector_store import RetrievedChunk
from tests._helpers import (
    StubEmbeddings,
    StubLLM,
    StubStore,
    make_claimant,
    make_property,
    unit_vector,
)


async def test_create_get_claim_and_state_rules(session):
    session.commit = session.flush  # type: ignore[method-assign]  # don't persist past rollback

    doc = StateRuleDoc(state="CA", title="California — demo rules",
                       body_md="# California\n## Notarization\nover threshold notarized")
    session.add(doc)
    await session.flush()
    chunks = [
        RuleChunk(doc_id=doc.id, state="CA", text="Proof of Identity: photo ID.",
                  embedding=unit_vector(0)),
        RuleChunk(doc_id=doc.id, state="CA", text="Proof of Address: utility bill.",
                  embedding=unit_vector(1)),
        RuleChunk(doc_id=doc.id, state="CA",
                  text="Notarization: claims over threshold require a notarized claim form.",
                  embedding=unit_vector(2)),
    ]
    session.add_all(chunks)
    claimant = make_claimant("Maria Gonzalez")
    prop = make_property("Maria Gonzalez", "1 Main St, Sacramento CA 95814", "CA", 500_000)
    session.add_all([claimant, prop])
    await session.flush()

    cite = RetrievedChunk(chunk_id=chunks[0].id, doc_id=doc.id, state="CA",
                          text=chunks[0].text, score=0.9)

    async def _override_session():
        yield session

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_workflow] = lambda: ClaimWorkflow(
        embeddings=StubEmbeddings(), llm=StubLLM(), store=StubStore([cite])
    )
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/claims",
                json={"claimant_id": str(claimant.id), "property_id": str(prop.id)},
            )
            assert created.status_code == 200, created.text
            data = created.json()
            claim_id = data["claim_id"]
            assert data["state"] == "CA"
            assert any("photo ID" in i["label"] for i in data["required_items"])
            assert any("Notarized" in i["label"] for i in data["required_items"])
            assert data["citations"]
            assert data["trace"]["retrieval_hits"] == 1

            fetched = await client.get(f"/claims/{claim_id}")
            assert fetched.status_code == 200
            assert fetched.json()["claim_id"] == claim_id

            rules = await client.get("/states/ca/rules")
            assert rules.status_code == 200
            assert rules.json()["state"] == "CA"
    finally:
        app.dependency_overrides.clear()


async def test_preview_claim_computes_without_persisting(session):
    count_stmt = select(func.count()).select_from(Claim)
    claims_before = (await session.execute(count_stmt)).scalar_one()

    doc = StateRuleDoc(state="CA", title="California — demo", body_md="# x")
    session.add(doc)
    await session.flush()
    chunks = [
        RuleChunk(doc_id=doc.id, state="CA", text="Proof of Identity: photo ID.",
                  embedding=unit_vector(0)),
        RuleChunk(doc_id=doc.id, state="CA", text="Proof of Address: utility bill.",
                  embedding=unit_vector(1)),
        RuleChunk(doc_id=doc.id, state="CA",
                  text="Notarization: claims over threshold require a notarized claim form.",
                  embedding=unit_vector(2)),
    ]
    session.add_all(chunks)
    await session.flush()
    cite = RetrievedChunk(chunk_id=chunks[0].id, doc_id=doc.id, state="CA",
                          text=chunks[0].text, score=0.9)

    async def _override_session():
        yield session

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_workflow] = lambda: ClaimWorkflow(
        embeddings=StubEmbeddings(), llm=StubLLM(), store=StubStore([cite])
    )
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/claims/preview", json={"state": "CA", "amount_cents": 150_000}
            )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        labels = [i["label"] for i in data["required_items"]]
        assert any("photo ID" in label for label in labels)
        assert any("Notarized" in label for label in labels)  # 150_000 > CA threshold 100_000
        assert "claim_id" not in data
    finally:
        app.dependency_overrides.clear()

    # Preview must not persist a claim (count unchanged).
    assert (await session.execute(count_stmt)).scalar_one() == claims_before

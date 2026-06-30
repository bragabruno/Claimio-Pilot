"""API test for POST /claims/{id}/documents (extraction → requirement satisfaction)."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.api.claims import get_document_processor
from app.api.deps import get_session
from app.claims.extraction import DocumentProcessor
from app.db.models import Claim
from app.main import app
from app.schemas.claim import RequiredItem
from tests._helpers import StubLLM, make_claimant, make_property

EXTRACT_PAYLOAD = {
    "doc_type": "drivers_license",
    "name": "Maria Gonzalez",
    "doc_number_last4": "1234",
    "field_confidence": {"name": 0.96, "doc_number_last4": 0.93},
}


async def test_upload_document_satisfies_requirement(session):
    session.commit = session.flush  # type: ignore[method-assign]

    claimant = make_claimant("Maria Gonzalez")
    prop = make_property("Maria Gonzalez", "1 Main St, Sacramento CA 95814", "CA", 50_000)
    session.add_all([claimant, prop])
    await session.flush()

    photo_id = RequiredItem(
        label="Government-issued photo ID", why="identity", requirement="required"
    )
    claim = Claim(
        claimant_id=claimant.id, property_id=prop.id, state="CA", status="needs_docs",
        required_items_json={"items": [photo_id.model_dump(mode="json")]},
        package_json={"draft_letter": "x", "needs_human_review": False, "citations": []},
    )
    session.add(claim)
    await session.flush()

    async def _override_session():
        yield session

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_document_processor] = lambda: DocumentProcessor(
        llm=StubLLM(EXTRACT_PAYLOAD)
    )
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/claims/{claim.id}/documents",
                json={"raw_text": "CA DL Maria Gonzalez ...", "doc_type_hint": "drivers_license"},
            )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["extracted"]["doc_type"] == "drivers_license"
        assert "Government-issued photo ID" in data["satisfied_labels"]
        assert data["required_items"][0]["satisfied_by_uploaded_doc"] is True
        assert data["mismatches"] == []
        assert data["status"] == "ready_to_file"  # the only required item is now satisfied
    finally:
        app.dependency_overrides.clear()


async def test_upload_document_flags_mismatch(session):
    session.commit = session.flush  # type: ignore[method-assign]

    claimant = make_claimant("Maria Gonzalez")
    prop = make_property("Maria Gonzalez", "1 Main St", "CA", 50_000)
    session.add_all([claimant, prop])
    await session.flush()
    claim = Claim(
        claimant_id=claimant.id, property_id=prop.id, state="CA", status="needs_docs",
        required_items_json={"items": [
            RequiredItem(label="Government-issued photo ID", why="id",
                         requirement="required").model_dump(mode="json")
        ]},
        package_json={},
    )
    session.add(claim)
    await session.flush()

    wrong_name = {"doc_type": "drivers_license", "name": "Robert Carter",
                  "field_confidence": {"name": 0.95}}
    app.dependency_overrides[get_session] = lambda: _yield(session)
    app.dependency_overrides[get_document_processor] = lambda: DocumentProcessor(
        llm=StubLLM(wrong_name)
    )
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/claims/{claim.id}/documents",
                json={"raw_text": "x", "doc_type_hint": "drivers_license"},
            )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["mismatches"]
        assert data["needs_human_review"] is True
        assert data["required_items"][0]["satisfied_by_uploaded_doc"] is False
    finally:
        app.dependency_overrides.clear()


async def _yield(session):
    yield session

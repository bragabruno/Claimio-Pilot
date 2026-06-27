"""API test for POST /properties/search via ASGI transport.

Overrides the endpoint's DB dependency with the rolled-back `session` fixture so the test is
self-contained and writes nothing permanent.
"""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.api.deps import get_session
from app.main import app
from tests._helpers import make_property


async def test_search_endpoint_returns_explained_candidates(session):
    session.add(make_property("Robert Carter", "456 Pine St, Austin TX 78701", "TX", 120_000))
    await session.flush()

    async def _override_session():
        yield session

    app.dependency_overrides[get_session] = _override_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/properties/search",
                json={
                    "name": "Robert Carter",
                    "addresses": ["456 Pine St, Austin TX 78701"],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["candidate_count"] >= 1
    top = data["candidates"][0]
    assert top["owner_name"] == "Robert Carter"
    assert top["confidence"] >= 70 and top["is_match"] is True
    assert top["match_reasons"]
    assert "data_quality_summary" in data

"""DB smoke test for PgVectorStore. Skips if Postgres is unreachable (see conftest).

Uses the `session` fixture which rolls back, so no data persists.
"""

from __future__ import annotations

from app.config import settings
from app.db.models import RuleChunk, StateRuleDoc
from app.services.vector_store import PgVectorStore


def _unit_vec(hot_index: int) -> list[float]:
    vec = [0.0] * settings.embed_dim
    vec[hot_index] = 1.0
    return vec


async def _seed_doc(session, state: str, vectors: list[list[float]]) -> None:
    doc = StateRuleDoc(state=state, title=f"{state} demo", body_md="# demo")
    session.add(doc)
    await session.flush()
    for i, vec in enumerate(vectors):
        session.add(RuleChunk(doc=doc, state=state, text=f"{state} chunk {i}", embedding=vec))
    await session.flush()


async def test_search_ranks_nearest_first(session):
    await _seed_doc(session, "CA", [_unit_vec(0), _unit_vec(1)])
    results = await PgVectorStore().search(
        session, state="CA", query_vec=_unit_vec(0), k=5
    )
    assert results
    assert results[0].text == "CA chunk 0"
    assert results[0].score > results[-1].score


async def test_search_is_state_filtered(session):
    await _seed_doc(session, "CA", [_unit_vec(0)])
    await _seed_doc(session, "NY", [_unit_vec(0)])
    results = await PgVectorStore().search(
        session, state="NY", query_vec=_unit_vec(0), k=5
    )
    assert results
    assert all(r.state == "NY" for r in results)

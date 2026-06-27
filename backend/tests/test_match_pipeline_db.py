"""DB-backed pipeline tests (blocking + scoring + dedupe + data quality).

Uses the rolled-back `session` fixture. Assertions are relative (>=) so they hold whether or
not the demo seed data is also present in the database.
"""

from __future__ import annotations

from app.match.pipeline import search
from app.match.scoring import MatchQuery
from tests._helpers import make_property


async def test_search_ranks_blocks_and_dedupes(session):
    session.add(make_property("Robert Carter", "456 Pine St, Austin TX 78701", "TX", 120_000))
    session.add(make_property("Robert Carter", "456 Pine St, Austin TX 78701", "TX", 120_000))
    session.add(make_property("Maria Gonzalez", "1 Bay St, Miami FL 33101", "FL", 50_000))
    await session.flush()

    result = await search(
        session, MatchQuery("Robert Carter", addresses=["456 Pine St, Austin TX 78701"])
    )

    assert result.candidates, "expected at least one candidate"
    top = result.candidates[0]
    assert top.property.owner_name == "Robert Carter"
    assert top.score.confidence >= 70 and top.score.is_match
    # The unrelated record shares no name token / zip, so blocking excludes it.
    owners = [c.property.owner_name for c in result.candidates]
    assert "Maria Gonzalez" not in owners
    # The injected exact duplicate is merged.
    assert result.data_quality.duplicates_merged >= 1


async def test_former_name_survives_blocking(session):
    session.add(make_property("Jennifer Lee", "18 Oak Ave, Oakland CA 94601", "CA", 90_000))
    await session.flush()

    result = await search(
        session,
        MatchQuery(
            "Sarah Johnson",
            prior_names=["Jennifer Lee"],
            addresses=["18 Oak Ave, Oakland CA 94601"],
        ),
    )
    owners = [c.property.owner_name for c in result.candidates]
    assert "Jennifer Lee" in owners


async def test_cross_state_match_survives_blocking(session):
    # Property reported in CA; claimant has since moved to TX. The match must survive blocking
    # on the shared name token even though no state or zip is shared (outdated-address case).
    session.add(make_property("Helen Brooks", "5 Lake Rd, Sacramento CA 95814", "CA", 80_000))
    await session.flush()

    result = await search(
        session, MatchQuery("Helen Brooks", addresses=["9 Pine St, Austin TX 78701"])
    )
    assert "Helen Brooks" in [c.property.owner_name for c in result.candidates]

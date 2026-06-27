"""Matching pipeline orchestration: normalize → block → dedupe → score → rank.

`search` is the single entry point used by both the API and the CLI. It returns scored
candidates plus the index data-quality summary (with duplicates-merged for this result set).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Property
from app.match.blocking import generate_candidates
from app.match.data_quality import DataQualitySummary, assess_index, dedupe_candidates
from app.match.scoring import MatchQuery, MatchTarget, ScoredMatch, score_match


@dataclass
class ScoredCandidate:
    property: Property
    score: ScoredMatch


@dataclass
class SearchResult:
    candidates: list[ScoredCandidate]
    data_quality: DataQualitySummary
    blocking_count: int


def _target_from(prop: Property) -> MatchTarget:
    return MatchTarget(
        owner_name=prop.owner_name,
        owner_last_address=prop.owner_last_address,
        owner_ssn_last4=prop.owner_ssn_last4,
        owner_dob=prop.owner_dob,
        owner_is_business=prop.owner_is_business,
    )


async def search(
    session: AsyncSession, query: MatchQuery, *, limit: int = 25
) -> SearchResult:
    blocked = await generate_candidates(session, query)
    deduped, merged = dedupe_candidates(blocked)

    scored = [
        ScoredCandidate(property=prop, score=score_match(query, _target_from(prop)))
        for prop in deduped
    ]
    scored.sort(key=lambda c: c.score.confidence, reverse=True)
    scored = scored[:limit]

    data_quality = await assess_index(session)
    data_quality.duplicates_merged = merged

    return SearchResult(
        candidates=scored, data_quality=data_quality, blocking_count=len(blocked)
    )

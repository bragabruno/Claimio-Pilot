"""Property search (matching) API."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.match.pipeline import SearchResult, search
from app.match.scoring import MatchQuery
from app.schemas.match import (
    CandidateMatch,
    DataQualitySummaryOut,
    PropertySearchRequest,
    PropertySearchResponse,
)

router = APIRouter(prefix="/properties", tags=["properties"])


def _to_response(result: SearchResult) -> PropertySearchResponse:
    candidates = [
        CandidateMatch(
            property_id=c.property.id,
            source_state=c.property.source_state,
            holder_name=c.property.holder_name,
            owner_name=c.property.owner_name,
            owner_last_address=c.property.owner_last_address,
            amount_cents=c.property.amount_cents,
            property_type=c.property.property_type,
            owner_deceased=c.property.owner_deceased,
            confidence=c.score.confidence,
            is_match=c.score.is_match,
            match_reasons=c.score.match_reasons,
            score_breakdown=c.score.breakdown,
        )
        for c in result.candidates
    ]
    return PropertySearchResponse(
        candidate_count=len(candidates),
        blocking_count=result.blocking_count,
        candidates=candidates,
        data_quality_summary=DataQualitySummaryOut(**vars(result.data_quality)),
    )


@router.post("/search", response_model=PropertySearchResponse)
async def search_properties(
    payload: PropertySearchRequest, session: AsyncSession = Depends(get_session)
) -> PropertySearchResponse:
    """Match a claimant against the property index → ranked candidates with explanations."""
    query = MatchQuery(
        name=payload.name,
        prior_names=payload.prior_names,
        addresses=payload.addresses,
        dob=payload.dob,
        ssn_last4=payload.ssn_last4,
        is_business=payload.is_business,
    )
    result = await search(session, query)
    return _to_response(result)

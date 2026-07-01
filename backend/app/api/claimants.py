"""Claimants API: create / list / fetch (supports the Search → create-claim UI flow)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.db.models import Claimant
from app.schemas.claimant import ClaimantCreate, ClaimantOut

router = APIRouter(prefix="/claimants", tags=["claimants"])


def _to_out(c: Claimant) -> ClaimantOut:
    return ClaimantOut(
        id=c.id, full_name=c.full_name, prior_names=list(c.prior_names),
        addresses=list(c.addresses), dob=c.dob, ssn_last4=c.ssn_last4,
        email=c.email, is_business=c.is_business,
    )


@router.post("", response_model=ClaimantOut)
async def create_claimant(
    payload: ClaimantCreate, session: AsyncSession = Depends(get_session)
) -> ClaimantOut:
    claimant = Claimant(
        full_name=payload.full_name, prior_names=payload.prior_names,
        addresses=payload.addresses, dob=payload.dob,
        ssn_last4=payload.ssn_last4,  # request already carries only the last 4
        email=payload.email, is_business=payload.is_business,
    )
    session.add(claimant)
    await session.commit()
    return _to_out(claimant)


@router.get("", response_model=list[ClaimantOut])
async def list_claimants(
    limit: int = 50, session: AsyncSession = Depends(get_session)
) -> list[ClaimantOut]:
    rows = (
        await session.execute(
            select(Claimant).order_by(desc(Claimant.created_at)).limit(limit)
        )
    ).scalars().all()
    return [_to_out(c) for c in rows]


@router.get("/{claimant_id}", response_model=ClaimantOut)
async def get_claimant(
    claimant_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> ClaimantOut:
    claimant = await session.get(Claimant, claimant_id)
    if claimant is None:
        raise HTTPException(status_code=404, detail="claimant not found")
    return _to_out(claimant)

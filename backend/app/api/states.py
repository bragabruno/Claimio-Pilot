"""States API: serve a state's rule doc so the UI can show a cited source."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.db.models import StateRuleDoc
from app.schemas.claim import StateRulesResponse

router = APIRouter(prefix="/states", tags=["states"])


@router.get("/{state}/rules", response_model=StateRulesResponse)
async def get_state_rules(
    state: str, session: AsyncSession = Depends(get_session)
) -> StateRulesResponse:
    code = state.upper()
    doc = (
        await session.execute(select(StateRuleDoc).where(StateRuleDoc.state == code))
    ).scalars().first()
    if doc is None:
        raise HTTPException(status_code=404, detail=f"no rules for state {code}")
    return StateRulesResponse(
        state=doc.state, title=doc.title, version=doc.version, body_md=doc.body_md
    )

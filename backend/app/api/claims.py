"""Claims API: create a claim (runs the pipeline) and fetch its full state."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.claims.extraction import DocumentProcessor
from app.claims.workflow import ClaimWorkflow, WorkflowResult
from app.db.models import Claim, Claimant, Property, RunTrace
from app.schemas.claim import (
    Citation,
    ClaimCreateRequest,
    ClaimPreviewRequest,
    ClaimPreviewResponse,
    ClaimResponse,
    RequiredItem,
    TraceStep,
    TraceSummary,
)
from app.schemas.document import DocumentUploadRequest, DocumentUploadResponse

router = APIRouter(prefix="/claims", tags=["claims"])


def get_workflow() -> ClaimWorkflow:  # overridable in tests
    return ClaimWorkflow()


def get_document_processor() -> DocumentProcessor:  # overridable in tests
    return DocumentProcessor()


def _result_to_response(r: WorkflowResult) -> ClaimResponse:
    return ClaimResponse(
        claim_id=r.claim_id, claimant_id=r.claimant_id, property_id=r.property_id,
        state=r.state, status=r.status, needs_human_review=r.needs_human_review,
        required_items=r.items,
        citations=[
            Citation(
                chunk_id=c.chunk_id, doc_id=c.doc_id, state=c.state, score=c.score, text=c.text
            )
            for c in r.citations
        ],
        draft_letter=r.letter,
        trace=TraceSummary(
            steps=[TraceStep(step=s, detail=d) for s, d in r.steps],
            retrieval_hits=len(r.citations), tokens=r.tokens, cost_cents=r.cost_cents,
        ),
    )


@router.post("", response_model=ClaimResponse)
async def create_claim(
    payload: ClaimCreateRequest,
    session: AsyncSession = Depends(get_session),
    workflow: ClaimWorkflow = Depends(get_workflow),
) -> ClaimResponse:
    """Create a claim: retrieval → grounded requirements → letter → trace."""
    claimant = await session.get(Claimant, payload.claimant_id)
    prop = await session.get(Property, payload.property_id)
    if claimant is None or prop is None:
        raise HTTPException(status_code=404, detail="claimant or property not found")
    result = await workflow.run(session, claimant, prop)
    await session.commit()
    return _result_to_response(result)


@router.post("/preview", response_model=ClaimPreviewResponse)
async def preview_claim(
    payload: ClaimPreviewRequest,
    session: AsyncSession = Depends(get_session),
    workflow: ClaimWorkflow = Depends(get_workflow),
) -> ClaimPreviewResponse:
    """Compute a hypothetical claim's requirements for one state — no persistence.

    Powers the compare-states view: call twice with the same claimant + amount and two states.
    """
    name = payload.name or "Prospective claimant"
    claimant = Claimant(
        full_name=name, is_business=payload.is_business, prior_names=[], addresses=[]
    )
    prop = Property(
        source_state=payload.state.upper(), amount_cents=payload.amount_cents,
        owner_deceased=payload.owner_deceased, holder_name="(preview)",
        owner_name=name, property_type="preview",
    )
    computed = await workflow.preview(session, claimant, prop)
    return ClaimPreviewResponse(
        state=computed.state,
        needs_human_review=computed.needs_human_review,
        required_items=computed.items,
        citations=[
            Citation(
                chunk_id=c.chunk_id, doc_id=c.doc_id, state=c.state, score=c.score, text=c.text
            )
            for c in computed.citations
        ],
        draft_letter=computed.letter,
        trace=TraceSummary(
            steps=[TraceStep(step=s, detail=d) for s, d in computed.steps],
            retrieval_hits=len(computed.citations), tokens=computed.tokens,
            cost_cents=computed.cost_cents,
        ),
    )


@router.post("/{claim_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    claim_id: uuid.UUID,
    payload: DocumentUploadRequest,
    session: AsyncSession = Depends(get_session),
    processor: DocumentProcessor = Depends(get_document_processor),
) -> DocumentUploadResponse:
    """Extract a synthetic document, flag mismatches, and flip satisfied requirements."""
    claim = await session.get(Claim, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="claim not found")
    claimant = await session.get(Claimant, claim.claimant_id)
    prop = await session.get(Property, claim.property_id)
    if claimant is None or prop is None:
        raise HTTPException(status_code=404, detail="claimant or property not found")

    result = await processor.process(session, claim, claimant, prop, payload)
    await session.commit()
    return DocumentUploadResponse(
        claim_id=claim.id, status=result.status, extracted=result.extracted,
        mismatches=result.mismatches, needs_human_review=result.needs_human_review,
        satisfied_labels=result.satisfied_labels, required_items=result.items,
    )


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> ClaimResponse:
    claim = await session.get(Claim, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="claim not found")

    trace = (
        await session.execute(
            select(RunTrace)
            .where(RunTrace.claim_id == claim_id)
            .order_by(desc(RunTrace.created_at))
            .limit(1)
        )
    ).scalar_one_or_none()

    pkg = claim.package_json or {}
    items = [RequiredItem(**it) for it in (claim.required_items_json or {}).get("items", [])]
    citations = [Citation(**c) for c in pkg.get("citations", [])]

    steps: list[TraceStep] = []
    retrieval_hits = tokens = 0
    cost = 0.0
    if trace is not None:
        steps_json = trace.steps_json or {}
        steps = [TraceStep(**s) for s in steps_json.get("steps", [])]
        retrieval_hits = steps_json.get("retrieval_hits", 0)
        tokens = trace.tokens
        cost = float(trace.cost_cents)

    return ClaimResponse(
        claim_id=claim.id, claimant_id=claim.claimant_id, property_id=claim.property_id,
        state=claim.state, status=claim.status,
        needs_human_review=bool(pkg.get("needs_human_review", False)),
        required_items=items, citations=citations, draft_letter=pkg.get("draft_letter", ""),
        trace=TraceSummary(
            steps=steps, retrieval_hits=retrieval_hits, tokens=tokens, cost_cents=cost
        ),
    )

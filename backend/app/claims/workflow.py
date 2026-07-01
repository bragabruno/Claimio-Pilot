"""ClaimWorkflow — orchestrates retrieval → requirements → letter → trace and persists a claim.

A thin, explicit pipeline (liftable into LangGraph later). The LLM is fail-soft: if it errors,
deterministic grounded requirements still produce a correct, cited result. Tokens + estimated
cost are recorded on the run trace.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.claims.letter import draft_letter
from app.claims.requirements import (
    deterministic_requirements,
    llm_requirements,
    merge_requirements,
)
from app.claims.retrieval import build_claim_query, chunks_for_state, retrieve_citations
from app.config import settings
from app.db.models import AuditEvent, Claim, Claimant, Property, RunTrace, StateRuleDoc
from app.schemas.claim import RequiredItem
from app.services.embeddings import EmbeddingsClient
from app.services.llm import LLMClient, estimate_cost_cents
from app.services.vector_store import PgVectorStore, RetrievedChunk


@dataclass
class WorkflowResult:
    claim_id: uuid.UUID
    claimant_id: uuid.UUID
    property_id: uuid.UUID
    state: str
    status: str
    needs_human_review: bool
    items: list[RequiredItem]
    citations: list[RetrievedChunk]
    letter: str
    steps: list[tuple[str, str]]
    tokens: int
    cost_cents: float


@dataclass
class ComputedClaim:
    """Result of the compute stage (retrieval → requirements → letter), before persistence."""

    state: str
    items: list[RequiredItem]
    citations: list[RetrievedChunk]
    letter: str
    needs_human_review: bool
    steps: list[tuple[str, str]]
    tokens: int
    cost_cents: float


async def _state_doc_title(session: AsyncSession, state: str) -> str:
    title = (
        await session.execute(select(StateRuleDoc.title).where(StateRuleDoc.state == state))
    ).scalars().first()
    return title or f"{state} unclaimed property rules"


class ClaimWorkflow:
    def __init__(
        self,
        *,
        embeddings: EmbeddingsClient | None = None,
        llm: LLMClient | None = None,
        store: PgVectorStore | None = None,
        top_k: int | None = None,
    ) -> None:
        self.embeddings = embeddings or EmbeddingsClient()
        self.llm = llm or LLMClient()
        self.store = store or PgVectorStore()
        self.top_k = top_k or settings.retrieval_top_k

    async def _compute(
        self, session: AsyncSession, claimant: Claimant, prop: Property
    ) -> ComputedClaim:
        """Retrieval → requirements → letter. No persistence (shared by run + preview)."""
        state = prop.source_state
        query = build_claim_query(claimant, prop)
        citations = await retrieve_citations(
            session, state=state, query_text=query, k=self.top_k,
            embeddings=self.embeddings, store=self.store,
        )
        state_chunks = await chunks_for_state(session, state)

        deterministic = deterministic_requirements(claimant, prop, state_chunks)
        llm_items, usage = await llm_requirements(claimant, prop, citations, self.llm)
        items = merge_requirements(deterministic, llm_items)

        title = await _state_doc_title(session, state)
        letter = draft_letter(claimant, prop, items, title)

        needs_review = any(i.status == "needs_human_review" for i in items)
        top_score = citations[0].score if citations else 0.0
        steps: list[tuple[str, str]] = [
            ("retrieval", f"retrieved {len(citations)} rule chunks for {state} "
                          f"(top score {top_score:.2f})"),
            ("deterministic_requirements", f"{len(deterministic)} deterministic items"),
            ("llm_requirements", f"{len(llm_items)} model-proposed items merged"),
            ("letter", "drafted claimant instruction letter"),
        ]
        return ComputedClaim(
            state=state, items=items, citations=citations, letter=letter,
            needs_human_review=needs_review, steps=steps,
            tokens=usage.total_tokens, cost_cents=estimate_cost_cents(self.llm.model, usage),
        )

    async def preview(
        self, session: AsyncSession, claimant: Claimant, prop: Property
    ) -> ComputedClaim:
        """Compute requirements + letter WITHOUT persisting — powers the compare-states view."""
        return await self._compute(session, claimant, prop)

    async def run(
        self, session: AsyncSession, claimant: Claimant, prop: Property
    ) -> WorkflowResult:
        computed = await self._compute(session, claimant, prop)
        status = "needs_docs"

        citation_payload = [
            {
                "chunk_id": str(c.chunk_id), "doc_id": str(c.doc_id), "state": c.state,
                "score": round(c.score, 4), "text": c.text,
            }
            for c in computed.citations
        ]
        claim = Claim(
            claimant_id=claimant.id, property_id=prop.id, state=computed.state, status=status,
            required_items_json={"items": [i.model_dump(mode="json") for i in computed.items]},
            package_json={
                "draft_letter": computed.letter,
                "needs_human_review": computed.needs_human_review,
                "citations": citation_payload,
            },
        )
        session.add(claim)
        await session.flush()

        steps = list(computed.steps)
        session.add(
            RunTrace(
                claim_id=claim.id,
                steps_json={
                    "steps": [{"step": s, "detail": d} for s, d in steps],
                    "retrieval_hits": len(computed.citations),
                },
                tokens=computed.tokens,
                cost_cents=round(computed.cost_cents),
            )
        )
        session.add(
            AuditEvent(
                claim_id=claim.id, type="claim_created",
                payload_json={"needs_human_review": computed.needs_human_review,
                              "item_count": len(computed.items)},
            )
        )
        await session.flush()
        steps.append(("persisted", f"claim {claim.id} status={status}"))

        return WorkflowResult(
            claim_id=claim.id, claimant_id=claimant.id, property_id=prop.id,
            state=computed.state, status=status,
            needs_human_review=computed.needs_human_review, items=computed.items,
            citations=computed.citations, letter=computed.letter, steps=steps,
            tokens=computed.tokens, cost_cents=computed.cost_cents,
        )

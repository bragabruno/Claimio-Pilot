"""Pydantic I/O models for claim creation, requirements, citations, and the run trace."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

RequirementKind = Literal["required", "conditional"]
ItemStatus = Literal["grounded", "needs_human_review"]
ItemOrigin = Literal["deterministic", "llm"]


class RequiredItem(BaseModel):
    label: str
    why: str
    requirement: RequirementKind
    satisfied_by_uploaded_doc: bool = False  # flipped in Phase 4 (document extraction)
    source_rule_chunk_id: uuid.UUID | None = None
    status: ItemStatus = "grounded"
    origin: ItemOrigin = "deterministic"


class Citation(BaseModel):
    chunk_id: uuid.UUID
    doc_id: uuid.UUID
    state: str
    score: float
    text: str


class TraceStep(BaseModel):
    step: str
    detail: str


class TraceSummary(BaseModel):
    steps: list[TraceStep]
    retrieval_hits: int
    tokens: int
    cost_cents: float


class ClaimCreateRequest(BaseModel):
    claimant_id: uuid.UUID
    property_id: uuid.UUID


class ClaimResponse(BaseModel):
    claim_id: uuid.UUID
    claimant_id: uuid.UUID
    property_id: uuid.UUID
    state: str
    status: str
    needs_human_review: bool = Field(
        ..., description="True if any required item could not be grounded with confidence"
    )
    required_items: list[RequiredItem]
    citations: list[Citation]
    draft_letter: str
    trace: TraceSummary


class StateRulesResponse(BaseModel):
    state: str
    title: str
    version: str
    body_md: str

"""Pydantic I/O models for document extraction (Phase 4)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.schemas.claim import RequiredItem


class ExtractedDoc(BaseModel):
    doc_type: str
    name: str | None = None
    dob: str | None = None
    address: str | None = None
    doc_number_last4: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    # Per-field confidence in [0, 1]; drives the human-review gate (docs/adr/0003).
    field_confidence: dict[str, float] = Field(default_factory=dict)


class DocumentUploadRequest(BaseModel):
    # The synthetic sample's text. (Real image/PDF + OCR/vision is a productionization point.)
    raw_text: str
    doc_type_hint: str | None = None


class DocumentUploadResponse(BaseModel):
    claim_id: uuid.UUID
    status: str
    extracted: ExtractedDoc
    mismatches: list[str]
    needs_human_review: bool
    satisfied_labels: list[str]
    required_items: list[RequiredItem]

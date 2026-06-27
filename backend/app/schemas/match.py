"""Pydantic I/O models for the property-search (matching) endpoint."""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, Field


class PropertySearchRequest(BaseModel):
    name: str = Field(..., description="Claimant's current full name")
    prior_names: list[str] = Field(default_factory=list)
    addresses: list[str] = Field(default_factory=list)
    # Optional corroborating identifiers — strengthen confidence when supplied.
    dob: dt.date | None = None
    ssn_last4: str | None = Field(default=None, max_length=4)
    is_business: bool | None = None


class CandidateMatch(BaseModel):
    property_id: uuid.UUID
    source_state: str
    holder_name: str
    owner_name: str
    owner_last_address: str | None
    amount_cents: int
    property_type: str
    owner_deceased: bool
    confidence: int = Field(..., ge=0, le=100)
    is_match: bool
    match_reasons: list[str]
    score_breakdown: dict[str, float | None]


class DataQualitySummaryOut(BaseModel):
    total_records: int
    missing_address: int
    missing_address_pct: float
    missing_reported_date: int
    invalid_amount: int
    duplicate_groups: int
    duplicate_records: int
    duplicates_merged: int


class PropertySearchResponse(BaseModel):
    candidate_count: int
    blocking_count: int = Field(..., description="Records that passed blocking (pre-scoring)")
    candidates: list[CandidateMatch]
    data_quality_summary: DataQualitySummaryOut

"""Pydantic I/O models for claimants."""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, Field


class ClaimantCreate(BaseModel):
    full_name: str
    prior_names: list[str] = Field(default_factory=list)
    addresses: list[str] = Field(default_factory=list)
    dob: dt.date | None = None
    ssn_last4: str | None = Field(default=None, max_length=4)
    email: str | None = None
    is_business: bool = False


class ClaimantOut(BaseModel):
    id: uuid.UUID
    full_name: str
    prior_names: list[str]
    addresses: list[str]
    dob: dt.date | None = None
    ssn_last4: str | None = None  # already last-4 only
    email: str | None = None
    is_business: bool

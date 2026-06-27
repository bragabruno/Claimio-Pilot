"""ClaimPilot domain model (see docs/adr/0001, 0006).

Seven tables: claimant, property, state_rule_doc, rule_chunk (with embeddings), claim,
run_trace, audit_event. Embedding dimension comes from config so the vector column is not
hard-coded to one provider.
"""

from __future__ import annotations

import datetime as dt
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.db.base import Base

CLAIM_STATUSES = ("draft", "needs_docs", "ready_to_file", "filed", "recovered")


def _uuid_col() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _created_at() -> Mapped[dt.datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Claimant(Base):
    __tablename__ = "claimant"

    id: Mapped[uuid.UUID] = _uuid_col()
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    prior_names: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list, server_default="{}"
    )
    addresses: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list, server_default="{}"
    )
    dob: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    ssn_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    is_business: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[dt.datetime] = _created_at()


class Property(Base):
    __tablename__ = "property"
    __table_args__ = (
        # GIN index supports the blocking step's `owner_name_tokens && :query_tokens`
        # array-overlap predicate (see app/match/blocking.py).
        Index("ix_property_owner_name_tokens_gin", "owner_name_tokens", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = _uuid_col()
    source_state: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    holder_name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_last_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    property_type: Mapped[str] = mapped_column(String(80), nullable=False)
    owner_deceased: Mapped[bool] = mapped_column(nullable=False, default=False)
    reported_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="unclaimed")

    # --- Reconciliation fields (Phase 2) ---
    # Derived at ingestion for normalization + blocking.
    normalized_owner_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_owner_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_name_tokens: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list, server_default="{}"
    )
    owner_zip: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    # Corroborating identifiers a holder report sometimes includes (often absent).
    owner_ssn_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    owner_dob: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    owner_is_business: Mapped[bool] = mapped_column(nullable=False, default=False)


class StateRuleDoc(Base):
    __tablename__ = "state_rule_doc"

    id: Mapped[uuid.UUID] = _uuid_col()
    state: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False, default="v1-demo")

    chunks: Mapped[list[RuleChunk]] = relationship(
        back_populates="doc", cascade="all, delete-orphan"
    )


class RuleChunk(Base):
    __tablename__ = "rule_chunk"
    __table_args__ = (
        # HNSW index for cosine similarity search, filtered by state at query time.
        Index(
            "ix_rule_chunk_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_col()
    doc_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("state_rule_doc.id", ondelete="CASCADE"), nullable=False
    )
    state: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Dimension from config — pgvector columns are fixed-dimension (see docs/adr/0001).
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embed_dim), nullable=False)

    doc: Mapped[StateRuleDoc] = relationship(back_populates="chunks")


class Claim(Base):
    __tablename__ = "claim"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','needs_docs','ready_to_file','filed','recovered')",
            name="ck_claim_status",
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_col()
    claimant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("claimant.id", ondelete="CASCADE"), nullable=False
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("property.id", ondelete="CASCADE"), nullable=False
    )
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    required_items_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    package_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[dt.datetime] = _created_at()
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class RunTrace(Base):
    __tablename__ = "run_trace"

    id: Mapped[uuid.UUID] = _uuid_col()
    claim_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("claim.id", ondelete="SET NULL"), nullable=True
    )
    steps_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[dt.datetime] = _created_at()


class AuditEvent(Base):
    __tablename__ = "audit_event"

    id: Mapped[uuid.UUID] = _uuid_col()
    claim_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("claim.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[dt.datetime] = _created_at()

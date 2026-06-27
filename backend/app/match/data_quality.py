"""Data-quality pass over the property index.

Reconciliation is only as good as the data feeding it, so the search surfaces a short health
report: how many records are missing an address, missing a reported date, or have an invalid
amount, and how many duplicate property records exist. Duplicate candidates returned by a
search are merged (collapsed) and counted.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Property


@dataclass
class DataQualitySummary:
    total_records: int = 0
    missing_address: int = 0
    missing_address_pct: float = 0.0
    missing_reported_date: int = 0
    invalid_amount: int = 0
    duplicate_groups: int = 0
    duplicate_records: int = 0
    duplicates_merged: int = 0  # collapsed within a given search result set


def _dupe_key(p: Property) -> tuple:
    return (
        p.source_state,
        p.normalized_owner_name or p.owner_name.lower(),
        p.normalized_owner_address or "",
        p.amount_cents,
    )


def dedupe_candidates(candidates: list[Property]) -> tuple[list[Property], int]:
    """Collapse exact-duplicate property records, keeping the first of each group."""
    seen: set[tuple] = set()
    unique: list[Property] = []
    merged = 0
    for prop in candidates:
        key = _dupe_key(prop)
        if key in seen:
            merged += 1
            continue
        seen.add(key)
        unique.append(prop)
    return unique, merged


async def assess_index(session: AsyncSession) -> DataQualitySummary:
    """Compute index-wide data-quality counts."""
    total = (await session.execute(select(func.count()).select_from(Property))).scalar_one()
    if total == 0:
        return DataQualitySummary()

    address_missing = (Property.owner_last_address.is_(None)) | (
        func.trim(Property.owner_last_address) == ""
    )
    missing_address = (
        await session.execute(
            select(func.count()).select_from(Property).where(address_missing)
        )
    ).scalar_one()

    missing_reported_date = (
        await session.execute(
            select(func.count())
            .select_from(Property)
            .where(Property.reported_date.is_(None))
        )
    ).scalar_one()

    invalid_amount = (
        await session.execute(
            select(func.count()).select_from(Property).where(Property.amount_cents <= 0)
        )
    ).scalar_one()

    # Duplicate groups: same state + normalized owner + normalized address + amount.
    group_counts = (
        await session.execute(
            select(func.count().label("c"))
            .select_from(Property)
            .group_by(
                Property.source_state,
                Property.normalized_owner_name,
                Property.normalized_owner_address,
                Property.amount_cents,
            )
            .having(func.count() > 1)
        )
    ).scalars().all()
    duplicate_groups = len(group_counts)
    duplicate_records = sum(c - 1 for c in group_counts)

    return DataQualitySummary(
        total_records=total,
        missing_address=missing_address,
        missing_address_pct=round(100.0 * missing_address / total, 1),
        missing_reported_date=missing_reported_date,
        invalid_amount=invalid_amount,
        duplicate_groups=duplicate_groups,
        duplicate_records=duplicate_records,
    )

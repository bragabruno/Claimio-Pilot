"""Shared API dependencies."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import SessionLocal


async def get_session() -> AsyncIterator[AsyncSession]:  # pragma: no cover - trivial
    async with SessionLocal() as session:
        yield session

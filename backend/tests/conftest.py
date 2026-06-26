"""Shared fixtures. DB-backed tests skip cleanly when Postgres is not reachable."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.db.base import SessionLocal, engine


@pytest.fixture
async def session():
    """An AsyncSession that rolls back after the test. Skips if the DB is unreachable.

    The engine pool is disposed on teardown: pytest-asyncio runs each test in its own event
    loop, and a pooled async connection is only valid on the loop that opened it.
    """
    db = SessionLocal()
    try:
        await db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 — any connection failure means "no DB here"
        await db.close()
        await engine.dispose()
        pytest.skip("Postgres not reachable (run `make dev && make migrate`)")
    try:
        yield db
    finally:
        await db.rollback()
        await db.close()
        await engine.dispose()

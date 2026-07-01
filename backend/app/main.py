"""FastAPI application — Phase 1 surface: health and observability.

Pipeline endpoints (search, claims, documents) land in later phases. The persistent
disclaimer is returned on the root so every consumer sees it.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, select, text

from app.api.claimants import router as claimants_router
from app.api.claims import router as claims_router
from app.api.properties import router as properties_router
from app.api.states import router as states_router
from app.config import settings
from app.db.base import SessionLocal
from app.db.models import RunTrace
from app.logging import configure_logging, get_logger

logger = get_logger(__name__)

DISCLAIMER = (
    "Demonstration system. Synthetic data. Not legal advice; "
    "does not replace official state claim processes."
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("ClaimPilot API starting")
    yield


app = FastAPI(title="ClaimPilot API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(claimants_router)
app.include_router(properties_router)
app.include_router(claims_router)
app.include_router(states_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "claimpilot", "disclaimer": DISCLAIMER}


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness + DB connectivity check."""
    async with SessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/debug/last-run")
async def last_run() -> dict:
    """Most recent pipeline trace (tokens + estimated cost). Empty until a claim runs."""
    async with SessionLocal() as session:
        stmt = select(RunTrace).order_by(desc(RunTrace.created_at)).limit(1)
        trace = (await session.execute(stmt)).scalar_one_or_none()
    if trace is None:
        return {"last_run": None}
    return {
        "last_run": {
            "id": str(trace.id),
            "claim_id": str(trace.claim_id) if trace.claim_id else None,
            "steps": trace.steps_json,
            "tokens": trace.tokens,
            "cost_cents": trace.cost_cents,
            "created_at": trace.created_at.isoformat(),
        }
    }

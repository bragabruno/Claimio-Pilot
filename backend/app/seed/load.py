"""Seed loader: synthetic claimants/properties + embedded state rules.

Idempotent: clears the demo tables, regenerates the synthetic dataset, ingests the 5 state
rule docs, chunks them, embeds each chunk via the OpenAI-compatible client, and stores the
vectors. Run with ``make seed`` (needs a reachable embedding model — see `.env.example`).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import delete

from app.db.base import SessionLocal
from app.db.models import (
    AuditEvent,
    Claim,
    Claimant,
    Property,
    RuleChunk,
    RunTrace,
    StateRuleDoc,
)
from app.logging import configure_logging, get_logger
from app.match.normalize import canonical_name, name_tokens, normalize_address
from app.seed.synthetic import build_dataset
from app.services.chunking import chunk_markdown
from app.services.embeddings import EmbeddingsClient
from app.states import STATE_CODES, code_for_slug, slug_for

logger = get_logger(__name__)

_RULES_DIR = Path(__file__).resolve().parents[3] / "seed" / "state_rules"

# Delete order respects foreign keys (children first).
_CLEAR_ORDER = (AuditEvent, RunTrace, Claim, RuleChunk, StateRuleDoc, Property, Claimant)


def _title_of(body_md: str, fallback: str) -> str:
    for line in body_md.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return fallback


def _enrich_property_normalization(prop) -> None:
    """Populate the derived normalization + blocking columns from raw owner fields."""
    prop.normalized_owner_name = canonical_name(prop.owner_name)
    prop.owner_name_tokens = sorted(name_tokens(prop.owner_name))
    parts = normalize_address(prop.owner_last_address)
    prop.normalized_owner_address = parts.normalized or None
    prop.owner_zip = parts.zip


async def load(embeddings: EmbeddingsClient | None = None) -> dict[str, int]:
    """Load all seed data. Returns inserted-row counts by entity."""
    embeddings = embeddings or EmbeddingsClient()
    claimants, properties = build_dataset()
    for prop in properties:
        _enrich_property_normalization(prop)

    async with SessionLocal() as session:
        for model in _CLEAR_ORDER:
            await session.execute(delete(model))

        session.add_all(claimants)
        session.add_all(properties)

        # Ingest + chunk all rule docs, collecting chunk texts for one batched embed call.
        docs: list[StateRuleDoc] = []
        pending: list[tuple[StateRuleDoc, str]] = []  # (doc, chunk_text)
        for code in STATE_CODES:
            path = _RULES_DIR / f"{slug_for(code)}.md"
            body_md = path.read_text(encoding="utf-8")
            doc = StateRuleDoc(
                state=code_for_slug(path.stem),
                title=_title_of(body_md, code),
                body_md=body_md,
            )
            docs.append(doc)
            for chunk_text in chunk_markdown(body_md):
                pending.append((doc, chunk_text))
        session.add_all(docs)

        vectors = await embeddings.embed_texts([text for _, text in pending])
        chunks = [
            RuleChunk(doc=doc, state=doc.state, text=text, embedding=vec)
            for (doc, text), vec in zip(pending, vectors, strict=True)
        ]
        session.add_all(chunks)

        await session.commit()

        counts = {
            "claimants": len(claimants),
            "properties": len(properties),
            "state_rule_docs": len(docs),
            "rule_chunks": len(chunks),
        }

    logger.info("seed complete: %s", counts)
    return counts


def main() -> None:
    configure_logging()
    counts = asyncio.run(load())
    print("Seeded:")
    for key, value in counts.items():
        print(f"  {key:16} {value}")


if __name__ == "__main__":
    main()

"""Requirement reasoning: deterministic logic + LLM nuance, all grounded in rule chunks.

Deterministic rules (identity, address, the notarization threshold, deceased/business docs)
are computed directly and grounded by locating their governing rule chunk — so the
guardrail-critical items are correct and cited regardless of the LLM. The LLM proposes
*additional* nuanced items, each of which must cite one of the retrieved chunks; anything
ungrounded is flagged `needs_human_review` rather than shown as authoritative (docs/adr/0003,
0004).
"""

from __future__ import annotations

import re

from app.claims.retrieval import find_chunk_by_keywords
from app.db.models import Claimant, Property, RuleChunk
from app.logging import get_logger
from app.schemas.claim import RequiredItem
from app.services.llm import LLMClient, LLMError, Usage
from app.services.vector_store import RetrievedChunk
from app.states import STATES

logger = get_logger(__name__)


def _norm_label(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", label.lower()).strip()


def _grounded(label: str, why: str, kind: str, chunk: RuleChunk | None) -> RequiredItem:
    if chunk is None:
        return RequiredItem(
            label=label, why=why, requirement=kind,
            source_rule_chunk_id=None, status="needs_human_review", origin="deterministic",
        )
    return RequiredItem(
        label=label, why=why, requirement=kind,
        source_rule_chunk_id=chunk.id, status="grounded", origin="deterministic",
    )


def deterministic_requirements(
    claimant: Claimant, prop: Property, state_chunks: list[RuleChunk]
) -> list[RequiredItem]:
    """Hard rules computed from the claimant + property, grounded by governing chunk."""
    threshold = STATES[prop.source_state]["notarization_threshold_cents"]
    items = [
        _grounded(
            "Government-issued photo ID",
            "Proof of identity is required for every claim.",
            "required",
            find_chunk_by_keywords(state_chunks, ["identity", "photo id"]),
        ),
        _grounded(
            "Proof of current address",
            "Proof of address links the claimant to the reported owner and address.",
            "required",
            find_chunk_by_keywords(state_chunks, ["address"]),
        ),
    ]

    if prop.amount_cents > threshold:
        items.append(
            _grounded(
                "Notarized claim form",
                f"Claim amount ${prop.amount_cents / 100:,.2f} exceeds the "
                f"${threshold / 100:,.0f} notarization threshold for {prop.source_state}.",
                "required",
                find_chunk_by_keywords(state_chunks, ["notar"]),
            )
        )

    if prop.owner_deceased:
        items.append(
            _grounded(
                "Certified death certificate",
                "The reported owner is deceased; a certified death certificate is required.",
                "required",
                find_chunk_by_keywords(state_chunks, ["deceased", "death", "heir"]),
            )
        )
        items.append(
            _grounded(
                "Proof of right to claim (heir/estate documentation)",
                "Heir or estate documentation establishes the right to a deceased owner's "
                "property.",
                "conditional",
                find_chunk_by_keywords(
                    state_chunks, ["heir", "estate", "letters", "affidavit", "administration"]
                ),
            )
        )

    if claimant.is_business:
        items.append(
            _grounded(
                "Business formation documents, EIN proof, and authorized signer",
                "Business-entity claims require formation documents, EIN proof, and an "
                "authorized signer.",
                "required",
                find_chunk_by_keywords(
                    state_chunks, ["business", "entity", "ein", "incorporation", "formation"]
                ),
            )
        )

    return items


_SYSTEM = (
    "You map US unclaimed-property rules to the documents a specific claimant must provide. "
    "Only output requirements explicitly supported by the provided rule excerpts. Never invent "
    "requirements or cite an excerpt that does not support the item. Respond with JSON only."
)


def _build_user_prompt(claimant: Claimant, prop: Property, citations: list[RetrievedChunk]) -> str:
    excerpts = "\n".join(f"[{i}] {c.text}" for i, c in enumerate(citations))
    return (
        f"Claimant: {'business entity' if claimant.is_business else 'individual'}.\n"
        f"Property: state {prop.source_state}, amount ${prop.amount_cents / 100:,.2f}, "
        f"owner_deceased={prop.owner_deceased}.\n\n"
        f"Rule excerpts (cite by index):\n{excerpts}\n\n"
        'Return JSON: {"items":[{"label":str,"why":str,'
        '"requirement":"required"|"conditional","source_index":int}]}. '
        "Only include items grounded in an excerpt; source_index must be one of the indices above."
    )


async def llm_requirements(
    claimant: Claimant, prop: Property, citations: list[RetrievedChunk], llm: LLMClient
) -> tuple[list[RequiredItem], Usage]:
    """LLM-proposed nuanced items. Each must cite a retrieved chunk or it is flagged for review."""
    if not citations:
        return [], Usage()

    try:
        data, usage = await llm.complete_json(
            system=_SYSTEM, user=_build_user_prompt(claimant, prop, citations)
        )
    except LLMError as exc:
        logger.warning("LLM requirement mapping failed; deterministic items only: %s", exc)
        return [], Usage()

    items: list[RequiredItem] = []
    for raw in data.get("items", [])[:12]:
        label = str(raw.get("label", "")).strip()
        if not label:
            continue
        why = str(raw.get("why", "")).strip()
        kind = raw.get("requirement", "required")
        if kind not in ("required", "conditional"):
            kind = "required"
        idx = raw.get("source_index")
        chunk = citations[idx] if isinstance(idx, int) and 0 <= idx < len(citations) else None
        if chunk is None:
            items.append(
                RequiredItem(
                    label=label, why=why or "Model-proposed; supporting citation missing.",
                    requirement=kind, source_rule_chunk_id=None,
                    status="needs_human_review", origin="llm",
                )
            )
        else:
            items.append(
                RequiredItem(
                    label=label, why=why, requirement=kind,
                    source_rule_chunk_id=chunk.chunk_id, status="grounded", origin="llm",
                )
            )
    return items, usage


def merge_requirements(
    deterministic: list[RequiredItem], llm_items: list[RequiredItem]
) -> list[RequiredItem]:
    """Deterministic items win; LLM items are appended unless they duplicate a label."""
    seen = {_norm_label(i.label) for i in deterministic}
    merged = list(deterministic)
    for item in llm_items:
        key = _norm_label(item.label)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged

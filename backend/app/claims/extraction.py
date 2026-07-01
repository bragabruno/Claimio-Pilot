"""Document extraction + requirement satisfaction (Phase 4, docs/adr/0002, 0003).

Extracts structured fields (with per-field confidence) from a synthetic document, cross-checks
the extracted name/address against the claimant + property, and flips the requirements the
document satisfies. Low confidence or a mismatch routes to human review — a satisfied
requirement is never asserted on weak evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditEvent, Claim, Claimant, Property, RunTrace
from app.logging import get_logger
from app.match.normalize import canonical_name, normalize_address
from app.schemas.claim import RequiredItem
from app.schemas.document import DocumentUploadRequest, ExtractedDoc
from app.services.llm import LLMClient, LLMError, Usage, estimate_cost_cents

logger = get_logger(__name__)

EXTRACTION_CONFIDENCE_FLOOR = 0.5
NAME_MATCH_FLOOR = 80.0
ADDRESS_MATCH_FLOOR = 70.0

# Document type → the requirement-label phrase it can satisfy.
DOC_TYPE_SATISFIES: dict[str, str] = {
    "drivers_license": "photo id",
    "driver_license": "photo id",
    "passport": "photo id",
    "state_id": "photo id",
    "id_card": "photo id",
    "utility_bill": "address",
    "bank_statement": "address",
    "lease": "address",
    "death_certificate": "death certificate",
}

_CORE_FIELDS = ("name", "address", "doc_number_last4", "dob", "issue_date", "expiry_date")

_SYSTEM = (
    "You extract fields from a US identity, address, or claim document. Output JSON only with "
    "keys doc_type, name, dob, address, doc_number_last4, issue_date, expiry_date, and a "
    "field_confidence object mapping each field to a number in [0,1]. Use null for absent "
    "fields with confidence 0. Do not invent values."
)


def _normalize_doc_type(doc_type: str | None) -> str:
    return (doc_type or "unknown").strip().lower().replace(" ", "_").replace("-", "_")


async def extract_document(
    raw_text: str, doc_type_hint: str | None, llm: LLMClient
) -> tuple[ExtractedDoc, Usage]:
    """Extract structured fields from document text. Fail-soft: on LLM failure, return an
    empty doc with zero confidence (which routes to human review)."""
    user = f"Document type hint: {doc_type_hint or 'unknown'}\n\nDocument text:\n{raw_text}"
    try:
        data, usage = await llm.complete_json(system=_SYSTEM, user=user)
    except LLMError as exc:
        logger.warning("Document extraction failed; routing to human review: %s", exc)
        return ExtractedDoc(doc_type=_normalize_doc_type(doc_type_hint)), Usage()

    raw_conf = data.get("field_confidence") or {}
    confidence = {k: float(v) for k, v in raw_conf.items() if isinstance(v, int | float)}
    return (
        ExtractedDoc(
            doc_type=_normalize_doc_type(data.get("doc_type") or doc_type_hint),
            name=data.get("name"),
            dob=data.get("dob"),
            address=data.get("address"),
            doc_number_last4=data.get("doc_number_last4"),
            issue_date=data.get("issue_date"),
            expiry_date=data.get("expiry_date"),
            field_confidence=confidence,
        ),
        usage,
    )


def detect_mismatches(extracted: ExtractedDoc, claimant: Claimant, prop: Property) -> list[str]:
    """Flag extracted name/address that don't agree with the claimant on record."""
    mismatches: list[str] = []

    if extracted.name:
        names = [claimant.full_name, *claimant.prior_names]
        doc_name = canonical_name(extracted.name)
        best = max(
            (fuzz.token_set_ratio(doc_name, canonical_name(n)) for n in names),
            default=0.0,
        )
        if best < NAME_MATCH_FLOOR:
            mismatches.append(
                f"name mismatch: document '{extracted.name}' not consistent with claimant"
            )

    if extracted.address and claimant.addresses:
        doc_addr = normalize_address(extracted.address).normalized
        best = max(
            (fuzz.token_set_ratio(doc_addr, normalize_address(a).normalized)
             for a in claimant.addresses),
            default=0.0,
        )
        if best < ADDRESS_MATCH_FLOOR:
            mismatches.append(
                f"address mismatch: document '{extracted.address}' not consistent with claimant"
            )

    return mismatches


def _doc_confidence(extracted: ExtractedDoc) -> float:
    """Mean confidence across the fields actually extracted.

    Mean (not min) so a single uncertain peripheral field — e.g. a hard-to-read expiry date —
    does not veto satisfying a requirement whose core identity fields were read confidently,
    while broadly low-confidence extraction still fails the floor.
    """
    present = [f for f in _CORE_FIELDS if getattr(extracted, f)]
    confs = [extracted.field_confidence.get(f, 0.0) for f in present]
    return sum(confs) / len(confs) if confs else 0.0


def apply_satisfaction(
    items: list[RequiredItem], extracted: ExtractedDoc, mismatches: list[str]
) -> tuple[list[RequiredItem], list[str], bool]:
    """Flip requirements the document satisfies. Returns (items, satisfied_labels, low_conf)."""
    phrase = DOC_TYPE_SATISFIES.get(extracted.doc_type)
    confidence = _doc_confidence(extracted)
    blocked = bool(mismatches)

    updated: list[RequiredItem] = []
    satisfied: list[str] = []
    low_confidence = False
    for item in items:
        new = item.model_copy()
        if not new.satisfied_by_uploaded_doc and phrase and phrase in new.label.lower():
            if not blocked and confidence >= EXTRACTION_CONFIDENCE_FLOOR:
                new.satisfied_by_uploaded_doc = True
                satisfied.append(new.label)
            elif confidence < EXTRACTION_CONFIDENCE_FLOOR:
                low_confidence = True
        updated.append(new)
    return updated, satisfied, low_confidence


@dataclass
class DocumentResult:
    extracted: ExtractedDoc
    mismatches: list[str]
    needs_human_review: bool
    satisfied_labels: list[str]
    items: list[RequiredItem]
    status: str


class DocumentProcessor:
    def __init__(self, *, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    async def process(
        self,
        session: AsyncSession,
        claim: Claim,
        claimant: Claimant,
        prop: Property,
        request: DocumentUploadRequest,
    ) -> DocumentResult:
        extracted, usage = await extract_document(request.raw_text, request.doc_type_hint, self.llm)
        mismatches = detect_mismatches(extracted, claimant, prop)

        items = [
            RequiredItem(**it) for it in (claim.required_items_json or {}).get("items", [])
        ]
        updated, satisfied, low_confidence = apply_satisfaction(items, extracted, mismatches)

        ungrounded = any(i.status == "needs_human_review" for i in updated)
        needs_review = bool(mismatches) or low_confidence or ungrounded
        all_required_satisfied = all(
            i.satisfied_by_uploaded_doc for i in updated if i.requirement == "required"
        )
        status = "ready_to_file" if all_required_satisfied and not needs_review else "needs_docs"

        claim.required_items_json = {"items": [i.model_dump(mode="json") for i in updated]}
        package = dict(claim.package_json or {})
        documents = list(package.get("documents", []))
        documents.append({"extracted": extracted.model_dump(), "mismatches": mismatches})
        package["documents"] = documents
        package["needs_human_review"] = needs_review or bool(package.get("needs_human_review"))
        claim.package_json = package
        claim.status = status

        session.add(
            RunTrace(
                claim_id=claim.id,
                steps_json={"steps": [{
                    "step": "document_extraction",
                    "detail": f"doc_type={extracted.doc_type}; {len(satisfied)} satisfied; "
                              f"{len(mismatches)} mismatch(es)",
                }]},
                tokens=usage.total_tokens,
                cost_cents=round(estimate_cost_cents(self.llm.model, usage)),
            )
        )
        session.add(
            AuditEvent(
                claim_id=claim.id, type="document_processed",
                payload_json={
                    "doc_type": extracted.doc_type, "satisfied": satisfied,
                    "mismatches": mismatches, "needs_human_review": needs_review,
                },
            )
        )
        await session.flush()

        return DocumentResult(
            extracted=extracted, mismatches=mismatches, needs_human_review=needs_review,
            satisfied_labels=satisfied, items=updated, status=status,
        )

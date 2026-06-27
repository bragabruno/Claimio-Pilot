import uuid

from app.claims.requirements import (
    deterministic_requirements,
    llm_requirements,
    merge_requirements,
)
from app.schemas.claim import RequiredItem
from app.services.vector_store import RetrievedChunk
from tests._helpers import StubLLM, make_chunk, make_claimant, make_property

# California notarization threshold is $1,000 (100_000 cents).
CA_CHUNKS = [
    make_chunk("Proof of Identity: a government-issued photo ID is required."),
    make_chunk("Proof of Address: a current utility bill within 60 days."),
    make_chunk("Notarization: claims over the threshold require a notarized claim form."),
    make_chunk("Deceased owner: a certified death certificate and heir documentation."),
    make_chunk("Business Entity Claims: articles of incorporation, EIN, authorized signer."),
]


def test_identity_and_address_always_required_and_grounded():
    claimant = make_claimant("Maria Gonzalez")
    prop = make_property("Maria Gonzalez", "1 Main St", "CA", 50_000)  # under threshold
    items = deterministic_requirements(claimant, prop, CA_CHUNKS)
    labels = [i.label for i in items]
    assert any("photo ID" in label for label in labels)
    assert any("address" in label.lower() for label in labels)
    assert all(i.source_rule_chunk_id is not None for i in items)
    assert all(i.status == "grounded" for i in items)


def test_notarization_threshold_is_deterministic():
    claimant = make_claimant("Maria Gonzalez")
    under = make_property("Maria Gonzalez", "1 Main St", "CA", 50_000)
    over = make_property("Maria Gonzalez", "1 Main St", "CA", 250_000)
    under_items = deterministic_requirements(claimant, under, CA_CHUNKS)
    over_items = deterministic_requirements(claimant, over, CA_CHUNKS)
    assert not any("Notarized" in i.label for i in under_items)
    assert any("Notarized" in i.label for i in over_items)


def test_deceased_and_business_add_items():
    deceased = make_property("Maria Gonzalez", "1 Main St", "CA", 50_000, owner_deceased=True)
    items = deterministic_requirements(make_claimant("Maria Gonzalez"), deceased, CA_CHUNKS)
    assert any("death certificate" in i.label.lower() for i in items)

    biz_claimant = make_claimant("Acme LLC", is_business=True)
    biz_items = deterministic_requirements(biz_claimant, deceased, CA_CHUNKS)
    assert any("EIN" in i.label for i in biz_items)


def test_missing_governing_chunk_routes_to_human_review():
    # No address chunk present → the address requirement cannot be grounded.
    chunks = [make_chunk("Proof of Identity: a government-issued photo ID is required.")]
    prop = make_property("Jane Doe", "x", "CA", 1)
    items = deterministic_requirements(make_claimant("Jane Doe"), prop, chunks)
    address_item = next(i for i in items if "address" in i.label.lower())
    assert address_item.status == "needs_human_review"
    assert address_item.source_rule_chunk_id is None


async def test_llm_items_grounded_or_flagged():
    cites = [
        RetrievedChunk(chunk_id=uuid.uuid4(), doc_id=uuid.uuid4(), state="CA", text="A", score=0.9),
        RetrievedChunk(chunk_id=uuid.uuid4(), doc_id=uuid.uuid4(), state="CA", text="B", score=0.8),
    ]
    payload = {
        "items": [
            {"label": "Valid item", "why": "ok", "requirement": "required", "source_index": 0},
            {"label": "Ungrounded item", "why": "x", "requirement": "required", "source_index": 99},
        ]
    }
    items, usage = await llm_requirements(
        make_claimant("Maria Gonzalez"),
        make_property("Maria Gonzalez", "1 Main St", "CA", 50_000),
        cites,
        StubLLM(payload),
    )
    grounded = next(i for i in items if i.label == "Valid item")
    flagged = next(i for i in items if i.label == "Ungrounded item")
    assert grounded.status == "grounded" and grounded.source_rule_chunk_id == cites[0].chunk_id
    assert flagged.status == "needs_human_review" and flagged.source_rule_chunk_id is None
    assert usage.total_tokens == 15


def test_merge_dedupes_by_label():
    det = [RequiredItem(label="Photo ID", why="x", requirement="required")]
    llm = [
        RequiredItem(label="photo  id", why="dup", requirement="required", origin="llm"),
        RequiredItem(label="Extra doc", why="y", requirement="conditional", origin="llm"),
    ]
    merged = merge_requirements(det, llm)
    assert [i.label for i in merged] == ["Photo ID", "Extra doc"]

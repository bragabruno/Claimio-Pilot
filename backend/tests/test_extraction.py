from app.claims.extraction import apply_satisfaction, detect_mismatches, extract_document
from app.schemas.claim import RequiredItem
from app.schemas.document import ExtractedDoc
from app.services.llm import LLMError, Usage
from tests._helpers import StubLLM, make_claimant, make_property

EXTRACT_PAYLOAD = {
    "doc_type": "Drivers License",
    "name": "Maria Gonzalez",
    "doc_number_last4": "1234",
    "address": "742 Evergreen Terrace, Sacramento CA 95814",
    "field_confidence": {"name": 0.95, "doc_number_last4": 0.9, "address": 0.92},
}


class _RaisingLLM:
    model = "stub"

    async def complete_json(self, *, system, user):
        raise LLMError("boom")


async def test_extract_document_parses_fields():
    doc, usage = await extract_document("raw", "drivers_license", StubLLM(EXTRACT_PAYLOAD))
    assert doc.doc_type == "drivers_license"  # normalized from "Drivers License"
    assert doc.name == "Maria Gonzalez"
    assert doc.doc_number_last4 == "1234"
    assert usage.total_tokens == 15


async def test_extract_document_failsoft_routes_to_review():
    doc, usage = await extract_document("raw", "passport", _RaisingLLM())
    assert doc.doc_type == "passport"
    assert doc.field_confidence == {}  # zero confidence → cannot satisfy anything
    assert usage == Usage()


def test_name_mismatch_detected():
    claimant = make_claimant("Maria Gonzalez")
    prop = make_property("Maria Gonzalez", "1 Main St", "CA", 1_000)
    wrong = ExtractedDoc(doc_type="passport", name="Robert Carter")
    right = ExtractedDoc(doc_type="passport", name="Maria Gonzalez")
    assert detect_mismatches(wrong, claimant, prop)
    assert not detect_mismatches(right, claimant, prop)


def test_satisfies_photo_id_with_high_confidence():
    items = [RequiredItem(label="Government-issued photo ID", why="id", requirement="required")]
    doc = ExtractedDoc(
        doc_type="drivers_license", name="Maria Gonzalez", doc_number_last4="1234",
        field_confidence={"name": 0.95, "doc_number_last4": 0.9},
    )
    updated, satisfied, low = apply_satisfaction(items, doc, [])
    assert updated[0].satisfied_by_uploaded_doc is True
    assert satisfied == ["Government-issued photo ID"]
    assert low is False


def test_low_confidence_does_not_satisfy():
    items = [RequiredItem(label="Government-issued photo ID", why="id", requirement="required")]
    doc = ExtractedDoc(doc_type="drivers_license", name="Maria Gonzalez",
                       field_confidence={"name": 0.2})
    updated, satisfied, low = apply_satisfaction(items, doc, [])
    assert updated[0].satisfied_by_uploaded_doc is False
    assert satisfied == []
    assert low is True


def test_mismatch_blocks_satisfaction():
    items = [RequiredItem(label="Government-issued photo ID", why="id", requirement="required")]
    doc = ExtractedDoc(doc_type="drivers_license", name="Someone Else", doc_number_last4="1",
                       field_confidence={"name": 0.95, "doc_number_last4": 0.95})
    updated, satisfied, _ = apply_satisfaction(items, doc, ["name mismatch: ..."])
    assert updated[0].satisfied_by_uploaded_doc is False
    assert satisfied == []

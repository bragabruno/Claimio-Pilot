from app.claims.letter import draft_letter
from app.schemas.claim import RequiredItem
from tests._helpers import make_claimant, make_property


def test_letter_renders_claimant_items_and_disclaimer():
    claimant = make_claimant("Maria Gonzalez")
    prop = make_property("Maria Gonzalez", "1 Main St", "CA", 250_000)
    items = [
        RequiredItem(label="Government-issued photo ID", why="identity", requirement="required"),
        RequiredItem(
            label="Notarized claim form", why="over threshold",
            requirement="required", status="needs_human_review",
        ),
    ]
    letter = draft_letter(claimant, prop, items, "California — demo rules")
    assert "Maria Gonzalez" in letter
    assert "Government-issued photo ID" in letter
    assert "$2,500.00" in letter
    assert "needs human review" in letter
    assert "not legal advice" in letter

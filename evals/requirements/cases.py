"""Golden cases for grounded requirement reasoning.

Each case pins the expected requirement *kinds* and the threshold-driven flags for a
(state, amount, deceased, business) combination — authored from the known per-state rules, not
from the code under test. Adversarial coverage: amounts just over/under each notarization
threshold, deceased owners, business entities, and combinations.

Requirement kinds: identity, address, notarization, death_certificate, heir, business.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RequirementCase:
    label: str
    state: str
    amount_cents: int
    owner_deceased: bool
    is_business: bool
    expected_kinds: set[str] = field(default_factory=set)


# Notarization thresholds (cents): CA 100_000 · NY 250_000 · TX 500_000 · FL 50_000 · IL 150_000
CASES: list[RequirementCase] = [
    RequirementCase("CA under threshold", "CA", 50_000, False, False, {"identity", "address"}),
    RequirementCase("CA over threshold", "CA", 150_000, False, False,
                    {"identity", "address", "notarization"}),
    RequirementCase("NY under threshold", "NY", 200_000, False, False, {"identity", "address"}),
    RequirementCase("NY over threshold", "NY", 300_000, False, False,
                    {"identity", "address", "notarization"}),
    RequirementCase("TX under threshold", "TX", 400_000, False, False, {"identity", "address"}),
    RequirementCase("TX over threshold", "TX", 600_000, False, False,
                    {"identity", "address", "notarization"}),
    RequirementCase("FL under threshold", "FL", 40_000, False, False, {"identity", "address"}),
    RequirementCase("FL over threshold", "FL", 60_000, False, False,
                    {"identity", "address", "notarization"}),
    RequirementCase("IL under threshold", "IL", 100_000, False, False, {"identity", "address"}),
    RequirementCase("IL over threshold", "IL", 200_000, False, False,
                    {"identity", "address", "notarization"}),
    RequirementCase("CA deceased, under threshold", "CA", 80_000, True, False,
                    {"identity", "address", "death_certificate", "heir"}),
    RequirementCase("TX deceased, over threshold", "TX", 600_000, True, False,
                    {"identity", "address", "notarization", "death_certificate", "heir"}),
    RequirementCase("NY business, over threshold", "NY", 300_000, False, True,
                    {"identity", "address", "notarization", "business"}),
    RequirementCase(
        "FL business + deceased, over threshold", "FL", 60_000, True, True,
        {"identity", "address", "notarization", "business", "death_certificate", "heir"},
    ),
]

# Threshold-driven flags scored for accuracy.
FLAG_KINDS = ("notarization", "heir", "business")


def label_to_kind(label: str) -> str | None:
    low = label.lower()
    if "photo id" in low:
        return "identity"
    if "address" in low:
        return "address"
    if "notar" in low:
        return "notarization"
    if "death certificate" in low:
        return "death_certificate"
    if "heir" in low or "estate" in low:
        return "heir"
    if "ein" in low or "business" in low or "formation" in low:
        return "business"
    return None

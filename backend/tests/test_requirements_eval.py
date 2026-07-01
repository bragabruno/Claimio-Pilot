"""Run the REQUIREMENT golden eval as a test so requirement-logic regressions fail CI."""

import pathlib
import types
import uuid
from dataclasses import dataclass

from evals.requirements.cases import CASES, FLAG_KINDS, label_to_kind

from app.claims.requirements import deterministic_requirements
from app.services.chunking import chunk_markdown
from app.states import slug_for

_RULES = pathlib.Path(__file__).resolve().parents[2] / "seed" / "state_rules"


@dataclass
class _Chunk:
    id: uuid.UUID
    text: str


def _kinds(case) -> set[str]:
    md = (_RULES / f"{slug_for(case.state)}.md").read_text(encoding="utf-8")
    chunks = [_Chunk(uuid.uuid4(), t) for t in chunk_markdown(md)]
    claimant = types.SimpleNamespace(full_name="Test", is_business=case.is_business)
    prop = types.SimpleNamespace(
        source_state=case.state, amount_cents=case.amount_cents,
        owner_deceased=case.owner_deceased,
    )
    items = deterministic_requirements(claimant, prop, chunks)
    return {k for k in (label_to_kind(i.label) for i in items) if k}


def test_requirement_golden_cases_match_expected():
    failures = [
        (c.label, sorted(c.expected_kinds), sorted(_kinds(c)))
        for c in CASES
        if _kinds(c) != c.expected_kinds
    ]
    assert not failures, failures


def test_threshold_flag_accuracy_is_perfect():
    for case in CASES:
        actual = _kinds(case)
        for flag in FLAG_KINDS:
            assert (flag in actual) == (flag in case.expected_kinds), (case.label, flag)

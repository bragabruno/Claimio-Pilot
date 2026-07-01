"""Requirement eval runner: precision / recall over required-item kinds + flag accuracy.

Runs the deterministic requirement logic against the golden cases using the real state rule
docs (chunked in memory — no database or LLM). Exits non-zero on any regression.
"""
# ruff: noqa: E402, I001 — sys.path is bootstrapped before the app/cases imports below.

from __future__ import annotations

import pathlib
import sys
import types
import uuid
from dataclasses import dataclass

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_ROOT / "backend"))
sys.path.insert(0, str(_HERE))

from app.claims.requirements import deterministic_requirements
from app.services.chunking import chunk_markdown
from app.states import slug_for
from cases import CASES, FLAG_KINDS, RequirementCase, label_to_kind

_RULES_DIR = _ROOT / "seed" / "state_rules"


@dataclass
class _Chunk:
    id: uuid.UUID
    text: str


def _load_chunks(state: str) -> list[_Chunk]:
    md = (_RULES_DIR / f"{slug_for(state)}.md").read_text(encoding="utf-8")
    return [_Chunk(id=uuid.uuid4(), text=t) for t in chunk_markdown(md)]


def _actual_kinds(case: RequirementCase) -> set[str]:
    claimant = types.SimpleNamespace(full_name="Test Claimant", is_business=case.is_business)
    prop = types.SimpleNamespace(
        source_state=case.state, amount_cents=case.amount_cents,
        owner_deceased=case.owner_deceased,
    )
    items = deterministic_requirements(claimant, prop, _load_chunks(case.state))
    return {k for k in (label_to_kind(i.label) for i in items) if k}


def evaluate() -> tuple[float, float, float, float, list[tuple]]:
    tp = fp = fn = 0
    flag_correct = flag_total = 0
    rows: list[tuple] = []
    for case in CASES:
        actual = _actual_kinds(case)
        expected = case.expected_kinds
        tp += len(actual & expected)
        fp += len(actual - expected)
        fn += len(expected - actual)
        case_flags_ok = True
        for flag in FLAG_KINDS:
            flag_total += 1
            if (flag in actual) == (flag in expected):
                flag_correct += 1
            else:
                case_flags_ok = False
        ok = actual == expected and case_flags_ok
        rows.append((case.label, sorted(expected), sorted(actual), ok))

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    flag_accuracy = flag_correct / flag_total if flag_total else 1.0
    return precision, recall, f1, flag_accuracy, rows


def main() -> int:
    precision, recall, f1, flag_accuracy, rows = evaluate()
    print("\nREQUIREMENT eval — golden case results")
    print("=" * 78)
    for label, expected, actual, ok in rows:
        print(f"{'✓' if ok else '✗'} {label}")
        if not ok:
            print(f"    expected={expected}")
            print(f"    actual  ={actual}")
    print("-" * 78)
    print(
        f"precision={precision:.2f}  recall={recall:.2f}  F1={f1:.2f}  "
        f"flag_accuracy={flag_accuracy:.2f}  ({sum(1 for r in rows if r[3])}/{len(rows)} cases)\n"
    )
    return 0 if all(r[3] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""MATCH eval runner: scores the golden cases and reports precision / recall / F1.

Run via `make eval-match` (or `make eval`). Exits non-zero if any case is mispredicted, so the
matching pipeline has a real regression gate. Pure scoring — no database required.
"""
# ruff: noqa: E402, I001 — sys.path is bootstrapped before the app/cases imports below.

from __future__ import annotations

import pathlib
import sys

# Make `app` (backend) and the sibling `cases` module importable when run as a script.
_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_ROOT / "backend"))
sys.path.insert(0, str(_HERE))

from app.match.scoring import DEFAULT_MATCH_THRESHOLD, score_match  # noqa: E402
from cases import CASES  # noqa: E402


def evaluate() -> tuple[float, float, float, list[tuple]]:
    tp = fp = tn = fn = 0
    rows: list[tuple] = []
    for case in CASES:
        scored = score_match(case.query, case.target)
        predicted = scored.confidence >= DEFAULT_MATCH_THRESHOLD
        correct = predicted == case.expected
        if predicted and case.expected:
            tp += 1
        elif predicted and not case.expected:
            fp += 1
        elif not predicted and case.expected:
            fn += 1
        else:
            tn += 1
        rows.append((case.label, case.expected, predicted, scored.confidence, correct))

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1, rows


def main() -> int:
    precision, recall, f1, rows = evaluate()

    print("\nMATCH eval — golden case results")
    print("=" * 78)
    print(f"{'case':<42} {'exp':>4} {'pred':>5} {'conf':>5}  ok")
    print("-" * 78)
    for label, expected, predicted, conf, correct in rows:
        print(
            f"{label:<42} {('Y' if expected else 'N'):>4} "
            f"{('Y' if predicted else 'N'):>5} {conf:>5}  {'✓' if correct else '✗'}"
        )
    print("-" * 78)
    print(
        f"threshold={DEFAULT_MATCH_THRESHOLD}  "
        f"precision={precision:.2f}  recall={recall:.2f}  F1={f1:.2f}  "
        f"({sum(1 for r in rows if r[4])}/{len(rows)} correct)\n"
    )

    return 0 if all(r[4] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())

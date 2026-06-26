"""Single source of truth for the 5 demo states.

These values are **illustrative/synthetic** — not real state rules. They are the canonical
reference for: the seed loader (placing amounts just over/under thresholds), the deterministic
notarization logic (Phase 3), and the eval harness (Phase 6). Keep them in sync with the prose
in ``seed/state_rules/<slug>.md``.
"""

from __future__ import annotations

from typing import TypedDict


class StateMeta(TypedDict):
    name: str
    slug: str
    notarization_threshold_cents: int


# Distinct notarization thresholds drive divergent checklists across states.
STATES: dict[str, StateMeta] = {
    "CA": {"name": "California", "slug": "california", "notarization_threshold_cents": 100_000},
    "NY": {"name": "New York", "slug": "new-york", "notarization_threshold_cents": 250_000},
    "TX": {"name": "Texas", "slug": "texas", "notarization_threshold_cents": 500_000},
    "FL": {"name": "Florida", "slug": "florida", "notarization_threshold_cents": 50_000},
    "IL": {"name": "Illinois", "slug": "illinois", "notarization_threshold_cents": 150_000},
}

STATE_CODES: list[str] = list(STATES.keys())


def slug_for(code: str) -> str:
    return STATES[code]["slug"]


def code_for_slug(slug: str) -> str:
    for code, meta in STATES.items():
        if meta["slug"] == slug:
            return code
    raise KeyError(f"Unknown state slug: {slug}")

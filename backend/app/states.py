"""Single source of truth for the 5 demo states.

These values are **illustrative/synthetic** — not real state rules. They are the canonical
reference for: the seed loader (placing amounts just over/under thresholds), the deterministic
notarization logic (Phase 3), and the eval harness (Phase 6). Keep them in sync with the prose
in ``seed/state_rules/<slug>.md``.
"""

from __future__ import annotations

from typing import TypedDict


class StateMeta(TypedDict):
    """Metadata for one demo state entry.

    Attributes:
        name: Human-readable state name.
        slug: Stable slug used to map state rules markdown files and APIs.
        notarization_threshold_cents: Synthetic claim-value threshold,
            in cents, used by the demo notarization logic.
    """
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
    """Return the configured slug for a two-letter state code.

    Args:
        code: Two-letter state code key present in ``STATES``.

    Returns:
        The corresponding state slug.
    """
    return STATES[code]["slug"]


def code_for_slug(slug: str) -> str:
    """Return the two-letter state code for a configured slug.

    Args:
        slug: State slug as stored in ``STATES`` and used by rule documents and
            API payloads. Matching is case-sensitive.

    Raises:
        KeyError: If the slug does not match any configured demo state.

    Returns:
        The corresponding two-letter state code.
    """
    for code, meta in STATES.items():
        if meta["slug"] == slug:
            return code
    raise KeyError(f"Unknown state slug: {slug}")

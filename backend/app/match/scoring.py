"""Multi-signal match scoring with explainability.

Produces a 0–100 confidence from independent signals — name (current AND prior names),
address overlap, SSN-last4 and DOB corroboration, and individual-vs-business consistency —
and returns human-readable `match_reasons` plus a numeric breakdown so every score is
auditable. This module is pure (no DB) so the eval harness can drive it directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from rapidfuzz import fuzz

from app.match.normalize import (
    AddressParts,
    canonical_name,
    looks_like_business,
    normalize_address,
)

# A candidate at or above this confidence is treated as a predicted match (evals, UI default).
DEFAULT_MATCH_THRESHOLD = 70

# Base-score weights for the always-comparable signals.
_NAME_WEIGHT = 0.6
_ADDRESS_WEIGHT = 0.4

# Corroboration adjustments applied on top of the weighted base.
_SSN_MATCH_BONUS = 12.0
_SSN_MISMATCH_PENALTY = -10.0
_DOB_MATCH_BONUS = 8.0
_DOB_MISMATCH_PENALTY = -8.0
_ENTITY_MATCH_BONUS = 4.0
_ENTITY_MISMATCH_PENALTY = -30.0


@dataclass
class MatchQuery:
    name: str
    prior_names: list[str] = field(default_factory=list)
    addresses: list[str] = field(default_factory=list)
    dob: date | None = None
    ssn_last4: str | None = None
    is_business: bool | None = None


@dataclass
class MatchTarget:
    """The property-side record being reconciled against (the unclaimed-funds owner)."""

    owner_name: str
    owner_last_address: str | None = None
    owner_ssn_last4: str | None = None
    owner_dob: date | None = None
    owner_is_business: bool | None = None


@dataclass
class ScoredMatch:
    confidence: int
    match_reasons: list[str]
    breakdown: dict[str, float | None]

    @property
    def is_match(self) -> bool:
        return self.confidence >= DEFAULT_MATCH_THRESHOLD


def _best_name(query: MatchQuery, owner_canonical: str) -> tuple[float, str, str]:
    """Best token_set_ratio over the current name and every prior name."""
    candidates = [("name", query.name)] + [("prior name", p) for p in query.prior_names]
    best = (0.0, query.name, "name")
    for which, value in candidates:
        score = float(fuzz.token_set_ratio(canonical_name(value), owner_canonical))
        if score > best[0]:
            best = (score, value, which)
    return best


def _best_address(
    query: MatchQuery, owner: AddressParts
) -> tuple[float, str | None, AddressParts | None]:
    best: tuple[float, str | None, AddressParts | None] = (0.0, None, None)
    if not owner.normalized:
        return best
    for addr in query.addresses:
        ap = normalize_address(addr)
        if not ap.normalized:
            continue
        score = float(fuzz.token_set_ratio(ap.normalized, owner.normalized))
        # Reward a shared state/zip — a strong locality signal beyond raw string overlap.
        if ap.state and ap.state == owner.state:
            score = min(100.0, score + 5.0)
        if ap.zip and ap.zip == owner.zip:
            score = min(100.0, score + 10.0)
        if score > best[0]:
            best = (score, addr, ap)
    return best


def _entity_is_business(explicit: bool | None, name: str) -> bool:
    return explicit if explicit is not None else looks_like_business(name)


def score_match(query: MatchQuery, target: MatchTarget) -> ScoredMatch:
    owner_canonical = canonical_name(target.owner_name)
    owner_addr = normalize_address(target.owner_last_address)

    name_score, matched_name, name_field = _best_name(query, owner_canonical)
    addr_score, matched_addr, _addr_parts = _best_address(query, owner_addr)

    reasons: list[str] = []
    breakdown: dict[str, float | None] = {"name": round(name_score, 1)}

    # Weighted base over the signals we could actually compare.
    if matched_addr is not None:
        base = name_score * _NAME_WEIGHT + addr_score * _ADDRESS_WEIGHT
        breakdown["address"] = round(addr_score, 1)
    else:
        base = name_score
        breakdown["address"] = None

    reasons.append(
        f"Matched on {name_field} '{matched_name}' (token_set {name_score / 100:.2f})"
    )
    if matched_addr is not None:
        reasons.append(
            f"Address overlap with '{matched_addr}' ({addr_score / 100:.2f})"
        )

    adjustment = 0.0

    # SSN last-4 corroboration (value never surfaced in reasons).
    if query.ssn_last4 and target.owner_ssn_last4:
        if query.ssn_last4 == target.owner_ssn_last4:
            adjustment += _SSN_MATCH_BONUS
            reasons.append("SSN last-4 corroborated")
            breakdown["ssn"] = _SSN_MATCH_BONUS
        else:
            adjustment += _SSN_MISMATCH_PENALTY
            reasons.append("Penalty: SSN last-4 differs")
            breakdown["ssn"] = _SSN_MISMATCH_PENALTY

    # DOB corroboration.
    if query.dob and target.owner_dob:
        if query.dob == target.owner_dob:
            adjustment += _DOB_MATCH_BONUS
            reasons.append(f"DOB corroborated ({target.owner_dob.isoformat()})")
            breakdown["dob"] = _DOB_MATCH_BONUS
        else:
            adjustment += _DOB_MISMATCH_PENALTY
            reasons.append("Penalty: DOB differs")
            breakdown["dob"] = _DOB_MISMATCH_PENALTY

    # Individual-vs-business consistency.
    q_biz = _entity_is_business(query.is_business, query.name)
    t_biz = _entity_is_business(target.owner_is_business, target.owner_name)
    if q_biz == t_biz:
        adjustment += _ENTITY_MATCH_BONUS
        reasons.append(
            f"Consistent entity type ({'business' if q_biz else 'individual'})"
        )
        breakdown["entity"] = _ENTITY_MATCH_BONUS
    else:
        adjustment += _ENTITY_MISMATCH_PENALTY
        reasons.append("Penalty: individual/business mismatch")
        breakdown["entity"] = _ENTITY_MISMATCH_PENALTY

    confidence = int(round(max(0.0, min(100.0, base + adjustment))))
    breakdown["base"] = round(base, 1)
    breakdown["confidence"] = float(confidence)
    return ScoredMatch(confidence=confidence, match_reasons=reasons, breakdown=breakdown)

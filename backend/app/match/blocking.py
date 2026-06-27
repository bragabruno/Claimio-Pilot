"""Candidate generation via blocking.

Blocking strategy
-----------------
A naive linkage compares every claimant against every property — O(claimants × properties),
which does not scale past a toy index. Instead we generate candidates with *blocking keys* and
only score records that share one:

  a property advances to scoring iff it shares at least one **name token** OR an exact **zip**
  with the query.

Name tokens are unioned across the current name AND every prior name, so a former-name match
survives blocking. State is deliberately **not** a hard filter: a claimant who has moved across
state lines must still reconcile against a property reported in their prior state (the
outdated-address case). State is parsed and available as a narrowing hint, but excluding on it
would drop legitimate cross-state matches. Properties carry pre-computed `owner_name_tokens`
(GIN-indexed) and `owner_zip` (btree), so blocking is a single indexed query — the array-overlap
operator (`&&`) does the token blocking in the database.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Property
from app.match.normalize import name_tokens, normalize_address
from app.match.scoring import MatchQuery


@dataclass
class BlockingKeys:
    name_tokens: set[str] = field(default_factory=set)
    states: set[str] = field(default_factory=set)  # 2-letter, lowercase
    zips: set[str] = field(default_factory=set)


def build_blocking_keys(query: MatchQuery) -> BlockingKeys:
    tokens: set[str] = set(name_tokens(query.name))
    for prior in query.prior_names:
        tokens |= name_tokens(prior)

    states: set[str] = set()
    zips: set[str] = set()
    for addr in query.addresses:
        parts = normalize_address(addr)
        if parts.state:
            states.add(parts.state)
        if parts.zip:
            zips.add(parts.zip)

    return BlockingKeys(name_tokens=tokens, states=states, zips=zips)


async def generate_candidates(session: AsyncSession, query: MatchQuery) -> list[Property]:
    """Return properties passing the blocking filter (the candidate set for scoring)."""
    keys = build_blocking_keys(query)
    if not keys.name_tokens and not keys.zips:
        return []  # nothing to block on — refuse an all-to-all scan

    predicates = []
    if keys.name_tokens:
        predicates.append(Property.owner_name_tokens.overlap(sorted(keys.name_tokens)))
    if keys.zips:
        predicates.append(Property.owner_zip.in_(sorted(keys.zips)))

    stmt = select(Property).where(or_(*predicates))
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows)

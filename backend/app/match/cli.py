"""Thin CLI demo for the matching pipeline (the 'visual' for Phase 2).

Runs a property search against the seeded index and prints a ranked, explained table plus the
data-quality summary. With no arguments it picks a seeded claimant that has a prior name, so the
former-name match is front and center.

    uv run python -m app.match.cli
    uv run python -m app.match.cli --name "Bob Smith" --address "123 Main St, Oakland CA 94601"
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import func, select

from app.db.base import SessionLocal
from app.db.models import Claimant
from app.logging import configure_logging
from app.match.pipeline import SearchResult, search
from app.match.scoring import MatchQuery


def _money(cents: int) -> str:
    return f"${cents / 100:,.2f}"


async def _demo_query(session) -> MatchQuery:
    stmt = select(Claimant).where(func.cardinality(Claimant.prior_names) > 0).limit(1)
    claimant = (await session.execute(stmt)).scalar_one_or_none()
    if claimant is None:
        claimant = (await session.execute(select(Claimant).limit(1))).scalar_one_or_none()
    if claimant is None:
        raise SystemExit("No claimants seeded. Run `make seed` first.")
    return MatchQuery(
        name=claimant.full_name,
        prior_names=list(claimant.prior_names),
        addresses=list(claimant.addresses),
        dob=claimant.dob,
        ssn_last4=claimant.ssn_last4,
        is_business=claimant.is_business,
    )


def _print(query: MatchQuery, result: SearchResult) -> None:
    print("\nClaimPilot — property match demo (synthetic data)")
    print("=" * 72)
    print(f"Claimant : {query.name}")
    if query.prior_names:
        print(f"Formerly : {', '.join(query.prior_names)}")
    for addr in query.addresses:
        print(f"Address  : {addr}")
    print(
        f"\nBlocked {result.blocking_count} candidate(s) → showing "
        f"{len(result.candidates)} scored:\n"
    )
    print(f"{'#':>2}  {'conf':>4}  {'st':<2}  {'amount':>13}  owner")
    print("-" * 72)
    for i, c in enumerate(result.candidates, 1):
        flag = "✓" if c.score.is_match else " "
        print(
            f"{i:>2}  {c.score.confidence:>3}{flag} {c.property.source_state:<2}  "
            f"{_money(c.property.amount_cents):>13}  {c.property.owner_name}"
        )
        print(f"      ↳ {'; '.join(c.score.match_reasons)}")
    dq = result.data_quality
    print("-" * 72)
    print(
        f"Data quality: {dq.total_records} records · {dq.missing_address_pct}% missing address · "
        f"{dq.duplicate_groups} duplicate group(s) ({dq.duplicate_records} record(s)) · "
        f"merged {dq.duplicates_merged} in results\n"
    )


async def _run(args: argparse.Namespace) -> None:
    async with SessionLocal() as session:
        if args.name:
            query = MatchQuery(
                name=args.name,
                prior_names=args.prior or [],
                addresses=args.address or [],
            )
        else:
            query = await _demo_query(session)
        result = await search(session, query)
    _print(query, result)


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="ClaimPilot property match demo")
    parser.add_argument("--name", help="Claimant current name (default: a seeded claimant)")
    parser.add_argument("--prior", action="append", help="Prior name (repeatable)")
    parser.add_argument("--address", action="append", help="Address (repeatable)")
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()

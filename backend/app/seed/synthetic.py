"""Synthetic claimant + property generation (Faker). No real PII (see docs/adr/0003).

The dataset is deliberately seeded with hard cases the later phases exercise:
- matches via **former name** or an **outdated address** (Phase 2 fuzzy match),
- **deceased** owners and **business-entity** owners (heir/business checklists),
- amounts **just over / under** each state's notarization threshold (deterministic logic + evals).
"""

from __future__ import annotations

import random

from faker import Faker

from app.db.models import Claimant, Property
from app.states import STATE_CODES, STATES


def _fmt_address(fake: Faker) -> str:
    return fake.address().replace("\n", ", ")


def _ssn_last4(rng: random.Random) -> str:
    return f"{rng.randint(0, 9999):04d}"


def build_dataset(seed: int = 42) -> tuple[list[Claimant], list[Property]]:
    """Return (claimants, properties). Deterministic for a given seed."""
    fake = Faker("en_US")
    Faker.seed(seed)
    rng = random.Random(seed)

    claimants: list[Claimant] = []
    properties: list[Property] = []

    # --- Individual claimants, several with a prior name and an older address ---
    for i in range(10):
        current_name = fake.name()
        prior_names: list[str] = []
        if i % 3 == 0:  # roughly a third changed their name
            prior_names = [fake.name()]
        addresses = [_fmt_address(fake) for _ in range(rng.randint(1, 3))]
        claimants.append(
            Claimant(
                full_name=current_name,
                prior_names=prior_names,
                addresses=addresses,
                dob=fake.date_of_birth(minimum_age=25, maximum_age=85),
                ssn_last4=_ssn_last4(rng),
                email=fake.email(),
                is_business=False,
            )
        )

    # --- Business claimants ---
    for _ in range(2):
        biz_name = fake.company()
        claimants.append(
            Claimant(
                full_name=biz_name,
                prior_names=[],
                addresses=[_fmt_address(fake)],
                dob=None,
                ssn_last4=None,
                email=fake.company_email(),
                is_business=True,
            )
        )

    states_cycle = STATE_CODES * 4

    # --- Matched properties: each references a claimant by a name they would search under
    #     (current OR prior name) and an address they have used. ---
    for idx, claimant in enumerate(claimants):
        state = states_cycle[idx]
        threshold = STATES[state]["notarization_threshold_cents"]
        owner_name = (
            claimant.prior_names[0]
            if claimant.prior_names and idx % 2 == 0
            else claimant.full_name
        )
        owner_addr = claimant.addresses[-1] if claimant.addresses else _fmt_address(fake)
        # Spread amounts across the threshold so checklists diverge.
        amount = rng.choice(
            [threshold - 2_500, threshold + 2_500, threshold * 2, max(5_000, threshold // 4)]
        )
        properties.append(
            Property(
                source_state=state,
                holder_name=fake.company(),
                owner_name=owner_name,
                owner_last_address=owner_addr,
                amount_cents=amount,
                property_type=rng.choice(
                    ["uncashed_check", "dormant_savings", "insurance_proceeds", "stock_dividend"]
                ),
                owner_deceased=(idx % 4 == 0 and not claimant.is_business),
                reported_date=fake.date_between(start_date="-6y", end_date="-1y"),
                status="unclaimed",
            )
        )

    # --- Per-state boundary properties (unmatched) to guarantee adversarial coverage:
    #     one just under and one just over each notarization threshold. ---
    for state in STATE_CODES:
        threshold = STATES[state]["notarization_threshold_cents"]
        for delta, _band in ((-2_500, "under"), (2_500, "over")):
            properties.append(
                Property(
                    source_state=state,
                    holder_name=fake.company(),
                    owner_name=fake.name(),
                    owner_last_address=_fmt_address(fake),
                    amount_cents=threshold + delta,
                    property_type="uncashed_check",
                    owner_deceased=False,
                    reported_date=fake.date_between(start_date="-5y", end_date="-1y"),
                    status="unclaimed",
                )
            )

    return claimants, properties

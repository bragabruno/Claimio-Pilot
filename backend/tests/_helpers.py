"""Test helpers for building normalized Property rows without the seed loader."""

from __future__ import annotations

from app.db.models import Property
from app.match.normalize import canonical_name, name_tokens, normalize_address


def make_property(
    owner_name: str,
    address: str | None,
    state: str,
    amount_cents: int,
    **kwargs,
) -> Property:
    parts = normalize_address(address)
    return Property(
        source_state=state,
        holder_name="Holder Co",
        owner_name=owner_name,
        owner_last_address=address,
        amount_cents=amount_cents,
        property_type="uncashed_check",
        normalized_owner_name=canonical_name(owner_name),
        normalized_owner_address=parts.normalized or None,
        owner_name_tokens=sorted(name_tokens(owner_name)),
        owner_zip=parts.zip,
        **kwargs,
    )

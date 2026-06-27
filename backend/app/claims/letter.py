"""Draft claimant instruction letter (deterministic template).

A template filled from the claim context and the generated checklist. Kept deterministic so the
demo always produces a clean, accurate letter; the structured requirements (with citations) are
the source of truth, and the letter simply renders them for the claimant.
"""

from __future__ import annotations

from app.db.models import Claimant, Property
from app.schemas.claim import RequiredItem

DISCLAIMER = (
    "This is a demonstration document generated from synthetic data. It is not legal advice "
    "and does not replace the official state claim process."
)


def draft_letter(
    claimant: Claimant, prop: Property, items: list[RequiredItem], state_title: str
) -> str:
    amount = f"${prop.amount_cents / 100:,.2f}"
    lines = [
        f"Re: Unclaimed property claim — {prop.source_state} ({amount})",
        "",
        f"Dear {claimant.full_name},",
        "",
        f"We have matched you to unclaimed property reported in {prop.source_state} in the "
        f"amount of {amount}. To file your claim, please provide the following documents, which "
        f"are required under {state_title}:",
        "",
    ]
    for i, item in enumerate(items, 1):
        tag = "required" if item.requirement == "required" else "if applicable"
        review = "  [needs human review]" if item.status == "needs_human_review" else ""
        lines.append(f"  {i}. {item.label} ({tag}){review}")
        lines.append(f"     Why: {item.why}")
    lines += [
        "",
        "Each requirement above is grounded in the cited state rule, available on request.",
        "",
        "Sincerely,",
        "ClaimPilot (demonstration)",
        "",
        f"— {DISCLAIMER}",
    ]
    return "\n".join(lines)

"""Golden cases for the matching pipeline.

Hand-authored (claimant query, property target, expected_match) triples covering the cases
that matter for record reconciliation — exact, former-name, nickname, outdated address,
corroboration, and the negatives (different person, individual/business mismatch,
address-only-but-wrong-name). Scoring is pure, so these run without a database.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from app.match.scoring import MatchQuery, MatchTarget


@dataclass
class Case:
    label: str
    query: MatchQuery
    target: MatchTarget
    expected: bool  # True = should be predicted a match


_DOB = dt.date(1984, 3, 2)
_DOB_OTHER = dt.date(1979, 11, 20)

CASES: list[Case] = [
    # --- Expected matches ---
    Case(
        "exact name + address",
        MatchQuery("Maria Gonzalez", addresses=["742 Evergreen Terrace, Sacramento CA 95814"]),
        MatchTarget("Maria Gonzalez", "742 Evergreen Terrace, Sacramento, CA 95814"),
        True,
    ),
    Case(
        "former name + address",
        MatchQuery(
            "Sarah Johnson",
            prior_names=["Jennifer Lee"],
            addresses=["18 Oak Ave, Oakland CA 94601"],
        ),
        MatchTarget("Jennifer Lee", "18 Oak Avenue, Oakland, CA 94601"),
        True,
    ),
    Case(
        "nickname, name only (Bob → Robert)",
        MatchQuery("Bob Smith"),
        MatchTarget("Robert Smith"),
        True,
    ),
    Case(
        "outdated address, strong name",
        MatchQuery("Robert Carter", addresses=["456 Pine St, Austin TX 78701"]),
        MatchTarget("Robert Carter", "999 Cedar Blvd, Dallas, TX 75201"),
        True,
    ),
    Case(
        "dropped middle name + address",
        MatchQuery("Robert James Carter", addresses=["12 Maple Dr, Chicago IL 60601"]),
        MatchTarget("Robert Carter", "12 Maple Drive, Chicago, IL 60601"),
        True,
    ),
    Case(
        "business exact",
        MatchQuery("Acme Holdings LLC", is_business=True),
        MatchTarget("Acme Holdings LLC", owner_is_business=True),
        True,
    ),
    Case(
        "ssn corroboration on abbreviated name",
        MatchQuery("Jonathan Reed", ssn_last4="4821"),
        MatchTarget("Jon Reed", owner_ssn_last4="4821"),
        True,
    ),
    Case(
        "punctuation + suffix normalization",
        MatchQuery("O'Brien, Daniel Jr.", addresses=["5 Bay St, Miami FL 33101"]),
        MatchTarget("Daniel OBrien", "5 Bay Street, Miami, FL 33101"),
        True,
    ),
    # --- Expected non-matches ---
    Case(
        "different person",
        MatchQuery("Robert Carter", addresses=["1 First St, Austin TX 78701"]),
        MatchTarget("Maria Gonzalez", "88 Elm Rd, Houston, TX 77001"),
        False,
    ),
    Case(
        "individual vs business, shared token",
        MatchQuery("John Smith", is_business=False),
        MatchTarget("Smith Industries LLC", owner_is_business=True),
        False,
    ),
    Case(
        "address-only, wrong name",
        MatchQuery("Thomas Walker", addresses=["742 Evergreen Terrace, Sacramento CA 95814"]),
        MatchTarget("Diane Foster", "742 Evergreen Terrace, Sacramento, CA 95814"),
        False,
    ),
    Case(
        "distinct names, no overlap",
        MatchQuery("Patricia Allen", addresses=["3 Hill St, Buffalo NY 14201"]),
        MatchTarget("Gregory Sanchez", "70 Lake Ave, Albany, NY 12201"),
        False,
    ),
    Case(
        "business query vs individual owner",
        MatchQuery("Globex Corporation", is_business=True),
        MatchTarget("George Bell", owner_is_business=False),
        False,
    ),
    Case(
        "dob mismatch pulls borderline down",
        MatchQuery("William Park", dob=_DOB, addresses=["9 Sun Rd, Reno NV 89501"]),
        MatchTarget("Wendy Park", "400 Moon Ave, Las Vegas, NV 89101", owner_dob=_DOB_OTHER),
        False,
    ),
]

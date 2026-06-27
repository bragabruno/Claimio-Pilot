"""Normalization for record linkage: names and US addresses.

Normalization is what makes fuzzy matching trustworthy — "Robert M. Smith Jr." and
"bob smith" should reconcile, and "123 N. Main St, Apt 4" and "123 north main street unit 4"
should look identical. We canonicalize both sides into comparable strings and token sets, and
parse the structured bits (zip, state) that drive blocking.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Common nicknames → canonical given name. Both forms collapse to the canonical token so
# "Bob Smith" and "Robert Smith" share a token and score as a match.
NICKNAMES: dict[str, str] = {
    "bob": "robert", "rob": "robert", "bobby": "robert",
    "bill": "william", "will": "william", "billy": "william",
    "jim": "james", "jimmy": "james", "jamie": "james",
    "joe": "joseph", "joey": "joseph",
    "mike": "michael", "mikey": "michael",
    "dave": "david",
    "dan": "daniel", "danny": "daniel",
    "tom": "thomas", "tommy": "thomas",
    "rick": "richard", "rich": "richard", "dick": "richard",
    "steve": "stephen", "steven": "stephen",
    "chris": "christopher",
    "matt": "matthew",
    "tony": "anthony",
    "ed": "edward", "eddie": "edward",
    "ken": "kenneth",
    "jen": "jennifer", "jenny": "jennifer", "jenn": "jennifer",
    "liz": "elizabeth", "beth": "elizabeth", "betty": "elizabeth",
    "kate": "katherine", "katie": "katherine", "kathy": "katherine", "cathy": "katherine",
    "peggy": "margaret", "meg": "margaret", "maggie": "margaret",
    "sue": "susan", "suzy": "susan",
    "becky": "rebecca",
    "patty": "patricia", "pat": "patricia",
    "cindy": "cynthia",
    "deb": "deborah", "debbie": "deborah",
    "sandy": "sandra",
    "nick": "nicholas",
    "alex": "alexander",
    "abby": "abigail",
}

# Name suffixes dropped during canonicalization.
NAME_SUFFIXES: frozenset[str] = frozenset(
    {"jr", "sr", "ii", "iii", "iv", "v", "md", "phd", "esq", "dds", "do"}
)

# Business-entity tokens — a name containing one looks like an organization, not a person.
BUSINESS_TOKENS: frozenset[str] = frozenset(
    {"inc", "llc", "llp", "lp", "ltd", "corp", "corporation", "co", "company",
     "group", "holdings", "partners", "associates", "trust", "foundation", "plc", "gmbh"}
)

# US street-type and directional abbreviations expanded to a canonical form.
STREET_ABBR: dict[str, str] = {
    "st": "street", "str": "street", "ave": "avenue", "av": "avenue",
    "rd": "road", "blvd": "boulevard", "dr": "drive", "ln": "lane",
    "ct": "court", "pl": "place", "ter": "terrace", "cir": "circle",
    "hwy": "highway", "pkwy": "parkway", "sq": "square", "trl": "trail",
    "apt": "apartment", "ste": "suite", "unit": "unit", "bldg": "building", "fl": "floor",
}
DIRECTIONALS: dict[str, str] = {
    "n": "north", "s": "south", "e": "east", "w": "west",
    "ne": "northeast", "nw": "northwest", "se": "southeast", "sw": "southwest",
}

US_STATE_CODES: frozenset[str] = frozenset(
    {"al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id", "il", "in",
     "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv",
     "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc", "sd", "tn",
     "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy", "dc"}
)
_STATE_NAMES: dict[str, str] = {
    "california": "ca", "new york": "ny", "texas": "tx", "florida": "fl", "illinois": "il",
}

_ZIP_RE = re.compile(r"\b(\d{5})(?:-\d{4})?\b")
_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def _base_clean(text: str) -> str:
    text = _strip_accents(text or "").lower()
    # Delete apostrophes so intra-name punctuation fuses (O'Brien → obrien); other
    # punctuation becomes a separator.
    text = text.replace("'", "").replace("’", "")
    text = _PUNCT_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


def canonical_name(raw: str) -> str:
    """Lowercase, de-accent, drop punctuation/suffixes, expand nicknames → canonical string."""
    tokens = [t for t in _base_clean(raw).split() if t and t not in NAME_SUFFIXES]
    expanded = [NICKNAMES.get(t, t) for t in tokens]
    return " ".join(expanded)


def name_tokens(raw: str) -> set[str]:
    """Blocking tokens for a name (canonicalized, length ≥ 2)."""
    return {t for t in canonical_name(raw).split() if len(t) >= 2}


def looks_like_business(raw: str) -> bool:
    return bool(name_tokens(raw) & BUSINESS_TOKENS)


@dataclass(frozen=True)
class AddressParts:
    normalized: str
    zip: str | None = None
    state: str | None = None  # 2-letter code, lowercase
    tokens: set[str] = field(default_factory=set)


def normalize_address(raw: str | None) -> AddressParts:
    """Canonicalize a US address string and parse zip + state."""
    if not raw or not raw.strip():
        return AddressParts(normalized="")

    zip_match = _ZIP_RE.search(raw)
    zip_code = zip_match.group(1) if zip_match else None

    cleaned = _base_clean(raw)
    expanded = [DIRECTIONALS.get(t, STREET_ABBR.get(t, t)) for t in cleaned.split()]
    normalized = " ".join(expanded)

    state = None
    for code in US_STATE_CODES:
        if re.search(rf"\b{code}\b", cleaned):
            state = code
            break
    if state is None:
        for name, code in _STATE_NAMES.items():
            if name in cleaned:
                state = code
                break

    tokens = {t for t in normalized.split() if len(t) >= 2}
    return AddressParts(normalized=normalized, zip=zip_code, state=state, tokens=tokens)

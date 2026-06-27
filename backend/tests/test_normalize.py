from app.match.normalize import (
    canonical_name,
    looks_like_business,
    name_tokens,
    normalize_address,
)


def test_canonical_name_drops_suffix_and_punct():
    assert canonical_name("O'Brien, Daniel Jr.") == "obrien daniel"


def test_canonical_name_expands_nickname():
    assert canonical_name("Bob Smith") == canonical_name("Robert Smith") == "robert smith"


def test_canonical_name_strips_accents():
    assert canonical_name("José Núñez") == "jose nunez"


def test_name_tokens_drop_short_tokens():
    assert name_tokens("J Robert Smith") == {"robert", "smith"}


def test_looks_like_business():
    assert looks_like_business("Acme Holdings LLC")
    assert not looks_like_business("Jane Doe")


def test_normalize_address_expands_and_parses():
    parts = normalize_address("123 N. Main St, Apt 4, Oakland CA 94601")
    assert "north" in parts.normalized
    assert "street" in parts.normalized
    assert parts.zip == "94601"
    assert parts.state == "ca"


def test_normalize_address_empty():
    parts = normalize_address(None)
    assert parts.normalized == ""
    assert parts.zip is None and parts.state is None


def test_normalize_address_full_state_name():
    assert normalize_address("10 Elm Rd, Texas").state == "tx"

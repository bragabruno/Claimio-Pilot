from app.match.data_quality import dedupe_candidates
from tests._helpers import make_property


def test_dedupe_collapses_exact_duplicates():
    a = make_property("Jane Doe", "1 Main St, Reno NV 89501", "NV", 10_000)
    b = make_property("Jane Doe", "1 Main St, Reno NV 89501", "NV", 10_000)  # dup of a
    c = make_property("Jane Doe", "1 Main St, Reno NV 89501", "NV", 20_000)  # diff amount
    unique, merged = dedupe_candidates([a, b, c])
    assert merged == 1
    assert len(unique) == 2


def test_dedupe_no_duplicates():
    a = make_property("Jane Doe", "1 Main St", "NV", 10_000)
    b = make_property("John Roe", "2 Oak St", "NV", 10_000)
    unique, merged = dedupe_candidates([a, b])
    assert merged == 0 and len(unique) == 2

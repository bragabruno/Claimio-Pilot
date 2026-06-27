from app.match.blocking import build_blocking_keys
from app.match.scoring import MatchQuery


def test_blocking_keys_union_current_and_prior_names():
    keys = build_blocking_keys(
        MatchQuery(
            "Sarah Johnson",
            prior_names=["Jennifer Lee"],
            addresses=["18 Oak Ave, Oakland CA 94601"],
        )
    )
    assert {"sarah", "johnson", "jennifer", "lee"} <= keys.name_tokens
    assert "ca" in keys.states
    assert "94601" in keys.zips


def test_blocking_keys_empty_without_signals():
    keys = build_blocking_keys(MatchQuery(""))
    assert not keys.name_tokens and not keys.states and not keys.zips

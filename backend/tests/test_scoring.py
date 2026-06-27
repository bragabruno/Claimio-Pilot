import datetime as dt

from app.match.scoring import (
    DEFAULT_MATCH_THRESHOLD,
    MatchQuery,
    MatchTarget,
    score_match,
)


def test_exact_name_and_address_high_confidence():
    q = MatchQuery("Maria Gonzalez", addresses=["742 Evergreen Terrace, Sacramento CA 95814"])
    t = MatchTarget("Maria Gonzalez", "742 Evergreen Terrace, Sacramento, CA 95814")
    sm = score_match(q, t)
    assert sm.confidence >= 90 and sm.is_match
    assert sm.breakdown["address"] is not None


def test_former_name_matches_via_prior():
    q = MatchQuery("Sarah Johnson", prior_names=["Jennifer Lee"])
    sm = score_match(q, MatchTarget("Jennifer Lee"))
    assert sm.confidence >= DEFAULT_MATCH_THRESHOLD
    assert any("prior name" in r for r in sm.match_reasons)


def test_individual_business_mismatch_penalized():
    q = MatchQuery("John Smith", is_business=False)
    sm = score_match(q, MatchTarget("Smith Industries LLC", owner_is_business=True))
    assert not sm.is_match
    assert any("mismatch" in r for r in sm.match_reasons)


def test_ssn_corroboration_boosts():
    # Use a non-saturated name so the corroboration bonus is observable (an exact name
    # already scores 100 and the bonus would be clamped).
    q_no = MatchQuery("Jonathan Reed")
    q_yes = MatchQuery("Jonathan Reed", ssn_last4="4821")
    base = score_match(q_no, MatchTarget("Jon Reed"))
    boosted = score_match(q_yes, MatchTarget("Jon Reed", owner_ssn_last4="4821"))
    assert base.confidence < 100  # guard: the name must not already be saturated
    assert boosted.confidence > base.confidence
    assert any("SSN last-4 corroborated" in r for r in boosted.match_reasons)


def test_ssn_value_not_leaked_in_reasons():
    q = MatchQuery("Jon Reed", ssn_last4="4821")
    sm = score_match(q, MatchTarget("Jon Reed", owner_ssn_last4="4821"))
    assert all("4821" not in r for r in sm.match_reasons)


def test_address_only_wrong_name_is_not_a_match():
    q = MatchQuery("Thomas Walker", addresses=["742 Evergreen Terrace, Sacramento CA 95814"])
    sm = score_match(q, MatchTarget("Diane Foster", "742 Evergreen Terrace, Sacramento, CA 95814"))
    assert not sm.is_match


def test_dob_mismatch_penalty():
    q = MatchQuery("Robert Carter", dob=dt.date(1980, 1, 1))
    sm = score_match(q, MatchTarget("Robert Carter", owner_dob=dt.date(1990, 1, 1)))
    assert any("DOB differs" in r for r in sm.match_reasons)

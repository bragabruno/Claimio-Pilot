from app.states import STATE_CODES, STATES, code_for_slug, slug_for


def test_five_states():
    assert set(STATE_CODES) == {"CA", "NY", "TX", "FL", "IL"}


def test_notarization_thresholds_are_distinct():
    thresholds = [m["notarization_threshold_cents"] for m in STATES.values()]
    assert len(set(thresholds)) == len(thresholds), "thresholds must differ to diverge checklists"


def test_slug_roundtrip():
    for code in STATE_CODES:
        assert code_for_slug(slug_for(code)) == code

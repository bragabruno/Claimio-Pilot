from app.seed.synthetic import build_dataset
from app.states import STATE_CODES, STATES


def test_deterministic():
    a_claimants, a_props = build_dataset(seed=42)
    b_claimants, b_props = build_dataset(seed=42)
    assert [c.full_name for c in a_claimants] == [c.full_name for c in b_claimants]
    assert [p.amount_cents for p in a_props] == [p.amount_cents for p in b_props]


def test_contains_hard_cases():
    claimants, props = build_dataset()
    assert any(c.is_business for c in claimants), "need a business claimant"
    assert any(c.prior_names for c in claimants), "need a former-name claimant"
    assert any(p.owner_deceased for p in props), "need a deceased-owner property"


def test_threshold_boundary_properties_exist_per_state():
    _, props = build_dataset()
    for code in STATE_CODES:
        threshold = STATES[code]["notarization_threshold_cents"]
        amounts = {p.amount_cents for p in props if p.source_state == code}
        assert any(a < threshold for a in amounts), f"{code}: need an under-threshold amount"
        assert any(a > threshold for a in amounts), f"{code}: need an over-threshold amount"


def test_no_full_ssn_stored():
    claimants, _ = build_dataset()
    for c in claimants:
        assert c.ssn_last4 is None or len(c.ssn_last4) == 4

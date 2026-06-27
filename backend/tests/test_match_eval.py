"""Run the MATCH golden eval set as a test so matching regressions fail CI."""

from evals.match.cases import CASES

from app.match.scoring import DEFAULT_MATCH_THRESHOLD, score_match


def test_all_golden_cases_predicted_correctly():
    failures = []
    for case in CASES:
        sm = score_match(case.query, case.target)
        predicted = sm.confidence >= DEFAULT_MATCH_THRESHOLD
        if predicted != case.expected:
            failures.append((case.label, case.expected, predicted, sm.confidence))
    assert not failures, f"mispredicted: {failures}"


def test_golden_set_has_both_classes():
    assert any(c.expected for c in CASES) and any(not c.expected for c in CASES)

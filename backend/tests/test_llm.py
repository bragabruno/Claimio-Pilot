from app.services.llm import Usage, estimate_cost_cents


def test_cost_estimate_known_model():
    usage = Usage(prompt_tokens=1000, completion_tokens=1000)
    assert estimate_cost_cents("gpt-4o-mini", usage) > 0


def test_cost_estimate_local_model_is_free():
    usage = Usage(prompt_tokens=1000, completion_tokens=1000)
    assert estimate_cost_cents("llama3.1", usage) == 0.0


def test_usage_total():
    assert Usage(prompt_tokens=3, completion_tokens=4).total_tokens == 7

# 0004 — Deterministic logic for hard thresholds; LLM for nuanced mapping

- **Status:** Accepted

## Context

Some claim rules are crisp and numeric (e.g. "claims over $X require a notarized claim form").
Others require reading prose and mapping a claimant's situation (deceased owner, business
entity, outdated address) to documentation. Using an LLM for the crisp parts is needless
non-determinism and a correctness risk; using only deterministic code for the nuanced parts is
brittle and misses context.

## Decision

Split the work by nature of the rule:

- **Deterministic code** decides hard, machine-checkable thresholds — chiefly the per-state
  **notarization dollar threshold**, and structural flags (deceased / business / amount bands).
  These are computed directly from the property + claimant, not asked of the model.
- **The LLM (+ retrieved rules)** handles nuanced mapping of prose requirements to checklist
  items, each still carrying a rule-chunk citation (see 0003).

## Consequences

- Threshold-driven outcomes are reproducible and unit-testable independent of any model.
- The adversarial eval cases (amount just over/under a threshold) test the deterministic path
  precisely.
- Clear boundary: if a rule is numeric and unambiguous, it belongs in code; if it requires
  reading and judgment, it goes to the LLM with grounding. New rule types are slotted by this
  same test.

# 0003 — Grounded requirements with citations

- **Status:** Accepted

## Context

The buyer is compliance-sensitive. A claim checklist that silently invents requirements is
worse than useless — it is a liability. Every requirement we surface must be traceable to a
specific state rule, and the system must visibly decline to guess when it is unsure.

## Decision

Every item in a generated `RequiredItemList` must reference the `rule_chunk` it is grounded in
(`source_rule_chunk_id`). The pipeline enforces:

- **Grounding:** no requirement item without a cited rule chunk. An item the model produces
  without a valid citation is downgraded to `needs_human_review`, never shown as authoritative.
- **Confidence gating:** retrieval scores and extraction per-field confidence are thresholded.
  Low-confidence retrieval or extraction routes the affected item to human review.
- **No silent guessing:** when grounding or confidence fails, the system says so explicitly.

## Consequences

- The UI can show the exact cited state rule behind each requirement (the trust-building move).
- Some items will land in `needs_human_review` rather than as confident requirements; this is a
  feature, not a defect, and is surfaced plainly.
- Requires retrieval to return chunk ids + scores and extraction to return per-field confidence
  (see 0002). The eval harness (Phase 6) scores requirement precision/recall and flag accuracy
  to keep this honest.

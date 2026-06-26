# 0006 — Monorepo layout with runnable-phase delivery

- **Status:** Accepted

## Context

This is a focused demo built to be walked through and trusted. It needs to be easy to navigate
in one repo, and it needs to be demonstrably runnable at each step rather than a big-bang reveal
that may or may not start.

## Decision

Use a **monorepo**: `/backend`, `/frontend`, `/seed`, `/evals`, plus `docker-compose.yml`,
`Makefile`, `.env.example`, and `docs/adr/`. Deliver in **six runnable phases**, committing after
each:

1. Scaffold + datastore + domain model + migrations + seed + embeddings ingestion
2. Property search/match (+ tests)
3. RAG retrieval + grounded requirement reasoning (+ tests)
4. Document extraction + requirement satisfaction
5. Next.js UI incl. compare-states
6. Eval harness + observability/trace + README

Each phase maps to one Linear issue with acceptance criteria.

## Consequences

- Every commit leaves the system in a runnable state; reviewers can stop at any phase.
- Phases are vertically useful (backend is exercisable via API/tests before the UI exists).
- No half-built stubs on the demo path; placeholders (`/evals`, `/frontend`) are clearly marked
  until their phase lands.

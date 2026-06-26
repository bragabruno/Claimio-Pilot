# 0005 — Next.js / Tailwind / shadcn frontend

- **Status:** Accepted

## Context

The demo's payoff is visual: a state-specific checklist with expandable citations and a
side-by-side compare-states view. The frontend should look product-grade in a pitch and mirror
the target company's stack so the code reads as familiar to their team.

## Decision

Build the UI in **Next.js (App Router) + TypeScript + Tailwind + shadcn/ui**, talking to the
FastAPI backend over REST. Four screens: Search, Claim workspace, Document upload, and the
centerpiece Compare-states view, plus a trace drawer showing pipeline steps and token/cost.

## Consequences

- Matches the target stack; clean, componentized UI with minimal custom CSS.
- Clear front/back separation over REST keeps the backend independently testable and the API
  contract explicit.
- Frontend is a later phase (Phase 5); backend phases are fully usable via API/tests before any
  UI exists.

# Architecture Decision Records

These ADRs capture the key decisions behind ClaimPilot. Format: Nygard
(Title · Status · Context · Decision · Consequences).

| ADR | Decision |
|-----|----------|
| [0001](0001-pgvector-as-vector-store.md) | pgvector as the vector store, behind a `VectorStore` protocol |
| [0002](0002-openai-compatible-llm-client.md) | OpenAI-compatible LLM/embedding client (local gateway or OpenAI); structured outputs |
| [0003](0003-grounded-requirements-with-citations.md) | Every requirement cites a retrieved rule chunk; low confidence → human review |
| [0004](0004-deterministic-rules-plus-llm.md) | Deterministic logic for hard thresholds; LLM for nuanced mapping |
| [0005](0005-nextjs-frontend.md) | Next.js / Tailwind / shadcn frontend |
| [0006](0006-monorepo-phased-delivery.md) | Monorepo layout with runnable-phase delivery |

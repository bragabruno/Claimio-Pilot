# 0001 — pgvector as the vector store

- **Status:** Accepted

## Context

ClaimPilot needs both relational data (claimants, properties, claims, audit) and vector
similarity search over state-rule chunks for RAG. We want a demo a CTO can stand up in one
step and trust. Running a dedicated vector database (Milvus, Qdrant) means a second service,
its own ops surface, and more moving parts than a 10-minute demo warrants. We have run Milvus
in production and may want it later at scale, so the decision must not lock us in.

## Decision

Use **PostgreSQL 16 + pgvector** as a single datastore for both relational rows and embeddings,
shipped as one `docker-compose` service. Place all retrieval behind a `VectorStore` Protocol
(`upsert_chunks`, `search(state, query_vec, k)`) with a `PgVectorStore` implementation, so the
store can be swapped to Milvus/Qdrant later without touching the pipeline.

Embeddings are stored in a fixed-dimension `vector(EMBED_DIM)` column. Because pgvector columns
are **fixed-dimension at table-creation time**, `EMBED_DIM` is a configuration value the
migration reads — not a hard-coded constant. State-filtered search uses a btree index on
`state` plus an HNSW index on the embedding.

## Consequences

- One container; `make dev` brings up the whole datastore.
- Swapping embedding providers (e.g. local `nomic-embed-text` at 768 dims ↔ OpenAI
  `text-embedding-3-small` at 1536 dims) changes the column dimension and therefore requires a
  re-migration and re-embedding. This coupling is explicit and documented (see 0002).
- At larger scale, retrieval can move to a dedicated vector DB by adding a new `VectorStore`
  implementation; callers are unaffected.

# 0002 — OpenAI-compatible LLM/embedding client

- **Status:** Accepted

## Context

The demo must run cheaply and locally for development, but also against hosted OpenAI for a
polished pitch — without code changes. We also need extraction and requirement reasoning to
return reliable structured data, not free text we regex-parse.

## Decision

Use a single **OpenAI-compatible client** configured by environment:
`OPENAI_BASE_URL`, `OPENAI_API_KEY`, `LLM_MODEL`, `EMBED_MODEL`, `EMBED_DIM`.

- **Default:** local gateway / Ollama (`http://localhost:11434/v1`, `llama3.1`,
  `nomic-embed-text`, `EMBED_DIM=768`) — no external key or cost.
- **Swap to OpenAI:** point `OPENAI_BASE_URL` at `api.openai.com`, set `gpt-4o-mini` +
  `text-embedding-3-small`, `EMBED_DIM=1536`.

All model outputs that feed logic use **structured outputs / JSON mode bound to Pydantic
schemas**. We never regex-parse model text.

## Consequences

- Provider choice is one config change; the same code path serves local and hosted runs.
- `EMBED_MODEL` and `EMBED_DIM` are coupled to the pgvector column dimension (see 0001):
  switching embedding models requires re-migrate + re-embed.
- Structured outputs give typed, validated data and let us attach per-field confidence used by
  the confidence gates (see 0003). Models lacking JSON-mode support are out of scope for the demo.
- Fail-fast: client/transport errors surface explicitly rather than being swallowed.

# ClaimPilot — Architecture diagrams

> **Demonstration system. Synthetic data. Not legal advice.**
>
> Legend for build status: ✅ built (Phases 1–4) · 🔜 planned (Phase 5 UI, per `docs/adr/0006`).
> Diagrams document the intended design; nodes touching unbuilt pipeline steps are marked 🔜.

## 1. System architecture

```mermaid
flowchart LR
    subgraph client["Client"]
        UI["Next.js UI<br/>Tailwind + shadcn 🔜"]
    end

    subgraph backend["FastAPI backend"]
        REST["REST endpoints<br/>/healthz, /debug/last-run ✅<br/>/claimants, /properties, /claims 🔜"]
        WF["ClaimWorkflow<br/>pipeline orchestrator 🔜"]
        LOG["JSON logging<br/>+ PII redaction ✅"]

        subgraph services["Services"]
            MATCH["Property match<br/>rapidfuzz 🔜"]
            EMB["Embeddings client<br/>OpenAI-compatible ✅"]
            VS["VectorStore protocol<br/>PgVectorStore ✅"]
            EXT["Document extraction 🔜"]
            REQ["Requirement reasoning<br/>deterministic + LLM 🔜"]
            LET["Letter / package gen 🔜"]
        end
    end

    subgraph data["Datastore"]
        PG[("PostgreSQL 16<br/>+ pgvector ✅")]
    end

    subgraph llm["OpenAI-compatible endpoint"]
        GW["Local Ollama (default)<br/>or OpenAI ✅"]
    end

    UI -->|REST/JSON| REST
    REST --> WF
    REST --> LOG
    WF --> MATCH
    WF --> VS
    WF --> EXT
    WF --> REQ
    WF --> LET
    MATCH --> PG
    VS --> PG
    EMB --> GW
    EMB --> PG
    EXT --> GW
    REQ --> GW
    REQ --> VS
    WF --> PG
```

## 2. Domain model (ER)

All seven tables exist as of Phase 1. `rule_chunk.embedding` is `vector(EMBED_DIM)` —
dimension from config (see `docs/adr/0001`).

```mermaid
erDiagram
    claimant ||--o{ claim : files
    property ||--o{ claim : "claimed via"
    state_rule_doc ||--o{ rule_chunk : "chunked into"
    claim ||--o{ run_trace : traces
    claim ||--o{ audit_event : audits

    claimant {
        uuid id PK
        string full_name
        text_array prior_names
        text_array addresses
        date dob
        string ssn_last4
        string email
        bool is_business
        timestamptz created_at
    }
    property {
        uuid id PK
        string source_state
        string holder_name
        string owner_name
        text owner_last_address
        bigint amount_cents
        string property_type
        bool owner_deceased
        date reported_date
        string status
    }
    state_rule_doc {
        uuid id PK
        string state
        string title
        text body_md
        string version
    }
    rule_chunk {
        uuid id PK
        uuid doc_id FK
        string state
        text text
        vector embedding
    }
    claim {
        uuid id PK
        uuid claimant_id FK
        uuid property_id FK
        string state
        string status
        jsonb required_items_json
        jsonb package_json
        timestamptz created_at
        timestamptz updated_at
    }
    run_trace {
        uuid id PK
        uuid claim_id FK
        jsonb steps_json
        int tokens
        int cost_cents
        timestamptz created_at
    }
    audit_event {
        uuid id PK
        uuid claim_id FK
        string type
        jsonb payload_json
        timestamptz created_at
    }
```

## 3. Claim pipeline (sequence)

The end-to-end flow a `POST /claims` will drive. Phase 1 ships the datastore, embeddings,
and state-filtered retrieval; the orchestrated steps land in Phases 2–5.

```mermaid
sequenceDiagram
    actor U as User (UI)
    participant API as FastAPI
    participant M as Property match 🔜
    participant E as Embeddings ✅
    participant V as VectorStore ✅
    participant L as LLM (Ollama/OpenAI) ✅
    participant DB as Postgres + pgvector ✅

    U->>API: POST /properties/search (name, prior_names, addresses) 🔜
    API->>M: fuzzy match
    M->>DB: scan property index
    DB-->>M: candidates + scores
    M-->>U: ranked candidates

    U->>API: POST /claims (claimant_id, property_id) 🔜
    API->>E: embed claim-context query
    E->>L: /embeddings
    L-->>E: query vector
    API->>V: search(state, query_vec, k)
    V->>DB: cosine search WHERE state = ?
    DB-->>V: top-k rule chunks (citations)
    API->>L: requirement reasoning (chunks + profile)
    L-->>API: RequiredItemList (structured)
    Note over API: deterministic notarization threshold<br/>ungrounded / low-conf → needs_human_review
    API->>L: draft claim letter
    API->>DB: persist claim + run_trace (tokens, cost)
    API-->>U: checklist + citations + letter + trace
```

## 4. Grounding guardrail (decision flow)

Every requirement item must cite a retrieved rule chunk; otherwise it is routed to human
review (see `docs/adr/0003`). Enforced in Phase 3.

```mermaid
flowchart TD
    START([Candidate requirement item]) --> CITE{"Cites a<br/>rule_chunk?"}
    CITE -- No --> HR[["needs_human_review"]]
    CITE -- Yes --> RCONF{"Retrieval<br/>confidence ok?"}
    RCONF -- No --> HR
    RCONF -- Yes --> ECONF{"Extraction<br/>confidence ok?<br/>(if doc-backed)"}
    ECONF -- No --> HR
    ECONF -- Yes --> OK[[Grounded required item<br/>with source_rule_chunk_id]]
```

## 5. Claim status lifecycle

The `claim.status` values enforced by a DB check constraint (built in Phase 1).

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> needs_docs: requirements computed
    needs_docs --> needs_docs: more docs requested
    needs_docs --> ready_to_file: all required items satisfied
    ready_to_file --> filed: package submitted
    filed --> recovered: funds released
    recovered --> [*]
```

## 6. Phased delivery

Runnable phases, one Linear issue each (BRA-920…925). See `docs/adr/0006`.

```mermaid
flowchart LR
    P1["Phase 1 ✅<br/>Scaffold + datastore<br/>+ model + seed + embeddings"]
    P2["Phase 2 ✅<br/>Property match<br/>(rapidfuzz)"]
    P3["Phase 3 ✅<br/>RAG + grounded<br/>requirements"]
    P4["Phase 4 ✅<br/>Doc extraction<br/>+ satisfaction"]
    P5["Phase 5 🔜<br/>Next.js UI<br/>+ compare-states"]
    P6["Phase 6 ✅<br/>Evals + trace<br/>+ README"]
    P1 --> P2 --> P3 --> P4 --> P5 --> P6
```

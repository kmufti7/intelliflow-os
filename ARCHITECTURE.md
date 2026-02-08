# IntelliFlow OS — Architecture

## Platform Shape
```mermaid
flowchart LR
  A[intelliflow-core<br/>contracts + governance UI] --> B[SupportFlow<br/>Banking module]
  A --> C[CareFlow<br/>Healthcare module]

  B --> D[(SQLite<br/>support_tickets + audit_logs)]
  C --> E[(SQLite<br/>patients + appointments + audit_logs)]

  B --> F[LLM<br/>gpt-4o-mini]
  C --> G[LLM<br/>gpt-4o-mini]
```

## SupportFlow Flow
```mermaid
flowchart TD
  U[Customer message] --> C1[Classifier<br/>enum output]
  C1 --> R[Router]
  R --> H1[Positive handler]
  R --> H2[Negative handler<br/>ticket + policy]
  R --> H3[Query handler<br/>policy retrieval]

  H1 --> L[Audit log]
  H2 --> L
  H3 --> L

  H2 --> DB[(SQLite)]
  L --> DB
```

## CareFlow Flow (Governed Deterministic Reasoning)
```mermaid
flowchart TD
  N[Clinic note] --> X[Extraction<br/>regex-first]
  X --> Q[Concept Query Builder<br/>de-identified concepts]
  Q --> KB[Guideline retrieval<br/>FAISS local / Pinecone cloud]
  X --> RE[Reasoning engine<br/>deterministic gap computation]
  KB --> RE
  RE --> A[Responder<br/>LLM formats + citations]
  A --> L[Audit log]
```

## Notes
- This is a reference implementation optimized for auditability and interview-ready proof.
- Deterministic logic is used where correctness matters.
- LLM translates and formats; code decides.

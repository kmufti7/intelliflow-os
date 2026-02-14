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

## FHIR Dual-Mode Ingestion
```mermaid
flowchart TD
  subgraph Legacy Path
    CN[Clinic Note<br/>free text] --> RX[Regex Extraction<br/>A1C, BP, meds, conditions]
  end

  subgraph FHIR Path
    FB[FHIR R4 Bundle] --> FP[FHIR Parser]
    FP --> PT[Patient Resource<br/>name extraction]
    FP --> OB[Observation Resource<br/>LOINC 4548-4 → A1C value]
  end

  RX --> EF[ExtractedFacts<br/>unified schema]
  PT --> AD[FHIR Adapter<br/>maps to ExtractedFacts]
  OB --> AD
  AD --> EF

  EF --> RE[Reasoning Engine<br/>deterministic gap rules]
```

## Chaos Mode Control Flow
```mermaid
flowchart TD
  UI[Sidebar Toggle<br/>Enable Chaos Mode] --> CHK{Chaos Enabled?}
  CHK -->|No| NORMAL[Normal Execution]
  CHK -->|Yes| INJ[Failure Injection<br/>configurable rate]

  INJ --> SF_F[SupportFlow Failures]
  INJ --> CF_F[CareFlow Failures]

  SF_F --> DB_F[Database Failure]
  SF_F --> VS_F[Vector Store Failure]

  CF_F --> FAISS_F[FAISS Failure]
  CF_F --> PIN_F[Pinecone Failure]

  DB_F --> GD[Graceful Degradation<br/>user-friendly error message]
  VS_F --> GD
  FAISS_F --> CLIN[Safe Clinical Fallback<br/>No clinical decisions should be made]
  PIN_F --> CLIN

  GD --> AL[Audit Log<br/>chaos event recorded]
  CLIN --> AL
```

## Developer Tools Layer
```mermaid
flowchart LR
  subgraph Shared SDK
    SC[contracts.py<br/>3 Pydantic Schemas]
    AL[(audit_logs<br/>SQLite)]
  end

  subgraph AI Test Generator
    SC -->|FieldInfo introspection| TG[LLM generates<br/>pytest suites]
    TG --> PY[pytest validates<br/>35 tests]
  end

  subgraph NL Log Query
    NL[Natural Language<br/>query] --> LLM1[LLM translates<br/>→ SQL WHERE]
    LLM1 --> VAL[Python validates<br/>column whitelist<br/>blocked keywords]
    VAL --> AL
  end

  subgraph Scaffold Generator
    DESC[Developer intent<br/>plain English] --> LLM2[LLM generates<br/>governance-wired code]
    SC -->|importlib introspection| LLM2
    LLM2 --> AST[ast.parse validates<br/>retries on error]
  end
```

## Notes
- This is a reference implementation optimized for auditability and interview-ready proof.
- Deterministic logic is used where correctness matters.
- LLM translates and formats; code decides.

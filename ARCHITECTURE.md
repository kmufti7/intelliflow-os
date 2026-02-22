# IntelliFlow OS — Architecture

## Platform Overview
```mermaid
flowchart TD
  subgraph Clients["Client Applications"]
    WEB[Web App]
    API[API Gateway]
    EHR[EHR / Core Banking]
  end

  subgraph VPC["Enterprise VPC"]
    RR[Request Router<br/>Deterministic]
    GW[Governance Wrapper<br/>Pydantic Validation · Audit Logging]

    subgraph Modules["Domain Modules"]
      SF[SupportFlow<br/>Banking]
      CF[CareFlow<br/>Healthcare]
      CLF[ClaimsFlow<br/>Insurance]
    end

    CORE[intelliflow-core v2<br/>LangGraph Engine · Kill-Switch · MCP Registry]
    FAISS[(FAISS<br/>PHI — Never Leaves VPC)]

    subgraph PE["Private Endpoints"]
      AZ_PE[Azure Private Endpoint]
      AWS_PE[AWS Bedrock PrivateLink]
    end
  end

  subgraph LLMs["LLM Providers — Outside VPC"]
    AZ[Azure OpenAI]
    BR[AWS Bedrock]
  end

  PIN[(Pinecone<br/>Guidelines Only · No PHI)]

  WEB --> RR
  API --> RR
  EHR --> RR
  RR --> GW
  GW --> SF
  GW --> CF
  GW --> CLF
  SF --> CORE
  CF --> CORE
  CLF --> CORE
  CORE --> AZ_PE
  CORE --> AWS_PE
  AZ_PE --> AZ
  AWS_PE --> BR
  CF --> FAISS
  CF --> PIN
```

## Module Flow
```mermaid
flowchart TD
  CORE[intelliflow-core v2<br/>LangGraph Engine · Kill-Switch · MCP Registry]

  CORE --> SF_MOD
  CORE --> CF_MOD
  CORE --> CLF_MOD

  subgraph SF_MOD["SupportFlow — Banking"]
    SF_RR[Deterministic Router<br/>enum classification] --> SF_PH[Policy Handler<br/>20 banking policies]
    SF_PH --> SF_AL[(Audit Log)]
  end

  subgraph CF_MOD["CareFlow — Healthcare"]
    CF_EX[Regex Extraction<br/>100% success rate] --> CF_KB[FAISS / Pinecone<br/>guideline retrieval]
    CF_KB --> CF_RE[Reasoning Engine<br/>deterministic gap computation]
    CF_RE --> CF_AL[(Audit Log)]
  end

  subgraph CLF_MOD["ClaimsFlow — Insurance"]
    CLF_LG[LangGraph Agent<br/>claims orchestration] --> CLF_FS[Fraud Score<br/>risk assessment]
    CLF_FS --> CLF_KS{Kill-Switch<br/>confidence threshold}
    CLF_KS -->|Pass| CLF_ADJ[Adjudication<br/>auto-approve]
    CLF_KS -->|Fail| CLF_ESC[Human Review<br/>escalation]
    CLF_ADJ --> CLF_AL[(Audit Log)]
    CLF_ESC --> CLF_AL
  end
```

## SupportFlow Flow
```mermaid
flowchart TD
  subgraph VPC["Enterprise VPC"]
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
  end
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
    TG --> PY[pytest validates<br/>35 generated · 193 total]
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
- Enterprise integration middleware optimized for auditability and regulatory compliance.
- Deterministic logic is used where correctness matters.
- LLM translates and formats; code decides.
- Designed for Azure OpenAI Service (BAA-eligible) to meet enterprise compliance requirements for regulated industries.

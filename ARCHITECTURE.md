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

## ClaimsFlow Flow (LangGraph Agentic Workflow)
```mermaid
flowchart TD
  START[__start__] --> INTAKE[Intake Node<br/>LLM extracts ClaimPayload]
  INTAKE --> FRAUD[Fraud Score Node<br/>Rule-based + MCP registry lookup]
  FRAUD --> KS{Kill-Switch Guard<br/>Edge Interceptor}
  KS -->|Pass: fraud_flag=False| ADJ[Adjudication Node<br/>Threshold-based decision]
  KS -->|Fail: fraud_flag=True| HALT[WORKFLOW HALTED<br/>KILL_SWITCH_TRIGGERED]
  ADJ --> END[__end__]

  INTAKE -.->|WORM| W1[INTAKE_COMPLETE]
  FRAUD -.->|WORM| W2[FRAUD_SCORE_COMPLETE]
  KS -.->|WORM| W3[KILL_SWITCH_TRIGGERED]
  ADJ -.->|WORM| W4[ADJUDICATION_COMPLETE]

  INTAKE -.->|FinOps| L1[Token Ledger Receipt]
  FRAUD -.->|FinOps| L2[Token Ledger Receipt]
  ADJ -.->|FinOps| L3[Token Ledger Receipt]
```

The Kill-Switch Guard is wired as a regular LangGraph node (not via `add_interceptor_slot`) — a typed wrapper function ensures LangGraph passes `ClaimsFlowState` (with custom fields) rather than the base `IntelliFlowState`. This architectural choice prevents LangGraph state reconstruction from stripping domain-specific fields (`fraud_score`, `fraud_flag`, `claim_data`).

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
    TG --> PY[pytest validates<br/>35 generated · 253 total]
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

## intelliflow-core v2 — Governed Agentic Runtime

### Strangler Fig Migration

v2 lives at `intelliflow_core/v2/` inside the existing intelliflow-core repo. v1 modules (`contracts.py`, `helpers.py`, `governance_ui.py`) remain 100% unchanged. Both generations coexist — v1 consumers are completely unaffected by v2's presence. New agentic workflows use v2; existing deterministic modules stay on v1.

### v2 Package Structure

```mermaid
flowchart TD
    V2[intelliflow_core/v2/__init__.py] --> RT[v2/runtime/]
    V2 --> ST[v2/storage/]
    V2 --> TS[v2/tests/]
    RT --> WF[workflow.py<br/>LangGraph StateGraph wrapper]
    RT --> STATE[state.py<br/>IntelliFlowState · Pydantic · frozen]
    RT --> INT[interceptors.py<br/>InterceptorNode ABC · kill-switch slot]
    RT --> EX[exceptions.py<br/>v2-specific error hierarchy]
```

### Python Version Boundary

v2 requires Python ≥3.10 (LangGraph dependency). v1 continues to support Python ≥3.9. An explicit version guard in `v2/__init__.py` raises `RuntimeError` if imported on Python <3.10. This is environmental defense by architecture — v1 consumers on 3.9 are completely isolated from v2's runtime requirements.

### v2 Runtime Dependency

LangGraph 1.0.9 is the v2 runtime framework. It is **not** listed in `pyproject.toml` — Strangler Fig isolation means v1 consumers never encounter it. v2 consumers install separately: `pip install "langgraph>=0.2.0"`.

### KillSwitchGuard — Governance Enforcement at Graph Level

KillSwitchGuard is a concrete `InterceptorNode` implementation that sits before any LLM-calling node in the LangGraph graph. It evaluates a list of GovernanceRule contracts against the current workflow state. Each GovernanceRule is a dataclass with three fields: `rule_id`, `description` (required — enforces self-documentation), and `logic` (a callable returning bool).

**Behavior:**
- **Fail-closed:** If a rule's logic raises an exception, the rule is treated as failed. The system never silently passes on error.
- **Collect-all-failures:** Every rule is evaluated even after early failures. The complete failure set is included in the KillSwitchTriggered exception for audit.
- **Structured result:** `Workflow.run()` catches KillSwitchTriggered and returns a WorkflowResult with `kill_switch_triggered=True`, `failed_rules`, and `error_message` — no raw exception propagation to callers.

Supporting files: `contracts.py` (GovernanceRule, WorkflowResult), `kill_switch.py` (KillSwitchGuard), `exceptions.py` (KillSwitchTriggered). 8 tests in `test_kill_switch.py`.

### WORM Audit Layer (v2)

DatabaseSessionManager provides a shared SQLite connection with WAL journaling. WORMLogRepository sits below the Workflow engine — it receives `log_event()` calls at WORKFLOW_START, WORKFLOW_END, and KILL_SWITCH_TRIGGERED checkpoints. Each entry is HMAC-SHA256 chained (`prev_hash` -> `entry_hash`). SQLite triggers enforce physical Write-Once at the DB layer. `trace_id` (UUID4 in IntelliFlowState) is the correlation key across all events in a single workflow execution. If any WORM write fails, `WORMStorageError` halts the workflow (fail-closed). `verify_chain()` recomputes all hashes sequentially to detect tampering. Supporting files: `storage/db.py` (DatabaseSessionManager), `storage/worm_logger.py` (WORMLogRepository), `exceptions.py` (+WORMStorageError). 12 tests in `test_worm_logger.py`.

### Token FinOps Tracker (v2)

TokenLedgerRepository provides append-only financial telemetry for LLM token consumption. It shares DatabaseSessionManager with WORMLogRepository for unified SQLite storage. Cost is calculated at write time using static Azure OpenAI pricing (immutable receipt pattern — stored cost_usd is never recalculated). The token_ledger table is append-only financial telemetry. In production deployments, a Data Lifecycle Management (DLM) policy (e.g., 90-day archival to cold storage) is required to prevent unbounded disk growth. See [ADR: Data Lifecycle Management](docs/enterprise/ADR_DATA_LIFECYCLE_MANAGEMENT.md) for the architecture decision rationale and deployer responsibility model. 13 tests in `test_token_ledger.py`.

## Notes
- Enterprise integration middleware optimized for auditability and regulatory compliance.
- Deterministic logic is used where correctness matters.
- LLM translates and formats; code decides.
- Designed for deployment within existing sovereign Azure/AWS perimeters — inherits enterprise identity, encryption, and network controls.

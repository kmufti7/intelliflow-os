# IntelliFlow OS — Governance & Compliance

## Purpose

This document describes the governance architecture of IntelliFlow OS, a reference implementation for AI systems in regulated industries.

## NIST AI Risk Management Framework (AI RMF) Alignment

Reference: [NIST AI RMF 1.0](https://www.nist.gov/artificial-intelligence/risk-management-framework)

### GOVERN — Establish governance structures

| Principle | IntelliFlow OS Implementation |
|-----------|-------------------------------|
| Accountability | Every AI decision logged with agent name, action, reasoning, and confidence score. Full audit trail per interaction. |
| Transparency | Governance UI panel renders real-time decision traces. Policy citations included in every response. |
| Role clarity | Agents have explicit responsibilities (classifier, handler, reasoner). No agent operates outside its defined scope. |

### MAP — Identify and categorize risks

| Risk Category | How Addressed |
|---------------|---------------|
| Clinical hallucination | "LLM extracts, code decides" — deterministic Python rules for gap detection, not LLM reasoning. |
| Data leakage (PHI) | PHI stays in local FAISS. External queries de-identified via Concept Query Builder. |
| Cost overrun | Per-interaction token tracking. Regex-first extraction eliminates unnecessary LLM calls. |
| Prompt injection | Enum-based classification constrains routing. System prompts enforce policy-grounded answers. |

### MEASURE — Assess and quantify risks

| Metric | Measurement |
|--------|-------------|
| Test coverage | 253 tests across platform (193 v1 legacy + 60 v2 LangGraph) |
| Extraction accuracy | 100% regex success rate on structured clinical data |
| Audit completeness | Every interaction produces audit log entries with timestamps, confidence, and reasoning |
| Cost visibility | Token counts and USD costs tracked per interaction, visible in governance UI |

### MANAGE — Prioritize and respond to risks

| Control | Implementation |
|---------|----------------|
| Chaos engineering | SupportFlow injects failures at 7 checkpoints (30% rate) to validate graceful degradation |
| Pydantic validation | All audit events and cost records validated through strict schemas; malformed data rejected |
| CI/CD gates | GitHub Actions runs full test suite on every push; no merge without green |
| Deterministic routing | Enum-based classification prevents unpredictable agent behavior |
| Kill-switch guard | Deterministic KillSwitchGuard interceptor evaluates GovernanceRule contracts (self-documenting, required description field) at graph level. Fail-closed: rule exceptions treated as failures. Collect-all-failures: full failure set for audit. Structured WorkflowResult replaces raw exception propagation. Aligns with SR 11-7 kill-switch principle. |
| ClaimsFlow Kill-Switch interceptor | ClaimsFlow wires KillSwitchGuard as an edge interceptor between fraud_score and adjudication nodes. GovernanceRule `sanctions_check`: if claimant flagged in OFAC/SIU registry (`fraud_flag == True`), workflow halts before adjudication. WORM logs KILL_SWITCH_TRIGGERED with failed_rules and state_snapshot. Demonstrates Kill-Switch in an agentic LangGraph workflow with real-world compliance trigger. |
| WORM audit log | WORMLogRepository: HMAC-SHA256 hash-chained append-only audit log. SQLite BEFORE UPDATE/DELETE triggers enforce Write-Once at DB layer. Fail-closed WORMStorageError halts workflow on write failure. Session-bounded trace_id links WORKFLOW_START, WORKFLOW_END, TOOL_EXECUTED, KILL_SWITCH_TRIGGERED. Aligned to SR 11-7 expectations and SEC 17a-4 record-keeping patterns. |

## Governance UI

Both SupportFlow and CareFlow render a real-time governance panel (Streamlit sidebar) showing:
- Timestamped audit entries
- Agent decisions with reasoning
- Confidence scores
- Token usage and cost per interaction
- Policy/guideline citations

This panel is powered by `intelliflow-core`'s `governance_ui.py` module, ensuring consistent governance rendering across all modules.

---

## EU AI Act Classification

Under the **EU AI Act**, the CareFlow module (Clinical Decision Support) would likely be classified as a **High-Risk AI System (Annex III)** if deployed in production.

**Why this matters:**
- Healthcare AI systems that influence clinical decisions fall under strict regulatory requirements in the EU.
- Understanding this classification demonstrates awareness of global AI regulatory landscape.

**Relevant Controls Implemented:**

| Article | Requirement | IntelliFlow OS Implementation |
|---------|-------------|-------------------------------|
| **Article 13** | Transparency | System explicitly identifies itself as an AI agent. Governance UI shows reasoning trace. |
| **Article 14** | Human Oversight | "Code as Judge" pattern ensures human-defined logic (Python) supersedes model probability for critical health metrics. |
| **Article 15** | Accuracy | Deterministic extraction (regex-first) ensures accuracy of input data. Pydantic validation rejects malformed data. |

**Disclaimer:** This is a reference implementation demonstrating architectural patterns. It is not a production-certified medical device and has not undergone formal EU AI Act conformity assessment.

### Token Ledger — Financial Governance Control

| Control | Implementation | Classification |
|---------|---------------|---------------|
| Per-invocation cost logging | TokenLedgerRepository.record_invocation() | Financial telemetry |
| Point-in-time cost immutability | cost_usd stored at write time | Accounting integrity |
| Partial failure cost capture | Per-invocation granularity, not per-workflow | Financial completeness |
| WORM linkage | trace_id FK to worm_log | Cross-control traceability |
| Fail-open design | TokenLedgerError does not halt execution | Operational resilience |

Token tracking is double-entry accounting. A token count without a locked USD value
is telemetry. A token count with an immutable USD cost at the time of inference is
an auditable financial receipt. IntelliFlow OS implements the latter.

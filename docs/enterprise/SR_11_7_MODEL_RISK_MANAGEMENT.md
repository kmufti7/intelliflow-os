# SR 11-7 Model Risk Management — IntelliFlow OS Alignment

## Status

**Self-Assessed Alignment** — February 2026

---

## 1. Overview

### What SR 11-7 Requires

[SR 11-7: Guidance on Model Risk Management](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm), issued by the Federal Reserve Board of Governors and the OCC, establishes the supervisory framework for how financial institutions must identify, measure, monitor, and control model risk. It applies to any quantitative method, system, or approach that processes inputs into quantitative estimates — which includes LLM-based systems that classify, route, extract, or generate outputs in regulated financial workflows.

### Why SR 11-7 Applies to LLM Deployments

LLMs in banking and financial services meet SR 11-7's definition of a "model" when they:

- **Process inputs into outputs used for decision-making.** SupportFlow classifies customer messages into sentiment categories (POSITIVE, NEGATIVE, QUERY) and routes them to policy-grounded handlers. The classification output directly determines which response path the customer receives.
- **Produce quantitative estimates.** Cost tracking calculates per-interaction token costs. Confidence scores accompany classification decisions. Severity tiers are computed deterministically.
- **Inform business decisions.** Escalation triggers, policy routing, and compliance citations are produced by the pipeline and consumed by human operators for customer-facing decisions.

SR 11-7 requires that institutions using models have:

1. **Robust model development, implementation, and use** — documented methodology, testing, and validation.
2. **Effective model validation** — independent review confirming the model performs as intended.
3. **Sound governance, policies, and controls** — clear ownership, oversight, audit trails, and change management.

### Scope of This Document

This document maps SR 11-7 requirements to IntelliFlow OS controls across both modules (SupportFlow, CareFlow). It describes what the platform provides and what the deploying institution must independently establish. IntelliFlow OS is a software platform — it provides controls and architecture patterns. SR 11-7 compliance is the responsibility of the deploying institution's model risk management function.

---

## 2. SR 11-7 Requirement Mapping

| SR 11-7 Requirement | Section | IntelliFlow OS Control | Evidence |
|---------------------|---------|----------------------|----------|
| **Model Development Documentation** | §IV.A | Architecture documented in ARCHITECTURE.md (7 Mermaid diagrams). Data flows, component interactions, and decision boundaries specified. | ARCHITECTURE.md, DATA_DICTIONARY.md |
| **Conceptual Soundness** | §IV.A.1 | "Code decides, LLM explains" principle separates model outputs (extraction, classification) from business logic (gap computation, policy routing, escalation). LLM is a data processing tool, not a decision-maker. | GOVERNANCE.md §Deterministic Reasoning, ADR_DETERMINISTIC_V1_VS_AGENTIC_V2.md |
| **Outcome Analysis** | §IV.A.2 | 276 automated ecosystem tests (253 platform-core + 23 ClaimsFlow) validate expected outcomes. Regex extraction achieves 100% accuracy on test patients. Gap computation is deterministic — same inputs produce same outputs. | TEST_STRATEGY.md, verify_cascade.py |
| **Ongoing Monitoring** | §IV.B | Per-interaction audit logging captures: component, action, timestamp, success/failure, confidence, reasoning, and cost. Governance panel provides real-time visibility. | OBSERVABILITY.md, AuditEventSchema |
| **Model Validation** | §V | Platform provides 150 automated verification checks and 15 cascade consistency checks. Independent validation (challenger models, backtesting) is the deploying institution's responsibility. | verify_enterprise_docs.py, verify_cascade.py |
| **Governance & Controls** | §VI | Pydantic-enforced schemas (AuditEventSchema, CostTrackingSchema, GovernanceLogEntry) ensure structured data integrity. No unvalidated data enters or exits the pipeline. | intelliflow-core contracts.py |
| **Audit Trail** | §VI.B | Every decision logged with evidence chain: input data → extraction result → business logic output → explanation with citations. Queryable via NL Log Query tool. | Governance log, nl_log_query.py |
| **Change Management** | §VI.C | 15-check cascade verification ensures changes propagate consistently across 4 repositories. CHANGELOG.md tracks version history. Semantic versioning policy documented. | verify_cascade.py, RELEASE_NOTES_VERSIONING.md |
| **Model Inventory** | §VI.D | Single model (gpt-4o-mini) documented in VENDOR_COMPARISON.md. Model selection rationale, alternatives considered, and cost implications recorded. | VENDOR_COMPARISON.md, COST_MODEL.md |
| **Roles & Responsibilities** | §VI.E | Platform distinguishes operator responsibilities from platform capabilities. Shared responsibility model documented. | SECURITY_PRIVACY_OVERVIEW.md |

---

## 3. SupportFlow-Specific Controls

SupportFlow operates in the banking domain where SR 11-7 directly applies. The following controls address model risk at each pipeline stage:

### 3.1 Deterministic Routing

Customer messages are classified into sentiment categories (POSITIVE, NEGATIVE, QUERY) via structured LLM outputs. The classification uses enum-constrained responses — the model selects from a predefined set, not free-text. Routing from classification to handler is deterministic Python code:

```
Classification → NEGATIVE → NegativeHandler → escalation + policy lookup
Classification → POSITIVE → PositiveHandler → acknowledgment
Classification → QUERY    → QueryHandler    → policy retrieval + response
```

**SR 11-7 alignment:** The routing logic is inspectable code, not model behavior. An auditor can trace any customer interaction from classification result to handler selection to policy citation. The model's role is constrained to selecting from a fixed enum — it cannot invent routing categories.

### 3.2 Citation Gating

Every SupportFlow response must cite the specific banking policy it references (e.g., POLICY-002 for fee disputes). Responses without policy citations are structurally invalid — Pydantic schema validation rejects them before they reach the customer.

**SR 11-7 alignment:** Citation gating addresses SR 11-7's requirement for outcome traceability. The response is not just "grounded" — it is structurally required to identify its source. An auditor can verify that response content matches the cited policy.

### 3.3 Policy Grounding

Policy retrieval uses keyword-based matching (60+ keywords mapped to 20 banking policies). This is deterministic — the same query always retrieves the same policies. No embedding-based retrieval, no semantic similarity scoring, no non-deterministic ranking.

**SR 11-7 alignment:** Policy grounding eliminates a common model risk vector in RAG architectures: retrieval quality variability. Keyword matching is fully inspectable. There is no hidden similarity threshold that might silently degrade retrieval accuracy.

---

## 4. CareFlow-Specific Controls

While CareFlow operates in healthcare (HIPAA applies), SR 11-7 principles extend to any regulated deployment. The following controls demonstrate model risk management patterns applicable to banking AI analogues:

### 4.1 Local Data Residency (FAISS)

Patient data resides exclusively in local FAISS vector indexes. No patient data is transmitted to cloud services. The Concept Query Builder de-identifies all queries before any external API call — converting patient-specific data (e.g., "John Smith, A1C 8.2") into concept-level queries (e.g., "diabetes management elevated A1C").

**SR 11-7 alignment:** Data residency controls address the model risk associated with data leakage. The architecture structurally prevents model inputs containing sensitive data from reaching external services — this is enforced by code, not policy.

### 4.2 Regex-First Extraction

Clinical data extraction uses regex patterns as the primary method. Regex extraction achieves 100% success rate on all test patients. LLM-based extraction exists as a fallback but is never triggered in current test scenarios.

**SR 11-7 alignment:** Regex extraction is a deterministic, non-model process. When regex succeeds, the extraction step carries zero model risk. The LLM fallback, when triggered, introduces model risk — but only for the extraction step, not for the downstream decision logic. This separation allows model risk to be precisely scoped.

### 4.3 Deterministic Severity Tiers

Gap detection uses deterministic Python code with explicit thresholds:
- A1C ≥ 7.0% → care gap detected
- Severity assigned based on deviation magnitude and guideline alignment

The LLM formats the explanation with dual citations (patient evidence + guideline evidence) but does not compute the gap or assign severity.

**SR 11-7 alignment:** Decision logic is fully deterministic and inspectable. An auditor can read the Python code, verify the thresholds, and confirm that the same inputs always produce the same outputs. The model's contribution is limited to explanation formatting — a function that carries no decision risk.

---

## 5. Kill-Switch Mandate

### What the Kill-Switch Provides

IntelliFlow OS v1 modules can operate with the LLM completely disabled:

| Component | LLM Enabled | LLM Disabled |
|-----------|-------------|--------------|
| **SupportFlow routing** | Enum-classified via LLM structured output | Keyword-based classification (deterministic fallback) |
| **SupportFlow policy retrieval** | 60+ keyword mapping (no LLM involved) | Identical — already deterministic |
| **SupportFlow response generation** | LLM formats natural language response | Raw policy text returned without formatting |
| **CareFlow extraction** | Regex-first, LLM fallback | Regex-only (100% success on test patients) |
| **CareFlow gap computation** | Deterministic Python (no LLM involved) | Identical — already deterministic |
| **CareFlow explanation** | LLM formats with dual citations | Structured gap data without narrative explanation |

### SR 11-7 Override Requirement

SR 11-7 §VI states that institutions must have the ability to "limit or cease model use" when model risk exceeds acceptable thresholds. The kill-switch provides this capability at the architecture level:

1. **Immediate effect.** Disabling the LLM takes effect on the next interaction — no redeployment, no configuration change propagation delay.
2. **No decision capability loss.** Business logic (routing, gap computation, policy retrieval) continues to function. Only natural language formatting is lost.
3. **Audit continuity.** Governance logging continues in kill-switch mode. The audit trail records that the LLM was disabled, when, and by whom.
4. **Reversible.** Re-enabling the LLM restores full functionality without data migration or system reconfiguration.

### KillSwitchGuard — v2 Implementation (intelliflow-core v2)

KillSwitchGuard (intelliflow-core v2): Deterministic interceptor node evaluated at the LangGraph graph level before any LLM call. Implements SR 11-7 kill-switch mandate with fail-closed semantics (rule exceptions treated as failures), collect-all-failures audit payload, and self-documenting GovernanceRule contracts (required description field enforced at type level). Raises KillSwitchTriggered with full rule failure set and state snapshot for downstream WORM logging (Step 4).

### ClaimsFlow Kill-Switch — OFAC/SIU Sanctions Intercept

ClaimsFlow (intelliflow-claimsflow) provides a production-pattern implementation of KillSwitchGuard with real-world compliance semantics. The 4-node LangGraph workflow (intake → fraud_score → kill_switch_guard → adjudication) wires the guard as an edge interceptor between risk assessment and decision-making. GovernanceRule `sanctions_check` evaluates `fraud_flag` — set by an MCP-scoped `registry_lookup` tool checking OFAC/SIU sanctions registries. If the claimant is flagged, the workflow halts with KILL_SWITCH_TRIGGERED before adjudication can execute. This demonstrates the SR 11-7 kill-switch mandate in an agentic context: the guard is deterministic code (`lambda s: not s.fraud_flag`), the trigger is an external compliance signal (sanctions registry), and the halt is fail-closed with full audit payload.

### WORMLogRepository — v2 Implementation (intelliflow-core v2)

WORMLogRepository (intelliflow-core v2): HMAC-SHA256 hash-chained audit log with SQLite-enforced Write-Once immutability. Logs KILL_SWITCH_TRIGGERED events with full GovernanceRule failure list and state snapshot. Fail-closed: WORMStorageError halts workflow if log write fails — no unlogged AI decisions. Session-bounded trace_id enables complete workflow lifecycle reconstruction for SR 11-7 audit. Each log entry chains to the previous entry via HMAC-SHA256 with a KMS-ready secret key — without the key, the chain cannot be mathematically rewritten, providing non-repudiation against database-level tampering. SQLite BEFORE UPDATE/DELETE triggers enforce physical immutability independent of application code. 12 tests validate table creation, trigger enforcement, hash chain integrity, tamper detection, fail-closed behavior, and workflow integration.

### Relationship to v2 (Agentic)

The kill-switch mandate is a key factor in the v1 vs v2 architecture decision (documented in ADR_DETERMINISTIC_V1_VS_AGENTIC_V2.md). Agentic architectures cannot provide an equivalent kill-switch because the agent is the orchestrator — disabling the LLM disables the workflow. This is why v1 modules are not retrofitted with agentic patterns: the kill-switch capability is the regulatory value proposition, not a limitation.

---

## 6. Limitations — What the Deploying Institution Must Provide

IntelliFlow OS provides architecture patterns and controls. The following SR 11-7 requirements must be fulfilled by the deploying institution's model risk management function:

### 6.1 Independent Model Validation

SR 11-7 requires that model validation be performed by parties independent of model development. IntelliFlow OS provides:
- 276 automated ecosystem tests (253 platform-core + 23 ClaimsFlow)
- 150 documentation verification checks
- Deterministic decision paths that are inspectable

The deploying institution must:
- Assign an independent model validation team (or engage a third party)
- Conduct challenger model testing (compare LLM outputs against alternative approaches)
- Perform backtesting against historical data
- Document validation findings in a Model Validation Report

### 6.2 Ongoing Monitoring Program

IntelliFlow OS provides per-interaction audit logging and governance panels. The deploying institution must:
- Define monitoring thresholds (e.g., classification accuracy degradation triggers)
- Establish alerting for model performance metrics
- Conduct periodic model performance reviews (quarterly or as policy dictates)
- Document monitoring findings and remediation actions

### 6.3 Stress Testing

The platform includes chaos engineering (28 tests across both modules) for infrastructure failure scenarios. The deploying institution must:
- Conduct stress testing for model-specific failure modes (adversarial inputs, distribution shift, novel query patterns)
- Test model behavior under production load conditions
- Document stress test results and identify risk thresholds

### 6.4 Model Risk Governance Committee

SR 11-7 requires senior management oversight of model risk. The deploying institution must:
- Establish a Model Risk Governance Committee (or equivalent)
- Define model risk appetite and tolerance levels
- Review and approve model use cases before deployment
- Receive periodic reporting on model performance and risk metrics

### 6.5 Model Inventory and Tiering

IntelliFlow OS uses a single model (gpt-4o-mini) documented in VENDOR_COMPARISON.md. The deploying institution must:
- Register IntelliFlow OS in their enterprise model inventory
- Assign a model risk tier based on the institution's tiering methodology
- Define review cadence based on the assigned tier
- Track model versioning (Azure OpenAI model version updates)

### 6.6 Third-Party Model Risk

Azure OpenAI Service is a third-party model provider. The deploying institution must:
- Include Azure OpenAI in their third-party risk management program
- Review Microsoft's model cards and documentation
- Assess concentration risk (dependence on a single inference provider)
- Monitor for provider-initiated model changes (version deprecations, behavior changes)
- Maintain the ADR_MANAGED_INFERENCE_VS_SELF_HOSTED.md rationale as a living document

---

## 7. References

| Reference | Relevance |
|-----------|-----------|
| [SR 11-7: Guidance on Model Risk Management](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm) | Primary guidance. Issued April 2011 by the Federal Reserve Board and OCC. Establishes model risk management framework for supervised institutions. |
| [OCC Bulletin 2011-12: Sound Practices for Model Risk Management](https://www.occ.gov/news-issuances/bulletins/2011/bulletin-2011-12.html) | OCC companion to SR 11-7. Identical content, issued jointly. Applies to national banks and federal savings associations. |
| [NIST AI Risk Management Framework (AI RMF)](https://www.nist.gov/artificial-intelligence/risk-management-framework) | Complementary framework. GOVERN and MEASURE functions align with SR 11-7 governance and validation requirements. IntelliFlow OS maps to both. |
| [HIPAA Security Rule — Audit Controls (§164.312(b))](https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html) | Relevant to CareFlow. Audit trail requirements parallel SR 11-7 audit trail expectations in the healthcare context. |
| [EU AI Act — Article 9 (Risk Management System)](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) | European parallel to SR 11-7. Requires risk management for high-risk AI systems. IntelliFlow OS controls apply to both frameworks. |
| [ADR: Managed Inference vs. Self-Hosted](ADR_MANAGED_INFERENCE_VS_SELF_HOSTED.md) | Architecture decision documenting managed inference selection. Relevant to SR 11-7 third-party model risk assessment. |
| [ADR: Deterministic v1 vs. Agentic v2](ADR_DETERMINISTIC_V1_VS_AGENTIC_V2.md) | Architecture decision documenting kill-switch mandate and model risk separation. Directly addresses SR 11-7 override requirements. |

### Token FinOps Tracker — Operational Efficiency Evidence

SR 11-7 requires ongoing monitoring of model performance and operational efficiency.
IntelliFlow OS satisfies this with TokenLedgerRepository, an append-only financial
ledger that records every LLM invocation with immutable point-in-time cost data.

This enables:
- Cost trend monitoring — detect model cost drift across versions or time periods
- Per-module efficiency reporting — identify which workflows consume disproportionate token budget
- PTU capacity justification — persistent consumption baselines support the business case for Provisioned Throughput Unit commitments to model validators

Token tracking is treated as double-entry accounting, not telemetry. The cost_usd
column stores the calculated USD value at write time — pricing changes cannot alter
historical records. This satisfies the SR 11-7 requirement for model monitoring data
to reflect conditions at the time of operation, not retroactively adjusted values.

---

*Apache 2.0 — Copyright 2025-2026 Kaizen Works, LLC*

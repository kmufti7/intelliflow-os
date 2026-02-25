# SLO / SLA Statement

## Executive Summary

IntelliFlow OS is a production-grade reference architecture — not a managed SaaS product. The service-level objectives (SLOs) documented here are **design targets validated through testing**, not contractual service-level agreements (SLAs). These targets demonstrate that the platform is architected for enterprise-grade reliability. Binding SLAs are established between the operator and their customers based on the operator's infrastructure, deployment configuration, and operational practices.

---

## Service Availability Targets

IntelliFlow OS is designed for high availability through architectural separation of concerns. Each component can fail independently without cascading failure to the rest of the system.

| Component | Design Target | Failure Behavior | Evidence |
|-----------|--------------|------------------|----------|
| Local FAISS vector index (PHI) | Available whenever host is running | No external dependency — runs in-process | Zero network hops for PHI retrieval |
| Pinecone cloud (guidelines) | Subject to Pinecone SLA | Graceful fallback: guideline retrieval returns cached or empty results | Chaos mode validates this path |
| Azure OpenAI Service (LLM) | Subject to Azure SLA | Graceful fallback: structured error with audit log entry | Chaos mode validates this path |
| SQLite audit database | Available whenever host is running | No external dependency — local file storage | Write-ahead logging enabled |
| Streamlit UI | Available whenever host is running | Stateless process — restart recovers immediately | No session persistence required |

**Key design principle:** PHI-aware components (FAISS, SQLite) have no external dependencies. Cloud components (Pinecone, Azure OpenAI Service) are non-PHI paths with graceful degradation validated through chaos engineering.

> For chaos mode architecture and failure injection details, see [ARCHITECTURE.md](../../ARCHITECTURE.md) — Chaos Mode Flow section.

---

## Performance Targets

Performance targets are measured against the platform's reference deployment (single-node, local FAISS, Azure OpenAI GPT-4o-mini).

| Operation | Design Target | Bottleneck | Optimization |
|-----------|--------------|------------|-------------|
| Regex extraction (CareFlow) | < 50ms per patient | CPU-bound, local | Regex-first pattern eliminates LLM round-trip for structured data |
| FAISS vector search (local) | < 100ms per query | CPU-bound, in-process | No network latency — same-machine retrieval |
| Pinecone guideline retrieval | < 500ms per query | Network-bound (cloud) | De-identified concept queries only; cacheable |
| Azure OpenAI inference | 1–5s per request | Network + model latency | GPT-4o-mini (lower latency than GPT-4o; regex-first extraction reduces LLM calls) |
| End-to-end gap analysis (CareFlow) | < 10s per patient | LLM explanation generation | Regex extraction + deterministic gap computation complete in < 200ms; LLM formats explanation |
| Policy routing (SupportFlow) | < 200ms per query | CPU-bound, keyword matching | No vector search — deterministic keyword lookup against 60+ mappings |
| Audit log write | < 10ms per event | Local SQLite I/O | Pydantic validation + SQLite insert; no network dependency |

**What these targets assume:** Single-node deployment, local FAISS indexes, Azure OpenAI Service with standard throughput limits. Production deployments with higher concurrency requirements should benchmark against their specific infrastructure.

> For the 5-layer cost optimization architecture that underpins these targets, see [COST_MODEL.md](../../COST_MODEL.md).

---

## Compliance & Audit Commitments

IntelliFlow OS provides the infrastructure for compliance evidence. All commitments below are architectural capabilities — not certifications.

| Commitment | Implementation | Evidence |
|------------|---------------|----------|
| **Audit trail completeness** | Every decision, data access, LLM call, cost event, and chaos injection is logged via Pydantic-validated schemas | [OBSERVABILITY.md](../../OBSERVABILITY.md) |
| **Audit trail queryability** | NL Log Query tool enables natural language search against audit logs with SQL injection prevention | [TEST_STRATEGY.md](../../TEST_STRATEGY.md) |
| **PHI data residency** | Patient data never leaves local infrastructure; only de-identified concepts reach cloud services | [SECURITY_PRIVACY_OVERVIEW.md](SECURITY_PRIVACY_OVERVIEW.md) |
| **Schema enforcement** | All inputs and outputs pass through Pydantic v2 contracts before processing — no unvalidated data enters the pipeline | [DATA_DICTIONARY.md](../../DATA_DICTIONARY.md) |
| **Deterministic reasoning** | Gap detection and clinical decisions are computed by Python code, not LLM inference — auditable and reproducible | [GOVERNANCE.md](../../GOVERNANCE.md) |
| **Resilience validation** | Chaos mode injects failures (FAISS, Pinecone, database) and validates graceful fallback with audit logging | [ARCHITECTURE.md](../../ARCHITECTURE.md) |
| **Framework alignment** | Design patterns mapped to NIST AI RMF, OWASP LLM Top 10, EU AI Act record-keeping requirements | [GOVERNANCE.md](../../GOVERNANCE.md), [SECURITY.md](../../SECURITY.md) |
| **Kill-switch enforcement (v2)** | KillSwitchGuard evaluates GovernanceRule contracts before any LLM node. Fail-closed: rule evaluation errors are treated as failures — the system defaults to blocking. Structured WorkflowResult carries full failure list for audit. | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

**SLO trade-off — fail-closed kill-switch:** The fail-closed design means a misconfigured GovernanceRule blocks workflows rather than silently passing. This is an explicit trade-off: safety over availability. Operators must validate GovernanceRule logic before deployment. A rule that always raises an exception will halt every workflow. This is by design — in regulated environments, a false positive (blocked workflow) is recoverable, while a false negative (undetected governance violation) may not be.

**SLO trade-off — fail-closed WORM logger:** WORMStorageError halts workflow execution when the WORM audit log write fails (database locked, disk full, connection lost). This is the same fail-closed contract as KillSwitchGuard: a SQLite write failure degrades availability to protect compliance. Under SEC 17a-4 and SR 11-7, an unlogged AI decision is treated as a compliance violation. Operators must ensure database health before deployment. Explicit trade-off: compliance over availability.

**What "audit trail completeness" means:** The platform logs every operation that touches data, makes a decision, or incurs cost. It does not guarantee that the operator's surrounding infrastructure (network logs, IAM events, OS-level access) is similarly instrumented. End-to-end audit coverage is a shared responsibility.

---

## Customer Responsibilities

IntelliFlow OS provides the governance architecture. The operator is responsible for production infrastructure, certifications, and contractual obligations.

| Responsibility | Platform Provides | Customer (Operator) Provides |
|----------------|-------------------|------------------------------|
| Application-level audit trails | ✅ Pydantic schemas, SQLite logging, NL query tool | Infrastructure-level logging (network, IAM, OS) |
| PHI data residency architecture | ✅ Local FAISS, de-identified cloud queries | Physical/network isolation, encryption at rest |
| Deterministic reasoning gates | ✅ Code-based decisions, no LLM gap detection | Validation of clinical accuracy for their population |
| Cost tracking and controls | ✅ 5-layer optimization, per-interaction tracking | Azure spend limits, budget alerts |
| Chaos engineering / resilience testing | ✅ Failure injection, graceful fallback, audit-logged | Production load testing, capacity planning |
| BAA execution with Azure | — | ✅ Customer executes BAA with Microsoft directly |
| SOC 2 certification | Platform provides structured audit evidence | ✅ Customer pursues certification with auditor |
| Penetration testing | Platform follows OWASP LLM Top 10 patterns | ✅ Customer engages qualified pen testing firm |
| Network security (VPC, private endpoints) | Platform supports VPC deployment patterns | ✅ Customer configures network isolation |
| Access control (RBAC) | Roadmap | ✅ Customer implements access controls until platform RBAC ships |
| Uptime SLAs to end users | Platform provides resilience architecture | ✅ Customer defines and commits to SLAs based on their deployment |
| Incident response | Platform provides audit evidence and failure logging | ✅ Customer operates incident response process |

**Key distinction:** IntelliFlow OS is a software platform, not a managed service. The platform provides the architectural patterns and evidence infrastructure. The operator is responsible for deployment, operations, and any SLA commitments made to their own customers.

---

## Exclusions & Limitations

### What Is Not Covered

- **Third-party service outages.** Azure OpenAI Service and Pinecone availability are governed by their respective SLAs. IntelliFlow OS validates graceful degradation through chaos engineering but cannot guarantee third-party uptime.
- **Infrastructure failures.** Host machine failures, disk corruption, network partitions, and power loss are outside platform scope. The platform assumes the operator provisions reliable infrastructure.
- **Data accuracy.** The platform enforces schema validation and deterministic reasoning. It does not guarantee the clinical accuracy of medical guidelines, policy documents, or other reference data loaded by the operator.
- **Regulatory compliance.** HIPAA-aligned design patterns are architectural demonstrations. Legal compliance is determined by the operator's full deployment environment, policies, certifications, and BAA coverage.
- **Scale beyond reference deployment.** Performance targets are validated on single-node deployments. Multi-node, high-concurrency, or multi-tenant deployments require operator-led capacity planning and benchmarking.

### Synthetic Data Only

All platform demonstrations and test suites use synthetic patient data. No production PHI is included in any repository, test fixture, or reference implementation environment. Operators deploying with real PHI must provision their own infrastructure with appropriate safeguards, encryption, and access controls.

---

## Measurement & Reporting

### How Targets Are Validated

| Method | Scope | Frequency |
|--------|-------|-----------|
| **Automated test suite** | 276 ecosystem tests (253 platform-core + 23 ClaimsFlow) covering extraction, reasoning, routing, chaos, PHI safety, FHIR, schema validation, fraud score, Kill-Switch intercept | Every commit via GitHub Actions CI |
| **Chaos mode testing** | Failure injection for FAISS, Pinecone, and database components with graceful fallback verification | On-demand via Streamlit UI toggle; validated in test suite |
| **Enterprise docs verification** | 150 automated checks across 18 enterprise documents for consistency, accuracy, and completeness | On-demand via `verify_enterprise_docs.py`; 15-check cascade verification via `verify_cascade.py` |
| **Cost tracking** | Per-interaction token usage and cost attribution logged via Pydantic schemas | Every LLM call; aggregated in audit logs |

### What the Platform Does Not Measure

- **Production uptime.** The platform does not include a status page, uptime monitor, or SLA tracking dashboard. Operators should integrate with their existing monitoring infrastructure (Datadog, PagerDuty, Grafana, etc.).
- **End-user response times.** The platform logs LLM latency and extraction times in audit records. End-to-end response time measurement (including network, load balancer, and UI rendering) is an operator responsibility.
- **Incident metrics (MTTR, MTTD).** The platform provides audit trails and failure logs. Incident tracking, mean-time-to-recovery, and mean-time-to-detect are measured by the operator's incident management process.

> For the full observability architecture, see [OBSERVABILITY.md](../../OBSERVABILITY.md). For the testing philosophy and coverage details, see [TEST_STRATEGY.md](../../TEST_STRATEGY.md).

---

*Apache 2.0 — Copyright 2025-2026 Kaizen Works, LLC*

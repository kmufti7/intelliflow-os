# Product Roadmap

## Executive Summary

IntelliFlow OS is a governance-first AI platform for regulated industries, built on the principle that deployability matters more than capability. The roadmap prioritizes operator control, compliance infrastructure, and production hardening — not feature expansion for its own sake.

---

## Now (v1.0 — Current Release)

v1.0 is the foundation: two production-ready modules, a shared governance SDK, and enterprise documentation that maps to real compliance frameworks.

| Category | What's Live |
|----------|-------------|
| **Modules** | SupportFlow (banking) + CareFlow (healthcare) + ClaimsFlow (insurance — LangGraph-native, OFAC/SIU Kill-Switch, SPOG dashboard) |
| **Stories** | 13 stories (A–M) built and cascaded across platform |
| **Tests** | 276 total ecosystem (253 platform-core + 23 ClaimsFlow) across 5 repositories |
| **Enterprise Evidence Pack** | 27 documents (19 original + 8 PRDs) mapped to NIST AI RMF, OWASP LLM Top 10, EU AI Act, SR 11-7 |
| **Developer Tools** | 3 tools: AI test generator, NL log query, scaffold generator |
| **SDK** | intelliflow-core — pip-installable shared governance SDK with 3 Pydantic contracts |
| **Verification** | 153 automated checks (enterprise docs) + 14-check cascade verification |
| **Deterministic Reasoning** | LLM extracts, code decides, LLM explains — no LLM authority over clinical or policy decisions |
| **Data Residency** | PHI stays local (FAISS). Only de-identified concepts reach cloud services (Pinecone) |
| **Chaos Engineering** | Failure injection for FAISS, Pinecone, and database with graceful fallback and audit logging |
| **FHIR Support** | FHIR R4 dual-mode ingestion (legacy clinic notes + structured Bundles, LOINC 4548-4) |
| **Cost Controls** | 5-layer optimization: regex-first extraction, structured outputs, model tiering, local FAISS, token tracking |

**Infrastructure:** Designed for deployment within existing sovereign Azure/AWS perimeters. Local FAISS for PHI. Pinecone for guidelines. SQLite for audit logs.

---

## Next (v1.1 — Near Term)

v1.1 focuses on operator control and enterprise integration. These are the capabilities most frequently requested during enterprise evaluation.

| Capability | Description | Why It Matters |
|------------|-------------|----------------|
| **Role-Based Access Control (RBAC)** | Operator-defined roles (admin, analyst, auditor) with permission boundaries for data access, configuration changes, and audit log visibility | Enterprise deployments require access segmentation. Current architecture supports single-operator mode; RBAC enables multi-user teams. |
| **Audit Log Export** | Structured export of audit trails to operator-managed systems (JSON, CSV) with configurable retention and filtering | Compliance teams need to ingest audit data into their existing SIEM/GRC tooling. Current SQLite storage is self-contained; export bridges the gap. |
| **Enterprise Connector (Jira or ServiceNow)** | Bidirectional integration with one enterprise workflow system for escalation routing, ticket creation, and status tracking | Regulated environments route escalations through existing workflow systems. Direct integration eliminates manual handoff between IntelliFlow OS and the operator's ticketing system. |

**What v1.1 does not include:** Multi-tenancy, horizontal scaling, or new domain modules. Scope is deliberately narrow — operator control infrastructure, not feature expansion.

---

## Later (v2.0 — Strategic)

v2.0 addresses production deployment at scale. These capabilities require architectural changes and are scoped for a major release.

| Capability | Description | Why It Matters |
|------------|-------------|----------------|
| **Infrastructure-as-Code (Helm / Terraform)** | Declarative deployment templates for Kubernetes (Helm) and cloud infrastructure (Terraform) with governance configuration baked in | Enterprise platform teams deploy via CI/CD pipelines, not manual setup. IaC templates reduce deployment friction and ensure governance configuration is version-controlled. |
| **Environment Separation** | Distinct configuration profiles for development, staging, and production with environment-specific secrets management and data isolation | Regulated deployments require environment separation for change management, testing, and audit trail integrity. Current single-environment design does not enforce this boundary. |
| **Admin Console UI** | Web-based operator dashboard for configuration management, user administration, audit log review, and system health monitoring | Operators need a management interface that does not require CLI access or direct database queries. The console consolidates operational tasks into a single governed surface. |

**What v2.0 does not include:** New AI capabilities, model fine-tuning, or autonomous agent behavior. The platform's value is in governance infrastructure, not AI novelty.

---

## Phase 3: v3.0 Capabilities Roadmap (Planned)

> Forward-looking roadmap. No capabilities in this section are currently implemented. Phase 3 represents deliberate engineering investments to deepen IntelliFlow OS's governance posture and operational maturity.

### Strategic Framing: The "Day 2 Operations" Mandate

Phase 1 and 2 proved IntelliFlow OS can govern AI deployment at the point of inception ("Day 1"). The 2026 enterprise market has shifted focus to "Day 2" operations: how do regulated institutions operate agents at scale without degradation, runaway costs, or compliance drift? Phase 3 addresses this directly across three capability tracks.

### Track 1 — Human-in-the-Loop Maker-Checker (Priority 1)

- **PRD:** PRD_HITL_MAKER_CHECKER.md
- **Pain point (CRO):** No enterprise will allow autonomous adjudication of high-value claims or transactions without dual-control mechanisms
- **Technical approach:** LangGraph persistent checkpointer + interrupt_before edge + SPOG Approvals Queue
- **Regulatory anchor:** OCC dual-control expectations, SR 11-7 ongoing model monitoring alignment
- **Interview answer:** "IntelliFlow OS v2.0 proved we can halt bad actors with a kill-switch. v3.0 introduces Maker-Checker state persistence — when the agent detects a high-variance scenario, it physically pauses, writes state to an escalation queue, and waits for a human underwriter to approve continuation."

### Track 2 — Continuous Evaluation Harness (Priority 2)

- **PRD:** PRD_CONTINUOUS_EVALS.md
- **Pain point (CRO/MLOps):** GenAI models degrade silently as vendor APIs update weights. SR 11-7 requires ongoing monitoring — v2.0 addresses conceptual soundness but not continuous post-deployment validation.
- **Technical approach:** intelliflow-evals repo, Golden Dataset (100 edge cases per module), nightly GitHub Actions, LLM-as-a-Judge scoring (Answer Relevance, Faithfulness, Policy Alignment)
- **Regulatory anchor:** SR 11-7 ongoing model monitoring (primary), NIST AI RMF Measure function alignment

### Track 3 — Edge SLM Routing (Priority 3)

- **PRD:** PRD_EDGE_SLM_ROUTING.md
- **Pain point (CFO/FinOps):** All inference routed to Azure OpenAI, including baseline PII extraction tasks that don't require frontier model reasoning. Unnecessary cost and data transmission risk.
- **Technical approach:** Deterministic SLM router — local Llama-3-8B for baseline tasks, Azure OpenAI GPT-4o reserved for complex reasoning. Token FinOps Tracker updated for local vs cloud cost split.
- **Regulatory anchor:** HIPAA minimum necessary principle alignment, data residency expectations

### Delivery Model: The "Heartbeat" Cadence

Phase 3 is delivered via monthly constrained engineering spikes (~50 lines of code per month). Each spike:
- Advances one track incrementally
- Generates authentic, code-backed content for LinkedIn
- Keeps GitHub commit graph active without full-time engineering commitment
- Produces a demonstrable artifact for portfolio and interview evidence

Phase 3 does not have a fixed completion date. Tracks are prioritized by interview demand and enterprise market signals.

---

## Guiding Principles

These principles govern every roadmap decision. Features that conflict with these principles are rejected regardless of market demand.

| Principle | What It Means in Practice |
|-----------|---------------------------|
| **Governance-first** | Every new feature ships with audit logging, cost tracking, and schema validation from day one. Governance is not retrofitted — it is a prerequisite for release. |
| **Deterministic reasoning** | LLMs extract data and format explanations. Deterministic code computes decisions. This boundary is non-negotiable — no roadmap item introduces LLM authority over clinical, financial, or compliance decisions. |
| **Compliance-aligned by design** | Architecture decisions are evaluated against NIST AI RMF, OWASP LLM Top 10, and EU AI Act requirements. Self-assessed alignment is documented; external certification is the operator's responsibility. |
| **Operator control** | The platform provides capabilities. The operator controls configuration, access, data, and SLA commitments. No feature bypasses operator authority or makes autonomous decisions on the operator's behalf. |
| **Transparency over capability** | The platform documents what it does, what it does not do, and where the operator's responsibility begins. Limitations are published, not hidden. |

---

## What We Don't Do

Transparency about boundaries is part of the governance posture. These are deliberate architectural constraints, not gaps to be filled.

| Constraint | Rationale |
|------------|-----------|
| **No PHI in cloud services** | Patient data never leaves local infrastructure. Only de-identified medical concepts reach cloud services. This is a structural guarantee enforced by architecture, not policy. No roadmap item changes this boundary. |
| **No LLM decision authority** | LLMs extract structured data and format human-readable explanations. Deterministic Python code computes all clinical, financial, and compliance decisions. The LLM never decides whether a care gap exists, whether a policy applies, or whether an escalation is warranted. |
| **No unchecked hallucinations** | Every LLM output passes through Pydantic schema validation before entering the pipeline. Structured outputs (enum classification, typed fields) constrain the response space. Free-text generation is limited to explanation formatting with dual citations (patient evidence + guideline evidence). |
| **No autonomous actions** | The platform does not send emails, create tickets, modify records, or take external actions without explicit operator configuration and approval. Automation is operator-initiated, not platform-initiated. |
| **No training on customer data** | The platform uses Azure OpenAI Service, which does not use customer data for model training under Microsoft's enterprise agreement. No roadmap item introduces model fine-tuning on operator data. |

---

*Apache 2.0 — Copyright 2025-2026 Kaizen Works, LLC*

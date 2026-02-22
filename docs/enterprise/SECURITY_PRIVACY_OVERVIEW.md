# Security & Privacy Overview

## Executive Summary

IntelliFlow OS is a production-grade reference architecture designed with privacy-first principles for regulated industries (healthcare, banking, insurance). Protected Health Information (PHI) never leaves local infrastructure — patient data resides in local FAISS vector indexes while public medical guidelines route to cloud storage. The platform implements deterministic validation gates (Pydantic schema enforcement, regex-first extraction, architecture-level data separation) to prevent unauthorized data exposure. All data access paths are audit-logged via structured governance schemas.

---

## Data Residency Model

IntelliFlow OS enforces data separation through architecture, not policy. The two data stores are never mixed — this is a structural guarantee, not an operational one.

| Data Type | Storage | Location | PHI Present |
|-----------|---------|----------|-------------|
| Patient clinical notes | FAISS vector index | Local (never leaves machine) | Yes |
| Patient FHIR R4 bundles | FAISS vector index | Local (never leaves machine) | Yes |
| Medical guidelines (ADA, AHA) | Pinecone vector store | Cloud | No |
| Audit logs | SQLite database | Local | Metadata only |

**How it works:**

- **CareFlow (Healthcare):** Patient data is embedded and stored in a local FAISS index. When the system needs to retrieve clinical guidelines, a Concept Query Builder strips patient identifiers and sends only de-identified medical concepts (e.g., "A1C management guidelines") to Pinecone cloud. The two retrieval paths never intersect.

- **SupportFlow (Banking):** Uses keyword-based policy retrieval (60+ keywords mapped to 20 policies). No vector search, no FAISS. Customer interaction data stays in local SQLite audit logs.

> For the full data flow diagram, see [ARCHITECTURE.md](../../ARCHITECTURE.md) — Data Flow section.

---

## Privacy Design Patterns

### Regex-First Extraction
PHI fields (A1C values, blood pressure, patient identifiers) are parsed locally using regex patterns before any LLM call is made. This achieves 100% extraction accuracy on structured data at zero API cost — PHI is captured without ever sending raw clinical text to an external service.

### Schema Validation (Pydantic)
All inputs and outputs pass through Pydantic-enforced schemas before processing. The shared SDK (intelliflow-core) provides three validated contracts — `AuditEventSchema`, `CostTrackingSchema`, and `GovernanceLogEntry` — ensuring no malformed or unexpected data enters the pipeline.

### No Raw Patient Data in LLM Prompts
The deterministic reasoning pattern ("LLM extracts, code decides, LLM explains") means the LLM receives structured, pre-extracted facts — not raw patient notes. Gap detection is performed by deterministic Python code. The LLM's role is limited to formatting explanations with dual citations (patient evidence + guideline evidence).

### Audit Logging on All Data Access Paths
Every data access — patient retrieval, guideline lookup, LLM call, cost event, chaos injection — is logged via Pydantic-validated audit schemas. The NL Log Query developer tool enables natural language queries against these logs (e.g., "Show me all escalations from last week") with SQL injection prevention (column whitelist, 13 blocked keywords).

---

## Compliance Alignment

IntelliFlow OS is designed around established compliance frameworks. All alignments below are self-attested design patterns — not independent certifications.

| Framework | Alignment Level | Evidence |
|-----------|----------------|----------|
| **HIPAA** | HIPAA-aligned design patterns | PHI-aware data residency, audit trails, de-identification. Design patterns only — not a legal compliance certification. |
| **NIST AI RMF** | Self-attested alignment | GOVERN, MAP, MEASURE, MANAGE functions mapped in [GOVERNANCE.md](../../GOVERNANCE.md) |
| **OWASP LLM Top 10** | Self-attested mapping | All 10 risks mapped with implemented/planned controls in [SECURITY.md](../../SECURITY.md) |
| **EU AI Act** | Record-keeping alignment | Article 13 (transparency), Article 14 (human oversight), Article 15 (accuracy) addressed in [GOVERNANCE.md](../../GOVERNANCE.md) |

**What "HIPAA-aligned" means:** The platform implements architectural patterns consistent with HIPAA's Privacy and Security Rules — data residency controls, access logging, minimum necessary principle. It does not constitute a covered entity, does not execute BAAs, and is not independently audited for HIPAA compliance.

---

## Customer Responsibility Model

IntelliFlow OS provides the governance architecture. Production deployment requires customer-owned infrastructure and certifications.

| Responsibility | Platform Provides | Customer (Operator) |
|----------------|-------------------|---------------------|
| PHI data residency architecture | ✅ Local FAISS, de-identified cloud queries | |
| Audit trail infrastructure | ✅ Pydantic schemas, SQLite logging, NL query tool | |
| Deterministic reasoning gates | ✅ Code-based decisions, no LLM gap detection | |
| Cost tracking and controls | ✅ 5-layer optimization, per-interaction tracking | |
| Chaos engineering / resilience testing | ✅ Failure injection, graceful fallback, audit-logged | |
| BAA execution with Azure | | ✅ Customer executes with Microsoft |
| SOC 2 certification | | ✅ Platform provides audit evidence structure |
| Penetration testing | | ✅ Platform follows OWASP LLM Top 10 patterns |
| Network security (VPC, private endpoints) | | ✅ Platform supports VPC deployment |
| Access control (RBAC) | Roadmap | ✅ Until platform RBAC ships |
| Data classification policy | | ✅ Platform demonstrates separation patterns |

---

## Azure OpenAI Service Deployment

IntelliFlow OS is designed for **Azure OpenAI Service**, not the direct OpenAI API. This distinction matters for regulated deployments:

- **BAA eligibility:** Azure OpenAI Service is covered under Microsoft's HIPAA Business Associate Agreement. Direct OpenAI API is not.
- **Data boundary:** All inference data remains within the customer's Azure tenant boundary. No data crosses to OpenAI's infrastructure.
- **No training on customer data:** Under Microsoft's enterprise agreement, customer data sent to Azure OpenAI Service is not used for model training or improvement.
- **Model selection:** The platform targets Azure OpenAI GPT-4o-mini (~10x cheaper than GPT-4o) for cost-optimized inference while maintaining clinical accuracy.

> See [VENDOR_COMPARISON.md](../../VENDOR_COMPARISON.md) for the full model selection rationale and [COST_MODEL.md](../../COST_MODEL.md) for the 5-layer cost optimization architecture.

---

## What We Don't Claim

Transparency about limitations is part of the governance posture:

- **Not SOC 2 certified.** The platform provides structured audit logging, event schemas, and queryable governance trails that map to SOC 2 evidence requirements — but certification is a customer responsibility.
- **Not independently penetration tested.** The platform follows OWASP LLM Top 10 patterns and provides defense-in-depth controls — but formal pen testing is a customer responsibility.
- **Not a BAA counterparty.** The operator executes BAAs directly with Azure/Microsoft. IntelliFlow OS is a software platform, not a covered entity or business associate.
- **HIPAA-aligned means design patterns — not legal compliance certification.** The architecture demonstrates how to handle PHI responsibly. Legal compliance depends on the operator's full deployment environment, policies, and certifications.
- **No production PHI in reference implementation environments.** All demonstrations use synthetic patient data. Real PHI requires customer-provisioned infrastructure with appropriate safeguards.

---

*Apache 2.0 — Copyright 2025-2026 Kaizen Works, LLC*

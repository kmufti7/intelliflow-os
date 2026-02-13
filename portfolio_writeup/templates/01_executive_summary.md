# Executive Summary

## What Is IntelliFlow OS?

IntelliFlow OS is a **governance-first AI platform** for regulated industries. It demonstrates how to build AI systems that can survive compliance audits, explain their decisions, and operate within enterprise constraints.

The platform consists of:
- **Two production-ready modules**: SupportFlow (banking) and CareFlow (healthcare)
- **One shared SDK**: intelliflow-core (pip-installable Python package)
- **{{total_tests}} passing tests** across the platform ({{hand_written_tests}} hand-written + {{ai_generated_tests}} AI-generated edge-case tests)
- **CI/CD pipelines** via GitHub Actions

---

## The Core Thesis

> "In regulated industries, AI that can't explain itself can't be deployed."

Most AI demos optimize for capability. IntelliFlow OS optimizes for **deployability in environments where every decision must be auditable, every cost must be tracked, and every failure must be handled gracefully**.

---

## What Was Built

### SupportFlow — Banking AI Assistant
A multi-agent workflow system for banking customer support.

**Key Features:**
- **Multi-agent routing**: Messages classified (positive/negative/query) and routed to specialized handlers
- **Policy-grounded responses**: Every AI response cites the specific banking policy it's based on ({{sf_policies}} policies)
- **Chaos engineering**: Deterministic failure injection for resilience testing
- **Full audit trail**: Every decision logged with timestamp, confidence, and reasoning
- **Cost tracking**: Per-interaction token usage and cost attribution

**Tests:** {{supportflow_tests}}/{{supportflow_tests}} passing

### CareFlow — Healthcare AI Assistant
A clinical gap analysis engine that identifies care gaps for diabetic patients.

**Key Features:**
- **"LLM extracts, code decides"**: Regex-first extraction with LLM fallback, deterministic Python rules for gap detection
- **No hallucination in reasoning**: Clinical gap logic is pure Python, not LLM-generated
- **PHI-aware data residency**: Patient data stays in local FAISS; only de-identified concepts query external systems
- **FHIR R4 ingestion**: Structured data intake from HL7 FHIR Bundles (Patient + Observation resources, LOINC-coded)
- **Chaos engineering**: Deterministic failure injection (FAISS/Pinecone) with safe fallback and audit logging
- **Explicit "Therefore" statements**: Every gap has a human-readable reasoning chain
- **Guideline citations**: Every recommendation traces to a specific clinical guideline

**Tests:** {{careflow_tests}}/{{careflow_tests}} passing

### intelliflow-core — Shared SDK
A pip-installable Python package that both modules import.

**Provides:**
- `GovernanceUI`: Streamlit sidebar components for real-time audit trails
- `AuditEventSchema`, `CostTrackingSchema`: Pydantic contracts for compliance
- `Helpers`: Event ID generation, timestamp formatting, cost calculation

**Tests:** {{core_tests}}/{{core_tests}} passing

### AI Test Generator — Developer Tooling
A schema-aware test generator (`tools/ai_test_generator.py`) that reads Pydantic schemas from intelliflow-core and produces edge-case pytest suites automatically.

- Analyzes `AuditEventSchema`, `CostTrackingSchema`, and `GovernanceLogEntry`
- Generates {{ai_generated_tests}} tests covering: valid construction, missing required fields, boundary conditions (`ge=0`), optional field defaults
- Implements Tier 2 of the [Developer Experience Strategy](../DEVELOPER_EXPERIENCE_STRATEGY.md)

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Total tests passing | {{total_tests}} ({{hand_written_tests}} hand-written + {{ai_generated_tests}} AI-generated) |
| Repositories | {{repos}} |
| Domains demonstrated | 2 (Banking, Healthcare) |
| Banking policies | {{sf_policies}} |
| Clinical guidelines | {{cf_guidelines}} |
| Sample patients | {{cf_test_patients}} |
| Chaos failure modes | 7 (5 SupportFlow + 2 CareFlow) |
| Enterprise docs | {{enterprise_docs}} |
| Regex extraction success rate | 100% (on test patients) |

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.9+ |
| UI Framework | Streamlit |
| LLM Provider | OpenAI (GPT-4o-mini) |
| Vector Store (local) | FAISS |
| Vector Store (cloud) | Pinecone |
| Embeddings | text-embedding-3-small |
| Database | SQLite (async via aiosqlite) |
| Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio |
| CI/CD | GitHub Actions |

---

## What Makes This Different

### 1. Platform, Not Project
Both applications import shared components from `intelliflow-core`. This isn't copy-paste code — it's a real pip-installable SDK with its own test suite.

### 2. Governance-First Architecture
Every architectural decision prioritizes auditability:
- Every LLM call is logged with input/output summaries
- Every decision has a confidence score and reasoning
- Every cost is tracked to the interaction level
- Every failure is caught, logged, and handled gracefully

### 3. "LLM Extracts, Code Decides"
CareFlow solves the "Therefore problem" in healthcare AI:
- **BAD**: LLM computes clinical logic (may hallucinate)
- **GOOD**: LLM extracts facts → Python rules detect gaps → LLM explains with citations

### 4. PHI-Aware Design
CareFlow demonstrates HIPAA-informed patterns:
- Patient data stays in local FAISS (never leaves the machine)
- External queries receive only de-identified clinical concepts
- Concept Query Builder strips identifiers before any cloud query

### 5. Five-Layer Cost Optimization
LLM cost is reduced through architecture, not negotiation — five compounding layers: regex-first extraction (100% success, zero LLM tokens on structured data), structured outputs (enum classification, no parsing retries), gpt-4o-mini model selection (~10x cheaper than gpt-4o), local FAISS for PHI queries (zero cloud vector DB cost), and per-interaction token tracking visible in the governance panel.

### 6. Chaos Engineering Built-In
Both modules include deterministic failure injection:
- **SupportFlow**: 30% failure rate with 5 scenarios (timeouts, DB errors, rate limits)
- **CareFlow**: Toggled FAISS/Pinecone failures with safe fallback responses and audit logging
- {{chaos_tests_total}} chaos tests across the platform (13 SupportFlow + 15 CareFlow)

### 7. Enterprise Documentation Suite
{{enterprise_docs}} enterprise-grade documents covering architecture (Mermaid), security (OWASP LLM Top 10), governance (NIST AI RMF + EU AI Act), cost modeling, observability, data dictionary, vendor comparison, ethics, and test strategy. Validated by a {{verification_checks}}-check automated verification script.

### 8. AI-Native Developer Tooling
A schema-aware test generator reads Pydantic contracts from the shared SDK and produces edge-case pytest suites (35 tests). A companion [Developer Experience Strategy](../DEVELOPER_EXPERIENCE_STRATEGY.md) memo frames three tiers of AI-native tooling for internal platforms.

---

## Demo Videos

| Module | Link |
|--------|------|
| SupportFlow | [Watch Demo](https://youtu.be/7B6mBKlNL5k) |
| CareFlow | [Watch Demo](https://youtu.be/Ct9z91649kg) |

---

## Repositories

| Repo | Description | Link |
|------|-------------|------|
| intelliflow-os | Platform overview | [GitHub](https://github.com/kmufti7/intelliflow-os) |
| intelliflow-core | Shared SDK | [GitHub](https://github.com/kmufti7/intelliflow-core) |
| intelliflow-supportflow | Banking module | [GitHub](https://github.com/kmufti7/intelliflow-supportflow) |
| intelliflow-careflow | Healthcare module | [GitHub](https://github.com/kmufti7/intelliflow-careflow) |

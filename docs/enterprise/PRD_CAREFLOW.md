# PRD: CareFlow

**Status:** Launched
**Version:** 1.0
**Owner:** Kaizen Works, LLC
**Last Updated:** 2026-02-25

## Problem Statement

Clinical care management teams perform gap analysis manually — reviewing patient records against clinical guidelines to identify missed screenings, uncontrolled conditions, and follow-up gaps. This process is slow, inconsistent across reviewers, and produces audit trails that are difficult to reconstruct. For a CFO, the cost is staff hours spent on repeatable analytical work. For a CRO, the risk is inconsistent gap detection and PHI exposure if patient data flows through uncontrolled cloud services.

## Target User

- **Primary:** Clinical operations and care management teams performing patient gap analysis
- **Secondary:** Compliance officers validating PHI data handling, quality officers auditing gap detection consistency

## Goals

1. Deterministic gap detection — code computes gaps, LLM formats explanations. Zero hallucinated clinical recommendations.
2. PHI-aware data residency — patient data never leaves local compute. Clinical guidelines stored separately in cloud vector store.
3. FHIR R4 dual-mode ingestion — accept both legacy clinic notes and FHIR R4 Bundles through a unified adapter pattern.
4. Regex-first extraction with 100% success rate on structured clinical data — LLM fallback exists but rarely triggers.
5. All 84 CareFlow tests passing across 7 test categories.

## Non-Goals

- **Not a clinical decision support system.** CareFlow identifies gaps in care documentation — it does not recommend treatments or diagnoses.
- **Not a certified EHR module.** CareFlow is a reference implementation demonstrating governance patterns for clinical AI, not an ONC-certified health IT module.
- **Not a production FHIR server.** FHIR R4 ingestion is read-only (Bundle → extraction). CareFlow does not write back to FHIR endpoints.
- **Not an LLM-powered reasoner.** The LLM does not decide whether a care gap exists. Deterministic Python code compares extracted values against guideline thresholds.

## Solution Overview

CareFlow implements a "LLM extracts, code decides, LLM explains" pipeline for clinical gap analysis. Patient records are processed through regex-first extraction (100% accuracy on structured data, LLM fallback available but never triggered in testing). Extracted clinical values feed deterministic Python rules that compute gap status against clinical guideline thresholds (e.g., A1C 8.2 > 7.0 = gap detected). The LLM's role is formatting — converting structured gap results into natural language explanations with patient evidence and guideline citations.

**PHI-aware dual-store architecture:** Patient data stays in local FAISS indexes (never leaves the machine). Clinical guidelines are stored in Pinecone cloud vector store. A Concept Query Builder strips patient identifiers before any external call. Two deployment modes: local-only (FAISS for both) and enterprise (FAISS local + Pinecone cloud).

**FHIR dual-mode ingestion:** An adapter pattern accepts both legacy clinic notes and FHIR R4 Bundles (Patient + Observation resources, LOINC 4548-4 coding). Both paths produce the same extraction output, enabling gradual migration from legacy to FHIR without code changes.

## Key Features

- **Regex-first extraction:** 100% success rate on structured clinical data. Zero LLM tokens spent on data that regex handles. LLM fallback exists but never triggered in testing.
- **Deterministic gap detection:** 3 gap types with severity tiers. Python code compares extracted values against guideline thresholds — no LLM in the decision path.
- **PHI-aware data residency:** Patient data in local FAISS. Guidelines in Pinecone cloud. Concept Query Builder de-identifies queries before external calls.
- **FHIR R4 dual-mode ingestion:** Adapter pattern — legacy clinic notes and FHIR R4 Bundles (Patient + Observation, LOINC 4548-4) produce identical extraction output.
- **Chaos engineering:** FAISS and Pinecone failure injection via sidebar toggle. Graceful fallback with safe clinical disclaimer. Audit-logged failure events.
- **WORM audit logging:** Every analysis logged to append-only store with HMAC integrity verification.
- **Semantic guideline search:** FAISS vector search using text-embedding-3-small for clinical guideline retrieval.

## Compliance Alignment

- **HIPAA-aligned design patterns:** PHI-aware data residency ensures patient data remains in local compute. De-identification layer strips identifiers before any external API call. Note: Pinecone HIPAA compliance depends on enterprise agreement, BAA execution with Pinecone, and deployment controls — not assumed by default.
- **ONC HTI-1 and CMS Interoperability and Prior Authorization Rule:** These certification programs reference FHIR R4 as the interoperability standard for applicable programs. CareFlow's dual-mode ingestion aligns to this direction.
- **SR 11-7 (Model Risk Management):** Clinical reasoning is deterministic — model risk is bounded to extraction and explanation, not decision-making.
- **NIST AI RMF:** GOVERN (PHI residency controls), MAP (extraction accuracy measurement), MEASURE (gap detection consistency), MANAGE (chaos engineering for failure modes).

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| intelliflow-core | v1 | Shared SDK — Pydantic contracts, WORM logger, token tracker |
| Azure OpenAI Service | gpt-4o-mini | LLM extraction fallback and explanation generation |
| Azure OpenAI Service | text-embedding-3-small | Guideline embedding for FAISS vector search |
| FAISS | latest | Local vector store for PHI patient data and guideline search |
| Pinecone | latest | Cloud vector store for clinical guidelines (enterprise mode) |
| SQLite | 3.x | WORM audit log backend |
| Streamlit | 1.x | UI and chaos mode toggle |

## Success Metrics (At Launch)

| Metric | Value |
|--------|-------|
| Tests passing | 84/84 (81 original + 3 integration) |
| Test categories | 7 |
| Regex extraction accuracy | 100% on structured clinical data |
| LLM fallback trigger rate | 0% (never triggered in testing) |
| Gap types | 3 with severity tiers |
| FHIR support | R4 Bundle (Patient + Observation), LOINC 4548-4 |
| PHI data residency | Local FAISS only — never transmitted externally |

## Open Questions / Known Gaps

1. **Guideline corpus freshness.** Gap detection accuracy depends on the clinical guideline corpus being current. No automated guideline update pipeline exists.
2. **Limited gap types.** 3 gap types with severity tiers cover the reference implementation scope. Production deployment would require institution-specific clinical rules.
3. **Regex extraction scope.** 100% accuracy on structured clinical data in test patients. Unstructured narrative notes may require LLM extraction path, which is implemented but lightly tested.
4. **Single-tenant.** No multi-tenant isolation. Production deployment would require patient-scoped data partitioning and role-based access controls.
5. **Pinecone BAA.** HIPAA compliance for the cloud vector store path requires BAA execution with Pinecone and institution-specific deployment controls.

## Related ADRs

- ADR-001: Deterministic Reasoning ("LLM extracts, code decides, LLM explains")
- ADR-002: PHI-Aware Data Residency (local FAISS + Pinecone cloud split)
- ADR-004: Cost Optimization — 5 Layers (regex-first as Layer 1)
- ADR-005: Chaos Engineering as First-Class Feature
- ADR-006: "Tests That Lie" — Integration Test Principle
- ADR-008: FHIR Dual-Mode Ingestion
- ADR-025: Deterministic v1 vs Agentic v2 (CareFlow is v1 architecture)
- ADR-026: Managed Inference vs Self-Hosted (Pinecone HIPAA scoping)

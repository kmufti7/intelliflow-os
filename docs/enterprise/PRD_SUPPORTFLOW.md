# PRD: SupportFlow

**Status:** Launched
**Version:** 1.0
**Owner:** Kaizen Works, LLC
**Last Updated:** 2026-02-25

## Problem Statement

Retail banking customer support operations face a fundamental tension: LLMs generate fluent, confident responses — but in a regulated environment, an uncontrolled LLM can fabricate policy details, omit required disclosures, or contradict institutional guidance. The cost of a wrong answer in banking is not a bad CSAT score — it is regulatory exposure. CROs need assurance that every customer-facing response is grounded in approved policy language. CFOs need cost predictability per interaction, not open-ended API spend.

## Target User

- **Primary:** Retail banking customer support operations teams
- **Secondary:** Compliance officers responsible for response audit, risk managers validating policy adherence

## Goals

1. Every customer-facing response cites the source banking policy by name — zero uncited responses
2. Deterministic routing: customer intent mapped to policy via keyword matching, not LLM classification
3. Per-interaction cost attribution across 7 LLM pricing tiers — visible in governance panel
4. Chaos engineering: graceful degradation under infrastructure failure, auditable failure modes
5. All 13 SupportFlow tests passing, including chaos and integration tests

## Non-Goals

- **Not a production call center deployment.** SupportFlow is a reference implementation demonstrating governance patterns, not a turnkey support product.
- **Not a vector search system.** SupportFlow uses deterministic keyword-based policy retrieval (60+ keywords → 20 policies). It does not use FAISS, embeddings, or any vector similarity search.
- **Not an autonomous agent.** The LLM does not decide which policy applies or whether the answer is correct. Code decides, LLM explains.
- **Not a policy authoring tool.** The policy corpus is static and requires manual updates when institutional policies change.

## Solution Overview

SupportFlow implements a "LLM explains, code decides" architecture for banking customer support. A multi-agent orchestrator classifies customer messages via deterministic keyword matching (60+ keywords mapped to 20 banking policies), routes to specialized handlers, and generates responses grounded in the matched policy with explicit citations.

The LLM's role is translation — converting structured policy content into natural language responses — not decision-making. Every response includes the policy name, relevant section, and a per-interaction cost record.

**Architecture pattern:** Deterministic orchestration with LLM translation layer. Single entry point (orchestrator) ensures all paths hit chaos checks and governance logging.

## Key Features

- **Deterministic policy routing:** 60+ keywords → 20 banking policies. No LLM classification in the routing path.
- **Citation gating:** Every response cites the source policy by name. Uncited responses are blocked.
- **7-tier cost attribution:** Per-interaction cost tracking across 7 LLM pricing tiers, visible in governance panel.
- **Chaos engineering:** Sidebar toggle for failure injection (database, vector store). Graceful fallback with audit-logged failure events. 5 failure types, 30% injection rate.
- **WORM audit logging:** Every interaction logged to append-only store with HMAC integrity verification.
- **Single entry point architecture:** All user interactions route through the orchestrator — no front-door bypass.

## Compliance Alignment

- **SR 11-7 (Model Risk Management):** LLM outputs are constrained to policy-grounded translation. Model risk is bounded by the deterministic routing layer — the LLM cannot select policies or override routing decisions.
- **OCC Guidance on Third-Party Risk:** Azure OpenAI Service used as managed inference provider. Token-level cost tracking enables vendor cost governance.
- **NIST AI RMF:** GOVERN (policy-grounded responses), MAP (deterministic routing classification), MEASURE (per-interaction cost and audit trail), MANAGE (chaos engineering for failure mode testing).

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| intelliflow-core | v1 | Shared SDK — Pydantic contracts, WORM logger, token tracker |
| Azure OpenAI Service | gpt-4o-mini | LLM translation layer |
| SQLite | 3.x | WORM audit log backend |
| Streamlit | 1.x | UI and chaos mode toggle |

## Success Metrics (At Launch)

| Metric | Value |
|--------|-------|
| Tests passing | 13/13 |
| Policy retrieval method | Keyword-based (60+ keywords → 20 policies) |
| Citation rate | 100% (gated — uncited responses blocked) |
| Chaos test coverage | 5 failure types, integration-tested |
| Cost attribution | Per-interaction, 7 pricing tiers |

## Open Questions / Known Gaps

1. **Static policy corpus.** Banking policies require manual updates when institutional guidance changes. No automated policy ingestion pipeline exists.
2. **Keyword coverage.** 60+ keywords cover common retail banking intents. Edge-case intents outside keyword coverage fall back to a generic response — not a policy-grounded one.
3. **Single-tenant.** No multi-tenant isolation. Production deployment would require tenant-scoped policy corpora and access controls.
4. **English only.** No multilingual support for policy retrieval or response generation.

## Related ADRs

- ADR-001: Deterministic Reasoning ("LLM extracts, code decides, LLM explains")
- ADR-005: Chaos Engineering as First-Class Feature
- ADR-006: "Tests That Lie" — Integration Test Principle
- ADR-016: Enterprise Evidence Pack
- ADR-025: Deterministic v1 vs Agentic v2 (SupportFlow is v1 architecture)

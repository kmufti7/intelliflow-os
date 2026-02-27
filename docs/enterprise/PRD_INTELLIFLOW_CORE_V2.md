# PRD: IntelliFlow Core v2 — Governed Agentic Runtime SDK

**Status:** Launched
**Version:** 2.0
**Owner:** Kaizen Works, LLC
**Last Updated:** 2026-02-25

## Problem Statement

Agentic AI systems — multi-step, tool-using, autonomous workflows — are entering regulated industries (banking, insurance, healthcare) without production-grade governance primitives. Existing LLM frameworks optimize for capability (tool use, chain-of-thought, agent loops) but treat governance as an afterthought: logging is optional, cost tracking is external, kill-switches do not exist, and tool access is ungoverned. For a CRO, this means deploying autonomous agents with no intervention mechanism. For a CFO, this means AI cost attribution that requires post-hoc forensics instead of per-step receipts.

The industry needs a governed agentic runtime — a shared SDK where governance primitives (kill-switches, WORM audit logs, cost tracking, tool registries) are embedded in the runtime, not bolted on by each consuming application.

## Target User

- **Primary:** Platform engineers and AI architects building agentic AI applications for regulated industries
- **Secondary:** Compliance engineers validating governance primitive integration, DevOps teams deploying governed AI workflows

## Goals

1. Provide 5 governance primitives as a pip-installable SDK: workflow engine, kill-switch, tool registry, WORM logger, token tracker
2. Strangler Fig migration: v2 coexists with v1 — zero disruption to existing SupportFlow and CareFlow consumers
3. Fail-closed kill-switch with collect-all evaluation — every governance rule fires before any decision
4. Tamper-evident audit trail with HMAC-SHA256 hash chain, KMS-ready key management
5. 253 platform-core tests passing (v1 + v2 combined)

## Non-Goals

- **Not a LangGraph replacement.** intelliflow-core v2 wraps LangGraph with governance primitives — it does not replace LangGraph's orchestration capabilities.
- **Not a distributed runtime.** Single-node execution. MCP Tool Registry is local — no distributed registry, no cross-node tool resolution.
- **Not a cloud service.** SDK is a Python library consumed via pip install. No hosted runtime, no SaaS offering, no managed service.
- **Not backwards-breaking.** v1 APIs remain untouched. v2 is additive via Strangler Fig pattern — consuming applications choose which version to import.

## Solution Overview

IntelliFlow Core v2 is a governed agentic runtime SDK providing 5 components that embed governance into the agentic workflow execution path:

### 1. LangGraph Workflow Engine
Agentic orchestration built on LangGraph 1.0.9. State-machine-based workflow definition with typed state objects. Each node is independently testable, audit-logged, and cost-tracked.

### 2. Kill-Switch Guard
Fail-closed governance interceptor. Evaluates all registered governance rules using a collect-all pattern — every rule fires, results are aggregated, and any trigger blocks the workflow. If the guard cannot evaluate (error, timeout, missing data), the workflow is blocked. Designed for the inverse of typical fail-open patterns.

### 3. MCP Tool Registry
Governed tool registration and invocation via Model Context Protocol. Tools are registered with schema validation (JSON Schema). Each workflow node sees only the tools it is authorized to invoke — dynamic scoping prevents tool sprawl.

### 4. WORM Logger
Append-only audit log with HMAC-SHA256 hash chain integrity. Each entry references the previous entry's hash, creating a tamper-evident chain. SQLite backend with KMS-ready key management interface. Aligned to SEC 17a-4 non-rewritable record patterns.

### 5. Token FinOps Tracker
Per-invocation cost attribution with immutable receipt pattern. cost_usd captured at write time using point-in-time pricing — immune to pricing drift. Supports 7 LLM pricing tiers. Enables chargeback and FinOps reporting without post-hoc cost reconstruction.

**Migration pattern:** Strangler Fig — v1 (deterministic orchestration for SupportFlow/CareFlow) and v2 (agentic runtime for ClaimsFlow) coexist in the same package. Consuming applications import from the version they need. No breaking changes to v1 APIs.

## Key Features

- **5 governance primitives:** Workflow engine, kill-switch guard, MCP tool registry, WORM logger, token FinOps tracker — all pip-installable as a single SDK
- **Fail-closed kill-switch:** Collect-all evaluation, any-trigger-blocks, error-blocks. The safe default is "stop," not "continue."
- **HMAC-SHA256 hash chain:** Tamper-evident audit trail. Each log entry references previous entry's hash. KMS-ready key interface.
- **Immutable cost receipts:** cost_usd at write time, point-in-time pricing, 7 LLM pricing tiers. No retroactive cost adjustment.
- **MCP dynamic tool scoping:** Per-node tool authorization. Schema-validated tool registration. Prevents unauthorized tool invocation.
- **Strangler Fig coexistence:** v1 and v2 in same package. Zero disruption to existing consumers. Python >= 3.10 for v2 features.
- **3 Pydantic contracts:** Shared data contracts between SDK and consuming applications. Schema-aware tooling (AI test generator reads these contracts).

## Compliance Alignment

- **SR 11-7 (Model Risk Management):** Kill-switch provides ongoing monitoring and intervention hooks. WORM logger provides model output audit trail. Token tracker enables model cost governance.
- **SEC 17a-4 (Non-rewritable records):** WORM logger with HMAC-SHA256 hash chain aligned to non-rewritable record patterns. Append-only, tamper-evident, hash-chain-verifiable.
- **EU AI Act (Record-keeping):** Article 12 record-keeping requirements aligned via WORM logger (system behavior logs) and token tracker (resource usage records).
- **NIST AI RMF:** GOVERN (kill-switch rules, tool registry governance), MAP (workflow state classification), MEASURE (token tracking, cost attribution), MANAGE (WORM audit trail, SPOG visibility).

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| LangGraph | 1.0.9 | Agentic workflow orchestration (v2) |
| Azure OpenAI Service | gpt-4o-mini | Default LLM for consuming applications |
| SQLite | 3.x | WORM audit log and token ledger backend |
| FAISS | latest | Local vector store (v1 consumers) |
| Pinecone | latest | Cloud vector store — enterprise mode (v1 consumers) |
| Pydantic | 2.x | Data contracts and schema validation |
| Python | >= 3.10 | Required for v2 (type union syntax, match statements) |

## Success Metrics (At Launch)

| Metric | Value |
|--------|-------|
| Platform-core tests passing | 253 (193 v1 legacy + 60 v2 LangGraph) |
| Governance primitives | 5 (workflow engine, kill-switch, tool registry, WORM logger, token tracker) |
| Pydantic contracts | 3 shared data contracts |
| SDK consumers | 3 (SupportFlow v1, CareFlow v1, ClaimsFlow v2) |
| Kill-switch behavior | Fail-closed, collect-all evaluation |
| WORM integrity | HMAC-SHA256 hash chain, KMS-ready |
| Migration pattern | Strangler Fig — v1 untouched, v2 coexists |

## Open Questions / Known Gaps

1. **DLM policy owned by deploying institution.** Data lifecycle management (retention periods, purge schedules, archival) is defined by the deploying institution, not by the SDK. See ADR-028.
2. **Single-node MCP Registry.** Tool registry is local to the process. No distributed registry, no cross-service tool resolution. Production multi-service deployments would need a centralized registry or service mesh integration.
3. **SQLite backend limits.** WORM logger and token ledger use SQLite. Production deployments at scale would need migration to PostgreSQL or similar — the WORM interface is backend-agnostic but only SQLite is implemented.
4. **KMS integration interface only.** HMAC key management exposes a KMS-ready interface but does not integrate with a specific KMS provider (AWS KMS, Azure Key Vault, etc.). Production deployment requires KMS provider binding.
5. **No SDK versioning policy.** v1/v2 coexistence is managed via Strangler Fig, but no formal deprecation timeline or API stability guarantees are published.

## Related ADRs

- ADR-025: Deterministic v1 vs Agentic v2 (Strangler Fig migration pattern)
- ADR-026: ClaimsFlow Agentic Claims Processing (primary v2 consumer)
- ADR-027: Executive SPOG Dashboard (visibility layer for v2 governance data)
- ADR-028: Data Lifecycle Management (DLM policy delegation)

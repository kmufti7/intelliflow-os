# PRD: ClaimsFlow

**Status:** Launched
**Version:** 1.0
**Owner:** Kaizen Works, LLC
**Last Updated:** 2026-02-25

## Problem Statement

Insurance claims processing is moving toward autonomous adjudication — LLM-powered agents that intake, score, and decide claims without human intervention. For a CRO, the risk is an autonomous agent approving a sanctions-flagged claim or adjudicating without audit trail. For a CFO, the cost is regulatory penalties from claims processed outside governance controls. The industry needs a pattern for agentic claims processing where governance primitives (kill-switches, audit logs, cost tracking) are embedded in the workflow — not bolted on after deployment.

## Target User

- **Primary:** Insurance claims operations teams managing adjudication workflows
- **Secondary:** Compliance officers responsible for sanctions screening, risk managers validating kill-switch behavior

## Goals

1. Agentic claims workflow with embedded governance — kill-switch intercepts sanctions-flagged claims before adjudication
2. Fail-closed kill-switch: blocked claims do not proceed to adjudication under any circumstances
3. Full audit trail: every workflow step logged to WORM store with per-step cost attribution
4. SDK consumer pattern: demonstrate intelliflow-core v2 consumption via pip install
5. All 23 ClaimsFlow tests passing

## Non-Goals

- **Not a production claims adjudication engine.** Adjudication logic is illustrative — production deployment requires institution-specific rules engines, actuarial models, and regulatory compliance specific to the jurisdiction.
- **Not a sanctions screening service.** OFAC/SIU flag evaluation is a boolean check on a pre-computed field. ClaimsFlow does not perform real-time sanctions list lookups.
- **Not a replacement for human adjusters.** The kill-switch pattern demonstrates where human oversight intersects agentic processing — it does not eliminate human review.
- **Not a multi-carrier platform.** Single-tenant, single-line-of-business reference implementation.

## Solution Overview

ClaimsFlow implements a 4-node LangGraph workflow for agentic insurance claims processing with embedded governance primitives:

```
Intake → Fraud Score → Kill-Switch Guard → Adjudication
```

**Intake** normalizes the claim and validates required fields. **Fraud Score** evaluates risk indicators and sets a fraud_flag. **Kill-Switch Guard** evaluates all governance rules (OFAC sanctions, SIU flags) using a collect-all pattern — every rule fires, results are aggregated, and any trigger blocks the claim. **Adjudication** runs only if the kill-switch passes.

The kill-switch is fail-closed: if the guard cannot evaluate (error, timeout, missing data), the claim is blocked. This is the inverse of typical fail-open patterns that prioritize throughput over compliance.

**SDK consumer pattern:** ClaimsFlow consumes intelliflow-core v2 via `pip install -e ../intelliflow-core`, demonstrating the governed agentic runtime as a reusable foundation.

## Key Features

- **4-node LangGraph workflow:** Intake → Fraud Score → Kill-Switch Guard → Adjudication. Each node is independently testable and audit-logged.
- **OFAC/SIU Kill-Switch:** Fail-closed interceptor. Collect-all evaluation pattern — every governance rule fires before decision. Any trigger blocks the claim.
- **MCP dynamic tool scoping:** Tools registered via MCPRegistry with schema validation. Each workflow node sees only the tools it is authorized to invoke.
- **WORM audit logging:** Every workflow step logged to append-only store with HMAC-SHA256 hash chain integrity.
- **Token FinOps tracking:** Per-step cost attribution with immutable receipt pattern. cost_usd captured at write time.
- **SDK consumer pattern:** Demonstrates intelliflow-core v2 as a pip-installable governed runtime.

## Compliance Alignment

- **SR 11-7 (Model Risk Management):** Kill-switch provides ongoing monitoring and intervention capability. Agentic workflow decisions are bounded by governance rules, not open-ended LLM reasoning.
- **OFAC sanctions screening expectations:** Kill-switch evaluates sanctions flags before any adjudication step. Fail-closed design ensures sanctions-flagged claims cannot bypass review.
- **SEC 17a-4 (Non-rewritable records):** WORM logger with HMAC-SHA256 hash chain provides tamper-evident audit trail aligned to non-rewritable record expectations.
- **NIST AI RMF:** GOVERN (kill-switch governance rules), MAP (fraud scoring classification), MEASURE (per-step cost and audit trail), MANAGE (fail-closed intervention).

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| intelliflow-core | v2 | Governed agentic runtime — Kill-Switch Guard, MCP Registry, WORM Logger, Token FinOps |
| LangGraph | 1.0.9 | Agentic workflow orchestration |
| Azure OpenAI Service | gpt-4o-mini | LLM for intake normalization and adjudication explanation |
| SQLite | 3.x | WORM audit log backend |

## Success Metrics (At Launch)

| Metric | Value |
|--------|-------|
| Tests passing | 23/23 |
| Workflow nodes | 4 (intake, fraud_score, kill_switch_guard, adjudication) |
| Kill-switch behavior | Fail-closed — blocked claims do not proceed |
| Governance rule evaluation | Collect-all — every rule fires before decision |
| Audit coverage | 100% of workflow steps logged to WORM store |
| Cost attribution | Per-step, immutable receipt pattern |

## Open Questions / Known Gaps

1. **Illustrative adjudication logic.** The adjudication node demonstrates the pattern but does not implement production actuarial models or jurisdiction-specific rules. Production deployment requires institution-specific rules engine integration.
2. **Pre-computed fraud flags.** OFAC/SIU evaluation checks a boolean field set by the fraud scoring node. Real-time sanctions list lookup (OFAC SDN list, SIU databases) is not implemented.
3. **Single line of business.** ClaimsFlow covers a single claim type. Multi-LOB (auto, property, liability) would require claim-type-specific workflow variants.
4. **No appeals workflow.** Kill-switch-blocked claims have no automated appeal or manual review queue. Production deployment would need human-in-the-loop review for blocked claims.

## Related ADRs

- ADR-025: Deterministic v1 vs Agentic v2 (ClaimsFlow is v2 architecture)
- ADR-026: ClaimsFlow Agentic Claims Processing
- ADR-027: Executive SPOG Dashboard
- ADR-028: Data Lifecycle Management (DLM policy owned by deploying institution)

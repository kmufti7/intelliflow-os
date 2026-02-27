# PRD: Human-in-the-Loop Maker-Checker Approval Gate

**Status:** Planned
**Version:** 0.1 (Draft)
**Owner:** Kaizen Works, LLC
**Last Updated:** 2026-02-25

## Problem Statement

Regulated enterprises cannot allow 100% autonomous execution of high-stakes workflows (e.g., claims adjudication, loan approval) without dual-control mechanisms. Current ClaimsFlow v1 uses a deterministic kill-switch to halt bad actors, but does not support human approval workflows for high-variance edge cases. A kill-switch blocks — it does not escalate. For a CRO, the gap is the space between "blocked" and "approved by a qualified human." OCC dual-control expectations for money movement and high-value transactions require a Maker-Checker pattern: one party initiates, a second party approves. IntelliFlow OS v2.0 has no such gate.

## Target User

- **Primary:** Risk Officers, Compliance Officers, Underwriters in regulated financial services and insurance organizations
- **Secondary:** Claims supervisors managing adjudication queues, internal audit teams reviewing approval chains

## Goals

1. Human approval gate before any adjudication above a configurable threshold
2. Serialized workflow state that survives process restarts — no in-memory-only state
3. Approval queue visible in SPOG to non-technical stakeholders
4. Full audit trail: who approved, when, what state was resumed, what state was rejected
5. Fail-closed: unapproved workflows do not auto-expire to adjudication — they remain queued until explicit human action

## Non-Goals

- **Not a full workflow management UI.** Approval queue will surface in SPOG only — not a standalone case management tool.
- **Not multi-approver consensus.** Single Maker-Checker gate in v3.0 — no quorum, no multi-level approval chains.
- **Not a notification layer.** Email/SMS/Slack alerts for pending approvals are out of scope for the reference architecture.
- **Not a general-purpose pause/resume mechanism.** The interrupt gate is purpose-built for compliance approval, not arbitrary workflow suspension.

## Solution Overview

The HITL Maker-Checker gate will upgrade the LangGraph orchestrator with a persistent state checkpointer (SQLite or PostgreSQL backend). ClaimsFlow's workflow graph will introduce an `interrupt_before=["Adjudication"]` edge — when the workflow reaches the adjudication boundary and the claim value exceeds a configurable threshold, LangGraph will physically pause execution and serialize the full workflow state to an escalation queue.

The Executive SPOG will gain a fourth panel — "Approvals Queue" — where a human Risk Officer can review the paused workflow state, inspect the fraud score, governance rule results, and audit trail, and then approve or reject. Approval resumes the LangGraph state from the checkpoint. Rejection terminates the workflow with a REJECTED status and full WORM audit entry.

The WORM logger will record the approval event with approver identity, timestamp, and the state hash at the point of approval — creating a tamper-evident record of the human decision.

## Key Features (Planned)

- **LangGraph persistent checkpointer:** Workflow state serialized to SQLite or PostgreSQL at interrupt edges. State survives process restarts.
- **Configurable threshold gate:** Claims below threshold proceed automatically. Claims above threshold pause for human approval. Threshold is configurable per deployment.
- **SPOG Approvals Queue panel:** Fourth SPOG column showing pending workflows with claim details, fraud score, governance rule results, and approve/reject controls.
- **WORM-logged approval events:** APPROVAL_GRANTED, APPROVAL_REJECTED, and APPROVAL_TIMEOUT events recorded with approver identity and state hash.
- **Fail-closed timeout:** Unapproved workflows do not auto-expire to adjudication. Configurable timeout results in APPROVAL_TIMEOUT event and workflow termination — never silent approval.

## Compliance Alignment

- **OCC dual-control expectations:** Designed to support Maker-Checker patterns for high-value transactions — one party initiates (workflow), a second party approves (Risk Officer via SPOG).
- **SR 11-7 (Model Risk Management):** Aligned to ongoing monitoring requirements — human oversight gate ensures model outputs are reviewed before high-stakes execution.
- **EU AI Act (Human Oversight):** Designed to support Article 14 human oversight requirements for high-risk AI systems — human can intervene before consequential decisions execute.
- **NIST AI RMF (MANAGE function):** Approval gate is a MANAGE control — human intervention capability embedded in the workflow execution path.

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| intelliflow-core | v2 | LangGraph Workflow Engine, WORM Logger, Token FinOps Tracker |
| intelliflow-claimsflow | 1.0 | ClaimsFlow workflow nodes (Intake, Fraud Score, Kill-Switch, Adjudication) |
| LangGraph | 1.0.9+ | Checkpointer API for persistent state serialization |
| SQLite or PostgreSQL | TBD | State persistence backend for checkpointed workflows |
| Streamlit | 1.x | SPOG Approvals Queue panel |

## Success Metrics (Definition of Done)

| Metric | Target |
|--------|--------|
| Workflow pauses deterministically at interrupt_before edge | Verified |
| State serializes and deserializes without data loss | Verified |
| SPOG Approvals Queue renders pending workflows | Verified |
| WORM logger records approval event with approver identity | Verified |
| Fail-closed timeout: unapproved workflows terminate, never auto-approve | Verified |
| Test coverage | 20+ tests covering pause, approve, reject, and timeout scenarios |

## Open Questions / Known Gaps

1. **Not yet implemented — roadmap item.** This PRD describes planned v3.0 capabilities.
2. **Checkpointer backend choice (SQLite vs PostgreSQL) TBD.** SQLite is consistent with existing WORM/TokenLedger backend but may not support concurrent multi-user approval workflows.
3. **Authentication layer for approver identity not yet designed.** SPOG is currently single-tenant with no authentication. Approval gate requires identity to be meaningful.
4. **Threshold configuration mechanism not yet specified.** Per-deployment threshold requires a configuration surface — environment variable, config file, or SPOG admin panel.
5. **Multi-approver escalation not in scope.** v3.0 covers single Maker-Checker only. Multi-level approval chains are a future extension.

## Related ADRs / Roadmap References

- ADR-025: Deterministic v1 vs Agentic v2 (HITL gate extends v2 agentic architecture)
- ADR-026: ClaimsFlow Agentic Claims Processing (primary consumer of HITL gate)
- ADR-027: Executive SPOG Dashboard (Approvals Queue extends SPOG)
- Product Roadmap: v3.0 Priority 1

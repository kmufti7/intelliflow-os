# PRD: Executive SPOG (Single Pane of Glass)

**Status:** Launched
**Version:** 1.0
**Owner:** Kaizen Works, LLC
**Last Updated:** 2026-02-25

## Problem Statement

AI governance primitives — kill-switches, audit trails, cost ledgers, tool registries — are invisible to the non-technical stakeholders who are ultimately accountable for AI risk. A CRO cannot assess governance posture by reading Python logs. A CFO cannot validate AI cost attribution from raw database tables. The gap is not missing governance — it is missing visibility. Executive stakeholders need a real-time, non-technical interface that surfaces governance state, audit history, and cost data without requiring engineering interpretation.

## Target User

- **Primary:** Executive stakeholders — CRO, CFO, Chief Compliance Officer
- **Secondary:** Risk officers, internal audit teams, board-level AI oversight committees

## Goals

1. Non-technical governance visibility — executive stakeholders can assess AI governance posture without engineering support
2. Three-panel layout covering the complete governance surface: state, history, cost
3. Demo-able in under 3 minutes — clean and fraud scenarios showing kill-switch activation
4. Built on real governance data from ClaimsFlow workflow execution, not mock dashboards

## Non-Goals

- **Not a production monitoring tool.** SPOG is a governance visibility dashboard, not an APM or infrastructure monitoring system.
- **Not multi-tenant.** Single-tenant demo. Production deployment requires authentication, role-based access control, and tenant isolation.
- **Not real-time streaming.** Dashboard reads from WORM log and token ledger after workflow completion. Not designed for sub-second streaming updates.
- **Not a BI tool.** Fixed three-panel layout purpose-built for governance visibility. Not a general-purpose analytics or reporting platform.

## Solution Overview

The Executive SPOG is a 3-column Streamlit dashboard that surfaces governance state from ClaimsFlow workflow execution:

**Panel 1 — Governance State:** Current status of all governance primitives. Kill-switch armed/triggered status, active governance rules, MCP tool registry state, workflow node status. Green/red visual indicators for at-a-glance assessment.

**Panel 2 — Audit Trail:** Chronological WORM log entries from the most recent workflow execution. Each entry shows timestamp, workflow node, action taken, and governance rule evaluation results. Tamper-evident — entries reference HMAC hash chain.

**Panel 3 — Cost Ledger:** Per-step token usage and cost attribution from the Token FinOps Tracker. Immutable receipt pattern — cost_usd captured at write time. Aggregated totals for the workflow execution.

**Demo runner:** `ui/demo_runner.py` executes clean and fraud claim scenarios, populating the SPOG with real governance data. The fraud scenario triggers the kill-switch, visually demonstrating fail-closed behavior in the dashboard.

## Key Features

- **3-panel governance dashboard:** Governance State, Audit Trail, Cost Ledger — complete governance surface in a single view
- **Kill-switch visibility:** Real-time (post-execution) kill-switch status with visual indicators. Fraud scenario shows kill-switch activation and claim blocking.
- **WORM audit trail viewer:** Browse tamper-evident log entries with HMAC hash chain references. Each entry tied to workflow step and governance rule.
- **Token FinOps cost view:** Per-step cost attribution with immutable receipts. Aggregated workflow cost totals.
- **Demo scenarios:** Clean claim (full workflow completion) and fraud claim (kill-switch triggered) demonstrate governance behavior end-to-end.
- **YouTube walkthrough:** Full demo available at https://youtu.be/SMpBgIB0HKQ

## Compliance Alignment

- **SR 11-7 (Model Risk Management):** SPOG provides the ongoing monitoring visibility that SR 11-7 expects — non-technical stakeholders can assess model governance posture without engineering intermediation.
- **EU AI Act (Article 13 — Transparency):** Dashboard surfaces AI system behavior, governance state, and cost attribution in a format accessible to non-technical oversight roles.
- **NIST AI RMF (MANAGE function):** SPOG is the MANAGE layer — it does not implement governance, it makes governance visible and auditable to the accountable stakeholders.

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| intelliflow-claimsflow | 1.0 | Source of governance data — workflow execution, kill-switch events |
| intelliflow-core v2 | latest | WORM Logger (audit trail source), Token FinOps Tracker (cost data source) |
| Streamlit | 1.x | Dashboard UI framework |
| SQLite | 3.x | Backend for WORM log and token ledger reads |

## Success Metrics (At Launch)

| Metric | Value |
|--------|-------|
| Dashboard panels | 3 (Governance State, Audit Trail, Cost Ledger) |
| Demo scenarios | 2 (clean claim, fraud claim with kill-switch trigger) |
| Demo time | Under 3 minutes end-to-end |
| Data source | Real ClaimsFlow workflow execution (not mock data) |
| YouTube demo | Published — https://youtu.be/SMpBgIB0HKQ |

## Open Questions / Known Gaps

1. **Single-tenant demo.** No authentication, no role-based access control. Production deployment requires an identity layer (e.g., Azure AD integration) and role-scoped views (CRO sees risk, CFO sees cost).
2. **Post-execution refresh.** Dashboard reads governance data after workflow completion. No WebSocket or SSE streaming for real-time updates during long-running workflows.
3. **Fixed layout.** Three-panel layout is purpose-built for the current governance surface. Adding new governance primitives (e.g., data lineage, model versioning) would require layout extensions.
4. **No alerting.** SPOG is a visibility tool, not an alerting system. Production deployment would need integration with PagerDuty, Slack, or similar for kill-switch trigger notifications.

## Related ADRs

- ADR-027: Executive SPOG Dashboard
- ADR-026: ClaimsFlow Agentic Claims Processing (data source)
- ADR-025: Deterministic v1 vs Agentic v2 (SPOG surfaces v2 governance)
- ADR-028: Data Lifecycle Management (retention policy affects audit trail display)

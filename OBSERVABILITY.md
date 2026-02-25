# IntelliFlow OS — Observability

This document describes the logging, monitoring, and alerting strategy for IntelliFlow OS.

## Observability Principles

1. **Every decision is logged.** No silent failures.
2. **Structured logs, not free text.** Machine-parseable for analysis.
3. **Cost visibility by default.** Token usage tracked per interaction.

---

## Current Implementation

### Audit Logging

Both modules log every interaction to SQLite with a consistent schema:

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique event ID |
| event_type | string | Step in the pipeline (e.g., "classification", "retrieval", "response") |
| input | string | Input to this step |
| output | string | Output from this step |
| tokens_in | int | Prompt tokens consumed |
| tokens_out | int | Completion tokens generated |
| cost_usd | float | Estimated cost for this step |
| timestamp | datetime | When the event occurred |

### Governance UI

The Streamlit interface includes a real-time governance panel showing:

- Step-by-step trace of the current interaction
- Token count per step
- Cumulative cost for the session
- Chaos mode status (if enabled)

### Cost Tracking

| Metric | Tracked | Displayed |
|--------|---------|-----------|
| Tokens per request | Yes | Yes (UI + logs) |
| Cost per request | Yes | Yes (UI + logs) |
| Session totals | Yes | Yes (UI) |
| Monthly rollups | No | No (not implemented) |

---

## Failure Logging

### Chaos Mode Events

When chaos mode triggers a failure, the audit log captures:

```
event_type: ChaosMode
input: failure_type (faiss_unavailable | pinecone_unavailable)
output: fallback_response
```

### Kill-Switch Events (v2)

When KillSwitchGuard halts a workflow, the KillSwitchTriggered exception carries a structured audit payload:

| Field | Type | Description |
|-------|------|-------------|
| failed_rules | list[GovernanceRule] | Every rule that failed evaluation (no short-circuit — all rules evaluated) |
| state_snapshot | dict | Full Pydantic state at the moment of halt (via `model_dump()`) |

This is the observable event for governance enforcement. Downstream consumers (log aggregators, alerting systems) can filter on `event_type: kill_switch_triggered` to detect governance halts. The fail-closed design means a rule whose logic raises an exception is recorded as a failure in `failed_rules` — never silently passed.

WORM logging is implemented in intelliflow-core v2 as WORMLogRepository. Every workflow execution writes an append-only, tamper-evident audit event to SQLite with HMAC-SHA256 hash chaining. Each entry is cryptographically linked to the previous entry — any retroactive modification breaks the chain and is detectable on next read.

### Tool Registry Events (v2)

Every `get_tools()` call on MCPRegistry is an observable event — it records which workflow node requested which tool subset and what was returned. This enables audit consumers to reconstruct the exact tool capabilities the agent had at any point in execution.

| Field | Type | Description |
|-------|------|-------------|
| node_name | str | The LangGraph node requesting tools |
| allowed_names | list[str] | Tool names the node was authorized to use |
| returned_tools | list[str] | Tool names actually returned (should match allowed_names) |
| registry_locked | bool | Whether the registry was locked at time of retrieval |

The static catalog design means the full tool inventory is deterministic from the codebase — auditors can verify the master list without runtime logs. Dynamic scoping events provide the per-execution evidence of which subset was active for each node.

WORM logging is active for all v2 workflow executions. Both kill-switch intercepts and standard workflow completions produce immutable audit records. Entries include trace ID, event type, payload hash, and HMAC chain link — satisfying SR 11-7 audit trail requirements and SEC 17a-4 non-rewritable record patterns.

### WORM Audit Events (v2)

`trace_id` is the primary correlation key across all observable events in a single workflow execution. Every WORM log entry carries the same `trace_id` (UUID4, auto-generated in IntelliFlowState), enabling complete audit trail reconstruction via `SELECT * FROM worm_log WHERE trace_id = ?`.

Event types logged to the WORM audit log:

| Event Type | When | Payload |
|------------|------|---------|
| WORKFLOW_START | Before graph invocation | workflow_id, trace_id, step_name |
| WORKFLOW_END | After successful completion | workflow_id, trace_id, success |
| KILL_SWITCH_TRIGGERED | When governance rules fail | trace_id, failed_rules, state_snapshot |
| TOOL_EXECUTED | When a tool is called | trace_id, tool_name, node |

Each entry is HMAC-SHA256 hash-chained to the previous entry. `verify_chain()` recomputes all hashes sequentially from the GENESIS anchor to detect tampering. DatabaseSessionManager with WAL journaling mode prevents write contention on the shared SQLite database.

### ClaimsFlow WORM Events

ClaimsFlow (intelliflow-claimsflow) extends the WORM audit trail with insurance-specific events:

| Event Type | When | Payload |
|------------|------|---------|
| INTAKE_COMPLETE | After claim extraction | claim_id, claimant_id, claimant_name, claim_type, amount |
| FRAUD_SCORE_COMPLETE | After risk assessment | claim_id, fraud_score, fraud_flag |
| KILL_SWITCH_TRIGGERED | When OFAC/SIU sanctions check fires | trace_id, failed_rules (sanctions_check), state_snapshot |
| ADJUDICATION_COMPLETE | After threshold-based decision | fraud_score, decision (APPROVED/ESCALATE/DENIED) |

The Kill-Switch interceptor sits between fraud_score and adjudication — if `fraud_flag == True`, KILL_SWITCH_TRIGGERED fires and adjudication never executes. This is observable in the WORM log as a missing ADJUDICATION_COMPLETE event for halted workflows.

### Executive Single Pane of Glass (SPOG)

The SPOG dashboard (Streamlit) provides executive-level observability across ClaimsFlow workflow executions. Three-column layout:

| Column | Content | Data Source |
|--------|---------|-------------|
| Governance State | Kill-Switch status, failed rules, workflow outcome | WORMLogRepository |
| Audit Trail | Chronological WORM events with trace_id correlation | WORMLogRepository |
| Cost Ledger | Per-node token spend, partial execution cost visibility | TokenLedgerRepository |

SPOG consumes the same audit primitives (WORMLogRepository, TokenLedgerRepository) that power the v2 runtime — no separate data pipeline. When a Kill-Switch fires, the Cost Ledger column shows receipts only for nodes that executed (intake + fraud_score), visually confirming governance halt.

Token FinOps is implemented in intelliflow-core v2 as TokenLedgerRepository. Every LLM invocation writes an immutable cost receipt to the ledger at point-in-time pricing. Costs are never recalculated after write — historical records reflect the USD cost at execution time, preventing pricing drift from corrupting financial audit trails. WORM audit events and FinOps ledger entries share the same SQLite session manager, ensuring atomic observability across both subsystems.

### Error Handling

| Error Type | Logged | User Response |
|------------|--------|---------------|
| LLM API failure | Yes | Graceful fallback message |
| Retrieval failure | Yes | Graceful fallback message |
| Extraction failure | Yes | Partial results + warning |
| Kill-switch triggered | Yes | WorkflowResult with `kill_switch_triggered=True` and full failure list |

---

## Future Enhancements (Not Implemented)

| Enhancement | Purpose | Priority |
|-------------|---------|----------|
| Structured JSON logs | Export to log aggregators (Datadog, Splunk) | Medium |
| Metrics endpoint | Prometheus-compatible /metrics | Medium |
| Alerting rules | Slack/PagerDuty on error thresholds | Low |
| Dashboard | Grafana visualization of cost/usage | Low |
| Distributed tracing | OpenTelemetry integration | Low |

---

## Operational Checklist

For production deployment (not current scope):

- [ ] Configure log retention policy
- [ ] Set up log aggregation pipeline
- [ ] Define alerting thresholds (error rate, latency, cost)
- [ ] Implement health check endpoint
- [ ] Add request rate limiting

---

## References

- Governance UI: Imported from `intelliflow-core`
- Audit schema: Defined in `intelliflow-core/contracts.py`

## Token FinOps Observability

TokenLedgerRepository (token_ledger table) provides per-invocation financial telemetry for all LLM calls.
Unlike the WORM audit log (fail-closed, compliance-grade), the token ledger is
fail-open — a write failure raises TokenLedgerError but does not halt workflow
execution. A missed receipt is an observability gap, not a compliance violation.

Key observability primitives:
- get_workflow_cost(workflow_id) — total cost for a workflow run
- get_module_cost(module_name) — aggregate cost across all workflows for a module
- get_ledger(trace_id) — all invocations for a specific WORM-traced execution

**Fail-open vs fail-closed distinction:**

| Component | Failure Mode | Rationale |
|-----------|-------------|-----------|
| WORMLogRepository | Fail-closed (halts workflow) | Compliance audit — missing entry = audit gap |
| TokenLedgerRepository | Fail-open (logs error, continues) | Financial telemetry — missed receipt does not block care or fraud detection |

This distinction is intentional. An AI that refuses to process a loan application
because it cannot log the token cost has the wrong failure hierarchy.

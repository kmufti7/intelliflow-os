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

### Error Handling

| Error Type | Logged | User Response |
|------------|--------|---------------|
| LLM API failure | Yes | Graceful fallback message |
| Retrieval failure | Yes | Graceful fallback message |
| Extraction failure | Yes | Partial results + warning |

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

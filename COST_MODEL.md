# IntelliFlow OS — Cost Model (Token Economics)

This document explains the unit economics of IntelliFlow OS interactions.
Values are illustrative scenarios based on Azure OpenAI gpt-4o-mini pricing at time of development (Feb 2026).

## What We Track

- Tokens in (prompt) and out (completion) per request
- Estimated USD cost per request
- Session-level rollups in governance UI

## Cost Per Interaction (Illustrative)

| Step | Typical Tokens | Notes |
|------|----------------|-------|
| Classification (SupportFlow) | ~200 in / ~10 out | Enum output keeps completion minimal |
| Policy Retrieval (SupportFlow) | ~500 in / ~200 out | Includes retrieved policy context |
| Extraction (CareFlow) | ~0 | Regex-first; LLM fallback rarely triggered |
| Reasoning (CareFlow) | ~800 in / ~300 out | Patient context + guidelines + response |

## Scenario Estimates

| Scenario | Interactions/Month | Est. Cost/Month | Notes |
|----------|-------------------|-----------------|-------|
| Reference implementation usage | 100 | < $1 | Minimal testing |
| Pilot (10K) | 10,000 | $10-30 | Depends on retrieval payload size |
| Scale (100K) | 100,000 | $100-300 | Volume discounts may apply |

*Note: These are rough estimates based on Azure OpenAI pricing as of Feb 2026. Actual costs depend on prompt engineering, retrieval chunk sizes, and provider pricing at time of deployment.*

## Cost Controls Implemented

| Control | Module | Impact |
|---------|--------|--------|
| Regex-first extraction | CareFlow | Eliminates LLM cost for structured data extraction (100% regex success rate) |
| Keyword policy retrieval | SupportFlow | Avoids embedding/vector costs for simple lookups |
| Enum-based classification | SupportFlow | Minimal completion tokens |
| Token tracking in governance UI | Both | Visibility into per-request costs |
| Dynamic tool scoping (MCPRegistry) | v2 Runtime | Each workflow node receives only its authorized tool subset via `get_tools()` — eliminates full catalog padding in function-calling context, reducing input tokens and hallucination surface |

## Future Optimizations (Not Implemented)

- Response caching for repeated queries
- Tiered model selection (smaller model for classification, larger for generation)
- Batch processing for non-real-time workflows

## Token FinOps Tracker — Immutable Receipt Architecture

IntelliFlow OS implements a production-grade token accounting ledger as part of
intelliflow-core v2. Every LLM invocation appends an immutable record to the
token_ledger SQLite table containing: model name, input tokens, output tokens,
workflow ID, module name, WORM trace_id reference, and cost_usd calculated at
write time.

**Why point-in-time costing matters:**
LLM API pricing changes frequently. Azure OpenAI has reduced rates on major models
multiple times since 2023. If cost is calculated dynamically on read (tokens x today's
price), historical financial reports retroactively rewrite themselves when prices drop.
This fails basic accounting principles and will not survive an audit. IntelliFlow OS
stores the calculated USD cost as an immutable receipt — pricing drift cannot corrupt
historical records.

**Departmental chargeback support:**
get_workflow_cost(workflow_id) and get_module_cost(module_name) provide aggregation
primitives for chargeback reporting. In Kubernetes environments where pods restart
frequently, append-only persistence ensures cost history survives container recycling.
Ephemeral cost tracking is a live dashboard widget, not FinOps.

**Partial failure handling:**
Cost is logged per LLM invocation, not per workflow completion. If a workflow executes
3 of 4 planned LLM calls before a kill-switch fires or a crash occurs, all 3 costs are
captured. The enterprise still paid for those tokens.

**Kill-Switch partial execution (ClaimsFlow):**
When KillSwitchGuard fires in the ClaimsFlow workflow (e.g., OFAC/SIU sanctions check),
the adjudication node never executes. The Token Ledger captures exactly 2 cost receipts
(intake + fraud_score) instead of 3. This is not a bug — it is observable proof that
governance halted execution before the decision node. The SPOG dashboard renders this
visually: the Cost Ledger column shows 2 entries for a halted workflow vs. 3 for a
clean workflow, providing executive-level confirmation that the Kill-Switch operated
correctly.

**PTU capacity forecasting:**
Persistent per-module cost aggregation enables the token consumption baselines required
for Provisioned Throughput Unit (PTU) capacity planning. PTU commitments require
accurate 30-day rolling consumption data — impossible without persistent per-invocation
records.

**Data Lifecycle Management (DLM) gap:**
The token_ledger table is append-only with no TTL. Production deployments require a
DLM policy (e.g., 90-day archival to cold storage). This is a known roadmap item.

**Pricing configuration:**
Default rates use Azure OpenAI pricing as of Feb 2026 (gpt-4o, gpt-4o-mini, text-embedding-3-small).
Override via INTELLIFLOW_TOKEN_PRICING_JSON environment variable — same KMS-ready
pattern as the WORM signing key.

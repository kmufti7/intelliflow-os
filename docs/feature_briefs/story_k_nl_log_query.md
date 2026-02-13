# Feature Brief: Story K — NL Log Query

**Story ID:** K
**Status:** Built
**Author:** Kamil (Architect Agent, based on CC build report)
**Date:** 2026-02-13

---

## 1. What Was Built

**Tool:** NL Log Query
**Location:** `tools/nl_log_query.py` (309 lines) in the intelliflow-os repo
**Tests:** `tests/test_nl_log_query.py` (198 lines, 15 tests passing)
**Data:** `data/nl_query_logs.db` (SQLite, auto-created with `audit_logs` schema)

**What it does:** Developers type natural language queries like "Show me all CareFlow errors from the last hour." The tool translates this into a validated SQL WHERE clause and executes it against the platform's audit log store.

**How it works:**
1. Developer inputs natural language query
2. LLM (gpt-4o-mini) translates to SQL WHERE clause
3. Python validates the generated SQL:
   - Blocked keywords: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, EXEC, UNION, SELECT (prevents subquery injection), --, /*, */, ;
   - Column whitelist enforced: `cost_usd`, `event_type`, `id`, `input`, `level`, `model`, `module`, `output`, `timestamp`, `tokens_in`, `tokens_out`
   - String literals stripped before validation (prevents false positives where values like 'ERROR' look like unknown columns)
   - Maximum query length limit
4. Validated query executes against SQLite `audit_logs` table
5. Returns formatted results (max 100 rows)

**Key design choice:** Added SELECT to blocked keywords. A WHERE clause should never contain SELECT -- blocking it prevents subquery injection (`id IN (SELECT ...)`).

**Governance self-logging:** Every query attempt (successful or failed) logs to the same `audit_logs` table with `event_type = 'nl_log_query'`, creating a full audit trail of tool usage.

**Cost tracking:** gpt-4o-mini pricing ($0.15/1M input, $0.60/1M output) computed per query.

---

## 2. Why It Matters

**Pain point:** Debugging governed AI systems means reading logs constantly. In regulated industries, logs are the evidence trail. But searching them requires knowing SQL or grep syntax. Developers waste time writing ad-hoc queries instead of investigating issues.

**Who cares:**
- **Developers** who need to debug production issues quickly without memorizing log schemas
- **Compliance teams** who need to audit system behavior but aren't SQL experts
- **Hiring managers** evaluating whether a PM understands developer experience and operational tooling

**Market context:** Observability tools (Datadog, Splunk) offer NL query features at enterprise pricing. Building a lightweight version demonstrates understanding of the space without vendor lock-in.

---

## 3. PM Framing

**Decision rationale:** The platform already logs everything (both SupportFlow and CareFlow use the same `audit_logs` schema). The data exists. The problem was access. Instead of building a dashboard, we built a query tool that meets developers where they already are: the terminal.

**Extensibility:** The pattern (NL -> structured query -> validation -> execution) is the same "LLM translates, code decides" pattern used in CareFlow's clinical reasoning. Proving it works for log queries validates it as a platform-wide pattern, not a one-off.

**Risk reduced:** SQL injection is the #1 risk in any NL-to-SQL tool. The validation layer (blocked keywords + column whitelist + string stripping + length limit) is defense-in-depth. Blocking SELECT in WHERE clauses specifically prevents subquery injection, which most tutorials miss.

---

## 4. Interview Hook

"Our platform logs every decision across both modules. But searching those logs meant writing SQL by hand. So I built a natural language query tool. You type 'show me CareFlow errors over $0.05' and it generates a validated WHERE clause. The key decision was blocking SELECT inside WHERE clauses. Most NL-to-SQL tutorials forget that subquery injection is a real attack vector. We validate against a column whitelist, strip string literals to avoid false positives, and log every query attempt to the same audit table. The tool audits itself."

---

## 5. Architecture Impact

**Architecture impact:** Minimal. Does not change CareFlow/SupportFlow control flow.

**New dependency:** SQLite database at `data/nl_query_logs.db` using the same `audit_logs` schema from DATA_DICTIONARY.md and OBSERVABILITY.md.

**Cross-module connection:** Both SupportFlow and CareFlow use the same `audit_logs` schema. This tool queries across both modules' logs from a single interface.

**Diagram updates:** Optional. Could add a "Developer Tools" layer to ARCHITECTURE.md showing tools/nl_log_query.py connecting to the shared audit_logs store.

---

## 6. New Data Structures

No new Pydantic schemas. Uses the existing `audit_logs` table schema already documented in DATA_DICTIONARY.md and OBSERVABILITY.md.

Column whitelist (from actual schema): `cost_usd`, `event_type`, `id`, `input`, `level`, `model`, `module`, `output`, `timestamp`, `tokens_in`, `tokens_out`

---

## 7. Trade-offs

| Chose | Gave Up | Why |
|-------|---------|-----|
| Token-based SQL validation | Full SQL AST parsing (e.g., sqlparse) | Token extraction is simpler, covers 95% of injection vectors. Full AST parsing adds dependency complexity for marginal gain. |
| SELECT in blocked keywords | Ability to use subqueries | WHERE clauses should never need SELECT. Blocking it eliminates an entire class of injection attacks. |
| String literal stripping before validation | Simpler validation code | Without stripping, values like `level = 'ERROR'` flag ERROR as an unknown column. Small complexity for correctness. |
| SQLite (standalone file) | Shared database connection | Tool creates its own DB if needed. No dependency on running modules. Developers can query logs offline. |
| Max 100 rows returned | Unlimited results | Prevents accidental full-table dumps. Pagination would add complexity for minimal portfolio value. |

**What production would need:**
- Full SQL AST parsing (sqlparse) for edge cases
- Time-range helpers ("last hour" -> proper timestamp math)
- Pagination for large result sets
- Query history and caching
- Connection to production log aggregation (Elasticsearch, CloudWatch, etc.)

---

## 8. Rough Edges

1. Column validation uses token extraction, not full SQL parsing. Could miss edge cases with deeply nested expressions.
2. No time-range helpers. "Last hour" requires LLM to know current time.
3. No pagination. Returns max 100 rows.
4. No query history or caching.
5. Depends on LLM output quality. If LLM generates valid SQL with wrong semantics, validation cannot catch it.

---

## 9. ATS Keywords

natural language query, NL-to-SQL, log analysis, SQL injection prevention, observability, developer tools, audit logging, SQLite, Python security, input validation, developer experience, DevOps tooling

---

## 10. Metrics Changed

| Metric | Before | After | File |
|--------|--------|-------|------|
| developer_tools | 1 | 2 | portfolio_config.yaml |
| total_tests | 164 | 179 (164 + 15) | portfolio_config.yaml |
| hand_written_tests | 129 | 144 (129 + 15) | portfolio_config.yaml |

---

## 11. Forbidden Phrases

| Forbidden | Use Instead |
|-----------|-------------|
| "1 developer tool" | "2 developer tools (AI test generator, NL log query)" |
| "164 total tests" | "179 total tests (144 hand-written + 35 AI-generated)" |
| "129 hand-written tests" | "144 hand-written tests" |

---

## 12. Cascade Checklist

- [ ] CLAUDE.md truth table updated
- [ ] CLAUDE.md story inventory updated
- [ ] CLAUDE.md forbidden phrases updated
- [ ] portfolio_config.yaml updated
- [ ] render_portfolio.py run (if metrics changed)
- [ ] 8 portfolio files updated with strategic context
- [ ] ARCHITECTURE.md updated (if architecture impact = yes)
- [ ] DATA_DICTIONARY.md updated (if new data structures)
- [ ] CHANGELOG.md entry added
- [ ] Module README updated
- [ ] verify_cascade.py passes
- [ ] No forbidden phrases in any updated file

---

**End of Feature Brief: Story K**

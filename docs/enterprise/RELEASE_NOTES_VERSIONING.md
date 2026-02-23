# Release Notes & Versioning

## Executive Summary

IntelliFlow OS follows semantic versioning to communicate the scope and impact of changes to operators deploying the platform. This document defines the versioning policy, release cadence, deprecation process, and communication model. As a reference architecture — not a managed SaaS product — release management is the operator's responsibility. This document provides the framework for operators to manage upgrades within their own change management processes.

---

## 1. Versioning Policy

IntelliFlow OS uses [Semantic Versioning 2.0.0](https://semver.org/) (MAJOR.MINOR.PATCH).

| Version Component | Trigger | Example |
|-------------------|---------|---------|
| **MAJOR** (X.0.0) | Breaking changes to SDK contracts, removal of public APIs, schema changes that require data migration | Removing a Pydantic schema field from `AuditEventSchema`, changing `intelliflow-core` import paths |
| **MINOR** (0.X.0) | New features, new enterprise documents, new developer tools, non-breaking schema additions | Adding FHIR R4 ingestion, adding a new Pydantic field with a default value, new chaos mode failure types |
| **PATCH** (0.0.X) | Bug fixes, documentation corrections, test additions, performance improvements with no API changes | Fixing regex extraction edge case, correcting a cross-reference in enterprise docs, adding test coverage |

### What Constitutes a Breaking Change

- Removal or rename of any field in `AuditEventSchema`, `CostTrackingSchema`, or `GovernanceLogEntry`
- Changes to `intelliflow-core` public API signatures (function names, required parameters)
- Removal of supported input formats (e.g., dropping legacy clinic note ingestion)
- Changes to audit log schema that would break existing NL Log Query queries
- Removal or restructuring of enterprise documentation that operators reference in compliance evidence

### What Does Not Constitute a Breaking Change

- Adding new optional fields to existing Pydantic schemas (with defaults)
- Adding new enterprise documents to the evidence pack
- Adding new developer tools
- Adding new test cases
- Internal refactoring that preserves all public interfaces

---

## 2. Release Cadence

IntelliFlow OS is released on a milestone basis, not a fixed calendar schedule. Each release is scoped around a coherent set of capabilities.

| Release Type | Scope | Communication |
|--------------|-------|---------------|
| **Major release** | Breaking changes requiring operator action | CHANGELOG.md entry + migration guide + minimum 90-day deprecation notice |
| **Minor release** | New features and non-breaking additions | CHANGELOG.md entry + release notes |
| **Patch release** | Bug fixes and corrections | CHANGELOG.md entry |

### Release Artifacts

Each release includes:
- Tagged Git commit with semantic version
- Updated CHANGELOG.md with structured entry
- Updated enterprise documentation (if applicable)
- Passing verification: `verify_cascade.py` (all checks) + `verify_enterprise_docs.py` (all checks)

---

## 3. Current Release

### v1.0.0 — Initial Release (February 2026)

**Status:** Released

**What's Included:**

| Category | Details |
|----------|---------|
| **Modules** | SupportFlow (banking) + CareFlow (healthcare) |
| **SDK** | intelliflow-core — pip-installable shared governance SDK with 3 Pydantic contracts |
| **Stories** | 12 stories (A–L) built and cascaded |
| **Tests** | 193 total (158 hand-written + 35 AI-generated) across 4 repositories |
| **Enterprise Evidence Pack** | 18 documents mapped to NIST AI RMF, OWASP LLM Top 10, EU AI Act record-keeping, SR 11-7 |
| **Developer Tools** | 3 tools (AI test generator, NL log query, scaffold generator) |
| **Verification** | 137 automated checks (enterprise docs) + 15-check cascade verification |
| **Compliance Alignment** | HIPAA-aligned design patterns, NIST AI RMF mapped, OWASP LLM Top 10 mapped |
| **Infrastructure** | Azure OpenAI Service (GPT-4o-mini), local FAISS (PHI), Pinecone (guidelines), SQLite (audit) |

**Key Capabilities:**
- Deterministic reasoning: LLM extracts, code decides, LLM explains
- PHI-aware data residency: patient data stays local, only de-identified concepts reach cloud
- Chaos engineering: failure injection with graceful fallback and audit logging
- FHIR R4 dual-mode ingestion with LOINC 4548-4 support
- 5-layer cost optimization (regex-first extraction, model tiering, local FAISS, token tracking, structured outputs)

### v2.0.0-alpha.1 — intelliflow-core v2 Step 2: Kill-Switch Guard (February 2026)

**Status:** In development (alpha)

**What Shipped:**

| Category | Details |
|----------|---------|
| **Kill-Switch Guard** | KillSwitchGuard — deterministic InterceptorNode that evaluates GovernanceRule contracts before any LLM node in a LangGraph workflow |
| **GovernanceRule Contract** | Self-documenting rule struct with required `description` field (rule_id + description + logic callable) |
| **WorkflowResult** | Structured return type replacing raw exception propagation — callers always receive success/failure status with optional failure details |
| **Tests** | 8 new kill-switch tests (23 total v2 tests); 216 total platform tests |

**Key Design Decisions:**
- **Fail-closed:** Rule evaluation exceptions are treated as failures — the system never silently passes on error
- **Collect-all-failures:** No short-circuit; every rule is evaluated and the full failure set is carried in the audit payload
- **GovernanceRule struct over plain callable:** Required `description` field ensures every governance constraint is self-documenting for auditors

**Known Open Gap (CLOSED):** ~~WORM (write-once, read-many) logging for tamper-proof governance audit records is planned for v2 Step 4.~~ Resolved in v2.0.0-alpha.2.

---

### v2.0.0-alpha.2 — Step 4: WORM Audit Log *(2026-02-22)*

**What Shipped:**

| Category | Details |
|----------|---------|
| **WORMLogRepository** | HMAC-SHA256 hash-chained, append-only audit log with SQLite BEFORE UPDATE/DELETE triggers enforcing Write-Once immutability at the database layer |
| **DatabaseSessionManager** | Shared SQLite connection manager with WAL (Write-Ahead Logging) journaling mode |
| **WORMStorageError** | Fail-closed exception — halts workflow execution when any WORM write operation fails |
| **trace_id** | UUID4 field in IntelliFlowState — session-bounded audit correlation key linking all events in a single workflow execution |
| **SQLite Triggers** | BEFORE UPDATE and BEFORE DELETE triggers physically reject row modifications at the database layer |
| **Workflow Wiring** | Workflow.run() logs WORKFLOW_START, WORKFLOW_END, and KILL_SWITCH_TRIGGERED events to the WORM audit log |
| **Tests** | 12 new WORM tests; 47 total v2 tests |

**Key Design Decisions:**
- **HMAC-SHA256 over plain SHA-256:** Non-repudiation — without the KMS key, the chain cannot be mathematically rewritten (ADR-021)
- **Fail-closed:** Under SEC 17a-4 and SR 11-7, an unlogged AI decision is treated as a compliance violation (ADR-022)
- **Session-bounded trace_id:** Enables complete workflow lifecycle reconstruction for audit (ADR-023)
- **Shared DatabaseSessionManager:** Single SQLite connection with isolated repositories — enterprise pattern enabling cross-domain queries (ADR-024)

**Closed Gap:** WORM logger gap from v2.0.0-alpha.1 is now resolved.

---

### v2.0.0-alpha.3 — Step 5: Token FinOps Tracker *(2026-02-22)*

**What Shipped:**

| Category | Details |
|----------|---------|
| **TokenLedgerRepository** | Append-only financial telemetry for LLM invocations |
| **TokenLedgerError** | Fail-open exception (does not halt workflow execution) |
| **cost_usd immutable receipt** | Point-in-time USD calculation at write time |
| **Per-invocation granularity** | Partial workflow failures fully costed |
| **Aggregation primitives** | get_workflow_cost() and get_module_cost() |
| **Pricing configuration** | Azure OpenAI rates; INTELLIFLOW_TOKEN_PRICING_JSON env var override |
| **Tests** | 13 new token-ledger tests including pricing drift isolation regression; 60 total v2 tests; 253 platform tests total |

**Key Design Decisions:**
- **Immutable receipt over dynamic costing:** cost_usd stored at write time prevents pricing drift from corrupting historical financial reports (ADR-025)
- **Fail-open:** TokenLedgerError does not halt workflow. A missed cost receipt is an observability gap, not a compliance violation. Intentional distinction from fail-closed WORMStorageError.
- **Per-invocation granularity:** Cost logged per LLM call, not per workflow completion. Partial workflow failures are still costed correctly.

**Known gap:**
DLM policy (90-day archival to cold storage) required in production. Not implemented.

**Phase 1 complete.** All 5 v2 components shipped: LangGraph Workflow Engine,
Kill-Switch Guard, MCP Tool Registry, WORM Audit Log, Token FinOps Tracker.
60/60 v2 tests. 253 platform tests total.

---

## 4. Change Log Format

All changes are recorded in [CHANGELOG.md](../../CHANGELOG.md) using the following format:

```
## YYYY-MM-DD — Title (Session/Context)
- Category: Description of change with specific details
- Category: Description of change with specific details
```

### Entry Categories

| Category | Usage |
|----------|-------|
| **Shipped** | New modules, major features, or production-ready capabilities |
| **Added** | New documents, tests, tools, or non-breaking features |
| **Updated** | Changes to existing features, documents, or configurations |
| **Fixed** | Bug fixes, corrections, stale data updates |
| **Removed** | Deprecated features or documents removed |
| **Security** | Security-related changes or vulnerability fixes |

### Entry Requirements

Each CHANGELOG.md entry must include:
- Date in ISO 8601 format (YYYY-MM-DD)
- Descriptive title summarizing the release scope
- Specific details for each change (not just "updated docs")
- References to affected stories, documents, or verification results where applicable

---

## 5. Deprecation Policy

Breaking changes follow a structured deprecation process to give operators time to adapt.

### Deprecation Timeline

| Phase | Duration | Action |
|-------|----------|--------|
| **Announcement** | Day 0 | Deprecation notice added to CHANGELOG.md and affected documentation |
| **Warning period** | 90 days minimum | Deprecated feature continues to work; runtime warnings logged via audit trail |
| **Removal** | After warning period | Feature removed in next MAJOR release; migration guide provided |

### What Gets Deprecated (Not Removed Immediately)

- Pydantic schema fields that are being renamed or restructured
- SDK functions being replaced by improved alternatives
- Enterprise document formats being reorganized
- Developer tool interfaces being updated

### What Can Be Removed Without Deprecation

- Internal implementation details not exposed through public APIs
- Test utilities and development-only tooling
- Documentation typos and formatting corrections

### Deprecation Communication

Each deprecation notice includes:
1. **What** is being deprecated (specific field, function, or interface)
2. **Why** the change is necessary (rationale)
3. **When** the removal will occur (target MAJOR version)
4. **How** to migrate (specific steps or migration guide reference)

---

## 6. Customer Communication

IntelliFlow OS is a software platform, not a managed service. Release communication follows a pull model — operators check for updates rather than receiving push notifications.

### Communication Channels

| Channel | Content | Audience |
|---------|---------|----------|
| **CHANGELOG.md** | All changes with structured entries | Operators, developers |
| **GitHub Releases** | Tagged versions with release notes | Operators, developers |
| **Enterprise Evidence Pack** | Updated compliance documentation | Compliance teams, auditors |
| **Migration Guides** | Step-by-step upgrade instructions for MAJOR releases | Operators |

### Operator Responsibilities

| Responsibility | Details |
|----------------|---------|
| **Version tracking** | Operators monitor GitHub releases for updates relevant to their deployment |
| **Upgrade testing** | Operators test new versions in their staging environment before production deployment |
| **Migration execution** | Operators follow migration guides and validate their deployment after MAJOR upgrades |
| **Compliance re-validation** | After upgrades, operators verify that their compliance posture is maintained using the updated enterprise evidence pack |
| **Downstream communication** | Operators communicate platform changes to their own customers per their own SLA commitments |

### What the Platform Does Not Provide

- **Push notifications.** The platform does not send emails, SMS, or webhook notifications about new releases. Operators should watch the GitHub repository or integrate with their own release monitoring tooling.
- **Automatic upgrades.** The platform does not auto-update. All upgrades are operator-initiated and operator-tested.
- **Upgrade support.** The platform provides migration guides and documentation. Hands-on upgrade assistance is outside platform scope.

---

*Apache 2.0 — Copyright 2025-2026 Kaizen Works, LLC*

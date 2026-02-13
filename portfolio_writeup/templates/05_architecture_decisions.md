# Architecture Decisions

**Audience:** Engineers, Architects, Technical Interviewers
**Format:** ADR-style (Architecture Decision Records)

---

## ADR-001: Multi-Agent Orchestrator Pattern (SupportFlow)

**Status:** Accepted
**Date:** 2026-01-XX

### Context
Banking support requires handling different message types (complaints, praise, queries) with different logic, priorities, and responses.

### Decision
Implement a **hierarchical multi-agent orchestration pattern** with:
- Central Orchestrator coordinating workflow
- Specialized agents (ClassifierAgent, PositiveHandler, NegativeHandler, QueryHandler)
- Agent registry mapping message categories to handlers

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| Single monolithic agent | Simpler initial implementation | Hard to test, debug, audit |
| Event-driven pub/sub | Loose coupling | Harder to trace decision flow |
| LangChain agent framework | Pre-built patterns | Opaque abstractions, harder to customize |

### Consequences
- **Positive:** Each agent can be tested independently; clear audit trail
- **Positive:** Easy to add new handlers without modifying existing code
- **Negative:** More files/classes to manage
- **Negative:** Sequential processing (not parallelized)

### Validation
{{supportflow_tests}} tests pass, including isolated tests for classifier and handlers.

---

## ADR-002: Policy-Grounded Response Generation (SupportFlow)

**Status:** Accepted
**Date:** 2026-01-XX

### Context
In regulated banking, AI responses must be traceable to documented policy. "The AI said" isn't acceptable for compliance.

### Decision
- Store {{sf_policies}} banking policies in markdown format
- Implement keyword-based policy retrieval with content matching
- Inject relevant policies into LLM prompts
- Format responses with explicit policy citations

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| Vector search (embeddings) | Semantic matching | Overkill for {{sf_policies}} policies; adds latency/cost |
| LLM with policy fine-tuning | Integrated knowledge | Can't trace specific citations |
| No policy grounding | Simpler | Compliance risk; hallucination risk |

### Consequences
- **Positive:** Every response cites specific policy IDs
- **Positive:** Compliance can verify AI outputs against documented rules
- **Negative:** Keyword matching may miss semantic relevance
- **Negative:** Policy changes require service restart

### Validation
Policy citations appear in all negative handler responses in demos.

---

## ADR-003: "LLM Extracts, Code Decides" Pattern (CareFlow)

**Status:** Accepted
**Date:** 2026-01-XX

### Context
Healthcare AI must not hallucinate clinical reasoning. The "Therefore problem" — where LLMs generate plausible but incorrect clinical logic — is the central risk.

### Decision
Separate concerns explicitly:
1. **LLM extracts** facts from clinical notes (with regex-first optimization)
2. **Python code applies** deterministic rules for gap detection
3. **LLM explains** results with citations to patient data and guidelines

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| LLM-only reasoning | Simpler; more flexible | Hallucination risk; not reproducible |
| Rules-only (no LLM) | Fully deterministic | Brittle extraction; poor explanations |
| Symbolic AI / knowledge graph | Formal reasoning | High complexity; slow iteration |

### Consequences
- **Positive:** Gap detection is reproducible (same input → same output)
- **Positive:** Rules are explicit and testable (14 reasoning tests)
- **Positive:** Clinicians can verify logic
- **Negative:** Rules must be manually coded (not learned)
- **Negative:** Adding new gap types requires code changes

### Validation
14 reasoning tests verify gap detection logic for all scenarios.

---

## ADR-004: Regex-First Extraction (CareFlow)

**Status:** Accepted
**Date:** 2026-01-XX

### Context
Clinical notes contain structured data (A1C values, blood pressure, medication lists). LLM extraction is expensive and variable.

### Decision
- Try regex patterns first (A1C, BP, medications, diagnoses)
- Fall back to LLM only if regex extraction is incomplete
- Track extraction method and confidence in ExtractedFacts

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| LLM-only extraction | Handles edge cases naturally | Expensive; slow; variable |
| Regex-only (no fallback) | Fully deterministic | Fails on unusual note formats |
| ML-based NER | Statistical robustness | Training data requirements; complexity |

### Consequences
- **Positive:** 100% regex success on test patients (zero LLM calls)
- **Positive:** ~100x faster than LLM extraction
- **Positive:** Zero cost for successful extractions
- **Negative:** Regex patterns must cover expected note formats
- **Negative:** LLM fallback adds code complexity

### Validation
11 extraction tests verify regex patterns work for all test patients.

---

## ADR-005: PHI-Aware Data Residency (CareFlow)

**Status:** Accepted
**Date:** 2026-01-XX

### Context
HIPAA requires controls on PHI storage and transmission. Cloud vector stores (like Pinecone) are not automatically HIPAA-compliant.

### Decision
- Patient data stored only in local FAISS indexes
- External queries (Pinecone) receive only de-identified clinical concepts
- ConceptQueryBuilder strips identifiers before any external call
- Mode switching allows local-only or hybrid operation

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| All data in Pinecone | Simpler architecture | PHI in cloud; compliance risk |
| Encrypted cloud storage | Cloud benefits with encryption | Key management complexity; still requires BAA |
| On-prem only | Maximum control | Limited scalability for guidelines |

### Consequences
- **Positive:** PHI never leaves the machine
- **Positive:** Guidelines can use cloud scale without privacy risk
- **Positive:** Same codebase works local-only or hybrid
- **Negative:** Two vector stores to manage
- **Negative:** Concept query adds complexity

### Validation
15 concept query tests verify PHI safety, including edge cases.

---

## ADR-006: Chaos Engineering (Both Modules)

**Status:** Accepted
**Date:** 2026-01-XX (SupportFlow), 2026-02-XX (CareFlow)

### Context
Production systems fail. Chaos engineering tests failure handling before deployment. Both modules need resilience verification.

### Decision
**SupportFlow:**
- Probabilistic failure injection (30% when enabled)
- 7 injection points throughout workflow
- 5 realistic failure scenarios (timeouts, DB errors, rate limits)

**CareFlow:**
- Toggled (not random) failure injection via sidebar checkbox
- 2 failure types: FAISS unavailable, Pinecone unavailable
- Safe clinical fallback: "No clinical decisions should be made based on this message"
- Every injected failure logged to governance audit trail
- Cache invalidation ensures chaos check runs on every patient selection

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| No chaos testing | Simpler | Unknown failure behavior |
| Random (always-on) chaos | More realistic | Flaky demos; unpredictable |
| External chaos tools (Gremlin) | Production-grade | Overkill for portfolio demo |

### Consequences
- **Positive:** Failure behavior is demonstrated, not assumed
- **Positive:** Graceful degradation is verified
- **Positive:** CareFlow proves safe clinical fallback during infrastructure failures
- **Positive:** Integration tests verify the actual patient-selection code path
- **Negative:** Deterministic chaos isn't fully realistic
- **Negative:** Production would use percentage-based injection with circuit breakers

### Validation
{{chaos_tests_total}} chaos tests across both modules (13 SupportFlow + 15 CareFlow). CareFlow integration tests call the same `analyze_patient()` method the UI uses — removing the chaos check breaks the tests.

---

## ADR-007: Shared SDK (intelliflow-core)

**Status:** Accepted
**Date:** 2026-01-XX

### Context
Both SupportFlow and CareFlow need governance UI, audit schemas, and cost tracking. Duplication creates drift.

### Decision
- Extract common components into pip-installable package
- Include: governance_ui, contracts (Pydantic), helpers
- Both apps import from intelliflow-core
- SDK has its own test suite ({{core_tests}} tests)

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| Copy-paste shared code | Simpler initial setup | Drift; inconsistency; maintenance burden |
| Monorepo | Single codebase | Doesn't demonstrate platform claim |
| Micro-packages | Maximum modularity | Overkill; version coordination complexity |

### Consequences
- **Positive:** Proves "platform" architecture claim
- **Positive:** Bug fixes propagate to both apps
- **Positive:** Consistent governance across applications
- **Negative:** Dependency management complexity
- **Negative:** SDK changes require updates in both apps

### Validation
Both apps successfully import and use intelliflow-core. {{core_tests}} SDK tests pass.

---

## ADR-008: SQLite for Data Storage

**Status:** Accepted
**Date:** 2026-01-XX

### Context
Demo needs persistent storage for tickets, audit logs, and token usage. Production would use PostgreSQL.

### Decision
- Use SQLite with async access (aiosqlite)
- Repository pattern abstracts data access
- Schema supports tickets, audit logs, token usage, model pricing

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| PostgreSQL | Production-grade | Infrastructure overhead for demo |
| In-memory only | Simplest | Data lost on restart |
| JSON files | No database setup | Concurrency issues; query limitations |

### Consequences
- **Positive:** Zero infrastructure for demo
- **Positive:** Repository pattern allows PostgreSQL swap
- **Positive:** Supports all required queries
- **Negative:** SQLite has concurrency limitations
- **Negative:** Not production-representative

### Validation
Database tests verify ticket creation, persistence, and querying.

---

## ADR-009: Streamlit for UI

**Status:** Accepted
**Date:** 2026-01-XX

### Context
Need rapid UI development for demos. Not building a production frontend.

### Decision
- Use Streamlit for both SupportFlow and CareFlow
- Shared governance panel in sidebar
- Metrics display in main content area

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| React/Next.js | Production-grade UI | Development time; overkill for demo |
| Gradio | Simple AI interfaces | Less customizable than Streamlit |
| CLI only | Simplest | Doesn't demonstrate UI patterns |

### Consequences
- **Positive:** Rapid iteration on UI
- **Positive:** Built-in session state management
- **Positive:** Easy to share via Streamlit Cloud
- **Negative:** Not representative of production frontend
- **Negative:** Limited customization

### Validation
Both demos run successfully in Streamlit with governance panels.

---

## ADR-010: OpenAI GPT-4o-mini as Default LLM

**Status:** Accepted
**Date:** 2026-01-XX

### Context
Need an LLM for classification, extraction fallback, and response generation. Multiple providers available.

### Decision
- Use OpenAI GPT-4o-mini as default
- LLMClient abstraction allows provider swapping
- Cost tracking supports multiple models

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| GPT-4o | Higher capability | Higher cost; overkill for demo tasks |
| Claude 3 | Different strengths | Anthropic API differences |
| Local LLM (Ollama) | No API cost | Lower capability; setup complexity |

### Consequences
- **Positive:** Cost-effective for demo volume
- **Positive:** Good capability for classification and extraction
- **Positive:** Well-documented API
- **Negative:** Vendor lock-in (mitigated by abstraction)
- **Negative:** API key required

### Validation
All LLM-dependent tests pass with GPT-4o-mini.

---

## ADR-011: FHIR R4 Ingestion (CareFlow)

**Status:** Accepted
**Date:** 2026-02-XX

### Context
Healthcare systems exchange data via HL7 FHIR. CareFlow's regex-first extraction handles unstructured notes, but structured FHIR data is increasingly common.

### Decision
- Support dual-mode ingestion: FHIR R4 Bundles and unstructured clinical notes
- Parse Patient and Observation resources from FHIR JSON
- Key lab results by LOINC codes (A1C = `4548-4`)
- Both paths feed the same deterministic reasoning engine

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| Unstructured-only | Simpler | Misses structured data sources |
| Full FHIR server (HAPI) | Production-grade | Massive overkill for demo |
| HL7 v2 messages | Legacy compatibility | Older standard; less relevant |

### Consequences
- **Positive:** Demonstrates interoperability awareness
- **Positive:** Structured data skips extraction uncertainty entirely
- **Positive:** Same reasoning engine regardless of input format
- **Negative:** FHIR parsing adds code complexity
- **Negative:** Only supports Bundle type (not full FHIR API)

### Validation
{{fhir_tests}} FHIR ingest tests verify Bundle parsing, LOINC-coded observation extraction, and Patient resource handling.

---

## ADR-012: AI-Powered Test Generation (Platform)

**Status:** Accepted
**Date:** 2026-02-XX

### Context
Edge-case tests for Pydantic schema validation (missing required fields, boundary conditions, type violations) are tedious to write manually and the first thing cut under deadline pressure.

### Decision
- Build a schema-aware test generator (`tools/ai_test_generator.py`)
- Read Pydantic schemas from `intelliflow-core/intelliflow_core/contracts.py`
- Analyze field types, constraints (`ge=0`), and optionality using Pydantic v2 `FieldInfo`
- Generate pytest functions for: valid construction, missing required fields, boundary conditions, optional field defaults

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| Manual test writing only | Full control | Tedious; often skipped; inconsistent coverage |
| Hypothesis (property-based testing) | Statistical coverage | Complex setup; harder to read; not schema-specific |
| LLM-generated tests (freeform) | Flexible | Non-deterministic; may not exercise constraints |

### Consequences
- **Positive:** {{ai_generated_tests}} additional tests generated across {{pydantic_schemas}} schemas (AuditEventSchema, CostTrackingSchema, GovernanceLogEntry)
- **Positive:** Output is verifiable (tests pass or fail — no ambiguity)
- **Positive:** Validates Tier 2 of the Developer Experience Strategy
- **Negative:** Only covers schema-level validation (not business logic)
- **Negative:** Generator must be updated if schema structure changes fundamentally

### Validation
{{ai_generated_tests}} generated tests pass against live schemas. Total platform tests: {{total_tests}} ({{hand_written_tests}} hand-written + {{ai_generated_tests}} generated).

---

## ADR-013: Multi-Layer Cost Optimization (Platform)

**Status:** Accepted
**Date:** 2026-02-XX

### Context
LLM costs scale linearly with usage. Enterprise buyers need predictable per-interaction costs. Optimizing at a single point (e.g., model selection) leaves savings on the table.

### Decision
Implement five compounding cost optimization layers:

1. **Regex-first extraction** — Pattern matching before any LLM call. 100% success on test patients = zero tokens on extraction.
2. **Structured outputs** — ClassifierAgent returns enums (POSITIVE/NEGATIVE/QUERY). No parsing ambiguity, no retry loops.
3. **Model tier selection** — gpt-4o-mini (~$0.15/M input) vs gpt-4o (~$2.50/M input). Sufficient for translation tasks, ~10x cheaper.
4. **Local vector storage for PHI** — Patient queries hit FAISS (free, local). Only guideline lookups touch Pinecone cloud in enterprise mode.
5. **Per-interaction token tracking** — Every LLM call records model, tokens, and cost. Visible in governance panel per-step and per-session.

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| Optimize model selection only | Simple | Leaves 4 other savings on the table |
| Prompt compression / caching | Reduces tokens | Adds complexity; prompt-specific |
| Usage quotas / rate limiting | Caps spend | Doesn't reduce per-interaction cost |

### Consequences
- **Positive:** Each layer reduces what reaches the next — savings compound
- **Positive:** Regex-first alone eliminated all LLM extraction calls in testing
- **Positive:** Token tracking enables per-query cost commitments to enterprise buyers
- **Negative:** Five layers = five architectural decisions to maintain
- **Negative:** Regex success rate (100%) is measured on synthetic patients; real-world notes are messier

### Validation
Cost tracking visible in governance panel. Regex-first extraction validated by 11 extraction tests (all patterns succeed).

---

## Decision Summary Table

| ID | Decision | Status | Key Trade-off |
|----|----------|--------|---------------|
| ADR-001 | Multi-agent orchestrator | Accepted | Auditability over simplicity |
| ADR-002 | Policy-grounded responses | Accepted | Compliance over flexibility |
| ADR-003 | LLM extracts, code decides | Accepted | Reproducibility over adaptability |
| ADR-004 | Regex-first extraction | Accepted | Cost/speed over generality |
| ADR-005 | PHI-aware data residency | Accepted | Privacy over simplicity |
| ADR-006 | Chaos engineering (both modules) | Accepted | Reliability confidence over demo stability |
| ADR-007 | Shared SDK | Accepted | Platform claim over independence |
| ADR-008 | SQLite | Accepted | Demo simplicity over production fidelity |
| ADR-009 | Streamlit | Accepted | Rapid development over UI polish |
| ADR-010 | GPT-4o-mini | Accepted | Cost over capability |
| ADR-011 | FHIR R4 ingestion | Accepted | Interoperability over simplicity |
| ADR-012 | AI test generation | Accepted | Automated coverage over manual consistency |
| ADR-013 | Multi-layer cost optimization | Accepted | Compounding savings over single-point optimization |

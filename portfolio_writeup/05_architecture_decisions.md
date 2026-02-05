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
13 tests pass, including isolated tests for classifier and handlers.

---

## ADR-002: Policy-Grounded Response Generation (SupportFlow)

**Status:** Accepted
**Date:** 2026-01-XX

### Context
In regulated banking, AI responses must be traceable to documented policy. "The AI said" isn't acceptable for compliance.

### Decision
- Store 20 banking policies in markdown format
- Implement keyword-based policy retrieval with content matching
- Inject relevant policies into LLM prompts
- Format responses with explicit policy citations

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| Vector search (embeddings) | Semantic matching | Overkill for 20 policies; adds latency/cost |
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

## ADR-006: Chaos Engineering (SupportFlow)

**Status:** Accepted
**Date:** 2026-01-XX

### Context
Production systems fail. Chaos engineering tests failure handling before deployment.

### Decision
- Deterministic failure injection (30% probability when enabled)
- 7 injection points throughout workflow
- 5 realistic failure scenarios
- Custom ChaosError exception with component tracking

### Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| No chaos testing | Simpler | Unknown failure behavior |
| Random (always-on) chaos | More realistic | Flaky demos; unpredictable |
| External chaos tools (Gremlin) | Production-grade | Overkill for portfolio demo |

### Consequences
- **Positive:** Failure behavior is demonstrated, not assumed
- **Positive:** Graceful degradation is verified
- **Positive:** Error handling paths are exercised
- **Negative:** Deterministic chaos isn't fully realistic
- **Negative:** 30% rate is arbitrary (production would tune)

### Validation
3 chaos tests verify triggering, probability, and error structure.

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
- SDK has its own test suite (32 tests)

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
Both apps successfully import and use intelliflow-core. 32 SDK tests pass.

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

## Decision Summary Table

| ID | Decision | Status | Key Trade-off |
|----|----------|--------|---------------|
| ADR-001 | Multi-agent orchestrator | Accepted | Auditability over simplicity |
| ADR-002 | Policy-grounded responses | Accepted | Compliance over flexibility |
| ADR-003 | LLM extracts, code decides | Accepted | Reproducibility over adaptability |
| ADR-004 | Regex-first extraction | Accepted | Cost/speed over generality |
| ADR-005 | PHI-aware data residency | Accepted | Privacy over simplicity |
| ADR-006 | Chaos engineering | Accepted | Reliability confidence over demo stability |
| ADR-007 | Shared SDK | Accepted | Platform claim over independence |
| ADR-008 | SQLite | Accepted | Demo simplicity over production fidelity |
| ADR-009 | Streamlit | Accepted | Rapid development over UI polish |
| ADR-010 | GPT-4o-mini | Accepted | Cost over capability |

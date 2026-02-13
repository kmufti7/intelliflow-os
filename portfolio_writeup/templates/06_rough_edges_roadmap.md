# Rough Edges & Roadmap

**Audience:** All — Honest assessment of current state and future work

---

## Philosophy

This document exists because:
1. **Interviewers ask:** "What would you do differently?"
2. **Self-awareness matters:** Knowing limitations is a strength
3. **Roadmap clarity:** What's next if development continues

---

## Current Limitations (Honest Assessment)

### SupportFlow Limitations

#### 1. Keyword-Based Policy Retrieval
**Current State:** Policies are matched using keyword mappings (105 keywords → policy IDs).

**Limitation:** No semantic understanding. "I want to dispute a charge" might not match "fee dispute" keywords.

**What Production Would Need:**
- Vector search over policy embeddings
- Semantic similarity matching
- Hybrid retrieval (keywords + embeddings)

**Why It's OK for Demo:**
- {{sf_policies}} policies is small enough for keyword coverage
- Demonstrates the citation pattern (the hard part)
- Swapping retrieval strategy is a config change, not architectural rewrite

#### 2. SQLite Single-Connection
**Current State:** SQLite with asyncio.Lock for concurrency.

**Limitation:** Single-connection bottleneck; not suitable for concurrent users.

**What Production Would Need:**
- PostgreSQL with connection pooling
- Proper transaction isolation
- Read replicas for scaling

**Why It's OK for Demo:**
- Repository pattern allows database swap
- Demo is single-user
- Schema design is production-appropriate

#### 3. Limited Customer History
**Current State:** Only last 5 tickets retrieved for context.

**Limitation:** Long-term customers with extensive history are under-served.

**What Production Would Need:**
- Summarization of historical context
- Relevance-based retrieval (not just recency)
- Customer profile/preferences

**Why It's OK for Demo:**
- Demonstrates the pattern of context injection
- Token limit management is intentional

#### 4. Static Policy Loading
**Current State:** Policies loaded from markdown at startup.

**Limitation:** Policy changes require service restart.

**What Production Would Need:**
- Database-backed policy storage
- Admin UI for policy management
- Version control for policy changes

**Why It's OK for Demo:**
- Policies don't change during demo
- Demonstrates the grounding pattern

---

### CareFlow Limitations

#### 1. Limited Gap Types
**Current State:** {{cf_gap_types}} gap types (A1C threshold, HTN ACE/ARB, BP control).

**Limitation:** Real clinical decision support covers dozens of gap types.

**What Production Would Need:**
- Comprehensive gap rule library
- Specialty-specific rule sets
- Evidence-level weighting

**Why It's OK for Demo:**
- Demonstrates the deterministic reasoning pattern
- Adding rules is additive (doesn't change architecture)
- Quality over quantity for portfolio

#### 2. Hardcoded Gap Rules
**Current State:** Gap detection rules (A1C ≥ 7.0, BP ≥ 140/90, diabetes + HTN + no ACE/ARB) are Python conditionals.

**Limitation:** Adding a new gap type requires code changes, not configuration. A production clinical decision support system would need a rules engine or configuration-driven approach.

**Why It's OK for Demo:**
- Three rules demonstrate the "code decides" pattern clearly
- Each rule is a single assertion test — adding rules is straightforward
- The architecture (extract → rules → explain) doesn't change

#### 3. No A/B Testing of "Therefore" Explanations
**Current State:** LLM generates natural language explanations using a single prompt template.

**Limitation:** Explanation quality depends on prompt quality. No way to compare formats or measure which explanation style clinicians prefer.

**What Production Would Need:**
- Multiple explanation templates
- Clinician feedback loop
- Metrics on explanation usefulness

#### 4. Regex Pattern Coverage
**Current State:** Regex patterns tuned for test patient note format.

**Limitation:** Real clinical notes have high variability (different EHR formats, physician styles).

**What Production Would Need:**
- Broader regex patterns
- More robust LLM fallback
- Possibly ML-based NER

**Mitigating Factor:**
- FHIR R4 ingestion (now built) bypasses regex entirely for structured data — HL7 Bundles with LOINC-coded observations are parsed directly, feeding the same deterministic reasoning engine at zero extraction uncertainty.

**Why It's OK for Now:**
- 100% success on test patients shows the pattern works
- LLM fallback exists for edge cases
- FHIR R4 provides a structured data path that avoids regex variability
- Demonstrates cost optimization intent

#### 5. No Real Clinical Validation
**Current State:** Guidelines are simplified for demonstration.

**Limitation:** Real clinical decision support requires:
- Evidence grading
- Contraindication checking
- Drug interaction awareness
- Patient preference consideration

**Why It's OK for Demo:**
- Reference implementation, not clinical tool
- Disclaimer is prominent
- Demonstrates architectural patterns, not clinical content

#### 6. FAISS Is In-Memory
**Current State:** Patient notes are indexed into in-memory FAISS on each session start.

**Limitation:** Restart loses the index. No persistence across sessions. Production would need FAISS with `write_index` / `read_index` or a managed vector store with persistence guarantees.

#### 7. Keyword-Based De-identification
**Current State:** Concept Query Builder strips PHI using pattern matching (decimal numbers, date formats, patient ID patterns).

**Limitation:** Keyword-based, not NER-based. A sophisticated PHI pattern that doesn't match the blocklist could leak through to external queries. Production would need clinical NER (e.g., spaCy with medical models) for robust de-identification.

#### 8. Pinecone API Key Management
**Current State:** Enterprise mode expects a Pinecone API key as an environment variable.

**Limitation:** No key rotation, secret management, or credential vaulting. Production would need integration with a secrets manager (Vault, AWS Secrets Manager) and key rotation policies.

#### 9. Single-Patient Context
**Current State:** Each analysis is independent; no cross-patient learning.

**Limitation:** Population health insights require aggregation.

**What Production Would Need:**
- Cohort analysis
- Trend detection
- Benchmarking

**Why It's OK for Demo:**
- Focuses on individual patient workflow
- Different (but complementary) use case

---

### intelliflow-core Limitations

#### 1. Governance UI Not Used by Apps
**Current State:** `render_governance_panel()` exists in SDK but apps use custom renderers.

**Limitation:** SDK UI component is underutilized.

**What Should Happen:**
- Apps should import and use shared `render_governance_panel()`
- OR SDK should provide only data contracts, not UI

**Why It Happened:**
- Apps were built first, SDK extracted later
- Custom renderers have app-specific styling
- Partial extraction (contracts used, UI not)

#### 2. No Semantic Versioning
**Current State:** intelliflow-core is installed from git (`pip install git+...@main`). No tagged releases, no semantic versioning (v1.2.3).

**Limitation:** Breaking changes to Pydantic contracts would silently propagate to both modules. No way to pin a known-good version.

**What Production Would Need:**
- Semantic versioning with tagged releases
- Changelog per version
- Deprecation warnings for breaking changes

#### 3. Only 3 Contracts
**Current State:** SDK defines AuditEventSchema, CostTrackingSchema, and GovernanceLogEntry.

**Limitation:** A production governance platform would need dozens of contracts (session schemas, user schemas, error schemas, metric schemas). Three schemas demonstrate the pattern but not the breadth.

#### 4. Limited Model Pricing
**Current State:** Hardcoded pricing for 7 models.

**Limitation:** Pricing changes; new models not included.

**What Production Would Need:**
- API-based pricing updates
- Admin interface for pricing management
- Historical pricing for accurate cost calculation

**Why It's OK for Demo:**
- Demonstrates cost tracking pattern
- Pricing is close enough for demo purposes

### Cost Optimization Limitations

#### 1. Per-Interaction Only
**Current State:** Token tracking is per-interaction and per-step.

**Limitation:** No per-user, per-department, or per-session aggregation. Production would need cost attribution by organizational unit for budgeting and chargeback.

#### 2. No Cost Alerting
**Current State:** Cost is tracked and displayed. No alerts when costs exceed thresholds.

**Limitation:** Visible ≠ actionable. Production would need budget caps, alerting on anomalous spend, and automated throttling when cost thresholds are breached.

#### 3. Synthetic Patient Baseline
**Current State:** Regex-first success rate (100%) is measured on {{cf_test_patients}} synthetic patients with predictable note formats.

**Limitation:** Real clinical notes (different EHR systems, physician abbreviations, dictation artifacts) would have lower regex success rates. The LLM fallback path is built but untested at scale.

---

## What I'd Do Differently

### If Starting Over

1. **Extract SDK First**
   - Build contracts and governance patterns before applications
   - Ensures consistent usage from the start
   - Avoids partial extraction problem

2. **Use Vector Search from Start (SupportFlow)**
   - Even for {{sf_policies}} policies, FAISS is not much harder than keywords
   - Would demonstrate semantic retrieval pattern
   - Better scaling story

3. **More Gap Types (CareFlow)**
   - 5-7 gap types would be more impressive
   - Still manageable for demo
   - Better coverage of clinical scenarios

4. **Integration Tests (Partially Addressed)**
   - CareFlow now has 15 chaos integration tests that exercise the `analyze_patient()` code path end-to-end
   - SupportFlow still lacks integration-level tests
   - More end-to-end workflow tests would add confidence across both modules

5. **Streamlit Cloud Deployment**
   - Live demos are more impressive than "clone and run"
   - Secrets management is the main blocker
   - Would require environment configuration work

---

## Future Roadmap (If Continuing)

### Phase 1: Polish (Low Effort, High Payoff)

| Item | Effort | Impact |
|------|--------|--------|
| Vector search for SupportFlow policies | 2 hrs | Semantic retrieval story |
| Streaming responses | 1 hr | Better UX in demos |
| Combined platform video | 30 min | Single demo showing both modules |
| Streamlit Cloud deployment | 2-3 hrs | Live demo links |

### Phase 2: Depth (Medium Effort)

| Item | Effort | Impact |
|------|--------|--------|
| 2-3 more CareFlow gap types | 4 hrs | Clinical credibility |
| End-to-end integration tests | 3 hrs | Confidence in workflows |
| Shared governance panel usage | 2 hrs | SDK value demonstration |
| PostgreSQL migration (SupportFlow) | 3 hrs | Production readiness |

### Phase 3: Breadth (Higher Effort)

| Item | Effort | Impact |
|------|--------|--------|
| Third module (ComplianceFlow?) | 8-12 hrs | Platform scale |
| MCP integration | 4-6 hrs | Enterprise integration story |
| Multi-tenant support | 6-8 hrs | SaaS pattern |
| Metrics dashboard | 4-5 hrs | Operations visibility |

---

## Known Technical Debt

| Debt | Location | Impact | Fix |
|------|----------|--------|-----|
| Governance panel not used | SupportFlow, CareFlow | SDK underutilized | Import from SDK |
| Hardcoded model pricing (7 models) | intelliflow-core | Pricing drift | Database-backed pricing |
| Limited integration tests | SupportFlow, intelliflow-core | Gaps in coverage | Add workflow tests (CareFlow has 15 chaos integration tests) |
| Async lock bottleneck | SupportFlow DB | Concurrency limit | PostgreSQL migration |
| Static policy loading | SupportFlow | Restart for changes | Database-backed policies |
| Test generator covers {{pydantic_schemas}} schemas | intelliflow-core | Limited to contract validation | Extend to app-specific models |

---

## Questions I'd Ask in Production

### Before Deployment
1. What's the SLA for response time? (Affects LLM choice, caching strategy)
2. What's the expected concurrent user count? (Affects database choice, scaling)
3. What compliance certifications are required? (SOC2, HIPAA BAA, etc.)
4. Who owns the AI decision policy? (Affects policy management workflow)
5. What's the escalation path for AI errors? (Affects error handling, alerting)

### During Operation
1. What's the actual cost per interaction? (Validates tracking)
2. Which gap types are most frequently detected? (Guides rule expansion)
3. What's the LLM fallback rate for extraction? (Guides regex improvement)
4. Which policies are cited most often? (Guides policy organization)
5. What's the chaos mode failure rate in staging? (Validates resilience)

---

## Interview Preparation: "What Would You Do Differently?"

### Short Answer
"I'd extract the shared SDK first, before building the applications. Building apps first then extracting led to partial adoption — the contracts are used but the UI components aren't. Starting with the SDK would ensure consistent patterns from day one."

### Longer Answer
"Three things:

1. **SDK-first development**: Extract governance patterns before building apps. The current state has apps using shared contracts but not the shared UI components.

2. **Vector search from the start**: Even for {{sf_policies}} policies, FAISS isn't much harder than keyword matching and tells a better story about semantic understanding.

3. **More comprehensive testing**: CareFlow now has chaos integration tests, but SupportFlow tests are still mostly unit-level. Broader end-to-end workflow tests would catch integration issues across both modules.

That said, the architectural patterns are sound. These are polish items, not structural problems."

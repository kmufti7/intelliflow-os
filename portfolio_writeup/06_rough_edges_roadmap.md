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
- 20 policies is small enough for keyword coverage
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
**Current State:** 3 gap types (A1C threshold, HTN ACE/ARB, BP control).

**Limitation:** Real clinical decision support covers dozens of gap types.

**What Production Would Need:**
- Comprehensive gap rule library
- Specialty-specific rule sets
- Evidence-level weighting

**Why It's OK for Demo:**
- Demonstrates the deterministic reasoning pattern
- Adding rules is additive (doesn't change architecture)
- Quality over quantity for portfolio

#### 2. Regex Pattern Coverage
**Current State:** Regex patterns tuned for test patient note format.

**Limitation:** Real clinical notes have high variability (different EHR formats, physician styles).

**What Production Would Need:**
- Broader regex patterns
- More robust LLM fallback
- Possibly ML-based NER

**Why It's OK for Demo:**
- 100% success on test patients shows the pattern works
- LLM fallback exists for edge cases
- Demonstrates cost optimization intent

#### 3. No Real Clinical Validation
**Current State:** Guidelines are simplified for demonstration.

**Limitation:** Real clinical decision support requires:
- Evidence grading
- Contraindication checking
- Drug interaction awareness
- Patient preference consideration

**Why It's OK for Demo:**
- Portfolio project, not clinical tool
- Disclaimer is prominent
- Demonstrates architectural patterns, not clinical content

#### 4. Single-Patient Context
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

#### 2. Limited Model Pricing
**Current State:** Hardcoded pricing for 5 models.

**Limitation:** Pricing changes; new models not included.

**What Production Would Need:**
- API-based pricing updates
- Admin interface for pricing management
- Historical pricing for accurate cost calculation

**Why It's OK for Demo:**
- Demonstrates cost tracking pattern
- Pricing is close enough for demo purposes

---

## What I'd Do Differently

### If Starting Over

1. **Extract SDK First**
   - Build contracts and governance patterns before applications
   - Ensures consistent usage from the start
   - Avoids partial extraction problem

2. **Use Vector Search from Start (SupportFlow)**
   - Even for 20 policies, FAISS is not much harder than keywords
   - Would demonstrate semantic retrieval pattern
   - Better scaling story

3. **More Gap Types (CareFlow)**
   - 5-7 gap types would be more impressive
   - Still manageable for demo
   - Better coverage of clinical scenarios

4. **Integration Tests**
   - Current tests are mostly unit/component level
   - End-to-end workflow tests would add confidence
   - Would catch integration issues earlier

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
| Hardcoded model pricing | intelliflow-core | Pricing drift | Database-backed pricing |
| No integration tests | All repos | Gaps in coverage | Add workflow tests |
| Async lock bottleneck | SupportFlow DB | Concurrency limit | PostgreSQL migration |
| Static policy loading | SupportFlow | Restart for changes | Database-backed policies |

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

2. **Vector search from the start**: Even for 20 policies, FAISS isn't much harder than keyword matching and tells a better story about semantic understanding.

3. **More comprehensive testing**: Current tests are mostly unit-level. End-to-end workflow tests would catch integration issues and build more confidence.

That said, the architectural patterns are sound. These are polish items, not structural problems."

# Interview Talking Points

**Audience:** Self — Quick reference for interviews

---

## The 30-Second Pitch

"I built IntelliFlow OS, a governance-first AI platform for regulated industries. It's two production-ready modules — banking support and healthcare gap analysis — sharing a common SDK. 111 tests passing, full audit trails, and patterns like 'LLM extracts, code decides' that prevent hallucination in critical reasoning. The key insight: in regulated industries, deployability matters more than capability."

---

## Quick Stats (Memorize These)

| Metric | Value |
|--------|-------|
| Total tests | 111 |
| Repositories | 4 |
| SupportFlow tests | 13 |
| CareFlow tests | 66 |
| intelliflow-core tests | 32 |
| Banking policies | 20 |
| Clinical guidelines | 10 |
| Sample patients | 5 |
| Chaos failure modes | 5 |
| Regex extraction success | 100% on test patients |

---

## Key Patterns (Name + One Sentence)

### 1. Governance-First Architecture
Every decision logged with timestamp, component, confidence, and reasoning.

### 2. "LLM Extracts, Code Decides"
LLM pulls facts from notes; Python rules detect gaps; LLM explains with citations. No hallucination in reasoning.

### 3. Policy-Grounded Responses
Every AI response cites the specific policy it's based on (POLICY-002, guideline_001).

### 4. PHI-Aware Data Residency
Patient data stays local (FAISS); external queries receive only de-identified concepts.

### 5. Chaos Engineering
Deterministic failure injection (30%) proves graceful degradation.

### 6. Regex-First Extraction
Try regex (free, fast, deterministic); fall back to LLM only when needed.

### 7. Platform SDK
Shared pip-installable package; both apps import same governance UI and contracts.

---

## Common Interview Questions

### "Tell me about a project you built."

"I built IntelliFlow OS, a governance-first AI platform for regulated industries. It has two modules: SupportFlow for banking and CareFlow for healthcare. Both share a common SDK.

The key innovation in SupportFlow is policy-grounded responses — every AI response cites the specific banking policy it's based on. In CareFlow, it's the 'LLM extracts, code decides' pattern — the LLM extracts facts from clinical notes, but Python rules detect care gaps. No hallucination in the reasoning step.

111 tests pass across the platform, including chaos engineering tests that verify graceful failure handling."

---

### "Why did you build this?"

"I wanted to demonstrate that AI can be both capable and deployable in regulated industries. Most AI demos optimize for impressiveness. Enterprise adoption is blocked by different concerns: Can we audit it? Can we explain it? Can we predict costs? Can we handle failures?

IntelliFlow OS addresses each of these directly. It's a portfolio reference implementation showing enterprise patterns that I couldn't easily demonstrate in my day job."

---

### "What was the hardest technical challenge?"

"The 'Therefore problem' in CareFlow. Healthcare AI demos often let the LLM reason about clinical logic — 'Patient has high A1C, therefore...' But LLMs hallucinate, and in healthcare that's dangerous.

The solution was separating extraction from reasoning. The LLM extracts facts (A1C: 8.2%, diagnoses: diabetes). Python code applies the rules (if a1c >= 7.0: gap = True). The LLM only explains the result with citations.

This makes gap detection reproducible — same patient, same gaps, every time. And the rules are explicit Python, so clinicians can verify them."

---

### "What would you do differently?"

"Three things:

1. Extract the SDK first, before building applications. I built apps first then extracted common code, which led to partial adoption — contracts are used, UI components aren't.

2. Use vector search for policy retrieval from the start. Keyword matching works for 20 policies, but FAISS isn't much harder and tells a better semantic story.

3. More comprehensive integration tests. Current tests are mostly unit-level. End-to-end workflow tests would build more confidence."

---

### "How does the audit logging work?"

"Every component logs to a governance trail: component name, action, timestamp, success/failure, confidence score, and reasoning. In SupportFlow, you can see: Classifier classified as NEGATIVE with 0.90 confidence, Router sent to negative_handler, PolicyService cited POLICY-002.

The logs are queryable — you can get all actions by a specific agent, all failures, average duration by component. If a regulator asks 'why did the system say X?', you can show the exact decision chain."

---

### "How do you handle PHI?"

"CareFlow has a PHI-aware data residency architecture. Patient data stays in local FAISS indexes — it never leaves the machine. When we need to query external systems like Pinecone for clinical guidelines, the Concept Query Builder strips all identifiers first.

So instead of sending 'Patient PT001 A1C 8.2%', we send 'diabetes glycemic control guidelines'. The external system never sees patient-specific data. There's also validation that catches patterns like dates, patient IDs, and numeric values before any external query."

---

### "How do you track costs?"

"Per-interaction token tracking. Every LLM call records: model used, input tokens, output tokens, calculated cost. The system knows the pricing for different models — GPT-4o-mini, GPT-4, Claude variants.

You can query cost by agent, by model, by session. The UI shows running session cost in real-time. This enables finance to budget and allocate costs to departments or use cases."

---

### "Why multi-agent instead of one agent?"

"Banking support has distinct task types — complaints need tickets, praise needs acknowledgment, queries need lookups. A single agent tries to do everything and fails at edge cases.

With specialized agents: ClassifierAgent determines type, then routes to PositiveHandler, NegativeHandler, or QueryHandler. Each agent has clear responsibility, can be tested independently, and improved without affecting others.

The orchestrator coordinates the flow and logs every decision. If something goes wrong, you know exactly which component failed."

---

### "What's the chaos engineering for?"

"Production systems fail — APIs time out, databases drop connections. The question isn't whether failures happen, it's whether the system handles them gracefully.

Chaos mode injects failures at 7 points in the workflow with 30% probability. Timeouts, rate limits, database errors. The system catches these, logs them, and returns user-friendly messages instead of crashing.

Three tests verify the chaos behavior. It's deterministic, so demos are reproducible — you can show failure handling on demand."

---

## For PM Interviews

### "How did you prioritize features?"

"Governance first, capability second. The features that get AI demos approved — audit trails, cost tracking, explainable decisions — are different from the features that make demos impressive.

I prioritized deployability over capability. Policy citations, deterministic reasoning, PHI protection, chaos testing. These aren't flashy, but they're what blocks enterprise adoption."

### "How did you validate requirements?"

"I reverse-engineered from compliance blockers. What does a compliance officer need to approve an AI system? Audit trail. What does legal need? Source citations. What does finance need? Cost predictability.

The test patients in CareFlow represent realistic clinical scenarios — Maria Garcia has 3 gaps (high risk), Linda Martinez is at goal (no gaps). The policies in SupportFlow cover real banking topics — fee disputes, card replacement, account closures."

### "What metrics would you track in production?"

"Four categories:

1. **Reliability**: Error rate, latency, chaos test pass rate
2. **Cost**: Per-interaction cost, cost by model, cost by use case
3. **Quality**: Policy citation rate, gap detection accuracy
4. **Compliance**: Audit completeness, PHI safety validation rate

The governance log already captures most of this. Production would add alerting and dashboards."

---

## For Technical Interviews

### "Walk me through the data flow."

**SupportFlow:**
```
Customer message
→ Orchestrator receives, creates ticket
→ ClassifierAgent categorizes (POSITIVE/NEGATIVE/QUERY)
→ Orchestrator routes to appropriate handler
→ Handler retrieves relevant policies
→ Handler generates response with citations
→ Orchestrator logs and returns result
```

**CareFlow:**
```
Patient ID selected
→ Extract facts from latest note (regex-first, LLM fallback)
→ Apply deterministic rules for gap detection
→ Generate "Therefore" statements
→ (Optional) Book appointment based on gaps
→ Compose explanation with citations
```

### "What's your testing strategy?"

"Layered:

1. **Unit tests**: Individual functions (regex patterns, cost calculation)
2. **Component tests**: Agents and services (classifier, reasoning engine)
3. **Contract tests**: Pydantic validation (schemas reject invalid data)
4. **Chaos tests**: Failure injection and handling

Missing: end-to-end integration tests. That's a known gap."

### "How would you scale this?"

"Three axes:

1. **Database**: SQLite → PostgreSQL with connection pooling
2. **Vector store**: FAISS → managed Pinecone for guidelines
3. **Compute**: Stateless handlers → containerized with horizontal scaling

The architecture supports this. Repository pattern abstracts database. LLMClient abstracts provider. The hard part — governance patterns — doesn't change with scale."

---

## Closing Statement (End of Interview)

"IntelliFlow OS demonstrates that AI can be both capable and compliant. The patterns — governance-first, deterministic reasoning, PHI-aware architecture — are what enterprise adoption actually requires. I built this to show I can think about AI systems holistically, not just prompt engineering."

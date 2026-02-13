# Interview Talking Points

**Audience:** Self — Quick reference for interviews

---

## The 30-Second Pitch

"I built IntelliFlow OS, a governance-first AI platform for regulated industries. It's two production-ready modules — banking support and healthcare gap analysis — sharing a common SDK. {{total_tests}} tests passing ({{hand_written_tests}} hand-written plus {{ai_generated_tests}} AI-generated from a schema-aware test generator), full audit trails, chaos engineering in both modules, FHIR R4 ingestion, and patterns like 'LLM extracts, code decides' that prevent hallucination in critical reasoning. Backed by {{enterprise_docs}} enterprise docs covering NIST AI RMF, OWASP, and EU AI Act. The key insight: in regulated industries, deployability matters more than capability."

---

## Quick Stats (Memorize These)

| Metric | Value |
|--------|-------|
| Total tests | {{total_tests}} ({{hand_written_tests}} hand-written + {{ai_generated_tests}} AI-generated) |
| Repositories | {{repos}} |
| SupportFlow tests | {{supportflow_tests}} |
| CareFlow tests | {{careflow_tests}} (7 categories) |
| intelliflow-core tests | {{core_tests}} |
| Banking policies | {{sf_policies}} |
| Clinical guidelines | {{cf_guidelines}} |
| Sample patients | {{cf_test_patients}} |
| Chaos failure modes | 7 (5 SupportFlow + 2 CareFlow) |
| Chaos tests | {{chaos_tests_total}} (13 + 15) |
| Enterprise docs | {{enterprise_docs}} |
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
Both modules: SupportFlow uses 30% probabilistic injection; CareFlow uses toggled FAISS/Pinecone failures with safe clinical fallback. {{chaos_tests_total}} tests total.

### 6. Regex-First Extraction
Try regex (free, fast, deterministic); fall back to LLM only when needed.

### 7. Platform SDK
Shared pip-installable package; both apps import same governance UI and contracts.

### 8. Enterprise Evidence Pack
{{enterprise_docs}} documents (NIST AI RMF, OWASP LLM Top 10, EU AI Act, cost model, observability, data dictionary, vendor comparison, ethics) validated by {{verification_checks}} automated checks.

### 9. AI Test Generator
Schema-aware tool reads Pydantic contracts from the shared SDK and generates {{ai_generated_tests}} edge-case pytest suites (boundary conditions, missing required fields, type validation). Output is binary — tests pass or fail.

### 10. Developer Experience Strategy
Strategy memo framing three tiers of AI-native developer tooling: onboarding (Tier 1), testing (Tier 2, implemented), observability (Tier 3). Recommends starting with testing because output is verifiable.

---

## Architecture Talking Points (Say These Out Loud)

### Deterministic Reasoning ("Code Decides")

- "The moment I stopped letting the LLM decide was when I realized I was asking a language model to do math. 8.2 is greater than 7.0. Code knows that. The LLM's job is to explain why that matters to the patient."

- "Every gap detection step in CareFlow is separately testable. I can assert that A1C 8.2 with threshold 7.0 produces a MODERATE severity gap. No mocking the LLM, no flaky tests."

- "If a regulator asks 'why did your system flag this patient,' I can point to the rule, the input value, and the threshold. Not 'the model thought so.'"

### PHI-Aware Data Residency

- "Patient data never leaves the machine. I split the vector architecture by data sensitivity class. PHI stays in local FAISS, guidelines go to Pinecone."

- "The Concept Query Builder is the boundary. It takes 'John Smith, A1C 8.2' and turns it into 'diabetes management elevated A1C.' The patient's identity never touches the cloud."

- "I designed two deployment modes because enterprise teams have different comfort levels. Local mode is zero-config, zero-risk. Enterprise mode adds cloud performance for guidelines without PHI exposure."

### Platform Architecture (Shared SDK)

- "Both modules import governance UI from the same pip-installable package. That's what makes it a platform, not two apps with similar code."

- "If I change the audit log schema in intelliflow-core, both modules get the update. With copy-paste, they'd drift."

- "I chose a separate SDK over a monorepo because I wanted independent deployment and clean interfaces. The Pydantic contracts ARE the interface."

### Cost Optimization (Five Layers)

- "Cost optimization isn't one decision, it's five. Regex-first eliminated LLM extraction calls entirely. Structured outputs prevent parsing retries. gpt-4o-mini is 10x cheaper than gpt-4o. Local FAISS means no cloud vector DB costs for PHI. And token tracking makes it all visible."

- "If someone asks me 'how much does each interaction cost,' I can show them. Per-step, per-interaction, visible in the governance panel."

- "The regex-first pattern is the biggest win. Why send a clinical note to an LLM to extract an A1C value that's always formatted as 'A1C: X.X%'? Pattern matching is free."

---

## Common Interview Questions

### "Tell me about a project you built."

"I built IntelliFlow OS, a governance-first AI platform for regulated industries. It has two modules: SupportFlow for banking and CareFlow for healthcare. Both share a common SDK.

The key innovation in SupportFlow is policy-grounded responses — every AI response cites the specific banking policy it's based on. In CareFlow, it's the 'LLM extracts, code decides' pattern — the LLM extracts facts from clinical notes, but Python rules detect care gaps. No hallucination in the reasoning step.

{{total_tests}} tests pass across the platform — {{hand_written_tests}} hand-written plus {{ai_generated_tests}} AI-generated from a schema-aware test generator — including {{chaos_tests_total}} chaos engineering tests across both modules and FHIR R4 ingestion for healthcare interoperability."

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

2. Use vector search for policy retrieval from the start. Keyword matching works for {{sf_policies}} policies, but FAISS isn't much harder and tells a better semantic story.

3. More comprehensive integration tests. CareFlow now has 15 chaos integration tests, but SupportFlow tests are still mostly unit-level. Broader end-to-end workflow tests across both modules would build more confidence."

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

### "What about compliance documentation?"

"I built an {{enterprise_docs}}-document Enterprise Evidence Pack mapped to real frameworks — NIST AI RMF for risk management, OWASP LLM Top 10 for security, EU AI Act for regulatory alignment. It also includes a cost model, observability guide, data dictionary, vendor comparison, and ethics framework.

The key is the {{verification_checks}}-check automated verification script. It validates that the documentation matches the actual codebase — schema counts, test counts, feature claims. So the docs aren't just written once and forgotten. If the code changes, the verification catches the drift."

---

### "Why multi-agent instead of one agent?"

"Banking support has distinct task types — complaints need tickets, praise needs acknowledgment, queries need lookups. A single agent tries to do everything and fails at edge cases.

With specialized agents: ClassifierAgent determines type, then routes to PositiveHandler, NegativeHandler, or QueryHandler. Each agent has clear responsibility, can be tested independently, and improved without affecting others.

The orchestrator coordinates the flow and logs every decision. If something goes wrong, you know exactly which component failed."

---

### "What's the chaos engineering for?"

"Production systems fail — APIs time out, databases drop connections. The question isn't whether failures happen, it's whether the system handles them gracefully.

Both modules have chaos engineering. SupportFlow injects failures at 7 points with 30% probability — timeouts, rate limits, database errors. CareFlow has toggled FAISS and Pinecone failures — when enabled, the system returns a safe fallback that explicitly warns 'no clinical decisions should be made.'

{{chaos_tests_total}} tests verify chaos behavior across both modules, including integration tests that exercise the exact patient-selection code path the UI uses. It's deterministic, so demos are reproducible."

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
  OR ingest structured data via FHIR R4 Bundle (Patient + Observation)
→ Chaos gate: check for injected failures (FAISS/Pinecone)
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
4. **Chaos tests**: Failure injection and handling ({{chaos_tests_total}} tests across both modules)
5. **Integration tests**: CareFlow has 15 chaos integration tests exercising the `analyze_patient()` code path end-to-end

Gap: SupportFlow still lacks integration-level tests."

### "How would you scale this?"

"Three axes:

1. **Database**: SQLite → PostgreSQL with connection pooling
2. **Vector store**: FAISS → managed Pinecone for guidelines
3. **Compute**: Stateless handlers → containerized with horizontal scaling

The architecture supports this. Repository pattern abstracts database. LLMClient abstracts provider. The hard part — governance patterns — doesn't change with scale."

---

## Closing Statement (End of Interview)

"IntelliFlow OS demonstrates that AI can be both capable and compliant. The patterns — governance-first, deterministic reasoning, PHI-aware architecture — are what enterprise adoption actually requires. I built this to show I can think about AI systems holistically, not just prompt engineering."

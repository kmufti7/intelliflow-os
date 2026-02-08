# IntelliFlow OS — Governance & Compliance

## Purpose

This document describes the governance architecture of IntelliFlow OS, a reference implementation for AI systems in regulated industries.

## NIST AI Risk Management Framework (AI RMF) Alignment

Reference: [NIST AI RMF 1.0](https://www.nist.gov/artificial-intelligence/risk-management-framework)

### GOVERN — Establish governance structures

| Principle | IntelliFlow OS Implementation |
|-----------|-------------------------------|
| Accountability | Every AI decision logged with agent name, action, reasoning, and confidence score. Full audit trail per interaction. |
| Transparency | Governance UI panel renders real-time decision traces. Policy citations included in every response. |
| Role clarity | Agents have explicit responsibilities (classifier, handler, reasoner). No agent operates outside its defined scope. |

### MAP — Identify and categorize risks

| Risk Category | How Addressed |
|---------------|---------------|
| Clinical hallucination | "LLM extracts, code decides" — deterministic Python rules for gap detection, not LLM reasoning. |
| Data leakage (PHI) | PHI stays in local FAISS. External queries de-identified via Concept Query Builder. |
| Cost overrun | Per-interaction token tracking. Regex-first extraction eliminates unnecessary LLM calls. |
| Prompt injection | Enum-based classification constrains routing. System prompts enforce policy-grounded answers. |

### MEASURE — Assess and quantify risks

| Metric | Measurement |
|--------|-------------|
| Test coverage | 111 tests across platform (32 SDK + 13 SupportFlow + 66 CareFlow) |
| Extraction accuracy | 100% regex success rate on structured clinical data |
| Audit completeness | Every interaction produces audit log entries with timestamps, confidence, and reasoning |
| Cost visibility | Token counts and USD costs tracked per interaction, visible in governance UI |

### MANAGE — Prioritize and respond to risks

| Control | Implementation |
|---------|----------------|
| Chaos engineering | SupportFlow injects failures at 7 checkpoints (30% rate) to validate graceful degradation |
| Pydantic validation | All audit events and cost records validated through strict schemas; malformed data rejected |
| CI/CD gates | GitHub Actions runs full test suite on every push; no merge without green |
| Deterministic routing | Enum-based classification prevents unpredictable agent behavior |

## Governance UI

Both SupportFlow and CareFlow render a real-time governance panel (Streamlit sidebar) showing:
- Timestamped audit entries
- Agent decisions with reasoning
- Confidence scores
- Token usage and cost per interaction
- Policy/guideline citations

This panel is powered by `intelliflow-core`'s `governance_ui.py` module, ensuring consistent governance rendering across all modules.

---

## EU AI Act Classification

Under the **EU AI Act**, the CareFlow module (Clinical Decision Support) would likely be classified as a **High-Risk AI System (Annex III)** if deployed in production.

**Why this matters:**
- Healthcare AI systems that influence clinical decisions fall under strict regulatory requirements in the EU.
- Understanding this classification demonstrates awareness of global AI regulatory landscape.

**Relevant Controls Implemented:**

| Article | Requirement | IntelliFlow OS Implementation |
|---------|-------------|-------------------------------|
| **Article 13** | Transparency | System explicitly identifies itself as an AI agent. Governance UI shows reasoning trace. |
| **Article 14** | Human Oversight | "Code as Judge" pattern ensures human-defined logic (Python) supersedes model probability for critical health metrics. |
| **Article 15** | Accuracy | Deterministic extraction (regex-first) ensures accuracy of input data. Pydantic validation rejects malformed data. |

**Disclaimer:** This is a reference implementation demonstrating architectural patterns. It is not a production-certified medical device and has not undergone formal EU AI Act conformity assessment.

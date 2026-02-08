# IntelliFlow OS — Test Strategy

## Principles

1. **Test structure, not prose.** Enums, DB state, event schemas, deterministic outputs.
2. **Deterministic logic is tested exhaustively.** Gap rules, extraction patterns, routing decisions.
3. **Model outputs are tested for required fields and citations, not exact wording.**

## Test Layers

| Layer | What It Tests | Examples |
|-------|---------------|----------|
| **Unit** | Pure functions | Extraction regexes, gap rule logic, schema validation, cost calculations |
| **Integration** | Orchestrator flows | End-to-end message handling, persistence, audit log creation |
| **Failure Mode** | Graceful degradation | Chaos toggle (SupportFlow), missing data handling |

## What We Intentionally Do Not Test

- Exact LLM phrasing (non-deterministic)
- Cosmetic UI formatting beyond smoke checks

## Coverage by Module

| Module | Tests | Focus Areas |
|--------|-------|-------------|
| intelliflow-core | 32 | Contracts, helpers, governance UI components |
| SupportFlow | 13 | Classification, routing, policy retrieval, ticket creation |
| CareFlow | 69 | Extraction (11), Reasoning (14), Booking (11), Concept Query (15), Retrieval (15), FHIR Ingest (3) |
| **Total** | **114** | |

## CI/CD

- GitHub Actions runs on every push
- All tests must pass before merge
- No flaky tests allowed (deterministic assertions only)

## Philosophy

> "If the LLM changes its phrasing, the test should still pass. If the logic changes its decision, the test should fail."

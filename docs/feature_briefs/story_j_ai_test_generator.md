# FEATURE BRIEF: AI Test Generator

**Story ID:** J
**Date:** 2026-02-12
**Produced by:** Architect Agent
**Consumed by:** Claude Code `/add-feature` command

---

## 1. What Was Built

A schema-aware AI test generator that reads Pydantic contracts from the shared SDK and produces edge-case pytest suites automatically. The tool introspects 3 Pydantic models (GovernanceEvent, CostRecord, AuditEntry) at runtime, extracts field types, constraints (min/max values, required vs. optional, allowed enum values), and generates 35 focused test cases covering boundary conditions, missing required fields, and type validation.

The generator uses the "LLM translates, code decides" pattern: the LLM reads schema definitions and produces Python test code, but the output is binary — tests either pass or fail. There's no ambiguity about quality because the generated tests validate against the live schemas.

**Location:** IntelliFlow_OS/tools/ai_test_generator.py
**New files:** ai_test_generator.py, generated test files (35 tests)
**Modified files:** None
**Tests added:** 35 AI-generated edge-case tests (boundary conditions, missing required fields, type validation)

---

## 2. Why It Matters

**Pain point:** Manual test writing for schema validation is tedious and incomplete — developers miss edge cases (boundary values, optional field combinations, type coercion) because they test the happy path and a few obvious failures.

**Who cares:** Engineering leads responsible for test coverage; QA teams evaluating schema robustness; platform teams maintaining shared contracts across multiple modules.

**Market context:** AI-assisted development is a growing category, but most tools generate code (Copilot, Cursor). Generating tests is harder because the output must be verifiable. This positions IntelliFlow OS in the "AI-native developer tooling" space with a key differentiator: the generated output has binary correctness (pass/fail), unlike generated application code which requires human review.

---

## 3. PM Framing

**Decision rationale:** Testing was chosen as the entry point for AI-native developer tooling because test output is verifiable — tests either pass or fail. Code generation (Copilot-style) requires human review to assess quality. Test generation produces artifacts with binary correctness, making it the safest starting point for AI-assisted development.

**Extensibility:** The same schema-introspection approach can generate API documentation, migration scripts, or mock data factories. The pattern is: read contracts → generate artifacts → validate output.

**Risk reduced:** Schema drift between modules. If a Pydantic contract changes (e.g., a field becomes required), regenerated tests catch the incompatibility immediately. Manual tests might not cover the changed constraint.

---

## 4. Interview Hook

> "I built an AI test generator that reads Pydantic schemas from the shared SDK and produces 35 edge-case pytest suites. The key insight is that testing is the right entry point for AI-native tooling because the output is binary — tests pass or fail. You don't need to review generated tests the way you'd review generated application code. It's the 'LLM translates, code decides' pattern applied to developer tools."

---

## 5. Architecture Impact

**Control flow changed?** No. The test generator is a standalone tool, not part of the runtime pipeline.
**New data paths?** No. It reads existing Pydantic schemas; it doesn't create new data flows.
**New dependencies?** No. Uses existing OpenAI client and Pydantic (already in the platform).
**Mermaid diagrams need update?** No.

---

## 6. New Data Structures

None. The tool reads existing Pydantic schemas (GovernanceEvent, CostRecord, AuditEntry) — it doesn't create new ones.

---

## 7. Trade-offs

**What you chose:** Schema-aware generation from Pydantic contracts, producing pytest files that validate against live schemas.

**What you gave up:** Full property-based testing (Hypothesis-style). Property-based testing generates random inputs and checks invariants. The AI generator produces specific, readable test cases. Property-based testing finds more edge cases but produces less readable tests.

**What production would need:** Regeneration on schema change (CI hook that re-runs the generator when Pydantic models change), coverage tracking to identify which schema constraints lack generated tests, and support for nested/composite schemas.

---

## 8. Rough Edges

1. Only reads top-level fields from 3 schemas — doesn't handle nested Pydantic models or complex validators
2. Generates tests once; no CI hook to regenerate when schemas change
3. No deduplication check — if run twice, produces duplicate test files
4. Limited to Pydantic v2 field introspection; custom validators not detected
5. Doesn't track which percentage of schema constraints are covered by generated tests

---

## 9. ATS Keywords

AI test generation, Pydantic, schema-aware, pytest, edge-case testing, developer tooling, AI-native, code generation, contract testing, schema validation

---

## 10. Metrics Changed

| Metric | Old Value | New Value |
|--------|-----------|-----------|
| total_tests | 129 | 164 |
| ai_generated_tests | 0 | 35 |

Note: These metrics are already reflected in portfolio_config.yaml and CLAUDE.md Truth Table.

---

## 11. Forbidden Phrases

| Forbidden | Use Instead |
|-----------|-------------|
| "3 developer tools" | "1 developer tool (AI test generator)" — NL log query and scaffold generator are NOT built |
| "intelliflow-core/tools/" | "IntelliFlow_OS/tools/" (actual location of ai_test_generator.py) |

Note: These are already in CLAUDE.md forbidden phrases.

---

## 12. Cascade Checklist

- [ ] CLAUDE.md truth table updated
- [ ] CLAUDE.md story inventory updated
- [ ] CLAUDE.md forbidden phrases updated (if any)
- [ ] portfolio_config.yaml updated (if metrics changed)
- [ ] render_portfolio.py run (if metrics changed)
- [ ] 8 portfolio files updated with strategic context
- [ ] ARCHITECTURE.md updated (if architecture impact = yes)
- [ ] DATA_DICTIONARY.md updated (if new data structures)
- [ ] CHANGELOG.md entry added
- [ ] Module README updated
- [ ] verify_cascade.py passes
- [ ] No forbidden phrases in any updated file

---

**End of Feature Brief**

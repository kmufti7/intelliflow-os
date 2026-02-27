# FEATURE BRIEF: Scaffold Generator

**Story ID:** L
**Date:** 2026-02-13
**Produced by:** Architect Agent
**Consumed by:** Claude Code `/add-feature` command

---

## 1. What Was Built

A developer tool that generates platform-compliant Python boilerplate from a natural language description. The tool reads Pydantic schemas from intelliflow-core (AuditEventSchema, CostTrackingSchema, GovernanceLogEntry), injects them into the LLM prompt as context, then validates every line of generated code using `ast.parse()` before returning it.

**Location:** intelliflow-os (this repo)
**New files:** `tools/scaffold_generator.py`, `tests/test_scaffold_generator.py`
**Modified files:** None
**Tests added:** 14 tests — ast.parse() validation (4), markdown fence stripping (2), end-to-end generation (3), retry logic (2), cost tracking (2), system prompt (1)

---

## 2. Why It Matters

**Pain point:** New developers joining a governance-first platform must learn import conventions, audit logging patterns, cost tracking, and Pydantic contract usage before writing a single useful line of code. Onboarding friction slows velocity.
**Who cares:** Platform engineering teams, dev leads hiring junior engineers, enterprises with compliance onboarding requirements
**Market context:** Developer experience tooling is a competitive differentiator for internal platforms. GitHub Copilot set the expectation that code generation should be context-aware. Platform-specific generators go further: they enforce organizational patterns, not just language syntax.

---

## 3. PM Framing

**Decision rationale:** The platform has 3 Pydantic contracts, specific import paths, and governance patterns that every new module must follow. Rather than a wiki page or CONTRIBUTING.md that drifts out of date, the scaffold generator reads the actual schemas and injects them into the generation prompt — so the output is always current with the SDK.
**Extensibility:** As new contracts or governance patterns are added to intelliflow-core, the generator automatically picks them up. No manual template maintenance.
**Risk reduced:** Eliminates the "blank page" problem for new contributors and prevents governance pattern omissions (missing audit logging, missing cost tracking) that would be caught in review anyway.

---

## 4. Interview Hook

> "The third developer tool I built was a scaffold generator. A developer describes what they want to build in plain English, the LLM generates Python code pre-wired with our governance patterns — audit logging, cost tracking, the right Pydantic contracts — and then ast.parse() validates every line before it's returned. If there's a syntax error, it retries with the error feedback. It's the same 'LLM generates, code validates' pattern, applied to developer onboarding."

---

## 5. Architecture Impact

**Control flow changed?** No
**New data paths?** No — reads existing contracts.py via importlib
**New dependencies?** No — uses only stdlib (ast, importlib, argparse) plus OpenAI
**Mermaid diagrams need update?** No

---

## 6. New Data Structures

None. Reads existing Pydantic schemas from intelliflow-core; does not introduce new ones.

---

## 7. Trade-offs

**What you chose:** ast.parse() for validation — catches all syntax errors, zero false positives, stdlib with no dependencies
**What you gave up:** Semantic validation (ast.parse() confirms syntax, not correctness — generated code might import a nonexistent module or call a wrong function). A full linter (pylint/mypy) would catch more but adds heavyweight dependencies and slow execution.
**What production would need:** Optional mypy/ruff pass, template library for common patterns (extraction pipeline, API handler, chaos test suite), integration with IDE plugins for in-editor generation

---

## 8. Rough Edges

1. **Syntax-only validation**: ast.parse() confirms valid Python syntax but not semantic correctness — generated code might reference nonexistent modules or use wrong function signatures
2. **No template library**: Every generation starts from scratch via LLM; common patterns (extraction pipeline, API handler) could be templated for consistency and speed
3. **No import verification**: Generated imports (e.g., `from intelliflow_core.helpers import generate_event_id`) are not checked against the actual SDK exports
4. **No version pinning**: If intelliflow-core contracts change, generated code reflects new schemas but previously generated scaffolds may be stale
5. **Single-file output**: Generates one module; multi-file scaffolds (module + test + config) would require orchestration

---

## 9. ATS Keywords

code generation, ast.parse, Python AST, scaffold generator, developer tooling, Pydantic schema introspection, governance automation, boilerplate generation, platform SDK

---

## 10. Metrics Changed

| Metric | Old Value | New Value |
|--------|-----------|-----------|
| total_tests | 179 | 193 |
| hand_written_tests | 144 | 158 |
| developer_tools | 2 | 3 |
| scaffold_generator_tests | (new) | 14 |

---

## 11. Forbidden Phrases

| Forbidden | Use Instead |
|-----------|-------------|
| "2 developer tools" | "3 developer tools" |
| "179 total tests" | "193 total tests" |
| "144 hand-written tests" | "158 hand-written tests" |

**REMOVE from forbidden list:** "3 developer tools" — this is now TRUE.

---

## 12. Cascade Checklist

- [ ] CLAUDE.md truth table updated (total_tests 179→193, hand_written 144→158, developer_tools 2→3)
- [ ] CLAUDE.md story inventory updated (Story L: ⛔ → ✅)
- [ ] CLAUDE.md forbidden phrases updated (remove "3 developer tools", add "2 developer tools", update test counts)
- [ ] portfolio_config.yaml updated (total_tests, hand_written_tests, developer_tools, scaffold_generator_tests)
- [ ] 8 portfolio files updated with Story L substance
- [ ] CHANGELOG.md entry added
- [ ] README.md updated (test counts, NL Log Query → add Scaffold Generator row)
- [ ] TEST_STRATEGY.md updated (add Scaffold Generator row, update totals)
- [ ] linkedin_experience.md updated
- [ ] verify_cascade.py passes (7/7)
- [ ] verify_enterprise_docs.py passes (153/153)
- [ ] No forbidden phrases in any updated file

---

**End of Feature Brief**

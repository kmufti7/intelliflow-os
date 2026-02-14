# Changelog

All notable changes to IntelliFlow OS are documented here.

## 2026-02-13 — Public Files Update (Session 5)
- Added: 3 Mermaid diagrams to ARCHITECTURE.md (FHIR Dual-Mode Ingestion, Chaos Mode Control Flow, Developer Tools Layer) — total now 6
- Updated: DATA_DICTIONARY.md with audit event types table, NL Log Query data structures, Scaffold Generator data structures
- Fixed: Stale test counts in portfolio files (111→193, 164→193, 144→158 hand-written)
- Verified: intelliflow-os README.md current (193 tests, 3 developer tools, all module rows)

## 2026-02-13 — Scaffold Generator Cascade (Story L)
- Built: Scaffold Generator tool (tools/scaffold_generator.py) — LLM generates, ast.parse() validates
- Added: 14 tests (tests/test_scaffold_generator.py) covering validation, retries, cost tracking, end-to-end
- Cascaded: Story L substantively updated across all 8 portfolio files + linkedin_experience.md
- Added: Pain Point #14 (new contributors reinvent governance patterns) in 04_enterprise_pain_points.md
- Added: ADR-018 (Scaffold Generator with ast.parse() validation) in 05_architecture_decisions.md
- Added: Scaffold Generator limitations section (5 items) in 06_rough_edges_roadmap.md
- Added: 3 talking points for Story L in 07_interview_talking_points.md
- Updated: Test counts 179 → 193 (158 hand-written + 35 AI-generated) across all files
- Updated: Developer tools 2 → 3 in CLAUDE.md truth table and portfolio_config.yaml
- Removed: "3 developer tools" from forbidden phrases (now true)
- Added: Feature Brief (docs/feature_briefs/story_l_scaffold_generator.md)

## 2026-02-13 — NL Log Query Cascade (Story K)
- Built: NL Log Query tool (tools/nl_log_query.py) — LLM translates, Python validates, code executes
- Added: 15 tests (tests/test_nl_log_query.py) covering injection attacks, column whitelist, end-to-end
- Cascaded: Story K substantively updated across all 8 portfolio files + linkedin_experience.md
- Added: Pain Point #13 (searching audit logs requires SQL expertise) in 04_enterprise_pain_points.md
- Added: ADR-017 (NL Log Query with SQL validation) in 05_architecture_decisions.md
- Added: NL Log Query limitations section (5 items) in 06_rough_edges_roadmap.md
- Added: 3 talking points for Story K in 07_interview_talking_points.md
- Updated: Test counts 164 → 179 (144 hand-written + 35 AI-generated) across all files
- Updated: Developer tools 1 → 2 in CLAUDE.md truth table and portfolio_config.yaml
- Added: Feature Brief (docs/feature_briefs/story_k_nl_log_query.md)

## 2026-02-12 — AI Test Generator Cascade (Story J)
- Cascaded: Story J (AI Test Generator) substantively updated across all 8 portfolio files
- Added: Pain Point #12 (schema validation test coverage) in 04_enterprise_pain_points.md
- Added: AI Test Generator limitations section in 06_rough_edges_roadmap.md
- Added: 3 talking points for Story J in 07_interview_talking_points.md
- Enhanced: "LLM translates, code decides" pattern explained across all portfolio files
- Added: Feature Brief (docs/feature_briefs/story_j_ai_test_generator.md)

## 2026-02-12 — Cascade System
- Added: Cascade automation system (/add-feature command, verify_cascade.py, Feature Brief template)
- Fixed: TEST_STRATEGY.md total updated 129 → 164 (includes 35 AI-generated tests)
- Fixed: verify_enterprise_docs.py check updated 126 → 164
- Baseline: verify_cascade.py 7/7, verify_enterprise_docs.py 59/59

## [Unreleased]
- Added: Enterprise evidence pack (SECURITY.md, ARCHITECTURE.md, COST_MODEL.md, TEST_STRATEGY.md, DOCS_INDEX.md)
- Added: EU AI Act classification section to GOVERNANCE.md
- Added: Demo video links to README.md

## [1.0.0] - 2026-02
- Shipped: SupportFlow module (banking support agent)
- Shipped: CareFlow module (clinical gap analysis)
- Shipped: intelliflow-core SDK (shared governance UI + contracts)
- Added: GOVERNANCE.md with NIST AI RMF alignment
- Added: CI/CD pipelines with 111 passing tests across platform

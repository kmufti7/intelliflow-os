# CLAUDE.md — IntelliFlow OS Platform Overview

## What This Repo Is

Platform overview and recruiter front door for IntelliFlow OS, a governance-first AI platform for regulated industries (banking, healthcare). Contains enterprise documentation, portfolio write-ups, strategy documents, and verification scripts.

**Owner:** Kamil Mufti, Head of Product & Architect | Kaizen Works, LLC

---

## Truth Table (Locked Facts)

These facts are verified. Do NOT contradict them in any output.

| Claim | Value | Source |
|-------|-------|--------|
| Total tests | 193 (158 hand-written + 35 AI-generated) | CI + test runs |
| intelliflow-core tests | 32 | CI |
| SupportFlow tests | 13 | CI |
| CareFlow tests | 84 (81 original + 3 integration) | CI |
| AI-generated tests | 35 (from ai_test_generator.py) | Test run |
| Enterprise docs | 11 | DOCS_INDEX.md |
| Verification checks | 59 | verify_enterprise_docs.py |
| Build time (actual) | ~7 hours (~4 SF, ~3 CF) | Kamil's report |
| Build time (estimated) | 29-48 hours | Architect estimate |
| SupportFlow policy retrieval | Keyword-based (60+ keywords → 20 policies). NO FAISS, NO embeddings. | Code review |
| CareFlow guideline retrieval | FAISS vector search (text-embedding-3-small). Actual semantic search. | Code review |
| CareFlow extraction | Regex-first. 100% success rate. LLM fallback exists but never triggered. | Test results |
| CareFlow gap computation | Deterministic Python code. LLM does NOT decide gaps. | Code review |
| CareFlow FHIR ingestion | FHIR R4 Bundle (Patient + Observation), LOINC 4548-4 | Code review |
| CareFlow Chaos Mode | FAISS/Pinecone failure injection, graceful fallback | Code review |
| SupportFlow Chaos Mode | Database/vector store failure injection | Code review |
| Total LOC | ~12,500+ | Repo stats |
| Developer tools | 3 (AI test generator, NL log query, scaffold generator) | IntelliFlow_OS/tools/ |
| Scaffold Generator | Developer intent → platform-compliant Python boilerplate. Schema introspection, governance injection, ast.parse() validation. 14 tests. | tools/scaffold_generator.py |
| NL Log Query | Natural language → SQL WHERE clause. Column whitelist, blocked keywords, ast validation. 15 tests. | tools/nl_log_query.py |

---

## Forbidden Phrases

| Forbidden | Use Instead |
|-----------|-------------|
| "SupportFlow uses vector search" | "SupportFlow uses keyword-based policy retrieval" |
| "SupportFlow uses FAISS" | "CareFlow uses FAISS for guideline retrieval" |
| "The LLM decides if there's a care gap" | "Code computes gaps deterministically. LLM formats the explanation." |
| "AI-powered gap detection" | "Deterministic gap detection with AI-powered explanations" |
| "Portfolio project" | "Platform" or "System" |
| "Demo" (as noun) | "Implementation" or "Reference implementation" |
| Strawman hooks ("Stop doing X", "Everyone ships garbage") | "Here's what I built and why" |
| "2 developer tools" | "3 developer tools (AI test generator, NL log query, scaffold generator)" |
| "1 developer tool" | "3 developer tools (AI test generator, NL log query, scaffold generator)" |
| "179 total tests" | "193 total tests (158 hand-written + 35 AI-generated)" |
| "144 hand-written tests" | "158 hand-written tests" |
| "164 total tests" | "193 total tests (158 hand-written + 35 AI-generated)" |
| "129 hand-written tests" | "158 hand-written tests" |
| "intelliflow-core/tools/" | "IntelliFlow_OS/tools/" (actual location of ai_test_generator.py) |

---

## Portfolio File Cascade Rule

When ANY metric, feature, or capability changes, update ALL of these files. Each file has a different purpose — content must match that purpose, not just mention a keyword.

| File | Purpose | Depth |
|------|---------|-------|
| portfolio_writeup/01_executive_summary.md | Quick overview (2 min read) | 1-2 sentences per topic |
| portfolio_writeup/02_technical_deep_dive.md | Technical audience, HOW it works | Full architecture, data flows, diagrams |
| portfolio_writeup/03_product_strategy.md | PM audience, WHY these decisions | Rationale, trade-offs, market context |
| portfolio_writeup/04_enterprise_pain_points.md | Pain → solution pairs | Enterprise problem + specific solution |
| portfolio_writeup/05_architecture_decisions.md | ADRs | Context, options, decision, rationale, trade-off |
| portfolio_writeup/06_rough_edges_roadmap.md | Honest limitations | Specific gaps + what production would need |
| portfolio_writeup/07_interview_talking_points.md | Conversational, ready to speak | Sentences you'd say out loud |
| portfolio_writeup/08_resume_writeup.md | ATS-scannable bullets | Specific mechanisms and numbers |
| linkedin_experience.md | LinkedIn experience entry | Under 2,000 chars total |
| PRIVATE_CHANGELOG.md | Session log | What changed, when |

### Substance Rule

Every update must include WHAT was built, WHY it matters, and HOW it works — appropriate to the file's depth level. A keyword mention ("added FHIR support") is NOT substantive. A description of the adapter pattern, LOINC 4548-4, and why dual-mode matters IS substantive.

### Verification After Updates

Run `python scripts/verify_portfolio_update.py` after any portfolio file changes. This checks numbers and keywords. It does NOT check substance — that requires manual review or LLM-assisted verification.

---

## Story Inventory

Every **built** story must appear substantively in all 8 portfolio_writeup files + linkedin_experience.md. Stories marked NOT BUILT must NOT appear in portfolio files until implemented.

| ID | Story | Key Details | Status |
|----|-------|-------------|--------|
| A | Deterministic Reasoning | "LLM extracts, code decides, LLM explains." A1C 8.2 > 7.0 = True. Python, not LLM. 3 gap types with severity tiers. | ✅ Built |
| B | PHI-Aware Data Residency | Patient data → local FAISS. Guidelines → Pinecone cloud. Concept Query Builder strips identifiers. Two modes: local/enterprise. | ✅ Built |
| C | Platform Architecture | intelliflow-core: pip-installable SDK. 3 Pydantic contracts. Both modules import, not copy-paste. | ✅ Built |
| D | Cost Optimization (5 Layers) | Regex-first (100%), structured outputs (enums), gpt-4o-mini (10x cheaper), local FAISS (zero cloud cost for PHI), token tracking. | ✅ Built |
| E | Chaos Mode Bug Fix | 12/12 tests passing, feature broken. Front-door bypass (dropdown skipped orchestrator). Silent catch (except Exception swallowed ChaosError). Fix: single entry point + explicit ChaosError catch. | ✅ Built |
| F | "Tests That Lie" | Unit tests validated components, not integration. Added 3 integration tests mirroring real user entry points. Principle: at least one test per feature must hit the real entry point. | ✅ Built |
| G | Chaos as Resilience | Both modules: sidebar toggle, failure injection, graceful fallback, audit-logged. Demo-able in 3 minutes. Enterprise buyer question: "what happens when your vector store goes down?" | ✅ Built |
| H | FHIR Dual-Mode Ingestion | Legacy clinic notes + FHIR R4 Bundles. Adapter pattern: both paths → same extraction output. LOINC 4548-4. CMS mandate context. | ✅ Built |
| I | Enterprise Evidence Pack | 11 docs (NIST AI RMF, OWASP LLM Top 10, EU AI Act, ethics, observability, etc.). 59 automated verification checks. Documentation drift prevention. | ✅ Built |
| J | AI Test Generator | Reads 3 Pydantic schemas → generates 35 edge-case pytest tests. Schema-aware. "LLM translates, code decides" pattern. Location: IntelliFlow_OS/tools/ai_test_generator.py | ✅ Built |
| K | NL Log Query | Natural language → SQL WHERE clause. LLM translates, Python validates (column whitelist, blocked keywords, string stripping), code executes against SQLite. 15 tests. Location: IntelliFlow_OS/tools/nl_log_query.py | ✅ Built |
| L | Scaffold Generator | Developer describes intent → platform-compliant Python boilerplate. Reads schemas, injects governance patterns. ast.parse() validation. 14 tests. Location: IntelliFlow_OS/tools/scaffold_generator.py | ✅ Built |

---

## Repos

| Repo | Purpose | URL |
|------|---------|-----|
| intelliflow-os | Platform overview (this repo) | https://github.com/kmufti7/intelliflow-os |
| intelliflow-core | Shared SDK | https://github.com/kmufti7/intelliflow-core |
| intelliflow-supportflow | Banking module | https://github.com/kmufti7/intelliflow-supportflow |
| intelliflow-careflow | Healthcare module | https://github.com/kmufti7/intelliflow-careflow |

---

## Feature Addition Cascade

### Required: Feature Brief

Before running `/add-feature`, the Architect Agent must produce a **Feature Brief** using the template at `docs/feature_briefs/TEMPLATE.md`. The brief contains:
- What was built (technical) and why it matters (business)
- PM framing and interview hook
- Architecture impact and new data structures
- Trade-offs, rough edges, ATS keywords
- Metrics changes and forbidden phrase additions
- Cascade checklist for verification

### Cascade Sequence

When `/add-feature` is invoked with a Feature Brief:

1. Read the Feature Brief
2. Update CLAUDE.md Truth Table (if metrics changed)
3. Update CLAUDE.md Story Inventory (add new story row)
4. Update CLAUDE.md Forbidden Phrases (if brief specifies any)
5. Update `portfolio_config.yaml` (if metrics changed)
6. Run `python scripts/render_portfolio.py` (if config changed)
7. Update all 8 portfolio_writeup files (substantively — see Substance Rule)
8. Update `linkedin_experience.md`
9. Update `ARCHITECTURE.md` (if architecture impact = yes)
10. Update `DATA_DICTIONARY.md` (if new data structures)
11. Update `CHANGELOG.md` with new entry
12. Run `python scripts/verify_cascade.py` — must pass
13. Print cascade report

### Substance Rule (Enforced)

Each portfolio file update must include WHAT was built, WHY it matters, and HOW it works — at the depth level appropriate to that file. A keyword mention is NOT substantive. The Feature Brief provides the strategic context needed to write substantive content for each file's audience.

### Verification

Run `python scripts/verify_cascade.py` after every cascade. It checks:
- Every built story has substance in 6+ of 8 portfolio files
- NOT BUILT stories do not appear in portfolio files
- No forbidden phrases in any portfolio file
- Numbers in portfolio files match `portfolio_config.yaml`
- Architecture diagrams exist (if applicable)
- CHANGELOG.md has recent entries
- Enterprise docs verification passes (if script exists)

---

## Output Standards

1. **Cornell-style numbering:** 1, 1.1, 1.1.1 for outputs longer than ~10 lines
2. **Confidence levels required:** 0.95+ (verified), 0.80-0.94 (high), 0.60-0.79 (medium), <0.60 (low)
3. **Rationale required:** Every recommendation includes What, Why, Trade-off
4. **No scope creep:** Deliver what's asked. Extras go to backlog only.

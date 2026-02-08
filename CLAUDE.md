# IntelliFlow OS — Working Memory

## Critical Rules
- **NEVER push private artifacts to GitHub.** Always confirm before any push. (portfolio_writeup/, linkedin_experience.md are .gitignored)
- **Post-write verification:** After batch file creation, re-read files to confirm content matches spec before reporting done.
- **Ask before pushing personal content.** User burned once — always confirm.

## Project Structure
- 4 repos: intelliflow-os (overview), intelliflow-core (SDK), intelliflow-supportflow, intelliflow-careflow
- 111 total tests (32 core + 13 SupportFlow + 66 CareFlow)
- Private artifacts in `portfolio_writeup/` (01-10 + PRIVATE_CHANGELOG.md) and `linkedin_experience.md`
- CLAUDE.md in repo root governs private artifact handling

## Private Artifacts Inventory
- 01-07: Portfolio write-up modules (exec summary through interview talking points)
- 08: Resume write-up (compact + detailed)
- 09: LinkedIn 5-post sequence (Posts 1-2 final, 3-5 pending)
- 10: YouTube descriptions (SupportFlow + CareFlow)
- PRIVATE_CHANGELOG.md: Log of all private artifact changes
- linkedin_experience.md: LinkedIn experience entry

## Public Enterprise Docs (pushed)
- DOCS_INDEX.md, ARCHITECTURE.md (Mermaid), SECURITY.md (OWASP LLM Top 10), GOVERNANCE.md (NIST AI RMF + EU AI Act), COST_MODEL.md, TEST_STRATEGY.md, CHANGELOG.md, CLAUDE.md

---

## Portfolio & Job Search Mode

This project includes non-code deliverables (LinkedIn posts, resume, interview prep, documentation).

### Private Artifacts
* Private artifacts live in `portfolio_writeup/` and `linkedin_experience.md` (both .gitignored).
* Log all private artifact changes to `portfolio_writeup/PRIVATE_CHANGELOG.md` with date and summary.
* Never commit private artifacts to GitHub.

### Operating Docs
* DNA and Context docs live in Claude Project Knowledge, not in this repo.
* Reference their version numbers (e.g., "DNA v1.0", "Context v1.2") when relevant.

### Accuracy Rules
* Before finalizing any content, verify claims against Technical Truth Table in DNA.
* Flag forbidden phrases (see DNA Section 9).
* Confidence levels required for recommendations.

### LinkedIn Posts
* Store drafts in `portfolio_writeup/09_linkedin_posts.md`.
* Track status: Draft → Revised → Final → Posted.
* No student framing ("portfolio project", "demo", "learning").

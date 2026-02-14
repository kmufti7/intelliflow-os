# FEATURE BRIEF: [Feature Name]

**Story ID:** [Letter]
**Date:** [YYYY-MM-DD]
**Produced by:** Architect Agent
**Consumed by:** Claude Code `/add-feature` command

---

## 1. What Was Built

_Technical description. What the code does, where it lives, what it touches._

**Location:** [repo/path/to/files]
**New files:** [list any new files created]
**Modified files:** [list any existing files changed]
**Tests added:** [count and what they test]

---

## 2. Why It Matters

_Business pain point this solves. Who has this problem and why they care._

**Pain point:** [One sentence: the problem in the real world]
**Who cares:** [Enterprise buyer type / regulator / end user]
**Market context:** [Regulation, industry trend, or procurement requirement that makes this relevant]

---

## 3. PM Framing

_How a product manager explains this decision to stakeholders. Not technical. Strategic._

**Decision rationale:** [Why build this instead of alternatives]
**Extensibility:** [What this enables in the future]
**Risk reduced:** [What failure mode or gap this closes]

---

## 4. Interview Hook

_The 30-second version you'd say out loud. Conversational, not scripted._

> "[First-person, natural language. Something you'd actually say in an interview.]"

---

## 5. Architecture Impact

**Control flow changed?** [Yes/No. If yes, describe before → after]
**New data paths?** [Yes/No. If yes, describe]
**New dependencies?** [Yes/No. If yes, list]
**Mermaid diagrams need update?** [Yes/No]

---

## 6. New Data Structures

_Pydantic schemas, FHIR resources, database tables, new config fields._

| Structure | Location | Purpose |
|-----------|----------|---------|
| [Name] | [file path] | [what it holds] |

_If none, write "None."_

---

## 7. Trade-offs

**What you chose:** [The approach taken]
**What you gave up:** [The alternative not taken, and why]
**What production would need:** [What's missing for real deployment]

---

## 8. Rough Edges

_Honest limitations. What doesn't work, what's minimal, what's scoped down._

1. [Specific limitation]
2. [Specific limitation]
3. [Specific limitation]

---

## 9. ATS Keywords

_Terms recruiters and ATS systems scan for. Include in resume and LinkedIn bullets._

[keyword1], [keyword2], [keyword3], [keyword4], [keyword5]

---

## 10. Metrics Changed

_Anything in portfolio_config.yaml that needs updating._

| Metric | Old Value | New Value |
|--------|-----------|-----------|
| [metric_key] | [old] | [new] |

_If none, write "None."_

---

## 11. Forbidden Phrases

_New phrases to add to CLAUDE.md forbidden list, if any._

| Forbidden | Use Instead |
|-----------|-------------|
| [phrase] | [correct alternative] |

_If none, write "None."_

---

## 12. Cascade Checklist

_For Claude Code to confirm after running /add-feature._

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

## 13. Public README Impact

_Does this feature require updates to the public intelliflow-os README.md?_

**Module Overview table:** [Yes/No — does this add a new module row or change test counts?]
**Developer Tools section:** [Yes/No — is this a new developer tool needing a subsection?]
**Platform Patterns section:** [Yes/No — does this introduce a new shared discipline?]
**Build Metrics table:** [Yes/No — do total test counts change?]

_Note: Build times, hour estimates, and time savings are NEVER included in the public README._

---

**End of Feature Brief**

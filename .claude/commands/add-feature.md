# /add-feature — Cascade a new feature across all platform files

## Prerequisites
- A Feature Brief file must exist (check `docs/feature_briefs/` or ask the user for the path)
- The feature's code must already be built and tested

## Steps

### Step 1: Read the Feature Brief
Read the brief file provided by the user. If any of these fields are empty or say "[TBD]", STOP and ask the user before proceeding:
- "Why it matters" (Section 2)
- "Interview hook" (Section 4)
- "Architecture impact" (Section 5)
- "Trade-offs" (Section 7)

These are required for substantive portfolio updates. Without them, you'll write shallow keyword mentions.

### Step 2: Update CLAUDE.md
- Truth Table: add or update the row for this feature
- Story Inventory: add or update the story row (mark ✅ Built)
- Forbidden Phrases: add any new entries from Section 11 of the brief
- If the story was previously marked ⛔ NOT BUILT, change to ✅ Built

### Step 3: Update portfolio_config.yaml
- Update any metrics listed in Section 10 of the brief
- If no metrics changed, skip this step

### Step 4: Run render_portfolio.py (if metrics changed)
```bash
python scripts/render_portfolio.py
```
This cascades numbers from portfolio_config.yaml into all template-rendered files.

### Step 5: Update portfolio files (8 files)
For EACH of these 8 files, READ the full file first, then ADD content appropriate to that file's purpose and depth level. Use the Feature Brief sections as source material.

| File | What to add | Source from Brief |
|------|-------------|-------------------|
| 01_executive_summary.md | 1-2 sentences | Section 2 (why it matters) |
| 02_technical_deep_dive.md | Full technical detail | Section 1 (what was built) + Section 5 (architecture) + Section 6 (data structures) |
| 03_product_strategy.md | PM rationale, market context | Section 3 (PM framing) + Section 2 (market context) |
| 04_enterprise_pain_points.md | Pain point → solution pair | Section 2 (pain point + who cares) |
| 05_architecture_decisions.md | ADR with context/options/decision/rationale/trade-off | Section 5 (architecture) + Section 7 (trade-offs) |
| 06_rough_edges_roadmap.md | Honest limitations | Section 8 (rough edges) |
| 07_interview_talking_points.md | Conversational talking points | Section 4 (interview hook) + expand to 2-3 points |
| 08_resume_writeup.md | ATS-scannable bullets with specifics | Section 9 (ATS keywords) + Section 1 (specifics) |

**SUBSTANCE RULE:** A keyword mention ("added X") is NOT substantive. Each file must include WHAT was built, WHY it matters, and HOW it works — at the depth appropriate to that file.

**FORBIDDEN PHRASES:** Check CLAUDE.md forbidden phrases list. Do not use any of them in any file.

### Step 6: Update ARCHITECTURE.md (if architecture impact = yes)
- Read Section 5 of the brief
- Update or add Mermaid diagrams showing the new control flow or data path
- If architecture impact = no, skip this step

### Step 7: Update DATA_DICTIONARY.md (if new data structures)
- Read Section 6 of the brief
- Add new schemas, resources, or data structures
- If no new data structures, skip this step

### Step 8: Update CHANGELOG.md
Add an entry:
```
## [Date] — [Feature Name] (Story [Letter])
- [One-line summary of what was added]
- [Files affected]
```

### Step 9: Update module README
- Identify which module the feature belongs to (CareFlow, SupportFlow, intelliflow-core, or intelliflow-os)
- Update that module's README to mention the feature
- If the feature is a platform-level tool (like AI test generator), update intelliflow-os README

### Step 10: Run verification
```bash
python scripts/verify_cascade.py
```
Report results. If any checks fail, fix them before completing.

### Step 11: Run forbidden phrase check
```bash
grep -rn "portfolio project\|3 developer tools\|intelliflow-core/tools/" portfolio_writeup/ linkedin_experience.md README.md
```
If any matches found, fix them.

### Step 12: Print cascade report
```
=== CASCADE REPORT: [Feature Name] (Story [Letter]) ===
CLAUDE.md truth table:        [UPDATED / SKIPPED / ALREADY CORRECT]
CLAUDE.md story inventory:    [UPDATED / SKIPPED / ALREADY CORRECT]
CLAUDE.md forbidden phrases:  [UPDATED / SKIPPED / ALREADY CORRECT]
portfolio_config.yaml:        [UPDATED / SKIPPED / NO CHANGES NEEDED]
render_portfolio.py:          [RAN / SKIPPED / NO CHANGES NEEDED]
Portfolio files (8):          [X/8 UPDATED]
ARCHITECTURE.md:              [UPDATED / SKIPPED / NO IMPACT]
DATA_DICTIONARY.md:           [UPDATED / SKIPPED / NO NEW STRUCTURES]
CHANGELOG.md:                 [UPDATED]
Module README:                [UPDATED — which one]
verify_cascade.py:            [PASSED / X FAILURES]
Forbidden phrases:            [CLEAN / X FOUND]

MANUAL ACTIONS NEEDED:
- [ ] Re-record video (if UI changed)
- [ ] Update screenshots (if UI changed)
- [ ] Update LinkedIn experience entry
- [ ] Update resume source file
```

### Step 13: Commit
```bash
git add -A
git commit -m "Cascade: Add [Feature Name] (Story [Letter]) to all platform files"
```

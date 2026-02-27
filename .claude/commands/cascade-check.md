# /cascade-check

Run after ANY repository change (not just /add-feature).

## Step 1: Identify What Changed
List all files modified, added, or deleted in the most recent commit(s).

## Step 2: Check Core Verification
Run `scripts/verify_cascade.py` and report results.

## Step 3: Check Enterprise Docs
Run `scripts/verify_enterprise_docs.py` and report results.

## Step 4: Assess Portfolio Writeup Cascade
For each file in `portfolio_writeup/`, determine if the change affects it:

| File | Check For |
|------|-----------|
| 01_executive_summary.md | Metrics, tech stack, differentiators, module status |
| 02_technical_deep_dive.md | Architecture, patterns, test counts, technical details |
| 03_product_strategy.md | Product decisions, trade-offs, positioning |
| 04_enterprise_pain_points.md | Pain points, solutions, compliance claims |
| 05_architecture_decisions.md | ADRs, technology choices, patterns |
| 06_rough_edges_roadmap.md | Limitations, roadmap items, backlog |
| 07_interview_talking_points.md | Talking points, validation, key stats |
| 08_resume_writeup.md | Resume bullets, ATS keywords, tech stack |
| 09_linkedin_posts.md | Post content, scheduling |
| 10_youtube_descriptions.md | Video descriptions, tech stack, links |
| linkedin_experience.md | LinkedIn entry, technologies |
| PRIVATE_CHANGELOG.md | Session log (ALWAYS update after any session) |

Report which files need updates and why.

## Step 5: Check Diagrams
If the change affects architecture, data flow, or module structure:
- Check ARCHITECTURE.md Mermaid diagrams (6 total)
- Check any diagrams in portfolio_writeup files
- Report if diagrams need updating

## Step 6: Check Cross-Repo Consistency
If the change affects:
- LICENSE → verify all 5 repos (4 active code repos + intelliflow-os platform overview) have matching LICENSE
- README patterns → verify all 5 repo READMEs are consistent
- SDK contracts → verify module repos reference correct version

## Step 7: Report
Output:
- verify_cascade.py result (X/14)
- verify_enterprise_docs.py result (X/153)
- Portfolio files needing update (list with reasons)
- Diagrams needing update (list with reasons)
- Cross-repo issues (list)

Do NOT auto-fix. Report only. Wait for exact content from user.

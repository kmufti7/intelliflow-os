#!/usr/bin/env python3
"""
QC Validation Script for DEVELOPER_EXPERIENCE_STRATEGY.md

Runs three layers of automated checks:
  Layer 1: Structure & rules (15 checks)
  Layer 2: Cross-reference against codebase (7 checks)

Layer 3 (tone self-review) is performed manually by the author.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STRATEGY_DOC = REPO_ROOT / "DEVELOPER_EXPERIENCE_STRATEGY.md"
DOCS_INDEX = REPO_ROOT / "DOCS_INDEX.md"

# Paths to search for schema definitions
CONTRACTS_CANDIDATES = [
    REPO_ROOT.parent / "intelliflow-core" / "intelliflow_core" / "contracts.py",
    REPO_ROOT / "intelliflow-core" / "intelliflow_core" / "contracts.py",
]

# Tech stack known to be in the codebase
VALID_TECH = {
    "faiss", "pinecone", "streamlit", "pydantic", "pytest",
    "openai", "python", "sqlite",
}

# Tech that SupportFlow does NOT use
SUPPORTFLOW_FORBIDDEN_TECH = {"vector search", "faiss", "embeddings"}


def read_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def word_count(text: str) -> int:
    """Count words in markdown, excluding code blocks and tables."""
    # Remove code blocks
    clean = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Remove table rows (keep header for context)
    clean = re.sub(r"^\|.*\|$", "", clean, flags=re.MULTILINE)
    # Remove markdown headers markers
    clean = re.sub(r"^#{1,6}\s+", "", clean, flags=re.MULTILINE)
    # Remove horizontal rules
    clean = re.sub(r"^---+$", "", clean, flags=re.MULTILINE)
    # Remove bold/italic markers
    clean = re.sub(r"\*{1,2}(.*?)\*{1,2}", r"\1", clean)
    return len(clean.split())


def find_contracts() -> Path | None:
    for p in CONTRACTS_CANDIDATES:
        if p.exists():
            return p
    return None


# =========================================================================
# Layer 1: Structure & Rules (15 checks)
# =========================================================================

def run_layer1(content: str, docs_index: str) -> list[tuple[int, str, bool]]:
    results = []

    # 1. File exists
    results.append((1, "File exists at DEVELOPER_EXPERIENCE_STRATEGY.md", STRATEGY_DOC.exists()))

    # 2-7. Section headings
    section_patterns = [
        (2, "Section 1 exists", r"##\s*(1\.?\s|Problem Statement)"),
        (3, "Section 2 exists", r"##\s*(2\.?\s|Three Capability Tiers)"),
        (4, "Section 3 exists", r"##\s*(3\.?\s|Build vs[.\s]*Buy)"),
        (5, "Section 4 exists", r"##\s*(4\.?\s|Measuring Developer Productivity)"),
        (6, "Section 5 exists", r"##\s*(5\.?\s|Recommendation)"),
        (7, "Section 6 exists", r"##\s*(6\.?\s|Proof of Concept)"),
    ]
    for num, label, pattern in section_patterns:
        results.append((num, label, bool(re.search(pattern, content, re.IGNORECASE))))

    # 8. At least one markdown table in Build vs Buy section
    bvb_match = re.search(
        r"(##\s*(3\.?\s|Build vs[.\s]*Buy).*?)(?=\n##\s|\Z)", content, re.DOTALL | re.IGNORECASE
    )
    has_table = False
    if bvb_match:
        section_text = bvb_match.group(1)
        has_table = bool(re.search(r"\|.*\|.*\|", section_text))
    results.append((8, "Build vs Buy section contains a table", has_table))

    # 9. Word count 1500-2000
    wc = word_count(content)
    results.append((9, f"Word count {wc} is between 1500-2000", 1500 <= wc <= 2000))

    # 10-14. Forbidden phrases
    forbidden = [
        (10, "portfolio project", r"(?i)\bportfolio\s+project\b"),
        (11, "demo (standalone noun)", r"(?i)\bdemo\b(?!nstrat)"),
        (12, "student", r"(?i)\bstudent\b"),
        (13, "Stop doing", r"(?i)\bstop\s+doing\b"),
        (14, "Everyone ships", r"(?i)\beveryone\s+ships\b"),
    ]
    for num, label, pattern in forbidden:
        found = bool(re.search(pattern, content))
        results.append((num, f'Does NOT contain "{label}"', not found))

    # 15. DOCS_INDEX.md references the strategy doc
    results.append((15, "DOCS_INDEX.md contains DEVELOPER_EXPERIENCE_STRATEGY", "DEVELOPER_EXPERIENCE_STRATEGY" in docs_index))

    return results


# =========================================================================
# Layer 2: Cross-Reference (7 checks)
# =========================================================================

def run_layer2(content: str) -> list[tuple[int, str, bool]]:
    results = []
    contracts_path = find_contracts()
    contracts_content = read_file(contracts_path) if contracts_path else ""

    # 16. AuditEventSchema exists if mentioned
    if "AuditEventSchema" in content:
        results.append((16, "AuditEventSchema exists in contracts.py", "class AuditEventSchema" in contracts_content))
    else:
        results.append((16, "AuditEventSchema not mentioned (skip)", True))

    # 17. CostTrackingSchema exists if mentioned
    if "CostTrackingSchema" in content:
        results.append((17, "CostTrackingSchema exists in contracts.py", "class CostTrackingSchema" in contracts_content))
    else:
        results.append((17, "CostTrackingSchema not mentioned (skip)", True))

    # 18. GovernanceLogEntry exists if mentioned
    if "GovernanceLogEntry" in content:
        results.append((18, "GovernanceLogEntry exists in contracts.py", "class GovernanceLogEntry" in contracts_content))
    else:
        results.append((18, "GovernanceLogEntry not mentioned (skip)", True))

    # 19. If test count mentioned, must be 129
    test_count_matches = re.findall(r"(\d+)\s+tests?\s+(already\s+)?pass", content, re.IGNORECASE)
    if test_count_matches:
        all_129 = all(m[0] == "129" for m in test_count_matches)
        results.append((19, f"Test count references are 129", all_129))
    else:
        results.append((19, "No test count claim found (skip)", True))

    # 20. ai_test_generator path is correct if mentioned
    if "ai_test_generator" in content:
        correct_path = "tools/ai_test_generator.py" in content
        results.append((20, "ai_test_generator path is tools/ai_test_generator.py", correct_path))
    else:
        results.append((20, "ai_test_generator not mentioned (skip)", True))

    # 21. Named tech exists in actual stack
    tech_mentions = re.findall(r"\b(FAISS|Pinecone|Streamlit|Pydantic|pytest|OpenAI|SQLite)\b", content, re.IGNORECASE)
    tech_lower = {t.lower() for t in tech_mentions}
    invalid_tech = tech_lower - VALID_TECH
    results.append((21, f"All named tech in actual stack (found: {', '.join(sorted(tech_lower)) or 'none'})", len(invalid_tech) == 0))

    # 22. No claim about SupportFlow using vector search/FAISS/embeddings
    sf_section = re.findall(r"(?i)supportflow.*?(?:\n|$)", content)
    sf_text = " ".join(sf_section).lower()
    sf_forbidden = any(term in sf_text for term in SUPPORTFLOW_FORBIDDEN_TECH)
    results.append((22, "No claim about SupportFlow using vector search/FAISS/embeddings", not sf_forbidden))

    return results


# =========================================================================
# Main
# =========================================================================

def main():
    content = read_file(STRATEGY_DOC)
    docs_index = read_file(DOCS_INDEX)

    if not content:
        print("ERROR: DEVELOPER_EXPERIENCE_STRATEGY.md not found or empty.")
        sys.exit(1)

    print("=" * 60)
    print("QC Layer 1: Structure & Rules")
    print("=" * 60)
    layer1 = run_layer1(content, docs_index)
    l1_pass = 0
    for num, label, passed in layer1:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] Check {num}: {label}")
        if passed:
            l1_pass += 1
    print(f"\nStructure checks: {l1_pass}/{len(layer1)} passed.\n")

    print("=" * 60)
    print("QC Layer 2: Cross-Reference")
    print("=" * 60)
    layer2 = run_layer2(content)
    l2_pass = 0
    for num, label, passed in layer2:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] Check {num}: {label}")
        if passed:
            l2_pass += 1
    print(f"\nCross-reference checks: {l2_pass}/{len(layer2)} passed.\n")

    # Word count for reference
    wc = word_count(content)
    print(f"Word count: {wc}")

    total = l1_pass + l2_pass
    total_checks = len(layer1) + len(layer2)
    print(f"\nTotal: {total}/{total_checks} checks passed.")

    if total < total_checks:
        print("\nFAILED — fix issues and re-run.")
        sys.exit(1)
    else:
        print("\nALL CHECKS PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()

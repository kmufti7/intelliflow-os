"""
Enterprise Documentation Verification Script.

Checks all enterprise docs in intelliflow-os for existence,
non-empty content, and required sections/keywords.
"""

import glob
import os
import re
import sys

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

results = []


def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((status, name, detail))


def read_file(filename):
    path = os.path.join(REPO_ROOT, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def check_exists_and_nonempty(filename):
    content = read_file(filename)
    check(f"{filename} exists", content is not None)
    if content is not None:
        check(f"{filename} is not empty", len(content.strip()) > 0)
    return content


def check_contains(filename, content, keyword, label=None):
    label = label or keyword
    check(f"{filename} contains \"{label}\"", keyword in content)


def check_contains_count(filename, content, keyword, min_count, label=None):
    label = label or keyword
    count = content.count(keyword)
    check(
        f"{filename} contains \"{label}\" (>={min_count}x)",
        count >= min_count,
        f"found {count}x",
    )


# --- GOVERNANCE.md ---
content = check_exists_and_nonempty("GOVERNANCE.md")
if content:
    check_contains("GOVERNANCE.md", content, "NIST AI Risk Management Framework")
    for section in ["GOVERN", "MAP", "MEASURE", "MANAGE"]:
        check_contains("GOVERNANCE.md", content, f"### {section}")
    check_contains("GOVERNANCE.md", content, "EU AI Act Classification")
    for article in ["Article 13", "Article 14", "Article 15"]:
        check_contains("GOVERNANCE.md", content, article)

# --- SECURITY.md ---
content = check_exists_and_nonempty("SECURITY.md")
if content:
    check_contains("SECURITY.md", content, "OWASP")
    for i in range(1, 11):
        check_contains("SECURITY.md", content, f"LLM{i:02d}")
    for status in ["Implemented", "Planned", "N/A"]:
        check_contains("SECURITY.md", content, status)

# --- ARCHITECTURE.md ---
content = check_exists_and_nonempty("ARCHITECTURE.md")
if content:
    check_contains_count("ARCHITECTURE.md", content, "```mermaid", 3)
    check_contains("ARCHITECTURE.md", content, "flowchart")

# --- COST_MODEL.md ---
check_exists_and_nonempty("COST_MODEL.md")

# --- TEST_STRATEGY.md ---
content = check_exists_and_nonempty("TEST_STRATEGY.md")
if content:
    check_contains("TEST_STRATEGY.md", content, "193")

# --- DATA_DICTIONARY.md ---
check_exists_and_nonempty("DATA_DICTIONARY.md")

# --- OBSERVABILITY.md ---
check_exists_and_nonempty("OBSERVABILITY.md")

# --- VENDOR_COMPARISON.md ---
check_exists_and_nonempty("VENDOR_COMPARISON.md")

# --- ETHICS.md ---
check_exists_and_nonempty("ETHICS.md")

# --- CHANGELOG.md ---
check_exists_and_nonempty("CHANGELOG.md")

# --- DOCS_INDEX.md ---
content = check_exists_and_nonempty("DOCS_INDEX.md")
if content:
    expected_links = [
        "README.md",
        "GOVERNANCE.md",
        "SECURITY.md",
        "ARCHITECTURE.md",
        "COST_MODEL.md",
        "TEST_STRATEGY.md",
        "DATA_DICTIONARY.md",
        "OBSERVABILITY.md",
        "VENDOR_COMPARISON.md",
        "ETHICS.md",
        "CHANGELOG.md",
    ]
    for doc in expected_links:
        link = f"]({doc})"
        check_contains("DOCS_INDEX.md", content, link, label=f"link to {doc}")


# --- Enterprise doc count consistency across all .md files ---
config_path = os.path.join(REPO_ROOT, "portfolio_config.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
expected_count = config["metrics"]["enterprise_docs"]

# Pattern: integer immediately adjacent to "Enterprise Evidence Pack"
# Matches: "16 Enterprise Evidence Pack", "Enterprise Evidence Pack | 16",
#           "Enterprise Evidence Pack** | 16"
count_pattern = re.compile(
    r"(\d+)\s*(?:documents?\s+mapped\s+to.*)?Enterprise Evidence Pack"
    r"|Enterprise Evidence Pack[^|]*\|\s*(\d+)"
)

scan_dirs = [
    os.path.join(REPO_ROOT, "docs", "enterprise"),
    os.path.join(REPO_ROOT, "portfolio_writeup"),
]
for scan_dir in scan_dirs:
    if not os.path.isdir(scan_dir):
        continue
    for md_path in sorted(glob.glob(os.path.join(scan_dir, "*.md"))):
        rel = os.path.relpath(md_path, REPO_ROOT)
        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line_num, line in enumerate(lines, start=1):
            for m in count_pattern.finditer(line):
                found = int(m.group(1) or m.group(2))
                check(
                    f"{rel}:{line_num} Enterprise Evidence Pack count = {expected_count}",
                    found == expected_count,
                    f"found {found}, expected {expected_count}" if found != expected_count else "",
                )


# --- Report ---
print("=" * 60)
print("  IntelliFlow OS — Enterprise Docs Verification")
print("=" * 60)
print()

passed = sum(1 for s, _, _ in results if s == "PASS")
failed = sum(1 for s, _, _ in results if s == "FAIL")

for status, name, detail in results:
    icon = "+" if status == "PASS" else "X"
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{icon}] {name}{suffix}")

print()
print("-" * 60)
print(f"  {passed} passed, {failed} failed, {len(results)} total")
print("-" * 60)

if failed > 0:
    sys.exit(1)

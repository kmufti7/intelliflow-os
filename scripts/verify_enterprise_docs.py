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


# --- Forbidden phrases in enterprise docs ---
# Phrases that must not appear in any enterprise documentation.
# "demo" is checked as a standalone word (noun usage), excluding verb forms
# like "demonstrate", "demonstrates", "demonstrating", "demo-able".
FORBIDDEN_PHRASES = [
    "side project",
    "portfolio project",
    "personal project",
    "hobby",
    "AgentFlow",
    "standalone app",
    "standalone application",
    "HIPAA compliant",
    "HIPAA certified",
    "NIST certified",
    "NIST compliant",
    "EU AI Act compliant",
]

# "demo" as noun: match word-boundary "demo" not followed by verb suffixes
# or preceded by "demo-able". Catches: demo, demos, demo-grade, demo-scale,
# demo scope, demo environment, portfolio demo, Demo usage.
DEMO_NOUN_PATTERN = re.compile(
    r"\bdemos?\b(?!nstrat|[-]able)", re.IGNORECASE
)

# "proof of concept" only flagged when NOT near "production-grade"
POC_PATTERN = re.compile(r"\bproof of concept\b", re.IGNORECASE)

enterprise_root_docs = [
    "COST_MODEL.md",
    "SECURITY.md",
    "GOVERNANCE.md",
    "ETHICS.md",
    "OBSERVABILITY.md",
    "VENDOR_COMPARISON.md",
    "TEST_STRATEGY.md",
    "DATA_DICTIONARY.md",
    "DEVELOPER_EXPERIENCE_STRATEGY.md",
    "ARCHITECTURE.md",
]

forbidden_files = []
# Collect enterprise root docs
for doc in enterprise_root_docs:
    full = os.path.join(REPO_ROOT, doc)
    if os.path.isfile(full):
        forbidden_files.append(full)
# Collect docs/enterprise/*.md
ent_dir = os.path.join(REPO_ROOT, "docs", "enterprise")
if os.path.isdir(ent_dir):
    forbidden_files.extend(sorted(glob.glob(os.path.join(ent_dir, "*.md"))))

forbidden_violations = 0
for fpath in forbidden_files:
    rel = os.path.relpath(fpath, REPO_ROOT)
    with open(fpath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line_num, line in enumerate(lines, start=1):
        line_lower = line.lower()
        # Check literal forbidden phrases
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() in line_lower:
                check(
                    f'{rel}:{line_num} no forbidden phrase "{phrase}"',
                    False,
                    f'found "{phrase}"',
                )
                forbidden_violations += 1
        # Check "demo" as noun
        if DEMO_NOUN_PATTERN.search(line):
            check(
                f'{rel}:{line_num} no "demo" as noun',
                False,
                f"found: {line.strip()[:80]}",
            )
            forbidden_violations += 1
        # Check "proof of concept" without "production-grade"
        if POC_PATTERN.search(line):
            if "production-grade" not in line_lower:
                check(
                    f'{rel}:{line_num} no bare "proof of concept"',
                    False,
                    f"found: {line.strip()[:80]}",
                )
                forbidden_violations += 1

if forbidden_violations == 0:
    check("Enterprise docs: no forbidden phrases", True)


# --- Semantic coverage: kill-switch guard across docs ---
SEMANTIC_COVERAGE = {
    "SECURITY.md": ["KillSwitchGuard", "fail-closed"],
    "ETHICS.md": ["KillSwitchGuard", "GovernanceRule"],
    "PRODUCT_BRIEF.md": ["KillSwitchGuard"],
    "DATA_DICTIONARY.md": [
        "KillSwitchGuard",
        "GovernanceRule",
        "KillSwitchTriggered",
        "WorkflowResult",
    ],
    "docs/enterprise/SLO_SLA_STATEMENT.md": ["fail-closed", "KillSwitchGuard"],
    "OBSERVABILITY.md": ["KillSwitchGuard", "KillSwitchTriggered"],
    "README.md": ["KillSwitchGuard"],
    "ARCHITECTURE.md": ["KillSwitchGuard"],
    "portfolio_writeup/01_executive_summary.md": ["KillSwitchGuard"],
    "portfolio_writeup/02_technical_deep_dive.md": ["KillSwitchGuard", "GovernanceRule"],
    "portfolio_writeup/04_enterprise_pain_points.md": ["KillSwitchGuard"],
    "portfolio_writeup/linkedin_experience.md": ["KillSwitchGuard"],
}

for filename, keywords in SEMANTIC_COVERAGE.items():
    content = read_file(filename)
    if content is None:
        for kw in keywords:
            check(f'{filename} contains "{kw}"', False, "file not found")
    else:
        for kw in keywords:
            check_contains(filename, content, kw)


# --- Semantic coverage: MCP Tool Registry across docs ---
MCP_REGISTRY_COVERAGE = {
    "SECURITY.md": ["MCPRegistry"],
    "OBSERVABILITY.md": ["MCPRegistry"],
    "README.md": ["MCPRegistry"],
    "COST_MODEL.md": ["MCPRegistry"],
    "DOCS_INDEX.md": ["tool_registry"],
    "portfolio_writeup/01_executive_summary.md": ["MCPRegistry"],
    "portfolio_writeup/02_technical_deep_dive.md": ["MCPRegistry", "ToolSchema"],
    "portfolio_writeup/04_enterprise_pain_points.md": ["MCPRegistry"],
}

for filename, keywords in MCP_REGISTRY_COVERAGE.items():
    content = read_file(filename)
    if content is None:
        for kw in keywords:
            check(f'{filename} contains "{kw}"', False, "file not found")
    else:
        for kw in keywords:
            check_contains(filename, content, kw)


# --- Semantic coverage: WORM audit log across docs ---
WORM_COVERAGE = {
    "SECURITY.md": ["WORMLogRepository", "HMAC-SHA256"],
    "GOVERNANCE.md": ["WORMLogRepository", "trace_id"],
    "OBSERVABILITY.md": ["WORM", "trace_id"],
    "ETHICS.md": ["WORM"],
    "DATA_DICTIONARY.md": ["WORMLogRepository", "WORMStorageError", "DatabaseSessionManager"],
    "PRODUCT_BRIEF.md": ["WORMLogRepository"],
    "README.md": ["WORMLogRepository"],
    "ARCHITECTURE.md": ["WORM"],
    "DOCS_INDEX.md": ["worm_logger"],
    "docs/enterprise/SLO_SLA_STATEMENT.md": ["WORMStorageError"],
    "docs/enterprise/SR_11_7_MODEL_RISK_MANAGEMENT.md": ["WORMLogRepository"],
    "portfolio_writeup/01_executive_summary.md": ["WORMLogRepository"],
    "portfolio_writeup/02_technical_deep_dive.md": ["WORMLogRepository", "DatabaseSessionManager"],
    "portfolio_writeup/04_enterprise_pain_points.md": ["WORMLogRepository", "WORMStorageError"],
    "portfolio_writeup/linkedin_experience.md": ["WORM"],
}

for filename, keywords in WORM_COVERAGE.items():
    content = read_file(filename)
    if content is None:
        for kw in keywords:
            check(f'{filename} contains "{kw}"', False, "file not found")
    else:
        for kw in keywords:
            check_contains(filename, content, kw)


# --- Semantic coverage: Token FinOps Tracker across docs ---
TOKEN_LEDGER_COVERAGE = {
    "COST_MODEL.md": [
        "token", "cost", "pricing", "FinOps", "PTU", "chargeback",
        "immutable receipt", "point-in-time", "pricing drift", "ledger",
    ],
    "OBSERVABILITY.md": [
        "token_ledger", "invocation", "per-invocation", "TokenLedgerRepository",
        "financial telemetry", "cost_usd",
    ],
    "DATA_DICTIONARY.md": [
        "token_ledger", "cost_usd", "input_tokens", "output_tokens",
        "trace_id", "workflow_id", "module_name",
    ],
}

for filename, keywords in TOKEN_LEDGER_COVERAGE.items():
    content = read_file(filename)
    if content is None:
        for kw in keywords:
            check(f'{filename} contains "{kw}"', False, "file not found")
    else:
        for kw in keywords:
            check_contains(filename, content, kw)


# --- Test count consistency in enterprise/strategy docs ---
expected_tests = config["metrics"]["total_tests"]
test_count_files = ["DEVELOPER_EXPERIENCE_STRATEGY.md"]
# Also scan docs/enterprise/ for any file mentioning test counts
test_count_pattern = re.compile(
    r"\b(\d+)\s+tests?\s+(?:already\s+)?passing\b"
)

for doc in test_count_files:
    fpath = os.path.join(REPO_ROOT, doc)
    if not os.path.isfile(fpath):
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line_num, line in enumerate(lines, start=1):
        for m in test_count_pattern.finditer(line):
            found = int(m.group(1))
            check(
                f"{doc}:{line_num} test count = {expected_tests}",
                found == expected_tests,
                f"found {found}, expected {expected_tests}" if found != expected_tests else "",
            )


# --- Cross-reference claims: assert numeric claims match config ---
CROSS_REFERENCE_CLAIMS = [
    # (regex_with_capture_group, config_key, description)
    (r"(\d+)\s+automated\s+(?:verification\s+)?checks", "verification_checks", "automated checks"),
    (r"(\d+)[- ]check\s+cascade", "cascade_checks", "cascade checks"),
    (r"across\s+(\d+)\s+enterprise\s+documents?", "enterprise_docs", "enterprise doc count"),
]

# Files to scan for cross-reference claims
cross_ref_scan_files = []
enterprise_dir = os.path.join(REPO_ROOT, "docs", "enterprise")
if os.path.isdir(enterprise_dir):
    for fname in sorted(os.listdir(enterprise_dir)):
        if fname.endswith(".md"):
            cross_ref_scan_files.append(os.path.join("docs", "enterprise", fname))

# Also scan root-level docs
for root_doc in ["SECURITY.md", "GOVERNANCE.md", "OBSERVABILITY.md", "COST_MODEL.md",
                 "DATA_DICTIONARY.md", "VENDOR_COMPARISON.md", "TEST_STRATEGY.md"]:
    cross_ref_scan_files.append(root_doc)

for pattern_str, config_key, desc in CROSS_REFERENCE_CLAIMS:
    expected_val = config["metrics"].get(config_key)
    if expected_val is None:
        continue
    expected_val = int(expected_val)
    pattern = re.compile(pattern_str)
    for rel_path in cross_ref_scan_files:
        abs_path = os.path.join(REPO_ROOT, rel_path)
        if not os.path.isfile(abs_path):
            continue
        fname = os.path.basename(rel_path)
        # Skip historical entries in RELEASE_NOTES and CHANGELOG
        if fname in ("RELEASE_NOTES_VERSIONING.md", "CHANGELOG.md"):
            continue
        with open(abs_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                for m in pattern.finditer(line):
                    found = int(m.group(1))
                    if found != expected_val:
                        check(
                            f"{fname}:{line_num} {desc} = {expected_val}",
                            False,
                            f"found {found}, expected {expected_val}",
                        )


# --- Completed v2 steps: detect stale "planned" language in OBSERVABILITY.md ---
completed_steps = config.get("completed_v2_steps", [])
if completed_steps:
    obs_content = read_file("OBSERVABILITY.md")
    if obs_content:
        for step_info in completed_steps:
            component = step_info["name"]
            step_num = step_info["step"]
            # Search for "planned" or "will make/add" within 200 chars of component name
            # Use a sliding window approach
            for i, line in enumerate(obs_content.splitlines(), start=1):
                if re.search(rf"(?i){re.escape(component)}", line):
                    if re.search(r"(?i)\bplanned\b|\bwill\s+(make|add)\b|\bnot yet\b", line):
                        check(
                            f"OBSERVABILITY.md:{i} {component} not marked as planned",
                            False,
                            f"Step {step_num} is complete per config but line contains stale planned/future language",
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

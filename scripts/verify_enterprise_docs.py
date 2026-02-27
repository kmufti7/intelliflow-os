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

CONFIG_PATH = os.path.join(REPO_ROOT, "portfolio_config.yaml")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

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
    expected_total = str(config["metrics"]["total_ecosystem"])
    check_contains("TEST_STRATEGY.md", content, expected_total)

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
        # Check "demo" as noun (skip PRD files — PRDs legitimately describe demo scenarios)
        if not os.path.basename(fpath).startswith("PRD_") and DEMO_NOUN_PATTERN.search(line):
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
# Federated schema: portfolio/executive docs validate against total_ecosystem (276),
# repo-specific docs validate against platform_core (253).
total_ecosystem = config["metrics"]["total_ecosystem"]
platform_core = config["metrics"]["platform_core"]

# Scope 1: Portfolio docs → total_ecosystem (276)
ecosystem_test_count_files = [
    os.path.join("portfolio_writeup", "01_executive_summary.md"),
    os.path.join("portfolio_writeup", "03_product_strategy.md"),
]

# Scope 2: Repo-specific docs → platform_core (253)
platform_test_count_files = [
    "DEVELOPER_EXPERIENCE_STRATEGY.md",
    os.path.join("docs", "enterprise", "PRODUCT_ROADMAP.md"),
]

test_count_patterns = [
    re.compile(r"\b(\d+)\s+tests?\s+(?:already\s+)?passing\b"),
    re.compile(r"\b(\d+)\s+total\s+(?:ecosystem\s+)?tests\b"),
    re.compile(r"\*\*(\d+)\s+(?:passing\s+)?tests?\*\*"),
]


def _check_test_counts(doc_list, expected, scope_label):
    for doc in doc_list:
        fpath = os.path.join(REPO_ROOT, doc)
        if not os.path.isfile(fpath):
            continue
        fname = os.path.basename(doc)
        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line_num, line in enumerate(lines, start=1):
            for pat in test_count_patterns:
                for m in pat.finditer(line):
                    found = int(m.group(1))
                    check(
                        f"{fname}:{line_num} test count ({scope_label}) = {expected}",
                        found == expected,
                        f"found {found}, expected {expected}" if found != expected else "",
                    )


_check_test_counts(ecosystem_test_count_files, total_ecosystem, "ecosystem")
_check_test_counts(platform_test_count_files, platform_core, "platform_core")


# --- Stale verification count in portfolio files ---
STALE_VERIFICATION_FILES = [
    os.path.join("portfolio_writeup", "01_executive_summary.md"),
    os.path.join("portfolio_writeup", "03_product_strategy.md"),
    os.path.join("portfolio_writeup", "05_architecture_decisions.md"),
]

stale_verif_pattern = re.compile(r"\b59[\s-](?:check|automated|verification)")

for rel_path in STALE_VERIFICATION_FILES:
    abs_path = os.path.join(REPO_ROOT, rel_path)
    if not os.path.isfile(abs_path):
        continue
    fname = os.path.basename(rel_path)
    with open(abs_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            if stale_verif_pattern.search(line):
                check(
                    f"{fname}:{line_num} no stale 59-check reference",
                    False,
                    f"found '59' verification count, expected 137",
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


# --- Semantic coverage: ClaimsFlow cascade across docs ---
CLAIMSFLOW_COVERAGE = {
    "GOVERNANCE.md": ["ClaimsFlow"],
    "OBSERVABILITY.md": ["ClaimsFlow"],
    "TEST_STRATEGY.md": ["ClaimsFlow"],
    "ARCHITECTURE.md": ["ClaimsFlow"],
}

for filename, keywords in CLAIMSFLOW_COVERAGE.items():
    content = read_file(filename)
    if content is None:
        for kw in keywords:
            check(f'{filename} contains "{kw}"', False, "file not found")
    else:
        for kw in keywords:
            check_contains(filename, content, kw)


# --- Semantic coverage: SPOG / Single Pane of Glass ---
SPOG_COVERAGE = {
    "OBSERVABILITY.md": [("Single Pane of Glass", "SPOG")],
    "portfolio_writeup/02_technical_deep_dive.md": [("Single Pane of Glass", "SPOG")],
}

for filename, keyword_groups in SPOG_COVERAGE.items():
    content = read_file(filename)
    if content is None:
        for group in keyword_groups:
            check(f'{filename} contains "SPOG"', False, "file not found")
    else:
        for group in keyword_groups:
            found = any(kw in content for kw in group)
            check(f'{filename} contains "SPOG" or "Single Pane of Glass"', found)


# --- Semantic coverage: federated test tracking ---
FEDERATED_COVERAGE = {
    "portfolio_writeup/01_executive_summary.md": [("federated", "276")],
    "README.md": [("federated", "276")],
}

for filename, keyword_groups in FEDERATED_COVERAGE.items():
    content = read_file(filename)
    if content is None:
        for group in keyword_groups:
            check(f'{filename} contains "federated" or "276"', False, "file not found")
    else:
        for group in keyword_groups:
            found = any(kw in content for kw in group)
            check(f'{filename} contains "federated" or "276"', found)


# --- Semantic coverage: OFAC / sanctions ---
OFAC_COVERAGE = {
    "docs/enterprise/SECURITY_PRIVACY_OVERVIEW.md": [("OFAC", "sanctions")],
    "docs/enterprise/SR_11_7_MODEL_RISK_MANAGEMENT.md": [("OFAC", "sanctions")],
}

for filename, keyword_groups in OFAC_COVERAGE.items():
    content = read_file(filename)
    if content is None:
        for group in keyword_groups:
            check(f'{filename} contains "OFAC" or "sanctions"', False, "file not found")
    else:
        for group in keyword_groups:
            found = any(kw in content for kw in group)
            check(f'{filename} contains "OFAC" or "sanctions"', found)


# --- Semantic coverage: DLM ADR ---
DLM_COVERAGE = {
    "docs/enterprise/ADR_DATA_LIFECYCLE_MANAGEMENT.md": [
        "accepted", "deploying institution", "WORM",
    ],
}

for filename, keywords in DLM_COVERAGE.items():
    content = read_file(filename)
    if content is None:
        for kw in keywords:
            check(f'{filename} contains "{kw}"', False, "file not found")
    else:
        for kw in keywords:
            check_contains(filename, content, kw)


# --- Semantic coverage: Kill-Switch in governance/observability ---
KILLSWITCH_GOVERNANCE_COVERAGE = {
    "GOVERNANCE.md": [("KillSwitch", "Kill-Switch")],
    "OBSERVABILITY.md": [("KillSwitch", "Kill-Switch")],
}

for filename, keyword_groups in KILLSWITCH_GOVERNANCE_COVERAGE.items():
    content = read_file(filename)
    if content is None:
        for group in keyword_groups:
            check(f'{filename} contains "KillSwitch" or "Kill-Switch"', False, "file not found")
    else:
        for group in keyword_groups:
            found = any(kw in content for kw in group)
            check(f'{filename} contains "KillSwitch" or "Kill-Switch"', found)


# --- Semantic coverage: PRDs (8 documents, 3 keywords each) ---
PRD_COVERAGE = {
    "docs/enterprise/PRD_SUPPORTFLOW.md": ["deterministic", "policy", "citation"],
    "docs/enterprise/PRD_CAREFLOW.md": ["FHIR", "FAISS", "PHI"],
    "docs/enterprise/PRD_CLAIMSFLOW.md": ["OFAC", "LangGraph", "fraud"],
    "docs/enterprise/PRD_SPOG.md": ["Streamlit", "governance", "non-technical"],
    "docs/enterprise/PRD_INTELLIFLOW_CORE_V2.md": ["WORM", "kill-switch", "LangGraph"],
    "docs/enterprise/PRD_HITL_MAKER_CHECKER.md": ["Planned", "checkpointer", "Maker-Checker"],
    "docs/enterprise/PRD_CONTINUOUS_EVALS.md": ["Planned", "golden dataset", "drift"],
    "docs/enterprise/PRD_EDGE_SLM_ROUTING.md": ["Planned", "SLM", "deterministic"],
}

for filename, keywords in PRD_COVERAGE.items():
    content = read_file(filename)
    if content is None:
        for kw in keywords:
            check(f'{filename} contains "{kw}"', False, "file not found")
    else:
        for kw in keywords:
            check_contains(filename, content, kw)


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

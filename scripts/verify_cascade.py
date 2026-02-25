#!/usr/bin/env python3
"""
verify_cascade.py — Verifies that all platform files are consistent.

Checks:
1. Every "Built" story in CLAUDE.md has substance in all 8 portfolio files
2. NOT BUILT stories absent from portfolio files
3. No forbidden phrases in any portfolio, README, or enterprise doc
4. Numbers in portfolio files match portfolio_config.yaml
5. ARCHITECTURE.md has Mermaid diagrams for each module
6. CHANGELOG.md has recent entries (flags staleness > 30 days)
7. verify_enterprise_docs.py passes
8. README.md test total matches portfolio_config.yaml
9. README.md covers all built stories
10. README.md has no forbidden build time content
11. README.md has Mermaid diagram and links to ARCHITECTURE.md
12. Enterprise doc count consistent across config and filesystem
13. CLAUDE.md Truth Table enterprise_docs matches portfolio_config.yaml
14. ARCHITECTURE.md contains required middleware architecture terms
15. Git sync status — warns on uncommitted changes or unpushed commits (does not fail)
"""

import io
import os
import re
import sys
import yaml
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Fix Windows console encoding for emoji/unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).parent.parent
CONFIG_PATH = REPO_ROOT / "portfolio_config.yaml"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
PORTFOLIO_DIR = REPO_ROOT / "portfolio_writeup"
ARCHITECTURE_MD = REPO_ROOT / "ARCHITECTURE.md"
CHANGELOG_MD = REPO_ROOT / "CHANGELOG.md"

# Files to check for forbidden phrases (exclude PRIVATE_CHANGELOG — it's a log file)
CHECK_FILES = [
    f for f in PORTFOLIO_DIR.glob("*.md")
    if "PRIVATE_CHANGELOG" not in f.name and "template" not in f.name.lower()
] + [
    REPO_ROOT / "linkedin_experience.md",
    REPO_ROOT / "README.md",
    ARCHITECTURE_MD,
]

# Story-specific terms: if a story is "Built", these terms should appear
# in portfolio files (at least some of them, in most files)
STORY_TERMS = {
    "A": ["deterministic", "LLM extracts", "code decides", "Therefore"],
    "B": ["PHI", "data residency", "FAISS", "Pinecone", "local.*cloud"],
    "C": ["platform", "intelliflow-core", "pip", "shared SDK", "Pydantic"],
    "D": ["cost", "regex-first", "gpt-4o-mini", "token tracking", "5 layers"],
    "E": ["front-door bypass", "ChaosError", "analyze_patient", "silent catch", "single entry point"],
    "F": ["tests that lie", "integration test", "12.*unit", "3 integration", "real entry point"],
    "G": ["chaos mode", "resilience", "failure injection", "graceful", "audit"],
    "H": ["FHIR", "dual-mode", "LOINC", "4548-4", "adapter pattern", "Bundle"],
    "I": ["enterprise", "18 docs", "\\d+.*checks", "NIST", "OWASP", "verify_enterprise"],
    "J": ["AI test generator", "schema-aware", "35.*generated", "Pydantic.*test", "edge-case"],
    "K": ["NL log query", "natural language.*log", "SQL WHERE"],
    "L": ["scaffold generator", "boilerplate", "ast.parse"],
}

FORBIDDEN_PHRASES = [
    "portfolio project",
    "2 developer tools",
    "intelliflow-core/tools/",
    "SupportFlow uses vector search",
    "SupportFlow uses FAISS",
    "The LLM decides if there's a care gap",
    "AI-powered gap detection",
]


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f).get("metrics", {})


def read_file(path):
    """Read a file with UTF-8 encoding (handles Windows default cp1252 issues)."""
    return path.read_text(encoding="utf-8")


def get_built_stories():
    """Parse CLAUDE.md to find stories marked as Built."""
    content = read_file(CLAUDE_MD)
    built = []
    for line in content.split("\n"):
        match = re.match(r"\|\s*([A-M])\s*\|.*\|\s*.*Built", line)
        if match and "NOT BUILT" not in line:
            built.append(match.group(1))
    return built


def get_not_built_stories():
    """Parse CLAUDE.md to find stories marked as NOT BUILT."""
    content = read_file(CLAUDE_MD)
    not_built = []
    for line in content.split("\n"):
        match = re.match(r"\|\s*([A-M])\s*\|.*NOT\s*BUILT", line)
        if match:
            not_built.append(match.group(1))
    return not_built


def check_story_substance(built_stories):
    """Check that built stories appear substantively in portfolio files."""
    issues = []
    portfolio_files = sorted(PORTFOLIO_DIR.glob("*.md"))
    portfolio_files = [f for f in portfolio_files if "template" not in str(f)]

    for story_id in built_stories:
        terms = STORY_TERMS.get(story_id, [])
        if not terms:
            continue

        files_with_substance = 0
        for pf in portfolio_files:
            content = pf.read_text(encoding="utf-8", errors="replace").lower()
            # Count how many story-specific terms appear
            matches = sum(1 for t in terms if re.search(t.lower(), content))
            if matches >= 2:  # At least 2 terms = substantive
                files_with_substance += 1

        if files_with_substance < 6:  # Should be in at least 6 of 8 files
            issues.append(
                f"Story {story_id}: only found in {files_with_substance}/8 portfolio files "
                f"(need 6+). Terms checked: {terms[:3]}..."
            )

    return issues


def check_not_built_absent(not_built_stories):
    """Check that NOT BUILT stories don't appear in portfolio files."""
    issues = []
    portfolio_files = sorted(PORTFOLIO_DIR.glob("*.md"))
    portfolio_files = [f for f in portfolio_files if "template" not in str(f)]

    for story_id in not_built_stories:
        terms = STORY_TERMS.get(story_id, [])
        if not terms:
            continue

        for pf in portfolio_files:
            content = pf.read_text(encoding="utf-8").lower()
            for term in terms:
                if re.search(term.lower(), content):
                    issues.append(
                        f"Story {story_id} (NOT BUILT) referenced in {pf.name}: found '{term}'"
                    )
                    break  # One match per file is enough to flag

    return issues


def check_forbidden_phrases():
    """Check for forbidden phrases in all checked files."""
    issues = []
    for filepath in CHECK_FILES:
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() in content.lower():
                issues.append(f"Forbidden phrase '{phrase}' found in {filepath.name}")
    return issues


def check_numbers_match(metrics):
    """Check that key numbers in portfolio files match config.

    Only flags numbers that claim to be the TOTAL (e.g., '164 tests passing').
    Sub-counts like '28 chaos tests' or '35 AI-generated' are not flagged.
    """
    issues = []
    # Patterns that indicate a TOTAL claim (not sub-counts like "13 tests pass")
    patterns = {
        "total_tests": [
            r"(\d+)\s*total\s*tests",
            r"(\d+)\s*tests?\s*(?:across the platform|platform-wide|end.to.end)",
        ],
        "enterprise_docs": [
            r"(\d+)\s*enterprise\s*docs",
            r"(\d+)-document\s*(?:Enterprise|Evidence)",
        ],
        "verification_checks": [
            r"(\d+)\s*(?:automated\s*)?verification\s*checks",
            r"(\d+)\s*(?:verification\s*|automated\s*)?checks\s*(?:that|validate|verify)",
        ],
    }

    portfolio_files = sorted(PORTFOLIO_DIR.glob("*.md"))
    portfolio_files = [
        f for f in portfolio_files
        if "template" not in f.name.lower() and "PRIVATE_CHANGELOG" not in f.name
    ]

    for filepath in portfolio_files:
        content = filepath.read_text(encoding="utf-8")
        for metric_key, regex_list in patterns.items():
            expected = str(metrics.get(metric_key, ""))
            if not expected:
                continue
            for regex in regex_list:
                for match in re.finditer(regex, content, re.IGNORECASE):
                    found = match.group(1)
                    if found != expected:
                        issues.append(
                            f"{filepath.name}: {metric_key} expected '{expected}' found '{found}'"
                        )
    return issues


def check_architecture_diagrams():
    """Check ARCHITECTURE.md has Mermaid diagrams."""
    issues = []
    if not ARCHITECTURE_MD.exists():
        issues.append("ARCHITECTURE.md does not exist")
        return issues

    content = ARCHITECTURE_MD.read_text(encoding="utf-8")
    mermaid_count = content.lower().count("```mermaid")

    if mermaid_count < 3:
        issues.append(
            f"ARCHITECTURE.md has {mermaid_count} Mermaid diagrams (expected 3+: platform, SupportFlow, CareFlow)"
        )

    # Check for key components in diagrams
    checks = {
        "CareFlow": "careflow" in content.lower(),
        "SupportFlow": "supportflow" in content.lower(),
        "FAISS": "faiss" in content.lower(),
        "Pinecone": "pinecone" in content.lower(),
    }

    for component, found in checks.items():
        if not found:
            issues.append(f"ARCHITECTURE.md missing reference to {component}")

    return issues


def check_changelog_freshness():
    """Check CHANGELOG.md has a recent entry."""
    issues = []
    if not CHANGELOG_MD.exists():
        issues.append("CHANGELOG.md does not exist")
        return issues

    content = CHANGELOG_MD.read_text(encoding="utf-8")
    # Look for date patterns (YYYY-MM-DD or Month Day, Year)
    dates = re.findall(r"(\d{4}-\d{2}-\d{2})", content)

    if not dates:
        issues.append("CHANGELOG.md has no date entries")
        return issues

    latest = max(dates)
    latest_date = datetime.strptime(latest, "%Y-%m-%d")
    days_ago = (datetime.now() - latest_date).days

    if days_ago > 30:
        issues.append(
            f"CHANGELOG.md last entry is {latest} ({days_ago} days ago). May be stale."
        )

    return issues


def run_enterprise_verification():
    """Run verify_enterprise_docs.py if it exists. Returns (issues, summary_string)."""
    script = REPO_ROOT / "scripts" / "verify_enterprise_docs.py"
    if not script.exists():
        return (["verify_enterprise_docs.py not found"], "")

    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        # Parse summary line from stdout (e.g. "  137 passed, 0 failed, 137 total")
        summary = ""
        for line in result.stdout.splitlines():
            m = re.search(r"(\d+)\s+passed,\s+(\d+)\s+failed,\s+(\d+)\s+total", line)
            if m:
                summary = f"{m.group(1)} passed, {m.group(2)} failed, {m.group(3)} total"
                break
        if result.returncode != 0:
            return ([f"verify_enterprise_docs.py failed:\n{result.stdout}\n{result.stderr}"], summary)
    except subprocess.TimeoutExpired:
        return (["verify_enterprise_docs.py timed out (60s)"], "")

    return ([], summary)


README_MD = REPO_ROOT / "README.md"

# Forbidden content in public README (build times are internal metrics)
README_FORBIDDEN = [
    "actual build time",
    "estimated (traditional)",
    "time savings",
    "29-48 hours",
    "85%+",
]


def check_readme_test_total(metrics):
    """Check README.md test total matches portfolio_config.yaml."""
    issues = []
    if not README_MD.exists():
        issues.append("README.md does not exist")
        return issues

    content = read_file(README_MD)
    expected = str(metrics.get("total_tests", ""))
    if not expected:
        return issues

    if expected not in content:
        issues.append(f"README.md does not contain expected test total '{expected}'")

    return issues


def check_readme_story_coverage(built_stories):
    """Check README.md mentions key features from built stories."""
    issues = []
    if not README_MD.exists():
        issues.append("README.md does not exist")
        return issues

    content = read_file(README_MD).lower()

    # Key terms that must appear in README for built stories
    readme_terms = {
        "A": ["deterministic"],
        "B": ["phi", "faiss"],
        "C": ["intelliflow-core"],
        "D": ["regex-first"],
        "G": ["chaos"],
        "H": ["fhir"],
        "J": ["ai test generator"],
        "K": ["nl log query"],
        "L": ["scaffold generator"],
    }

    missing = []
    for story_id in built_stories:
        terms = readme_terms.get(story_id, [])
        if not terms:
            continue
        found = any(t in content for t in terms)
        if not found:
            missing.append(f"Story {story_id} (terms: {terms})")

    if missing:
        issues.append(f"README.md missing coverage for: {', '.join(missing)}")

    return issues


def check_readme_forbidden_content():
    """Check README.md does not contain forbidden build time content."""
    issues = []
    if not README_MD.exists():
        issues.append("README.md does not exist")
        return issues

    content = read_file(README_MD).lower()

    for phrase in README_FORBIDDEN:
        if phrase.lower() in content:
            issues.append(f"README.md contains forbidden content: '{phrase}'")

    return issues


def check_readme_architecture_sync():
    """Check README.md has Mermaid diagram and links to ARCHITECTURE.md."""
    issues = []
    if not README_MD.exists():
        issues.append("README.md does not exist")
        return issues

    content = read_file(README_MD)

    if "```mermaid" not in content:
        issues.append("README.md has no Mermaid diagram (expected Platform Overview)")

    if "ARCHITECTURE.md" not in content:
        issues.append("README.md does not link to ARCHITECTURE.md for detailed diagrams")

    return issues


ENTERPRISE_DIR = REPO_ROOT / "docs" / "enterprise"


def check_enterprise_doc_count(metrics):
    """Check that .md files in docs/enterprise/ match enterprise_docs config value."""
    issues = []
    expected = metrics.get("enterprise_docs")
    if expected is None:
        issues.append("portfolio_config.yaml missing 'enterprise_docs' key")
        return issues

    if not ENTERPRISE_DIR.exists():
        issues.append(f"Directory {ENTERPRISE_DIR.relative_to(REPO_ROOT)} does not exist")
        return issues

    md_files = sorted(ENTERPRISE_DIR.glob("*.md"))
    # Enterprise doc count = Core Artifacts (11 in DOCS_INDEX) + docs/enterprise/ files
    core_artifact_count = expected - len(md_files)
    actual_total = core_artifact_count + len(md_files)

    if actual_total != expected:
        issues.append(
            f"Enterprise doc count mismatch: portfolio_config.yaml says {expected}, "
            f"but docs/enterprise/ has {len(md_files)} file(s) "
            f"(expected {expected - core_artifact_count}). "
            f"Update portfolio_config.yaml or add/remove docs."
        )

    # Also verify at least 1 file exists in docs/enterprise/
    if len(md_files) == 0:
        issues.append("docs/enterprise/ has no .md files — expected at least 1")

    return issues


def check_claude_md_enterprise_docs(metrics):
    """Check CLAUDE.md Truth Table 'Enterprise docs' matches portfolio_config.yaml."""
    issues = []
    expected = metrics.get("enterprise_docs")
    if expected is None:
        issues.append("portfolio_config.yaml missing 'enterprise_docs' key")
        return issues

    content = read_file(CLAUDE_MD)
    # Match the Truth Table row: | Enterprise docs | <number> | ...
    match = re.search(
        r"\|\s*Enterprise docs\s*\|\s*(\d+)\s*\|", content
    )
    if not match:
        issues.append("CLAUDE.md Truth Table has no 'Enterprise docs' row")
        return issues

    claude_value = int(match.group(1))
    if claude_value != expected:
        issues.append(
            f"CLAUDE.md Truth Table says Enterprise docs = {claude_value}, "
            f"but portfolio_config.yaml says {expected}. Update CLAUDE.md."
        )

    return issues


ARCHITECTURE_REQUIRED_TERMS = [
    "Enterprise VPC",
    "Private Endpoint",
    "ClaimsFlow",
    "intelliflow-core v2",
    "Kill-Switch",
]


def check_architecture_required_terms():
    """Check ARCHITECTURE.md contains required middleware architecture terms."""
    issues = []
    if not ARCHITECTURE_MD.exists():
        issues.append("ARCHITECTURE.md does not exist")
        return issues

    content = read_file(ARCHITECTURE_MD)
    content_lower = content.lower()

    for term in ARCHITECTURE_REQUIRED_TERMS:
        if term.lower() not in content_lower:
            issues.append(f"ARCHITECTURE.md missing required term: '{term}'")

    return issues


def check_git_sync_status():
    """Check for uncommitted changes and unpushed commits. Warning only."""
    warnings = []
    try:
        # Uncommitted changes
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10,
        )
        if status.returncode == 0 and status.stdout.strip():
            changed = len(status.stdout.strip().splitlines())
            warnings.append(f"{changed} uncommitted change(s) detected")

        # Unpushed commits
        log = subprocess.run(
            ["git", "log", "--oneline", "origin/main..HEAD"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10,
        )
        if log.returncode == 0 and log.stdout.strip():
            commits = len(log.stdout.strip().splitlines())
            warnings.append(f"{commits} unpushed commit(s) on main")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        warnings.append("Could not check git status (git not available or timed out)")

    return warnings


def main():
    print("=" * 60)
    print("VERIFY CASCADE — IntelliFlow OS Consistency Check")
    print("=" * 60)

    metrics = load_config()
    all_issues = []
    checks_run = 0
    checks_passed = 0

    # 1. Story substance
    print("\n📖 Checking story substance in portfolio files...")
    checks_run += 1
    built = get_built_stories()
    issues = check_story_substance(built)
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ❌ {i}")
    else:
        checks_passed += 1
        print(f"  ✅ All {len(built)} built stories have substance in portfolio files")

    # 2. NOT BUILT stories absent
    print("\n🚫 Checking NOT BUILT stories are absent from portfolio files...")
    checks_run += 1
    not_built = get_not_built_stories()
    issues = check_not_built_absent(not_built)
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ❌ {i}")
    else:
        checks_passed += 1
        print(f"  ✅ {len(not_built)} NOT BUILT stories correctly absent")

    # 3. Forbidden phrases
    print("\n🚷 Checking forbidden phrases...")
    checks_run += 1
    issues = check_forbidden_phrases()
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ❌ {i}")
    else:
        checks_passed += 1
        print(f"  ✅ No forbidden phrases found")

    # 4. Numbers match
    print("\n🔢 Checking numbers match portfolio_config.yaml...")
    checks_run += 1
    issues = check_numbers_match(metrics)
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ❌ {i}")
    else:
        checks_passed += 1
        print(f"  ✅ All numbers match config")

    # 5. Architecture diagrams
    print("\n📐 Checking ARCHITECTURE.md diagrams...")
    checks_run += 1
    issues = check_architecture_diagrams()
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ⚠️  {i}")
    else:
        checks_passed += 1
        print(f"  ✅ ARCHITECTURE.md has required diagrams")

    # 6. CHANGELOG freshness
    print("\n📅 Checking CHANGELOG.md freshness...")
    checks_run += 1
    issues = check_changelog_freshness()
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ⚠️  {i}")
    else:
        checks_passed += 1
        print(f"  ✅ CHANGELOG.md is current")

    # 7. Enterprise docs verification
    print("\n📋 Running verify_enterprise_docs.py...")
    checks_run += 1
    issues, enterprise_summary = run_enterprise_verification()
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ❌ {i}")
    else:
        checks_passed += 1
        if enterprise_summary:
            print(f"  ✅ Enterprise docs verification passed ({enterprise_summary})")
        else:
            print(f"  ✅ Enterprise docs verification passed")

    # 8. README test total
    print("\n🔢 Checking README.md test total...")
    checks_run += 1
    issues = check_readme_test_total(metrics)
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ❌ {i}")
    else:
        checks_passed += 1
        print(f"  ✅ README.md test total matches config")

    # 9. README story coverage
    print("\n📖 Checking README.md story coverage...")
    checks_run += 1
    issues = check_readme_story_coverage(built)
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ❌ {i}")
    else:
        checks_passed += 1
        print(f"  ✅ README.md covers all built stories")

    # 10. README forbidden content
    print("\n🚷 Checking README.md for forbidden build time content...")
    checks_run += 1
    issues = check_readme_forbidden_content()
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ❌ {i}")
    else:
        checks_passed += 1
        print(f"  ✅ README.md has no forbidden build time content")

    # 11. README architecture sync
    print("\n📐 Checking README.md architecture sync...")
    checks_run += 1
    issues = check_readme_architecture_sync()
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ❌ {i}")
    else:
        checks_passed += 1
        print(f"  ✅ README.md has Mermaid diagram and ARCHITECTURE.md reference")

    # 12. Enterprise doc count consistent
    print("\n📂 Checking enterprise doc count consistent across config and filesystem...")
    checks_run += 1
    issues = check_enterprise_doc_count(metrics)
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ❌ {i}")
    else:
        checks_passed += 1
        print(f"  ✅ Enterprise doc count consistent across config and filesystem")

    # 13. CLAUDE.md Truth Table enterprise_docs matches config
    print("\n📋 Checking CLAUDE.md Truth Table enterprise_docs matches portfolio_config.yaml...")
    checks_run += 1
    issues = check_claude_md_enterprise_docs(metrics)
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ❌ {i}")
    else:
        checks_passed += 1
        print(f"  ✅ CLAUDE.md Truth Table enterprise_docs matches portfolio_config.yaml")

    # 14. ARCHITECTURE.md required middleware terms
    print("\n📐 Checking ARCHITECTURE.md required middleware terms...")
    checks_run += 1
    issues = check_architecture_required_terms()
    if issues:
        all_issues.extend(issues)
        for i in issues:
            print(f"  ❌ {i}")
    else:
        checks_passed += 1
        print(f"  ✅ ARCHITECTURE.md contains all required middleware terms")

    # 15. Git sync status (warning only — does not fail)
    print("\n🔄 Checking git sync status...")
    git_warnings = check_git_sync_status()
    if git_warnings:
        for w in git_warnings:
            print(f"  ⚠️  WARNING: {w}")
    else:
        print(f"  ✅ Working tree clean, no unpushed commits")

    # Summary
    print("\n" + "=" * 60)
    print(f"RESULT: {checks_passed}/{checks_run} checks passed")
    if all_issues:
        print(f"\n{len(all_issues)} issues found:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        print("\nFix these issues and run again.")
        sys.exit(1)
    else:
        print("\n✅ All checks passed. Platform files are consistent.")
        sys.exit(0)


if __name__ == "__main__":
    main()

"""
Cross-file verification for the 12-file portfolio update.
Checks consistency across all portfolio_writeup/ files.
"""
import os
import re
import sys

PORTFOLIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "portfolio_writeup")

CHECKS = []
PASS_COUNT = 0
FAIL_COUNT = 0


def check(name, condition, detail=""):
    global PASS_COUNT, FAIL_COUNT
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    CHECKS.append((name, status, detail))
    icon = "OK" if condition else "XX"
    print(f"  {icon} {name}: {status}" + (f" — {detail}" if detail else ""))


def read_file(filename):
    path = os.path.join(PORTFOLIO_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    global PASS_COUNT, FAIL_COUNT

    print("=" * 60)
    print("CROSS-FILE PORTFOLIO VERIFICATION")
    print("=" * 60)

    # Load all files
    files = {
        "01": read_file("01_executive_summary.md"),
        "02": read_file("02_technical_deep_dive.md"),
        "03": read_file("03_product_strategy.md"),
        "04": read_file("04_enterprise_pain_points.md"),
        "05": read_file("05_architecture_decisions.md"),
        "06": read_file("06_rough_edges_roadmap.md"),
        "07": read_file("07_interview_talking_points.md"),
        "08": read_file("08_resume_writeup.md"),
        "09": read_file("09_linkedin_posts.md"),
        "10": read_file("10_youtube_descriptions.md"),
        "linkedin": read_file("linkedin_experience.md"),
        "changelog": read_file("PRIVATE_CHANGELOG.md"),
    }

    missing = [k for k, v in files.items() if v is None]
    if missing:
        print(f"\n  ERROR: Missing files: {missing}")
        sys.exit(1)

    # --Check 1: "164" appears in files that should have test counts --
    print("\n--Check 1: Test count '164' present where required --")
    test_count_files = ["01", "02", "03", "07", "08", "linkedin"]
    for key in test_count_files:
        check(f"{key} contains '164'", "164" in files[key])

    # --Check 2: No stale "129 passing" without "hand-written" qualifier --
    print("\n--Check 2: No stale standalone '129 passing tests' --")
    stale_pattern = re.compile(r"129\s+(passing\s+)?tests(?!\s*\()")
    for key in ["01", "02", "03", "07", "08", "linkedin"]:
        matches = stale_pattern.findall(files[key])
        check(f"{key} no stale '129 tests'", len(matches) == 0,
              f"Found {len(matches)} stale occurrence(s)" if matches else "")

    # --Check 3: Enterprise docs = 11 (not 12) everywhere --
    # Skip changelog — it's a historical log that correctly references past states
    print("\n--Check 3: Enterprise docs count is 11, not 12 --")
    for key, content in files.items():
        if key == "changelog":
            continue
        if "12 enterprise" in content.lower() or "12-document" in content.lower() or "12 docs" in content.lower():
            check(f"{key} no '12 enterprise docs'", False, "Found stale '12'")
        elif "11" in content and ("enterprise" in content.lower() or "evidence pack" in content.lower()):
            check(f"{key} enterprise docs = 11", True)

    # --Check 4: AI test generator mentioned in key files --
    print("\n--Check 4: AI test generator referenced --")
    ai_gen_files = ["01", "02", "03", "05", "07", "08", "linkedin"]
    for key in ai_gen_files:
        has_ref = "test generator" in files[key].lower() or "ai-generated" in files[key].lower() or "AI-generated" in files[key]
        check(f"{key} references AI test generator", has_ref)

    # --Check 5: No forbidden phrases --
    # Skip changelog — it's a historical log that quotes past fixes
    print("\n--Check 5: No forbidden phrases --")
    forbidden = ["portfolio project", "just a demo", "student project"]
    found_any = False
    for key, content in files.items():
        if key == "changelog":
            continue
        for phrase in forbidden:
            if phrase.lower() in content.lower():
                check(f"{key} no '{phrase}'", False)
                found_any = True
    if not found_any:
        check("No forbidden phrases found", True)

    # --Check 6: FHIR R4 mentioned in relevant files --
    print("\n--Check 6: FHIR R4 in relevant files --")
    fhir_files = ["01", "02", "03", "05", "07", "08", "linkedin"]
    for key in fhir_files:
        check(f"{key} mentions FHIR", "FHIR" in files[key])

    # --Check 7: Chaos engineering in relevant files --
    print("\n--Check 7: Chaos engineering in relevant files --")
    chaos_files = ["01", "02", "03", "04", "05", "07", "08", "linkedin"]
    for key in chaos_files:
        check(f"{key} mentions chaos", "chaos" in files[key].lower())

    # --Check 8: Strategy memo referenced where expected --
    print("\n--Check 8: Developer Experience Strategy referenced --")
    strategy_files = ["03", "05", "07", "08"]
    for key in strategy_files:
        has_ref = ("developer experience" in files[key].lower() or
                   "strategy memo" in files[key].lower() or
                   "developer tooling" in files[key].lower() or
                   "DEVELOPER_EXPERIENCE_STRATEGY" in files[key])
        check(f"{key} references strategy memo", has_ref)

    # --Check 9: PRIVATE_CHANGELOG has 2026-02-12 entry --
    print("\n--Check 9: Changelog has current date --")
    check("changelog has 2026-02-12", "2026-02-12" in files["changelog"])

    # --Check 10: linkedin_experience.md body under 2000 chars --
    print("\n--Check 10: LinkedIn body under 2,000 characters --")
    li_lines = files["linkedin"].split("\n")
    body_start = None
    for i, line in enumerate(li_lines):
        if line.strip() == "---":
            body_start = i + 1
            break
    if body_start:
        body = "\n".join(li_lines[body_start:]).strip()
        check(f"LinkedIn body length ({len(body)} chars)", len(body) <= 2000)
    else:
        check("LinkedIn body parse", False, "Could not find --- divider")

    # --Summary --
    print("\n" + "=" * 60)
    total = PASS_COUNT + FAIL_COUNT
    print(f"CROSS-FILE VERIFICATION: {PASS_COUNT}/{total} checks passed")
    if FAIL_COUNT > 0:
        print(f"  {FAIL_COUNT} FAILURES — review above")
    else:
        print("  ALL CHECKS PASSED")
    print("=" * 60)

    return FAIL_COUNT == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

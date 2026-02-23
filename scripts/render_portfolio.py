#!/usr/bin/env python3
"""
render_portfolio.py - Render portfolio templates using metrics from portfolio_config.yaml.

Single source of truth: portfolio_config.yaml holds all metrics.
Templates in portfolio_writeup/templates/ use {{metric_name}} placeholders.
Rendered output goes to portfolio_writeup/.

Usage:
    python scripts/render_portfolio.py --render           # templates/ -> portfolio_writeup/
    python scripts/render_portfolio.py --validate         # check rendered files match templates
    python scripts/render_portfolio.py --init-templates   # create templates from current files
    python scripts/render_portfolio.py --diff             # show what --render would change
"""

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "portfolio_config.yaml"
PORTFOLIO_DIR = ROOT / "portfolio_writeup"
TEMPLATES_DIR = PORTFOLIO_DIR / "templates"

# Files managed by the template system (01-08 + linkedin_experience)
MANAGED_FILES = [
    "01_executive_summary.md",
    "02_technical_deep_dive.md",
    "03_product_strategy.md",
    "04_enterprise_pain_points.md",
    "05_architecture_decisions.md",
    "06_rough_edges_roadmap.md",
    "07_interview_talking_points.md",
    "08_resume_writeup.md",
    "linkedin_experience.md",
]

# ---------------------------------------------------------------------------
# Context-aware replacement rules for --init-templates
# Order matters: longer/more-specific patterns first to avoid partial matches.
# Format: (literal_or_regex, replacement, is_regex)
# ---------------------------------------------------------------------------
TEMPLATIZE_RULES = [
    # --- Composite test count expressions (longest first) ---
    ("164 passing tests (129 hand-written + 35 AI-generated)",
     "{{total_tests}} passing tests ({{hand_written_tests}} hand-written + {{ai_generated_tests}} AI-generated)", False),
    ("164 (129 hand-written + 35 AI-generated)",
     "{{total_tests}} ({{hand_written_tests}} hand-written + {{ai_generated_tests}} AI-generated)", False),
    ("164 tests (129 hand-written + 35 generated)",
     "{{total_tests}} tests ({{hand_written_tests}} hand-written + {{ai_generated_tests}} generated)", False),
    ("164 (129 hand-written + 35 generated)",
     "{{total_tests}} ({{hand_written_tests}} hand-written + {{ai_generated_tests}} generated)", False),
    ("129 hand-written + 35 AI-generated",
     "{{hand_written_tests}} hand-written + {{ai_generated_tests}} AI-generated", False),
    ("129 hand-written + 35 generated",
     "{{hand_written_tests}} hand-written + {{ai_generated_tests}} generated", False),
    ("129 hand-written plus 35 AI-generated",
     "{{hand_written_tests}} hand-written plus {{ai_generated_tests}} AI-generated", False),

    # --- Test counts with context ---
    ("164 passing tests", "{{total_tests}} passing tests", False),
    ("164 tests", "{{total_tests}} tests", False),

    # Module test counts (X/X passing format)
    ("84/84 passing", "{{careflow_tests}}/{{careflow_tests}} passing", False),
    ("32/32 passing", "{{core_tests}}/{{core_tests}} passing", False),
    ("13/13 passing", "{{supportflow_tests}}/{{supportflow_tests}} passing", False),

    # Module test counts with context
    ("84 tests, 7 categories", "{{careflow_tests}} tests, 7 categories", False),
    ("84 tests", "{{careflow_tests}} tests", False),
    ("84 (7 categories)", "{{careflow_tests}} (7 categories)", False),
    ("84 (81 original + 3 integration)", "{{careflow_tests}} ({{careflow_original_tests}} original + {{careflow_integration_tests}} integration)", False),
    ("81 original + 3 integration", "{{careflow_original_tests}} original + {{careflow_integration_tests}} integration", False),
    ("32 tests", "{{core_tests}} tests", False),
    ("13 tests", "{{supportflow_tests}} tests", False),
    ("35 edge-case pytest suites", "{{ai_generated_tests}} edge-case pytest suites", False),
    ("35 edge-case pytest tests", "{{ai_generated_tests}} edge-case pytest tests", False),
    ("35 edge-case tests", "{{ai_generated_tests}} edge-case tests", False),
    ("35 tests covering", "{{ai_generated_tests}} tests covering", False),
    ("35 generated tests", "{{ai_generated_tests}} generated tests", False),
    ("35 additional tests", "{{ai_generated_tests}} additional tests", False),

    # Chaos tests
    ("28 tests verify chaos", "{{chaos_tests_total}} tests verify chaos", False),
    ("28 chaos tests", "{{chaos_tests_total}} chaos tests", False),
    ("28 chaos engineering tests", "{{chaos_tests_total}} chaos engineering tests", False),
    ("28 tests across", "{{chaos_tests_total}} tests across", False),
    ("28 tests, safe", "{{chaos_tests_total}} tests, safe", False),
    ("28 tests total", "{{chaos_tests_total}} tests total", False),
    ("15 chaos tests", "15 chaos tests", False),  # CareFlow-specific, keep literal
    ("13 chaos tests", "13 chaos tests", False),  # SupportFlow-specific, keep literal
    ("15 chaos integration tests", "15 chaos integration tests", False),
    ("3 dedicated FHIR tests", "{{fhir_tests}} dedicated FHIR tests", False),

    # Enterprise docs
    ("11-document Enterprise Evidence Pack", "{{enterprise_docs}}-document Enterprise Evidence Pack", False),
    ("11 enterprise-grade documents", "{{enterprise_docs}} enterprise-grade documents", False),
    ("11 enterprise docs", "{{enterprise_docs}} enterprise docs", False),
    ("11-document enterprise", "{{enterprise_docs}}-document enterprise", False),
    ("11 documents", "{{enterprise_docs}} documents", False),
    ("11 docs", "{{enterprise_docs}} docs", False),

    # Verification checks
    ("137-check automated verification", "{{verification_checks}}-check automated verification", False),
    ("137-check automated", "{{verification_checks}}-check automated", False),
    ("137 automated verification checks", "{{verification_checks}} automated verification checks", False),
    ("137 automated checks", "{{verification_checks}} automated checks", False),
    ("137 checks", "{{verification_checks}} checks", False),
    ("137-check", "{{verification_checks}}-check", False),

    # SupportFlow specifics
    ("20 banking policies", "{{sf_policies}} banking policies", False),
    ("20 policies", "{{sf_policies}} policies", False),
    ("20 specific policies", "{{sf_policies}} specific policies", False),

    # CareFlow specifics
    ("10 clinical guidelines", "{{cf_guidelines}} clinical guidelines", False),
    ("5 synthetic patients", "{{cf_test_patients}} synthetic patients", False),
    ("5 test patients", "{{cf_test_patients}} test patients", False),

    # Gap types - use regex for "3 gap types" but not standalone "3"
    (r"\b3 gap types\b", "{{cf_gap_types}} gap types", True),
    (r"\b3 Pydantic contracts\b", "{{pydantic_schemas}} Pydantic contracts", True),
    (r"\b3 Pydantic schemas\b", "{{pydantic_schemas}} Pydantic schemas", True),
    (r"\b3 schemas\b", "{{pydantic_schemas}} schemas", True),

    # Repos
    (r"\b4 repositories\b", "{{repos}} repositories", True),
    (r"\b4 repos\b", "{{repos}} repos", True),

    # Build time
    ("~7 hours of actual build time (estimated 29-48 hours traditional)",
     "{{build_time_actual}} of actual build time (estimated {{build_time_estimated}} hours traditional)", False),
    ("~7 hours of actual build time",
     "{{build_time_actual}} of actual build time", False),
    ("~7 hours vs. 29-48 estimated",
     "{{build_time_actual}} vs. {{build_time_estimated}} estimated", False),
    ("~7 hours (~4 SF, ~3 CF)",
     "{{build_time_actual}} ({{build_time_actual_sf}} SF, {{build_time_actual_cf}} CF)", False),

    # Developer tools
    (r"\b3 developer tools\b", "{{developer_tools}} developer tools", True),

    # LOC
    ("12,500+", "{{total_loc}}", False),

    # --- Table-format values (pipe-delimited rows) ---
    # These must come AFTER prose rules to avoid double-replacement.
    # 01_executive_summary Key Metrics table
    ("| Repositories | 4 |", "| Repositories | {{repos}} |", False),
    ("| Banking policies | 20 |", "| Banking policies | {{sf_policies}} |", False),
    ("| Clinical guidelines | 10 |", "| Clinical guidelines | {{cf_guidelines}} |", False),
    ("| Sample patients | 5 |", "| Sample patients | {{cf_test_patients}} |", False),
    ("| Enterprise docs | 11 |", "| Enterprise docs | {{enterprise_docs}} |", False),

    # 07_interview_talking_points Quick Stats table
    ("| SupportFlow tests | 13 |", "| SupportFlow tests | {{supportflow_tests}} |", False),
    ("| CareFlow tests | 84 (7 categories) |",
     "| CareFlow tests | {{careflow_tests}} (7 categories) |", False),
    ("| intelliflow-core tests | 32 |", "| intelliflow-core tests | {{core_tests}} |", False),
    ("| Banking policies | 20 |", "| Banking policies | {{sf_policies}} |", False),
    ("| Clinical guidelines | 10 |", "| Clinical guidelines | {{cf_guidelines}} |", False),
    ("| Sample patients | 5 |", "| Sample patients | {{cf_test_patients}} |", False),
    ("| Chaos tests | 28 (13 + 15) |", "| Chaos tests | {{chaos_tests_total}} (13 + 15) |", False),
    ("| Enterprise docs | 11 |", "| Enterprise docs | {{enterprise_docs}} |", False),
    ("| Repositories | 4 |", "| Repositories | {{repos}} |", False),

    # Prose values that need more context
    ("All 35 tests pass", "All {{ai_generated_tests}} tests pass", False),
    ("35 tests pass", "{{ai_generated_tests}} tests pass", False),
    ("32 SDK tests pass", "{{core_tests}} SDK tests pass", False),

    # 05_architecture_decisions.md specific patterns
    ("11 extraction tests", "11 extraction tests", False),  # keep literal (sub-breakdown)

    # FHIR test count in ADR context
    ("3 FHIR ingest tests", "{{fhir_tests}} FHIR ingest tests", False),
    ("3 FHIR tests", "{{fhir_tests}} FHIR tests", False),
]


def load_config():
    """Load metrics from portfolio_config.yaml."""
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config not found: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("metrics", {})


def render_template(template_text, metrics):
    """Replace {{key}} placeholders with values from metrics dict."""
    def replacer(match):
        key = match.group(1).strip()
        if key in metrics:
            return str(metrics[key])
        return match.group(0)  # leave unresolved placeholders as-is

    return re.sub(r"\{\{(\w+)\}\}", replacer, template_text)


def templatize(text):
    """Convert hardcoded metrics in text to {{placeholder}} syntax."""
    result = text
    for rule in TEMPLATIZE_RULES:
        pattern, replacement, is_regex = rule
        if is_regex:
            result = re.sub(pattern, replacement, result)
        else:
            result = result.replace(pattern, replacement)
    return result


def find_unresolved_placeholders(text):
    """Find any {{key}} placeholders that weren't resolved."""
    return re.findall(r"\{\{(\w+)\}\}", text)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_render(metrics, dry_run=False):
    """Render templates to portfolio_writeup/."""
    if not TEMPLATES_DIR.exists():
        print(f"ERROR: Templates directory not found: {TEMPLATES_DIR}")
        print("Run --init-templates first to create templates from current files.")
        return False

    ok = True
    rendered_count = 0

    for filename in MANAGED_FILES:
        template_path = TEMPLATES_DIR / filename
        output_path = PORTFOLIO_DIR / filename

        if not template_path.exists():
            print(f"  SKIP  {filename} (no template)")
            continue

        with open(template_path, "r", encoding="utf-8") as f:
            template_text = f.read()

        rendered = render_template(template_text, metrics)

        # Check for unresolved placeholders
        unresolved = find_unresolved_placeholders(rendered)
        if unresolved:
            print(f"  WARN  {filename}: unresolved placeholders: {unresolved}")

        if dry_run:
            if output_path.exists():
                with open(output_path, "r", encoding="utf-8") as f:
                    current = f.read()
                if current != rendered:
                    print(f"  DIFF  {filename} (would change)")
                else:
                    print(f"  OK    {filename} (no changes)")
            else:
                print(f"  NEW   {filename} (would create)")
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered)
            print(f"  OK    {filename}")
            rendered_count += 1

    if not dry_run:
        print(f"\nRendered {rendered_count} file(s).")
    return ok


def cmd_validate(metrics):
    """Check that rendered files match what templates would produce."""
    if not TEMPLATES_DIR.exists():
        print("ERROR: Templates directory not found. Run --init-templates first.")
        return False

    ok = True
    for filename in MANAGED_FILES:
        template_path = TEMPLATES_DIR / filename
        output_path = PORTFOLIO_DIR / filename

        if not template_path.exists():
            continue

        if not output_path.exists():
            print(f"  MISS  {filename} (rendered file missing)")
            ok = False
            continue

        with open(template_path, "r", encoding="utf-8") as f:
            template_text = f.read()
        with open(output_path, "r", encoding="utf-8") as f:
            current_text = f.read()

        rendered = render_template(template_text, metrics)

        if current_text == rendered:
            print(f"  OK    {filename}")
        else:
            print(f"  DRIFT {filename} (rendered file differs from template output)")
            ok = False
            # Show first difference
            for i, (a, b) in enumerate(zip(current_text.splitlines(), rendered.splitlines())):
                if a != b:
                    print(f"         Line {i+1}:")
                    print(f"           current:  {a[:100]}")
                    print(f"           expected: {b[:100]}")
                    break

    return ok


def cmd_init_templates():
    """Create templates from current portfolio files by replacing metrics with placeholders."""
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    created = 0
    for filename in MANAGED_FILES:
        source_path = PORTFOLIO_DIR / filename
        template_path = TEMPLATES_DIR / filename

        if not source_path.exists():
            print(f"  SKIP  {filename} (source not found)")
            continue

        with open(source_path, "r", encoding="utf-8") as f:
            source_text = f.read()

        template_text = templatize(source_text)

        # Count placeholders inserted
        placeholders = re.findall(r"\{\{\w+\}\}", template_text)
        unique_keys = set(re.findall(r"\{\{(\w+)\}\}", template_text))

        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template_text)

        print(f"  OK    {filename} ({len(placeholders)} placeholders, {len(unique_keys)} unique keys)")
        created += 1

    print(f"\nCreated {created} template(s) in {TEMPLATES_DIR}")
    print("\nNext steps:")
    print("  1. Review templates for correctness")
    print("  2. Run: python scripts/render_portfolio.py --validate")
    print("  3. If valid, future metric changes go in portfolio_config.yaml")
    print("     then run: python scripts/render_portfolio.py --render")
    return True


def cmd_diff(metrics):
    """Show what --render would change without writing files."""
    print("Dry-run: showing what --render would change\n")
    return cmd_render(metrics, dry_run=True)


def cmd_list_placeholders():
    """List all placeholders used across templates."""
    if not TEMPLATES_DIR.exists():
        print("ERROR: Templates directory not found.")
        return False

    all_keys = {}
    for filename in MANAGED_FILES:
        template_path = TEMPLATES_DIR / filename
        if not template_path.exists():
            continue
        with open(template_path, "r", encoding="utf-8") as f:
            text = f.read()
        keys = re.findall(r"\{\{(\w+)\}\}", text)
        for k in keys:
            all_keys.setdefault(k, []).append(filename)

    print(f"{'Placeholder':<30} {'Files':>5}  Used in")
    print("-" * 70)
    for key in sorted(all_keys.keys()):
        files = all_keys[key]
        print(f"  {{{{{key}}}}}  {'':>{26-len(key)}} {len(files):>3}    {', '.join(f[:4] for f in files)}")

    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Render portfolio templates from portfolio_config.yaml"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--render", action="store_true",
                       help="Render templates to portfolio_writeup/")
    group.add_argument("--validate", action="store_true",
                       help="Check rendered files match template output")
    group.add_argument("--init-templates", action="store_true",
                       help="Create templates from current portfolio files")
    group.add_argument("--diff", action="store_true",
                       help="Show what --render would change")
    group.add_argument("--list", action="store_true",
                       help="List all placeholders across templates")

    args = parser.parse_args()

    metrics = load_config()

    print(f"Config: {CONFIG_PATH}")
    print(f"Metrics loaded: {len(metrics)}")
    print()

    if args.init_templates:
        ok = cmd_init_templates()
    elif args.render:
        ok = cmd_render(metrics)
    elif args.validate:
        ok = cmd_validate(metrics)
    elif args.diff:
        ok = cmd_diff(metrics)
    elif args.list:
        ok = cmd_list_placeholders()
    else:
        parser.print_help()
        ok = False

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

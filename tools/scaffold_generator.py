#!/usr/bin/env python3
"""
Scaffold Generator for IntelliFlow OS

Generates platform-compliant Python boilerplate from a developer's natural
language description. Reads Pydantic schemas from intelliflow-core, injects
governance patterns (audit logging, cost tracking), and validates the output
with ast.parse() before returning.

Pattern: "LLM generates, code validates"

Usage:
    python tools/scaffold_generator.py "a CareFlow extraction pipeline for lab results"
    python tools/scaffold_generator.py --output scaffolds/ "SupportFlow intent classifier"
    python tools/scaffold_generator.py --contracts path/to/contracts.py "new audit handler"
"""

import argparse
import ast
import importlib.util
import json
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_CONTRACTS_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "intelliflow-core"
    / "intelliflow_core"
    / "contracts.py"
)

MAX_RETRIES = 2  # Retry LLM generation if ast.parse fails


# ---------------------------------------------------------------------------
# Schema discovery (shared pattern with ai_test_generator.py)
# ---------------------------------------------------------------------------

def load_contracts(contracts_path: Path):
    """Dynamically load the contracts module from a file path."""
    spec = importlib.util.spec_from_file_location("contracts", contracts_path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(f"Cannot load contracts from {contracts_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_schemas(module) -> list:
    """Find all Pydantic BaseModel subclasses in a module."""
    from pydantic import BaseModel

    schemas = []
    for name in dir(module):
        obj = getattr(module, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, BaseModel)
            and obj is not BaseModel
        ):
            schemas.append(obj)
    return schemas


def summarize_schema(schema_cls) -> str:
    """Produce a human-readable summary of a Pydantic schema for the LLM prompt."""
    lines = [f"class {schema_cls.__name__}(BaseModel):"]
    for name, field_info in schema_cls.model_fields.items():
        annotation = field_info.annotation
        type_name = getattr(annotation, "__name__", str(annotation))
        required = field_info.is_required()
        desc = field_info.description or ""
        req_str = "required" if required else "optional"
        lines.append(f"    {name}: {type_name}  # {req_str} — {desc}")
    return "\n".join(lines)


def summarize_enums(module) -> str:
    """Summarize any Enum classes in the contracts module."""
    from enum import Enum

    lines = []
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, Enum) and obj is not Enum:
            members = [f'"{m.value}"' for m in obj]
            lines.append(f"{name}: {', '.join(members)}")
    return "\n".join(lines) if lines else "None"


# ---------------------------------------------------------------------------
# Code validation
# ---------------------------------------------------------------------------

class ScaffoldValidationError(Exception):
    """Raised when generated code fails ast.parse() validation."""
    pass


def validate_python(code: str) -> str:
    """
    Validate generated Python code using ast.parse().

    Returns the code if valid, raises ScaffoldValidationError with the
    syntax error details if invalid.
    """
    if not code or not code.strip():
        raise ScaffoldValidationError("Empty code generated")

    try:
        ast.parse(code)
    except SyntaxError as e:
        raise ScaffoldValidationError(
            f"Generated code has syntax error at line {e.lineno}: {e.msg}"
        ) from e

    return code


# ---------------------------------------------------------------------------
# LLM Generation
# ---------------------------------------------------------------------------

def build_system_prompt(schema_summaries: str, enum_summaries: str) -> str:
    """Build the system prompt with schema context injected."""
    return textwrap.dedent(f"""\
        You are a code generator for IntelliFlow OS, a governance-first AI platform.

        Generate ONLY valid Python code. No markdown fences, no explanations, no comments
        outside the code. The output must be parseable by ast.parse().

        Platform conventions:
        - Import contracts: from intelliflow_core.contracts import AuditEventSchema, CostTrackingSchema, GovernanceLogEntry
        - Import helpers: from intelliflow_core.helpers import generate_event_id, calculate_cost
        - Every public function must log an audit event using AuditEventSchema
        - Every LLM call must track cost using CostTrackingSchema
        - Use Pydantic models for all data validation
        - Use type hints on all functions
        - Include a module docstring explaining what the file does
        - Include a __main__ block with argparse for CLI usage

        Available Pydantic schemas from intelliflow-core:

        {schema_summaries}

        Available enums:

        {enum_summaries}

        Code patterns to follow:
        1. Deterministic logic in Python, not LLM (LLM extracts/translates, code decides)
        2. Structured outputs with Pydantic validation
        3. Cost tracking: calculate tokens and USD for every LLM call
        4. Audit logging: log every significant action with AuditEventSchema
        5. Error handling: explicit exception types, no bare except

        Generate a complete, runnable Python module. Include imports, classes, functions,
        and a CLI entry point.""")


def generate_scaffold(description: str, contracts_path: Path = None, client=None) -> dict:
    """
    Generate a platform-compliant Python scaffold from a natural language description.

    Orchestrates the two-step pattern:
    1. LLM generates Python code with governance patterns injected
    2. ast.parse() validates the output is syntactically correct

    Args:
        description: Natural language description of what to build
        contracts_path: Path to contracts.py (default: sibling intelliflow-core repo)
        client: Optional OpenAI client (pass a mock for testing)

    Returns:
        dict with keys: code, validation_passed, error, cost, retries
    """
    if not description or not description.strip():
        return {
            "code": None,
            "validation_passed": False,
            "error": "Empty description provided",
            "cost": {"tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0},
            "retries": 0,
        }

    # Load schemas for context injection
    if contracts_path is None:
        contracts_path = DEFAULT_CONTRACTS_PATH

    try:
        module = load_contracts(contracts_path)
        schemas = discover_schemas(module)
        schema_summaries = "\n\n".join(summarize_schema(s) for s in schemas)
        enum_summaries = summarize_enums(module)
    except FileNotFoundError:
        schema_summaries = "(contracts.py not found — generate with standard patterns)"
        enum_summaries = "None"

    system_prompt = build_system_prompt(schema_summaries, enum_summaries)

    if client is None:
        from openai import OpenAI
        client = OpenAI()

    total_tokens_in = 0
    total_tokens_out = 0
    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a Python module for: {description}"},
        ]

        # On retry, include the error so the LLM can self-correct
        if last_error and attempt > 0:
            messages.append({
                "role": "user",
                "content": f"The previous code had a syntax error: {last_error}. "
                           f"Fix it and return ONLY the corrected Python code.",
            })

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0,
            max_tokens=4000,
        )

        usage = response.usage
        tokens_in = usage.prompt_tokens if usage else 0
        tokens_out = usage.completion_tokens if usage else 0
        total_tokens_in += tokens_in
        total_tokens_out += tokens_out

        raw_code = response.choices[0].message.content.strip()

        # Strip markdown fences if the LLM wraps code in them
        raw_code = _strip_markdown_fences(raw_code)

        try:
            validated = validate_python(raw_code)
            # gpt-4o-mini pricing: $0.15/1M input, $0.60/1M output
            cost_usd = (total_tokens_in * 0.00000015) + (total_tokens_out * 0.0000006)
            return {
                "code": validated,
                "validation_passed": True,
                "error": None,
                "cost": {
                    "tokens_in": total_tokens_in,
                    "tokens_out": total_tokens_out,
                    "cost_usd": cost_usd,
                },
                "retries": attempt,
            }
        except ScaffoldValidationError as e:
            last_error = str(e)

    # All retries exhausted
    cost_usd = (total_tokens_in * 0.00000015) + (total_tokens_out * 0.0000006)
    return {
        "code": raw_code,
        "validation_passed": False,
        "error": f"Code failed validation after {MAX_RETRIES + 1} attempts: {last_error}",
        "cost": {
            "tokens_in": total_tokens_in,
            "tokens_out": total_tokens_out,
            "cost_usd": cost_usd,
        },
        "retries": MAX_RETRIES,
    }


def _strip_markdown_fences(code: str) -> str:
    """Remove markdown code fences (```python ... ```) if present."""
    lines = code.split("\n")
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate platform-compliant Python scaffolds for IntelliFlow OS."
    )
    parser.add_argument(
        "description",
        type=str,
        help="Natural language description of the component to generate",
    )
    parser.add_argument(
        "--contracts",
        type=Path,
        default=DEFAULT_CONTRACTS_PATH,
        help="Path to contracts.py",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory for generated scaffold",
    )
    args = parser.parse_args()

    result = generate_scaffold(args.description, contracts_path=args.contracts)

    if not result["validation_passed"]:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        if result["code"]:
            print("\n--- Generated (invalid) code ---", file=sys.stderr)
            print(result["code"], file=sys.stderr)
        sys.exit(1)

    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        # Generate a filename from the description
        slug = "_".join(args.description.lower().split()[:4])
        slug = "".join(c if c.isalnum() or c == "_" else "" for c in slug)
        out_file = args.output / f"scaffold_{slug}.py"
        out_file.write_text(result["code"], encoding="utf-8")
        print(f"Generated: {out_file}")
    else:
        print(result["code"])

    print(f"\n--- Generation Info ---", file=sys.stderr)
    print(f"  Validation: PASSED", file=sys.stderr)
    print(f"  Retries: {result['retries']}", file=sys.stderr)
    print(f"  Tokens: {result['cost']['tokens_in']} in / {result['cost']['tokens_out']} out", file=sys.stderr)
    print(f"  Cost: ${result['cost']['cost_usd']:.6f}", file=sys.stderr)


if __name__ == "__main__":
    main()

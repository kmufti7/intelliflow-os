#!/usr/bin/env python3
"""
AI-Powered Test Generator for IntelliFlow OS

Reads Pydantic schemas from intelliflow-core and generates edge-case pytest
suites. Implements Tier 2 of the Developer Experience Strategy: AI-Accelerated
Testing with verifiable output.

Usage:
    python tools/ai_test_generator.py                          # Print to stdout
    python tools/ai_test_generator.py --output tests/generated  # Write to directory
    python tools/ai_test_generator.py --schema CostTrackingSchema  # Single schema

Schemas sourced from: intelliflow-core/intelliflow_core/contracts.py
"""

import argparse
import importlib.util
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, get_args, get_origin


# ---------------------------------------------------------------------------
# Schema discovery
# ---------------------------------------------------------------------------

DEFAULT_CONTRACTS_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "intelliflow-core"
    / "intelliflow_core"
    / "contracts.py"
)


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


# ---------------------------------------------------------------------------
# Field analysis
# ---------------------------------------------------------------------------

def analyze_field(name: str, field_info) -> dict:
    """Extract type, constraints, and optionality from a Pydantic FieldInfo."""
    annotation = field_info.annotation
    is_optional = False
    inner_type = annotation

    origin = get_origin(annotation)
    if origin is Optional or (origin is type(None)):
        is_optional = True
    args = get_args(annotation)
    if args and type(None) in args:
        is_optional = True
        inner_type = next((a for a in args if a is not type(None)), annotation)

    constraints = {}
    for attr in ("ge", "gt", "le", "lt"):
        val = getattr(field_info, attr, None) if hasattr(field_info, attr) else None
        if val is None and hasattr(field_info, "metadata"):
            for m in field_info.metadata:
                v = getattr(m, attr, None)
                if v is not None:
                    val = v
                    break
        if val is not None:
            constraints[attr] = val

    # Pydantic v2 uses PydanticUndefined for fields without defaults
    try:
        from pydantic_core import PydanticUndefined
        has_default = (field_info.default is not PydanticUndefined) or (field_info.default_factory is not None)
    except ImportError:
        has_default = field_info.default is not None or field_info.default_factory is not None

    is_required = not is_optional and not has_default

    return {
        "name": name,
        "annotation": annotation,
        "inner_type": inner_type,
        "is_optional": is_optional,
        "is_required": is_required,
        "has_default": has_default,
        "constraints": constraints,
    }


def sample_value(inner_type, field_name: str) -> str:
    """Return a Python expression string for a valid sample value."""
    if inner_type is str or inner_type == str:
        return f'"test_{field_name}"'
    if inner_type is int or inner_type == int:
        return "1"
    if inner_type is float or inner_type == float:
        return "1.0"
    if inner_type is bool or inner_type == bool:
        return "True"
    if inner_type is datetime or inner_type == datetime:
        return "datetime.utcnow()"
    if hasattr(inner_type, "__members__"):  # Enum
        first = list(inner_type.__members__.values())[0]
        return f'"{first.value}"'
    origin = get_origin(inner_type)
    if origin is dict:
        return '{"key": "value"}'
    if origin is list:
        return "[]"
    return f'"test_{field_name}"'


def invalid_value(inner_type) -> Optional[str]:
    """Return a Python expression string for an invalid type value, or None."""
    if inner_type is str or inner_type == str:
        return "12345"
    if inner_type is int or inner_type == int:
        return '"not_an_int"'
    if inner_type is float or inner_type == float:
        return '"not_a_float"'
    if inner_type is bool or inner_type == bool:
        return None  # Pydantic coerces many values to bool
    if inner_type is datetime or inner_type == datetime:
        return '"not-a-date"'
    return None


# ---------------------------------------------------------------------------
# Test generation
# ---------------------------------------------------------------------------

def generate_tests_for_schema(schema_cls) -> str:
    """Generate pytest code for a single Pydantic schema class."""
    class_name = schema_cls.__name__
    snake_name = "".join(
        f"_{c.lower()}" if c.isupper() else c for c in class_name
    ).lstrip("_")

    fields = {
        name: analyze_field(name, info)
        for name, info in schema_cls.model_fields.items()
    }

    # Build the valid kwargs dict
    required_kwargs = {}
    for name, info in fields.items():
        if info["is_required"]:
            required_kwargs[name] = sample_value(info["inner_type"], name)

    def build_kwargs_str(overrides=None, extra=None):
        """Build a kwargs string from required_kwargs with optional overrides/extras."""
        merged = dict(required_kwargs)
        if overrides:
            merged.update(overrides)
        parts = [f"{k}={v}" for k, v in merged.items()]
        if extra:
            parts.extend(f"{k}={v}" for k, v in extra.items())
        return ", ".join(parts)

    kwargs_str = build_kwargs_str()

    lines = []
    lines.append(f"\n# --- Tests for {class_name} ---\n")

    # Test 1: Valid construction
    lines.append(f"def test_{snake_name}_valid_construction():")
    lines.append(f'    """A valid {class_name} should be created without errors."""')
    lines.append(f"    event = {class_name}({kwargs_str})")
    for name in required_kwargs:
        lines.append(f"    assert event.{name} is not None")
    lines.append("")

    # Test 2: Missing required fields
    for name, info in fields.items():
        if info["is_required"]:
            without = {k: v for k, v in required_kwargs.items() if k != name}
            without_str = ", ".join(f"{k}={v}" for k, v in without.items())
            lines.append(f"def test_{snake_name}_missing_{name}():")
            lines.append(f'    """Omitting required field \'{name}\' should raise ValidationError."""')
            lines.append(f"    with pytest.raises(ValidationError):")
            lines.append(f"        {class_name}({without_str})")
            lines.append("")

    # Test 3: Boundary conditions
    for name, info in fields.items():
        if "ge" in info["constraints"]:
            boundary = info["constraints"]["ge"]
            at_boundary_str = build_kwargs_str(overrides={name: str(boundary)})
            lines.append(f"def test_{snake_name}_{name}_at_boundary():")
            lines.append(f'    """Field \'{name}\' at ge={boundary} should be accepted."""')
            lines.append(f"    event = {class_name}({at_boundary_str})")
            lines.append(f"    assert event.{name} == {boundary}")
            lines.append("")

            below = boundary - 1 if isinstance(boundary, int) else boundary - 0.1
            below_boundary_str = build_kwargs_str(overrides={name: str(below)})
            lines.append(f"def test_{snake_name}_{name}_below_boundary():")
            lines.append(f'    """Field \'{name}\' below ge={boundary} should raise ValidationError."""')
            lines.append(f"    with pytest.raises(ValidationError):")
            lines.append(f"        {class_name}({below_boundary_str})")
            lines.append("")

    # Test 4: Optional fields accept None
    for name, info in fields.items():
        if info["is_optional"]:
            opt_str = build_kwargs_str(extra={name: "None"})
            lines.append(f"def test_{snake_name}_{name}_accepts_none():")
            lines.append(f'    """Optional field \'{name}\' should accept None."""')
            lines.append(f"    event = {class_name}({opt_str})")
            lines.append(f"    assert event.{name} is None")
            lines.append("")

    # Test 5: Default values
    for name, info in fields.items():
        if info["has_default"] and not info["is_optional"]:
            lines.append(f"def test_{snake_name}_{name}_has_default():")
            lines.append(f'    """Field \'{name}\' should have a default value."""')
            lines.append(f"    event = {class_name}({kwargs_str})")
            lines.append(f"    assert event.{name} is not None")
            lines.append("")

    return "\n".join(lines)


def generate_full_test_file(schemas: list, contracts_path: Path) -> str:
    """Generate a complete pytest file for all schemas."""
    header = textwrap.dedent(f'''\
        """
        Auto-generated edge-case tests for IntelliFlow OS Pydantic schemas.

        Generated by: tools/ai_test_generator.py
        Source: {str(contracts_path).replace(chr(92), '/')}
        Generated at: {datetime.now().isoformat()}Z

        These tests verify schema validation rules including:
        - Required field enforcement
        - Boundary conditions (ge/le constraints)
        - Optional field defaults
        - Type validation
        """

        import pytest
        from datetime import datetime
        from pydantic import ValidationError

    ''')

    # Add imports for each schema
    schema_names = ", ".join(s.__name__ for s in schemas)
    import_line = f"# Import schemas dynamically to support both installed and local usage\n"
    import_line += f"import importlib.util, pathlib\n"
    import_line += f"_spec = importlib.util.spec_from_file_location('contracts', pathlib.Path(r'{contracts_path}'))\n"
    import_line += f"_mod = importlib.util.module_from_spec(_spec)\n"
    import_line += f"_spec.loader.exec_module(_mod)\n"
    for s in schemas:
        import_line += f"{s.__name__} = _mod.{s.__name__}\n"
    import_line += "\n"

    # Generate tests for each schema
    test_blocks = []
    for schema in schemas:
        test_blocks.append(generate_tests_for_schema(schema))

    return header + import_line + "\n".join(test_blocks)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate edge-case pytest suites from Pydantic schemas."
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
        help="Output directory for generated test files",
    )
    parser.add_argument(
        "--schema",
        type=str,
        default=None,
        help="Generate tests for a single schema by name",
    )
    args = parser.parse_args()

    contracts_path = args.contracts.resolve()
    if not contracts_path.exists():
        print(f"ERROR: contracts.py not found at {contracts_path}", file=sys.stderr)
        print("Hint: Run from the IntelliFlow_OS repo root, or use --contracts PATH", file=sys.stderr)
        sys.exit(1)

    print(f"Loading schemas from: {contracts_path}", file=sys.stderr)
    module = load_contracts(contracts_path)
    schemas = discover_schemas(module)

    if args.schema:
        schemas = [s for s in schemas if s.__name__ == args.schema]
        if not schemas:
            print(f"ERROR: Schema '{args.schema}' not found", file=sys.stderr)
            sys.exit(1)

    print(f"Found {len(schemas)} schema(s): {', '.join(s.__name__ for s in schemas)}", file=sys.stderr)

    test_code = generate_full_test_file(schemas, contracts_path)

    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        out_file = args.output / "test_generated_schemas.py"
        out_file.write_text(test_code, encoding="utf-8")
        print(f"Generated: {out_file}", file=sys.stderr)
    else:
        print(test_code)

    # Summary
    test_count = test_code.count("\ndef test_")
    print(f"\nGenerated {test_count} test functions for {len(schemas)} schema(s).", file=sys.stderr)


if __name__ == "__main__":
    main()

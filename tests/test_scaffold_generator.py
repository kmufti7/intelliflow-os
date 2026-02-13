"""
Tests for the Scaffold Generator tool.

Covers: ast.parse() validation, markdown fence stripping, schema discovery,
empty input handling, retry logic, cost tracking, and end-to-end generation.
"""

import ast
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure the tools directory is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from scaffold_generator import (
    ScaffoldValidationError,
    _strip_markdown_fences,
    build_system_prompt,
    generate_scaffold,
    validate_python,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_PYTHON = '''\
"""Sample module for IntelliFlow OS."""

from datetime import datetime


def hello(name: str) -> str:
    """Greet a user."""
    return f"Hello, {name}"


if __name__ == "__main__":
    print(hello("world"))
'''

INVALID_PYTHON = """\
def broken(
    # Missing closing paren and colon
"""

VALID_WITH_FENCES = f"""\
```python
{VALID_PYTHON}
```"""


def make_mock_client(code: str, tokens_in: int = 50, tokens_out: int = 200):
    """Build a mock OpenAI client that returns the given code."""
    client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = code
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = tokens_in
    mock_usage.completion_tokens = tokens_out
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    client.chat.completions.create.return_value = mock_response
    return client


def make_retry_client(first_code: str, second_code: str,
                      tokens_in: int = 50, tokens_out: int = 200):
    """Build a mock client that returns different code on successive calls."""
    client = MagicMock()

    def side_effect(*args, **kwargs):
        mock_choice = MagicMock()
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = tokens_in
        mock_usage.completion_tokens = tokens_out
        mock_response = MagicMock()
        mock_response.usage = mock_usage

        # First call returns first_code, subsequent calls return second_code
        if client.chat.completions.create.call_count <= 1:
            mock_choice.message.content = first_code
        else:
            mock_choice.message.content = second_code

        mock_response.choices = [mock_choice]
        return mock_response

    client.chat.completions.create.side_effect = side_effect
    return client


# ---------------------------------------------------------------------------
# Tests: validate_python
# ---------------------------------------------------------------------------

def test_validate_python_accepts_valid_code():
    """Valid Python code should pass ast.parse() validation."""
    result = validate_python(VALID_PYTHON)
    assert result == VALID_PYTHON


def test_validate_python_rejects_syntax_error():
    """Code with syntax errors should raise ScaffoldValidationError."""
    with pytest.raises(ScaffoldValidationError, match="syntax error"):
        validate_python(INVALID_PYTHON)


def test_validate_python_rejects_empty():
    """Empty string should raise ScaffoldValidationError."""
    with pytest.raises(ScaffoldValidationError, match="Empty code"):
        validate_python("")


def test_validate_python_rejects_whitespace_only():
    """Whitespace-only string should raise ScaffoldValidationError."""
    with pytest.raises(ScaffoldValidationError, match="Empty code"):
        validate_python("   \n  \t  ")


# ---------------------------------------------------------------------------
# Tests: _strip_markdown_fences
# ---------------------------------------------------------------------------

def test_strip_markdown_fences_removes_fences():
    """Markdown code fences (```python ... ```) should be stripped."""
    result = _strip_markdown_fences(VALID_WITH_FENCES)
    assert "```" not in result
    # The actual code should still be present
    assert "def hello" in result


def test_strip_markdown_fences_noop_on_plain_code():
    """Plain Python code without fences should pass through unchanged."""
    result = _strip_markdown_fences(VALID_PYTHON)
    assert result == VALID_PYTHON


# ---------------------------------------------------------------------------
# Tests: generate_scaffold
# ---------------------------------------------------------------------------

def test_generate_scaffold_empty_description():
    """Empty description should return error without calling LLM."""
    result = generate_scaffold("", client=MagicMock())
    assert result["validation_passed"] is False
    assert "Empty description" in result["error"]
    assert result["code"] is None


def test_generate_scaffold_valid_generation():
    """Valid LLM output should pass validation and return code."""
    client = make_mock_client(VALID_PYTHON, tokens_in=100, tokens_out=300)
    result = generate_scaffold(
        "a simple greeting module",
        contracts_path=Path("nonexistent/contracts.py"),
        client=client,
    )
    assert result["validation_passed"] is True
    assert result["error"] is None
    assert "def hello" in result["code"]
    assert result["retries"] == 0


def test_generate_scaffold_strips_fences():
    """LLM output wrapped in markdown fences should still pass."""
    client = make_mock_client(VALID_WITH_FENCES, tokens_in=100, tokens_out=300)
    result = generate_scaffold(
        "a greeting module",
        contracts_path=Path("nonexistent/contracts.py"),
        client=client,
    )
    assert result["validation_passed"] is True
    assert "```" not in result["code"]


def test_generate_scaffold_retry_on_syntax_error():
    """If first generation has a syntax error, the tool should retry and succeed."""
    client = make_retry_client(INVALID_PYTHON, VALID_PYTHON)
    result = generate_scaffold(
        "a module with retries",
        contracts_path=Path("nonexistent/contracts.py"),
        client=client,
    )
    assert result["validation_passed"] is True
    assert result["retries"] == 1
    assert client.chat.completions.create.call_count == 2


def test_generate_scaffold_all_retries_exhausted():
    """If all retries produce invalid code, return error with the code."""
    client = make_mock_client(INVALID_PYTHON)
    result = generate_scaffold(
        "a broken module",
        contracts_path=Path("nonexistent/contracts.py"),
        client=client,
    )
    assert result["validation_passed"] is False
    assert "failed validation" in result["error"]
    assert result["retries"] == 2  # MAX_RETRIES


def test_generate_scaffold_cost_tracking():
    """Cost should be tracked across all LLM calls including retries."""
    client = make_mock_client(VALID_PYTHON, tokens_in=100, tokens_out=400)
    result = generate_scaffold(
        "a cost-tracked module",
        contracts_path=Path("nonexistent/contracts.py"),
        client=client,
    )
    assert result["cost"]["tokens_in"] == 100
    assert result["cost"]["tokens_out"] == 400
    assert result["cost"]["cost_usd"] > 0


def test_generate_scaffold_cost_accumulates_on_retry():
    """Cost should accumulate across retries."""
    client = make_retry_client(INVALID_PYTHON, VALID_PYTHON, tokens_in=50, tokens_out=200)
    result = generate_scaffold(
        "a retried module",
        contracts_path=Path("nonexistent/contracts.py"),
        client=client,
    )
    # Two calls: 50+50=100 tokens_in, 200+200=400 tokens_out
    assert result["cost"]["tokens_in"] == 100
    assert result["cost"]["tokens_out"] == 400


# ---------------------------------------------------------------------------
# Tests: build_system_prompt
# ---------------------------------------------------------------------------

def test_system_prompt_contains_schema_context():
    """System prompt should include schema summaries for the LLM."""
    prompt = build_system_prompt("class AuditEventSchema(BaseModel):", "AuditEventType: user_query")
    assert "AuditEventSchema" in prompt
    assert "AuditEventType" in prompt
    assert "governance" in prompt.lower()
    assert "ast.parse" in prompt.lower() or "valid Python" in prompt

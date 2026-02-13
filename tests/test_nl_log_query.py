"""
Tests for NL Log Query Tool (Story K)

Covers:
- Valid WHERE clause acceptance
- Blocked keyword rejection (INSERT, DROP, DELETE, UNION, SELECT, --, ;)
- Unknown column rejection
- Column whitelist enforcement
- Empty/malformed input handling
- Max query length enforcement
- SQL injection patterns blocked
- Happy path end-to-end with mocked LLM and seeded data
- Cost tracking
- Query attempt governance logging
"""

import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add tools/ to path so we can import nl_log_query
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from nl_log_query import (
    KNOWN_COLUMNS,
    LOG_TABLE,
    QueryValidationError,
    ensure_log_store,
    execute_query,
    format_results,
    nl_query,
    validate_where_clause,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mock_client(where_clause: str, tokens_in: int = 50, tokens_out: int = 20):
    """Build a mock OpenAI client that returns a specific WHERE clause."""
    client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = where_clause
    response.usage.prompt_tokens = tokens_in
    response.usage.completion_tokens = tokens_out
    client.chat.completions.create.return_value = response
    return client


def seed_log_entries(db_path: Path):
    """Insert sample log entries for end-to-end testing."""
    conn = ensure_log_store(db_path)
    rows = [
        ("evt-001", "classification", "SupportFlow", "INFO", "hello",
         "POSITIVE", 10, 5, 0.001, "gpt-4o-mini", "2026-02-12T10:00:00"),
        ("evt-002", "retrieval", "CareFlow", "ERROR", "patient query",
         "retrieval failed", 20, 10, 0.002, "gpt-4o-mini", "2026-02-12T11:00:00"),
        ("evt-003", "response", "CareFlow", "INFO", "gap analysis",
         "A1C above threshold", 50, 30, 0.01, "gpt-4o-mini", "2026-02-12T12:00:00"),
        ("evt-004", "ChaosMode", "CareFlow", "WARN", "faiss_unavailable",
         "fallback response", 0, 0, 0.0, "gpt-4o-mini", "2026-02-12T13:00:00"),
        ("evt-005", "classification", "SupportFlow", "ERROR", "timeout",
         "service unavailable", 15, 8, 0.003, "gpt-4o-mini", "2026-02-12T14:00:00"),
    ]
    conn.executemany(
        f"""INSERT INTO {LOG_TABLE}
            (id, event_type, module, level, input, output,
             tokens_in, tokens_out, cost_usd, model, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# 1. Valid WHERE clause accepted
# ---------------------------------------------------------------------------

def test_valid_where_clause_accepted():
    """A well-formed WHERE clause referencing known columns should pass validation."""
    clause = "level = 'ERROR' AND module = 'CareFlow'"
    result = validate_where_clause(clause)
    assert result == clause


# ---------------------------------------------------------------------------
# 2-7. Blocked keywords rejected
# ---------------------------------------------------------------------------

def test_blocked_keyword_insert():
    """INSERT in a WHERE clause should be rejected."""
    with pytest.raises(QueryValidationError, match="Blocked keyword.*INSERT"):
        validate_where_clause("id = '1'; INSERT INTO audit_logs VALUES ('x')")


def test_blocked_keyword_drop():
    """DROP in a WHERE clause should be rejected."""
    with pytest.raises(QueryValidationError, match="Blocked keyword.*DROP"):
        validate_where_clause("id = '1'; DROP TABLE audit_logs")


def test_blocked_keyword_delete():
    """DELETE in a WHERE clause should be rejected."""
    with pytest.raises(QueryValidationError, match="Blocked keyword.*DELETE"):
        validate_where_clause("1=1; DELETE FROM audit_logs")


def test_blocked_keyword_union():
    """UNION in a WHERE clause should be rejected (prevents subquery attacks)."""
    with pytest.raises(QueryValidationError, match="Blocked keyword.*UNION"):
        validate_where_clause("id = '1' UNION SELECT * FROM audit_logs")


def test_blocked_keyword_semicolon():
    """Semicolons should be rejected (prevents statement chaining)."""
    with pytest.raises(QueryValidationError, match="Blocked keyword"):
        validate_where_clause("level = 'ERROR'; DROP TABLE audit_logs")


def test_blocked_keyword_sql_comment():
    """SQL comment markers (--) should be rejected."""
    with pytest.raises(QueryValidationError, match="Blocked keyword"):
        validate_where_clause("level = 'ERROR' -- ignore rest")


# ---------------------------------------------------------------------------
# 8-9. Column whitelist enforcement
# ---------------------------------------------------------------------------

def test_unknown_column_rejected():
    """A reference to a column not in KNOWN_COLUMNS should be rejected."""
    with pytest.raises(QueryValidationError, match="Unknown column.*password"):
        validate_where_clause("password = 'secret'")


def test_column_whitelist_all_known_columns():
    """Every column in KNOWN_COLUMNS should be accepted in a valid clause."""
    for col in KNOWN_COLUMNS:
        # Simple equality check — should not raise
        validate_where_clause(f"{col} = 'test_value'")


# ---------------------------------------------------------------------------
# 10-11. Edge cases
# ---------------------------------------------------------------------------

def test_empty_query_returns_error(tmp_path):
    """An empty query string should return an error without calling the LLM."""
    result = nl_query("", db_path=tmp_path / "test.db")
    assert result["validation_passed"] is False
    assert result["error"] == "Empty query provided"
    assert result["results"] == []


def test_max_length_exceeded():
    """A WHERE clause exceeding MAX_QUERY_LENGTH should be rejected."""
    long_clause = "level = 'ERROR' AND " * 100  # well over 500 chars
    with pytest.raises(QueryValidationError, match="exceeds maximum length"):
        validate_where_clause(long_clause)


# ---------------------------------------------------------------------------
# 12. SQL injection via subquery blocked
# ---------------------------------------------------------------------------

def test_injection_subquery_blocked():
    """A subquery (SELECT inside WHERE) should be rejected."""
    with pytest.raises(QueryValidationError, match="Blocked keyword.*SELECT"):
        validate_where_clause("id IN (SELECT id FROM audit_logs WHERE level = 'ERROR')")


# ---------------------------------------------------------------------------
# 13. Happy path end-to-end with mocked LLM
# ---------------------------------------------------------------------------

def test_happy_path_end_to_end(tmp_path):
    """Full pipeline: mock LLM -> validation -> execution against seeded data."""
    db_path = tmp_path / "test.db"
    seed_log_entries(db_path)

    # Mock LLM returns a valid WHERE clause matching CareFlow errors
    mock_client = make_mock_client("level = 'ERROR' AND module = 'CareFlow'")

    result = nl_query("show me CareFlow errors", db_path=db_path, client=mock_client)

    assert result["validation_passed"] is True
    assert result["error"] is None
    assert len(result["results"]) == 1
    assert result["results"][0]["id"] == "evt-002"
    assert result["results"][0]["module"] == "CareFlow"
    assert result["results"][0]["level"] == "ERROR"
    assert result["where_clause"] == "level = 'ERROR' AND module = 'CareFlow'"


# ---------------------------------------------------------------------------
# 14. Cost tracking
# ---------------------------------------------------------------------------

def test_cost_tracking_computed(tmp_path):
    """Cost should be computed from token counts using gpt-4o-mini pricing."""
    db_path = tmp_path / "test.db"
    seed_log_entries(db_path)

    mock_client = make_mock_client(
        "level = 'INFO'", tokens_in=100, tokens_out=50
    )

    result = nl_query("show info logs", db_path=db_path, client=mock_client)

    assert result["cost"]["tokens_in"] == 100
    assert result["cost"]["tokens_out"] == 50
    # gpt-4o-mini: $0.15/1M input + $0.60/1M output
    expected_cost = (100 * 0.00000015) + (50 * 0.0000006)
    assert abs(result["cost"]["cost_usd"] - expected_cost) < 1e-10


# ---------------------------------------------------------------------------
# 15. Query attempt logged for governance
# ---------------------------------------------------------------------------

def test_query_attempt_logged(tmp_path):
    """Every query attempt should be logged to the audit_logs table."""
    db_path = tmp_path / "test.db"
    seed_log_entries(db_path)

    mock_client = make_mock_client("module = 'SupportFlow'")
    nl_query("show SupportFlow logs", db_path=db_path, client=mock_client)

    # Reopen the database and check for the governance log entry
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        f"SELECT * FROM {LOG_TABLE} WHERE event_type = 'nl_log_query'"
    )
    log_entries = [dict(row) for row in cursor.fetchall()]
    conn.close()

    assert len(log_entries) == 1
    entry = log_entries[0]
    assert entry["module"] == "core"
    assert entry["event_type"] == "nl_log_query"
    assert entry["input"] == "show SupportFlow logs"

    # The output field contains JSON with the generated SQL
    output_data = json.loads(entry["output"])
    assert output_data["sql"] == "module = 'SupportFlow'"
    assert output_data["valid"] is True

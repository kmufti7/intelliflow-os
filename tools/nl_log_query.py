#!/usr/bin/env python3
"""
Natural Language Log Query Tool for IntelliFlow OS

Translates natural language queries into validated SQL WHERE clauses,
executes them against the audit log store, and returns formatted results.

Pattern: "LLM translates, Python validates, code executes"

Usage:
    python tools/nl_log_query.py "show me all errors from CareFlow"
    python tools/nl_log_query.py --db path/to/logs.db "cost over $0.05"
    python tools/nl_log_query.py "find requests where tokens exceeded 500"
"""

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KNOWN_COLUMNS = {
    "id",
    "event_type",
    "module",
    "level",
    "input",
    "output",
    "tokens_in",
    "tokens_out",
    "cost_usd",
    "model",
    "timestamp",
}

BLOCKED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "EXEC", "UNION", "SELECT", "--", "/*", "*/", ";",
]

# SQL keywords that are valid in WHERE clauses (not column names)
SQL_KEYWORDS = {
    "AND", "OR", "NOT", "LIKE", "IN", "IS", "NULL", "BETWEEN",
    "TRUE", "FALSE", "ASC", "DESC", "WHERE", "ESCAPE", "GLOB",
    "EXISTS", "CASE", "WHEN", "THEN", "ELSE", "END",
}

MAX_QUERY_LENGTH = 500

DEFAULT_DB_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "nl_query_logs.db"
)

LOG_TABLE = "audit_logs"


# ---------------------------------------------------------------------------
# Log Store
# ---------------------------------------------------------------------------

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {LOG_TABLE} (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    module TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'INFO',
    input TEXT,
    output TEXT,
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    model TEXT,
    timestamp TEXT NOT NULL
)
"""


def ensure_log_store(db_path: Path) -> sqlite3.Connection:
    """Create or connect to the log store. Returns a connection with Row factory."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# SQL Validation
# ---------------------------------------------------------------------------

class QueryValidationError(Exception):
    """Raised when a generated SQL WHERE clause fails validation."""
    pass


def validate_where_clause(where_clause: str) -> str:
    """
    Validate a generated SQL WHERE clause against security rules.

    Checks:
    1. Non-empty
    2. Under MAX_QUERY_LENGTH characters
    3. No blocked keywords (INSERT, DROP, DELETE, UNION, SELECT, etc.)
    4. All column references exist in KNOWN_COLUMNS whitelist

    Returns the validated clause string or raises QueryValidationError.
    """
    if not where_clause or not where_clause.strip():
        raise QueryValidationError("Empty WHERE clause generated")

    clause = where_clause.strip()

    # Length check
    if len(clause) > MAX_QUERY_LENGTH:
        raise QueryValidationError(
            f"WHERE clause exceeds maximum length ({len(clause)} > {MAX_QUERY_LENGTH})"
        )

    # Blocked keywords check (case-insensitive)
    clause_upper = clause.upper()
    for keyword in BLOCKED_KEYWORDS:
        if keyword.upper() in clause_upper:
            raise QueryValidationError(f"Blocked keyword detected: '{keyword}'")

    # Column whitelist check
    # Strip single-quoted string literals first to avoid false positives
    # e.g., level = 'ERROR' -> level =   (so 'ERROR' isn't checked as a column)
    stripped = re.sub(r"'[^']*'", "", clause)

    # Extract word-like tokens (identifiers start with letter or underscore)
    tokens = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", stripped)

    known_lower = {c.lower() for c in KNOWN_COLUMNS}
    for token in tokens:
        if token.upper() in SQL_KEYWORDS:
            continue
        if token.lower() not in known_lower:
            raise QueryValidationError(
                f"Unknown column referenced: '{token}'. "
                f"Allowed columns: {sorted(KNOWN_COLUMNS)}"
            )

    return clause


# ---------------------------------------------------------------------------
# LLM Translation
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = f"""You are a SQL query assistant. Given a natural language query about log data, \
generate ONLY a SQL WHERE clause (without the word WHERE).

Available columns: {', '.join(sorted(KNOWN_COLUMNS))}

Column types:
- id: TEXT (unique event ID)
- event_type: TEXT (e.g., 'classification', 'retrieval', 'response', 'ChaosMode', 'nl_log_query')
- module: TEXT ('CareFlow', 'SupportFlow', 'core')
- level: TEXT ('INFO', 'WARN', 'ERROR')
- input: TEXT (input to this step)
- output: TEXT (output from this step)
- tokens_in: INTEGER (prompt tokens)
- tokens_out: INTEGER (completion tokens)
- cost_usd: REAL (cost in USD)
- model: TEXT (LLM model used, e.g., 'gpt-4o-mini')
- timestamp: TEXT (ISO 8601 format, e.g., '2026-02-12T14:30:00')

Rules:
- Output ONLY the WHERE clause content, nothing else
- Use single quotes for string values
- Use standard SQL operators: =, !=, <, >, <=, >=, LIKE, BETWEEN, IN, AND, OR, NOT, IS NULL, IS NOT NULL
- For time-based queries, use timestamp with ISO 8601 format
- Do NOT use subqueries, UNION, or any DDL/DML statements
- Do NOT use functions like LOWER(), UPPER(), etc.

Example:
Input: "show errors from CareFlow"
Output: level = 'ERROR' AND module = 'CareFlow'

Input: "requests costing more than 5 cents"
Output: cost_usd > 0.05"""


def translate_nl_to_where(query: str, client=None) -> dict:
    """
    Use LLM to translate a natural language query into a SQL WHERE clause.

    Args:
        query: Natural language query string
        client: OpenAI client instance (creates one if not provided)

    Returns:
        dict with keys: where_clause, tokens_in, tokens_out
    """
    if client is None:
        from openai import OpenAI
        client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0,
        max_tokens=200,
    )

    usage = response.usage
    return {
        "where_clause": response.choices[0].message.content.strip(),
        "tokens_in": usage.prompt_tokens if usage else 0,
        "tokens_out": usage.completion_tokens if usage else 0,
    }


# ---------------------------------------------------------------------------
# Query Execution
# ---------------------------------------------------------------------------

def execute_query(conn: sqlite3.Connection, where_clause: str) -> list[dict]:
    """Execute a validated WHERE clause against the log store. Returns up to 100 rows."""
    sql = f"SELECT * FROM {LOG_TABLE} WHERE {where_clause} ORDER BY timestamp DESC LIMIT 100"
    cursor = conn.execute(sql)
    return [dict(row) for row in cursor.fetchall()]


def format_results(results: list[dict]) -> str:
    """Format query results for terminal display."""
    if not results:
        return "No matching log entries found."

    lines = [f"Found {len(results)} matching log entries:\n"]
    for i, row in enumerate(results, 1):
        lines.append(f"--- Entry {i} ---")
        for key, value in row.items():
            if value is not None:
                lines.append(f"  {key}: {value}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Governance: Query Logging
# ---------------------------------------------------------------------------

def log_query_attempt(
    conn: sqlite3.Connection,
    nl_query: str,
    generated_sql: str,
    validation_passed: bool,
    result_count: int,
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost_usd: float = 0.0,
):
    """Log every query attempt to the audit log for governance."""
    event_id = f"nlq-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    conn.execute(
        f"""INSERT INTO {LOG_TABLE}
            (id, event_type, module, level, input, output,
             tokens_in, tokens_out, cost_usd, model, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            event_id,
            "nl_log_query",
            "core",
            "INFO" if validation_passed else "WARN",
            nl_query,
            json.dumps({
                "sql": generated_sql,
                "valid": validation_passed,
                "results": result_count,
            }),
            tokens_in,
            tokens_out,
            cost_usd,
            "gpt-4o-mini",
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def nl_query(query: str, db_path: Path = None, client=None) -> dict:
    """
    Execute a natural language query against the audit log store.

    Orchestrates the three-step pattern:
    1. LLM translates natural language -> SQL WHERE clause
    2. Python validates the WHERE clause (blocked keywords, column whitelist)
    3. Code executes the validated query against SQLite

    Args:
        query: Natural language query string
        db_path: Path to SQLite database (default: data/nl_query_logs.db)
        client: Optional OpenAI client (pass a mock for testing)

    Returns:
        dict with keys: results, where_clause, validation_passed, error, cost
    """
    if not query or not query.strip():
        return {
            "results": [],
            "where_clause": None,
            "validation_passed": False,
            "error": "Empty query provided",
            "cost": {"tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0},
        }

    if db_path is None:
        db_path = DEFAULT_DB_PATH

    conn = ensure_log_store(db_path)
    where_clause = None
    tokens_in = 0
    tokens_out = 0
    cost_usd = 0.0

    try:
        # Step 1: LLM translates
        translation = translate_nl_to_where(query, client=client)
        where_clause = translation["where_clause"]
        tokens_in = translation["tokens_in"]
        tokens_out = translation["tokens_out"]
        # gpt-4o-mini pricing: $0.15/1M input, $0.60/1M output
        cost_usd = (tokens_in * 0.00000015) + (tokens_out * 0.0000006)

        # Step 2: Python validates
        validated = validate_where_clause(where_clause)

        # Step 3: Code executes
        results = execute_query(conn, validated)

        # Governance: log the attempt
        log_query_attempt(
            conn, query, where_clause, True, len(results),
            tokens_in, tokens_out, cost_usd,
        )

        return {
            "results": results,
            "where_clause": validated,
            "validation_passed": True,
            "error": None,
            "cost": {
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": cost_usd,
            },
        }

    except QueryValidationError as e:
        log_query_attempt(
            conn, query, where_clause or "", False, 0,
            tokens_in, tokens_out, cost_usd,
        )
        return {
            "results": [],
            "where_clause": where_clause,
            "validation_passed": False,
            "error": str(e),
            "cost": {
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": cost_usd,
            },
        }

    except Exception as e:
        return {
            "results": [],
            "where_clause": where_clause,
            "validation_passed": False,
            "error": f"Query execution failed: {e}",
            "cost": {
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": cost_usd,
            },
        }

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Query IntelliFlow OS logs using natural language."
    )
    parser.add_argument(
        "query",
        type=str,
        help="Natural language query (e.g., 'show me all errors from CareFlow')",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to SQLite log database",
    )
    args = parser.parse_args()

    result = nl_query(args.query, db_path=args.db)

    if result["error"]:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        if result["where_clause"]:
            print(f"Generated SQL: {result['where_clause']}", file=sys.stderr)
        sys.exit(1)

    print(format_results(result["results"]))
    print(f"\n--- Query Info ---")
    print(f"  WHERE clause: {result['where_clause']}")
    print(f"  Tokens: {result['cost']['tokens_in']} in / {result['cost']['tokens_out']} out")
    print(f"  Cost: ${result['cost']['cost_usd']:.6f}")


if __name__ == "__main__":
    main()

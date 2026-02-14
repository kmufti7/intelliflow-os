# IntelliFlow OS — Data Dictionary

This document defines the data structures, schemas, and data flows across the platform.

## SupportFlow Data

### Tables (SQLite)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| support_tickets | Customer complaint tickets | id, customer_message, classification, policy_id, response, created_at |
| audit_logs | Governance trace | id, event_type, input, output, tokens_in, tokens_out, cost_usd, timestamp |

### Classification Enum

| Value | Meaning |
|-------|---------|
| POSITIVE | Positive feedback, thank customer |
| NEGATIVE | Complaint, create ticket + cite policy |
| QUERY | Question, retrieve relevant policy |

### Policy KB

| Field | Type | Description |
|-------|------|-------------|
| policy_id | string | Unique identifier (e.g., "POL-001") |
| keywords | list[string] | Trigger keywords for retrieval |
| content | string | Policy text |

---

## CareFlow Data

### Tables (SQLite)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| patients | Patient records | id, name, dob, created_at |
| appointments | Scheduled appointments | id, patient_id, specialist, reason, scheduled_at |
| audit_logs | Governance trace | id, event_type, input, output, tokens_in, tokens_out, cost_usd, timestamp |

### Extracted Patient Facts Schema

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| patient_name | string | Clinic note / FHIR | Patient identifier |
| a1c_value | float | Regex / FHIR | Hemoglobin A1C percentage |
| blood_pressure | string | Regex | Format: "systolic/diastolic" |
| medications | list[string] | Regex | Current medications |
| conditions | list[string] | Regex | Diagnosed conditions |

### Gap Rules Schema

| Gap Type | Rule | Severity Logic |
|----------|------|----------------|
| A1C_THRESHOLD | Diabetic + A1C ≥ 7.0% | LOW: 7.0-7.5, MODERATE: 7.5-9.0, HIGH: >9.0 |
| HTN_ACE_ARB | Diabetes + HTN + No ACE/ARB | Always HIGH |
| BP_CONTROL | HTN + BP ≥ 140/90 | MODERATE: 140-159, HIGH: ≥160 |

### FHIR Bundle Schema (Supported)

| Resource Type | Fields Extracted |
|---------------|------------------|
| Patient | name (given + family) |
| Observation | value (when LOINC code = 4548-4 for A1C) |

---

## Audit Event Types

The `audit_logs` table stores governance events across all modules and tools. The `event_type` field distinguishes sources:

| event_type | Source | Description |
|------------|--------|-------------|
| classification | SupportFlow | Customer message classified (POSITIVE/NEGATIVE/QUERY) |
| response | SupportFlow | Response generated with policy citation |
| chaos_error | Both modules | Failure injected during chaos mode |
| extraction | CareFlow | Patient facts extracted from note or FHIR |
| gap_detection | CareFlow | Deterministic gap rules evaluated |
| nl_log_query | NL Log Query tool | Query attempt (successful or rejected) — self-logged |
| scaffold_generation | Scaffold Generator | Code generation attempt with cost tracking |

---

## Developer Tools Data Structures

### NL Log Query

| Field | Type | Description |
|-------|------|-------------|
| natural_language_query | string | User's plain English query |
| generated_where_clause | string | LLM-translated SQL WHERE clause |
| validation_result | string | "accepted" or "rejected" with reason |
| column_whitelist | list[string] | 11 allowed columns from audit_logs schema |
| blocked_keywords | list[string] | 13 blocked SQL keywords (INSERT, DROP, SELECT, etc.) |

### Scaffold Generator

| Field | Type | Description |
|-------|------|-------------|
| description | string | Developer's natural language intent |
| generated_code | string | LLM-generated Python with governance patterns |
| validation_method | string | ast.parse() — syntax-only validation |
| retries | int | Number of retry attempts (max 2) |
| schemas_loaded | list[string] | Pydantic schemas discovered via importlib |

---

## Data Residency

| Data Type | Storage | Location | Rationale |
|-----------|---------|----------|-----------|
| Patient notes (PHI) | FAISS | Local only | Compliance — PHI never leaves machine |
| Medical guidelines | Pinecone | Cloud | Public data, safe for cloud storage |
| Audit logs | SQLite | Local | Governance trace, not transmitted |

---

## Data Flow Summary

```
Input (Note/FHIR)
  → Extraction (regex-first)
  → Patient Facts Schema
  → Reasoning Engine (deterministic rules)
  → Gap Detection
  → LLM Response (with citations)
  → Audit Log
```

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

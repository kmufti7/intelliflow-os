# Technical Deep Dive

**Audience:** Engineers, Architects, Technical Interviewers

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        APPLICATIONS                              │
├────────────────────────────┬────────────────────────────────────┤
│        SupportFlow         │            CareFlow                │
│         (Banking)          │          (Healthcare)              │
│                            │                                    │
│  Orchestrator Pattern      │  Extract-Reason-Explain Pattern   │
│  ├─ ClassifierAgent        │  ├─ PatientFactExtractor          │
│  ├─ PositiveHandler        │  ├─ ReasoningEngine               │
│  ├─ NegativeHandler        │  ├─ ConceptQueryBuilder           │
│  ├─ QueryHandler           │  ├─ GuidelineRetriever            │
│  └─ PolicyService          │  └─ BookingTool                   │
│                            │                                    │
└────────────┬───────────────┴──────────────┬─────────────────────┘
             │                              │
             │    pip install from git      │
             └──────────────┬───────────────┘
                            │
┌───────────────────────────┴───────────────────────────────────┐
│                     intelliflow-core                           │
│                                                                │
│  contracts.py          governance_ui.py       helpers.py      │
│  ├─ AuditEventSchema   ├─ init_governance    ├─ generate_id   │
│  ├─ CostTrackingSchema ├─ add_governance_log ├─ format_ts     │
│  └─ GovernanceLogEntry └─ render_panel       └─ calc_cost     │
└────────────────────────────────────────────────────────────────┘
```

---

## SupportFlow Technical Implementation

### Orchestrator Pattern

The system uses a **hierarchical multi-agent orchestration pattern**:

```python
# Execution flow
Customer Message
    ↓
Orchestrator.process_message()
    ├─ Step 1: Create initial ticket
    ├─ Step 2: Route to ClassifierAgent
    ├─ Step 3: Update ticket with classification
    ├─ Step 4: Route to appropriate handler
    ├─ Step 5: Generate response
    ├─ Step 6: Update ticket with response
    └─ Step 7: Calculate costs & finalize
```

**Agent Registry:**
```python
handlers = {
    MessageCategory.POSITIVE: PositiveHandler,
    MessageCategory.NEGATIVE: NegativeHandler,
    MessageCategory.QUERY: QueryHandler,
}
```

**Dependency Injection:** All agents receive:
- `DatabaseConnection` (db)
- `LLMClient` (llm_client)
- `TokenTracker` (token_tracker)
- `AuditService` (audit_service)

### Policy Service Implementation

**Storage:** Markdown file (`data/policy_kb.md`) with 20 banking policies

**Parsing:** Regex-based extraction:
```python
pattern = r'### (POLICY-\d+): (.+?)\n(.+?)(?=\n###|\n---|\Z)'
```

**Retrieval Strategy:**
1. **Keyword mapping**: 105 pre-defined keyword → policy ID mappings
2. **Content-based search**: Word intersection scoring
3. **Context injection**: Policies formatted into LLM prompts

**Citation Format:**
```
Per POLICY-001 (Card Replacement): [policy content]
```

### Chaos Engineering

**Implementation:**
```python
def _maybe_trigger_chaos(self, component: str, chaos_mode: bool):
    if chaos_mode and random.random() < 0.3:  # 30% failure rate
        raise ChaosError(component, random.choice(failure_messages))
```

**Injection Points:** 7 checkpoints throughout workflow

**Failure Scenarios:**
- Simulated network timeout
- Service temporarily unavailable
- Database connection dropped
- Rate limit exceeded
- Internal processing error

### Audit Logging Schema

```python
@dataclass
class AuditLog:
    ticket_id: str
    agent_name: str              # "classifier", "negative_handler"
    action: AuditAction          # CLASSIFY, ROUTE, RESPOND, ESCALATE
    input_summary: str           # Truncated to 200 chars
    output_summary: str          # Truncated to 200 chars
    decision_reasoning: str      # Why the agent made this decision
    confidence_score: float      # 0-1
    duration_ms: int             # Execution time
    success: bool
    error_message: str
```

### Cost Tracking

```python
# Cost calculation with cache token support
regular_input_tokens = response.input_tokens - response.cached_tokens
cached_input_cost = (cached_tokens / 1000) * pricing.cached_input_cost_per_1k
regular_input_cost = (regular_input_tokens / 1000) * pricing.input_cost_per_1k
output_cost = (output_tokens / 1000) * pricing.output_cost_per_1k
```

**Seeded Models:** gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo, claude-3-opus/sonnet/haiku

### Database Schema

```sql
-- 4 tables
tickets (id, customer_id, category, status, priority, response, metadata)
audit_logs (id, ticket_id, agent_name, action, reasoning, confidence, duration_ms)
token_usage (id, ticket_id, agent_name, model, input_tokens, output_tokens, cost_usd)
model_pricing (model_name, provider, input_cost_per_1k, output_cost_per_1k)
```

**Repository Pattern:** Clean separation of data access from business logic

---

## CareFlow Technical Implementation

### "LLM Extracts, Code Decides" Pattern

```
1. EXTRACT (Regex + LLM fallback)
   │
   └→ PatientFactExtractor.extract(note_text)
      ├─ Try regex patterns first
      ├─ Fall back to LLM if regex incomplete
      └─ Return ExtractedFacts dataclass

2. REASON (Pure Python)
   │
   └→ ReasoningEngine.evaluate_patient(facts, patient_id)
      ├─ Apply deterministic rules
      ├─ Generate "Therefore" statements
      └─ Return GapResults with citations

3. EXPLAIN (LLM with citations)
   │
   └→ CareOrchestrator.compose_response()
      ├─ Format gaps with evidence
      ├─ Generate natural language
      └─ Include [PATIENT: X] and [GUIDELINE: Y] citations
```

### Regex-First Extraction

**Key Patterns:**
```python
# A1C
r'(?:A1C|HbA1c|Hemoglobin A1c)[\s:]*(?:of\s+)?(\d+\.?\d*)'

# Blood Pressure
r'(?:BP|Blood\s*Pressure)[\s:]*(\d{2,3})\s*/\s*(\d{2,3})'
```

**Confidence Scoring:**
- Regex-only: 1.0 confidence
- Regex+LLM hybrid: 0.85 confidence
- LLM-only: 0.8 confidence

**Normalization:**
- Diagnosis keywords mapped to canonical forms
- Negation handling ("No HTN" → excluded)
- Medication cleanup (removes parenthetical notes)

### Deterministic Reasoning Engine

**Three Core Rules:**

```python
# Rule 1: A1C Threshold (guideline_001)
if patient.a1c >= 7.0:
    gap_detected = True
    severity = "high" if a1c >= 9.0 else "moderate"

# Rule 2: HTN ACE/ARB (guideline_002)
if has_diabetes and has_hypertension and not on_ace_or_arb:
    gap_detected = True
    severity = "high"

# Rule 3: BP Control (guideline_004)
if systolic >= 140 or diastolic >= 90:
    gap_detected = True
    severity = "high" if systolic >= 160 or diastolic >= 100 else "moderate"
```

**GapResult Structure:**
```python
@dataclass
class GapResult:
    gap_type: str           # "A1C_THRESHOLD"
    gap_detected: bool
    patient_fact: dict      # {"a1c": 8.2}
    guideline_fact: dict    # {"threshold": 7.0}
    comparison: str         # "8.2% >= 7.0%"
    therefore: str          # "Patient's A1C exceeds target"
    recommendation: str     # "Intensify treatment"
    severity: str           # "moderate"
    guideline_id: str       # "guideline_001_a1c_threshold"
```

### PHI-Aware Vector Strategy

**Architecture:**
```
Patient Notes (PHI)          Medical Guidelines (Public)
       │                              │
       ▼                              ▼
   FAISS (Local)              FAISS or Pinecone
       │                              │
       └──────────┬───────────────────┘
                  │
         ConceptQueryBuilder
         (De-identifies before external query)
```

**Concept Query De-identification:**
```python
# Input (Patient Data)
diagnoses: ["Type 2 Diabetes", "Hypertension"]
a1c: 8.2
blood_pressure: 142/94

# Output (De-identified Query)
"diabetes glycemic a1c hypertension blood pressure
 antihypertensive metabolic guidelines clinical recommendations"
```

**PHI Safety Validation:**
- Blocks decimal numbers (potential A1C/lab values)
- Blocks fraction patterns (###/###) (potential BP readings)
- Blocks date patterns
- Blocks patient ID patterns (PT###, MRN###)

### Planner Agent

**Intent Classification:**
```python
INTENT_PATTERNS = {
    "gap_analysis": ["care gap", "gaps", "what's missing"],
    "booking": ["book", "schedule", "appointment"],
    "explanation": ["why", "explain", "tell me more"],
}
```

**Execution Plans:**
- Gap Analysis: Extract → Retrieve → Compute → Respond
- Booking: Extract → Compute → Book → Respond
- Explanation: Retrieve → Compute → Explain

### Booking Tool

**Gap-to-Specialty Mapping:**
```python
GAP_TO_SPECIALTY = {
    "A1C_THRESHOLD": "Endocrinology",
    "HTN_ACE_ARB": "Cardiology",
    "BP_CONTROL": "Cardiology",
}
```

---

## intelliflow-core SDK

### Contracts Module

```python
class AuditEventType(str, Enum):
    USER_QUERY = "user_query"
    AI_RESPONSE = "ai_response"
    POLICY_CHECK = "policy_check"
    POLICY_VIOLATION = "policy_violation"
    # ... 15 total event types

class AuditEventSchema(BaseModel):
    event_id: str
    event_type: AuditEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    component: str
    action: str
    success: bool = True
    details: Dict[str, Any] = {}

class CostTrackingSchema(BaseModel):
    event_id: str
    model: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0.0)
```

### Governance UI Module

```python
def init_governance_state():
    """Initialize st.session_state.governance_logs"""

def add_governance_log(component, action, success, details):
    """Append GovernanceLogEntry to session state"""

def render_governance_panel(title="Governance Log"):
    """Render audit trail in Streamlit sidebar"""
```

### Helpers Module

```python
def generate_event_id(prefix="EVT") -> str:
    """Generate unique event ID: EVT_A1B2C3D4E5F6"""

def calculate_cost(input_tokens, output_tokens, model="gpt-4o-mini") -> float:
    """Calculate API cost from token counts"""

def format_timestamp_short(dt=None) -> str:
    """Format as HH:MM:SS for UI display"""
```

---

## Test Coverage

### SupportFlow Tests (13)
| Category | Tests | Focus |
|----------|-------|-------|
| Classifier | 4 | POSITIVE/NEGATIVE classification accuracy |
| Query Handler | 2 | Ticket retrieval, customer history |
| Database | 2 | Ticket creation, persistence |
| Chaos Mode | 3 | Failure injection, probability |

### CareFlow Tests (66)
| Category | Tests | Focus |
|----------|-------|-------|
| Extraction | 11 | A1C, BP, medications, negation handling |
| Reasoning | 14 | Gap detection, thresholds, severity |
| Booking | 11 | Appointment creation, specialty mapping |
| Concept Query | 15 | De-identification, PHI safety |
| Retrieval | 15 | FAISS, Pinecone, fallback |

### intelliflow-core Tests (32)
| Category | Tests | Focus |
|----------|-------|-------|
| Contracts | 11 | Pydantic validation, enums |
| Helpers | 21 | ID generation, cost calculation |

---

## Technical Decisions Summary

| Decision | Choice | Alternative Considered | Rationale |
|----------|--------|----------------------|-----------|
| Database | SQLite | PostgreSQL | Zero infrastructure for demo; repository pattern allows swap |
| Vector Store | FAISS | Pinecone only | PHI safety requires local-first; Pinecone available for enterprise |
| LLM | GPT-4o-mini | GPT-4, Claude | Cost-effective for demo; swappable via client abstraction |
| Extraction | Regex-first | LLM-only | 100x faster, zero cost, deterministic; LLM fallback for robustness |
| Reasoning | Python rules | LLM reasoning | Reproducibility, auditability; prevents hallucination in clinical logic |
| Async | aiosqlite | sync sqlite3 | Non-blocking I/O for Streamlit; cleaner async/await patterns |

---

## Code Quality Indicators

- **Type hints**: Throughout codebase
- **Dataclasses**: For all domain models
- **Pydantic**: For all API contracts
- **Repository pattern**: Clean data access layer
- **Dependency injection**: Testable agent design
- **Custom exceptions**: Semantic error hierarchy
- **Async/await**: Non-blocking I/O throughout

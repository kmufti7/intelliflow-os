# IntelliFlow OS — Cost Model (Token Economics)

This document explains the unit economics of IntelliFlow OS interactions.
Values are illustrative scenarios based on Azure OpenAI gpt-4o-mini pricing at time of development.

## What We Track

- Tokens in (prompt) and out (completion) per request
- Estimated USD cost per request
- Session-level rollups in governance UI

## Cost Per Interaction (Illustrative)

| Step | Typical Tokens | Notes |
|------|----------------|-------|
| Classification (SupportFlow) | ~200 in / ~10 out | Enum output keeps completion minimal |
| Policy Retrieval (SupportFlow) | ~500 in / ~200 out | Includes retrieved policy context |
| Extraction (CareFlow) | ~0 | Regex-first; LLM fallback rarely triggered |
| Reasoning (CareFlow) | ~800 in / ~300 out | Patient context + guidelines + response |

## Scenario Estimates

| Scenario | Interactions/Month | Est. Cost/Month | Notes |
|----------|-------------------|-----------------|-------|
| Demo usage | 100 | < $1 | Minimal testing |
| Pilot (10K) | 10,000 | $10-30 | Depends on retrieval payload size |
| Scale (100K) | 100,000 | $100-300 | Volume discounts may apply |

*Note: These are rough estimates. Actual costs depend on prompt engineering, retrieval chunk sizes, and Azure pricing at time of deployment.*

## Cost Controls Implemented

| Control | Module | Impact |
|---------|--------|--------|
| Regex-first extraction | CareFlow | Eliminates LLM cost for structured data extraction (100% regex success rate) |
| Keyword policy retrieval | SupportFlow | Avoids embedding/vector costs for simple lookups |
| Enum-based classification | SupportFlow | Minimal completion tokens |
| Token tracking in governance UI | Both | Visibility into per-request costs |

## Future Optimizations (Not Implemented)

- Response caching for repeated queries
- Tiered model selection (smaller model for classification, larger for generation)
- Batch processing for non-real-time workflows

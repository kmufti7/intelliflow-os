# PRD: Continuous Evaluation Harness

**Status:** Planned
**Version:** 0.1 (Draft)
**Owner:** Kaizen Works, LLC
**Last Updated:** 2026-02-25

## Problem Statement

GenAI model outputs are non-deterministic and degrade silently over time as vendor APIs update model weights. IntelliFlow OS v2.0 validates at build time (253 platform-core tests + 23 ClaimsFlow tests) but has no runtime or scheduled evaluation harness to detect output drift post-deployment. A model that passes all tests today may produce subtly degraded outputs next month after a silent vendor model update. SR 11-7 requires ongoing model monitoring — v2.0 addresses conceptual soundness and outcome analysis at build time but not continuous validation in production. For a CRO, this means governance coverage has a temporal gap between deployments.

## Target User

- **Primary:** MLOps engineers, model risk managers, compliance officers in regulated institutions operating IntelliFlow OS in production
- **Secondary:** Platform engineers responsible for CI/CD pipelines and nightly health checks

## Goals

1. Nightly automated evaluation run across all 3 LOB modules (SupportFlow, CareFlow, ClaimsFlow)
2. LLM-as-a-Judge scoring on 3 dimensions per workflow: Answer Relevance, Faithfulness, Policy Alignment
3. Drift detection with configurable threshold alerts
4. Results visible in SPOG observability panel
5. SR 11-7 ongoing model monitoring evidence artifact — auditable, timestamped, hash-chained

## Non-Goals

- **Not real-time inference monitoring.** Nightly batch cadence only in v3.0 — not sub-second streaming evaluation.
- **Not human-in-the-loop eval review.** Automated LLM-as-a-Judge scoring only — no human grading workflow.
- **Not SDK internals coverage.** Evaluation targets LOB module outputs (SupportFlow, CareFlow, ClaimsFlow), not intelliflow-core v2 SDK internals.
- **Not a model selection tool.** The harness detects drift — it does not recommend or auto-switch models.

## Solution Overview

The Continuous Evaluation Harness will introduce a new repository (`intelliflow-evals`) containing golden datasets, evaluation pipelines, and scoring infrastructure.

**Golden datasets:** 100 historical edge-case workflows per LOB module — curated from known-good outputs, boundary conditions, and previously-caught failure modes. Each golden record includes input, expected output characteristics, and scoring rubric.

**Evaluation pipeline:** GitHub Actions scheduled nightly run executes each golden record through the corresponding LOB module, captures the output, and submits the (input, output, expected) tuple to an LLM-as-a-Judge scorer.

**LLM-as-a-Judge scoring:** Using ragas or LangSmith (framework TBD), each output will be scored on 3 dimensions: Answer Relevance (does the output address the input?), Faithfulness (is the output grounded in source data?), and Policy Alignment (does the output conform to governance constraints?).

**Drift detection:** Configurable thresholds per dimension. When any score drops below threshold, the harness will fire a drift alert. Alert mechanism TBD — initial implementation will publish results to SPOG observability panel.

**SPOG integration:** The Executive SPOG will gain an observability section showing eval scores over time, current drift status, and last-run timestamp.

## Key Features (Planned)

- **Golden dataset per module:** 100+ curated edge-case records per LOB module, versioned alongside eval code.
- **Nightly automated run:** GitHub Actions scheduled pipeline — no manual intervention required.
- **3-dimension LLM-as-a-Judge scoring:** Answer Relevance, Faithfulness, Policy Alignment per workflow output.
- **Configurable drift thresholds:** Per-dimension, per-module threshold configuration. Alert on breach.
- **SPOG observability panel:** Eval scores, drift status, and run history visible to non-technical stakeholders.
- **WORM-logged eval results:** Each eval run recorded to WORM audit log with hash chain — tamper-evident evaluation history.

## Compliance Alignment

- **SR 11-7 (Model Risk Management):** Designed to support ongoing model monitoring requirements — continuous evaluation provides evidence that model outputs remain within acceptable bounds post-deployment. Primary compliance driver for this capability.
- **NIST AI RMF (MEASURE function):** Aligned to MEASURE function — systematic, quantitative assessment of AI system outputs over time.
- **EU AI Act (Post-market monitoring):** Designed to support Article 72 post-market monitoring requirements for high-risk AI systems — continuous evaluation provides the monitoring evidence that regulators expect.

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| intelliflow-core | v2 | WORM Logger (eval result audit trail), Token FinOps Tracker (eval cost tracking) |
| intelliflow-supportflow | 1.0 | SupportFlow module under evaluation |
| intelliflow-careflow | 1.0 | CareFlow module under evaluation |
| intelliflow-claimsflow | 1.0 | ClaimsFlow module under evaluation |
| ragas or LangSmith | TBD | LLM-as-a-Judge evaluation framework |
| GitHub Actions | N/A | CI/CD runner for nightly scheduled eval pipeline |
| Azure OpenAI Service | gpt-4o or equivalent | LLM-as-a-Judge inference |

## Success Metrics (Definition of Done)

| Metric | Target |
|--------|--------|
| Nightly GitHub Actions run completes without manual intervention | Verified |
| Scoring covers Answer Relevance, Faithfulness, Policy Alignment | 3 dimensions per output |
| Drift alert fires when any score drops below threshold | Verified |
| Results appear in SPOG within 1 hour of eval completion | Verified |
| Golden dataset coverage | 100+ edge cases per module |
| Eval results WORM-logged | Hash-chained, tamper-evident |

## Open Questions / Known Gaps

1. **Not yet implemented — roadmap item.** This PRD describes planned v3.0 capabilities.
2. **Eval framework choice (ragas vs LangSmith) not yet decided.** Both support LLM-as-a-Judge patterns — selection depends on licensing, cost, and integration complexity.
3. **Golden dataset curation methodology not yet defined.** Requires a process for selecting, validating, and versioning golden records per module.
4. **PTU cost implications of nightly LLM-as-a-Judge runs not yet modeled.** 300+ golden records evaluated nightly will consume LLM tokens — cost must be modeled against FinOps budget.
5. **SPOG observability panel extension not yet designed.** Current SPOG is a 3-panel layout — adding eval results requires layout extension or a dedicated eval view.
6. **Scoring calibration not yet validated.** LLM-as-a-Judge scoring reliability varies by domain — calibration against human judgment is needed before production reliance.

## Related ADRs / Roadmap References

- ADR-025: Deterministic v1 vs Agentic v2 (eval harness covers both v1 and v2 modules)
- ADR-024: Managed Inference vs Self-Hosted (eval inference cost considerations)
- docs/enterprise/SR_11_7_MODEL_RISK_MANAGEMENT.md (ongoing monitoring gap this addresses)
- Product Roadmap: v3.0 Priority 2

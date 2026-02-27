# PRD: Edge SLM Routing — Local Small Language Model Router

**Status:** Planned
**Version:** 0.1 (Draft)
**Owner:** Kaizen Works, LLC
**Last Updated:** 2026-02-25

## Problem Statement

Enterprise FinOps and data sovereignty requirements push regulated institutions to minimize cloud API calls for baseline tasks. IntelliFlow OS v2.0 uses Azure OpenAI for all LLM inference, including simple PII extraction and classification tasks that do not require frontier model reasoning capability. This creates unnecessary cost and third-party data transmission risk for low-complexity workloads. For a CFO, every cloud API call has a cost — and baseline extraction tasks that a local 8B model handles are burning budget on GPT-4o-mini tokens. For a data sovereignty officer, every cloud API call is a data transmission event — and PHI extraction that could run locally is crossing a network boundary it does not need to cross.

## Target User

- **Primary:** Enterprise architects, FinOps teams, data sovereignty officers in regulated institutions with strict data residency requirements or aggressive cost reduction mandates
- **Secondary:** Platform engineers deploying IntelliFlow OS modules in environments with limited or restricted cloud API access

## Goals

1. Deterministic task-type router — routing decision based on task classification, not LLM judgment
2. Local SLM handles PII extraction and classification tasks without cloud API calls
3. Azure OpenAI reserved for complex reasoning tasks only
4. Token FinOps Tracker updated to track local vs cloud inference costs separately
5. No PHI transmitted to cloud for baseline tasks that local SLM can handle

## Non-Goals

- **Not GPU infrastructure management.** Local compute provisioning is the deployer's responsibility — the SDK provides the routing layer, not the infrastructure.
- **Not SLM fine-tuning.** Pre-trained open-weight model consumed as-is. Fine-tuning workflows are out of scope.
- **Not dynamic routing based on output quality.** Routing is deterministic by task type — no runtime quality evaluation or fallback escalation in v3.0.
- **Not a model marketplace.** Single local SLM + single cloud LLM. No model catalog, no A/B testing, no multi-model ensemble.

## Solution Overview

The Edge SLM Router will introduce a routing layer in intelliflow-core v2 that classifies each inference request by task type and routes to the appropriate model:

**Task classification:** Each inference request will carry a task-type tag (e.g., `extraction`, `classification`, `reasoning`, `explanation`). The tag is set by the calling workflow node — not by LLM inference. This keeps routing deterministic and auditable.

**Local SLM path:** Baseline tasks (`extraction`, `classification`) will route to a locally hosted open-weight model (e.g., Llama-3-8B or equivalent) running inside the deployer's VPC. No data leaves the local compute boundary. Token usage will be tracked by the Token FinOps Tracker at local pricing (effectively zero marginal cost for self-hosted inference).

**Cloud LLM path:** Complex tasks (`reasoning`, `explanation`) will continue routing to Azure OpenAI GPT-4o or GPT-4o-mini via existing private endpoint configuration. Token usage tracked at cloud pricing tiers.

**FinOps split reporting:** The Token FinOps Tracker will gain a `routing_target` field — `local` or `cloud` — enabling cost split reporting in the SPOG Cost Ledger panel. Deployers will see exactly what percentage of inference spend goes to cloud vs local.

**MCP Registry integration:** The MCP Tool Registry will register both local and cloud inference endpoints as tools. Workflow nodes will request inference via the registry — the router resolves the target based on task type.

## Key Features (Planned)

- **Deterministic task-type router:** No LLM in the routing decision. Task type set by workflow node, resolved by router configuration.
- **Local SLM inference:** Open-weight model (Llama-3-8B or equivalent) for baseline extraction and classification. Zero cloud API calls for baseline tasks.
- **Cloud LLM fallback:** Azure OpenAI for complex reasoning. Existing private endpoint configuration unchanged.
- **FinOps split reporting:** Token FinOps Tracker records local vs cloud routing target per invocation. SPOG Cost Ledger shows cost split.
- **MCP Registry integration:** Both inference endpoints registered as MCP tools. Dynamic scoping controls which nodes can access which models.
- **PHI containment for baseline tasks:** Extraction tasks that handle PHI will route to local SLM only — no PHI transmitted to cloud for tasks the local model handles.

## Compliance Alignment

- **HIPAA minimum necessary principle:** Designed to support data minimization — PHI stays local for baseline tasks that do not require cloud inference. Reduces the data transmission surface.
- **SR 11-7 (Model Risk Management):** Aligned to model risk documentation requirements — deterministic routing is auditable and documented. Each model's scope is bounded by task type.
- **Data residency and sovereignty:** Designed to support regulated industry data residency expectations — deployers can configure baseline tasks to never leave their compute boundary.
- **NIST AI RMF (GOVERN function):** Routing configuration is a GOVERN control — it defines which model handles which task type, documented and auditable.

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| intelliflow-core | v2 | MCP Tool Registry (model registration), Token FinOps Tracker (cost split tracking) |
| Llama-3-8B or equivalent | TBD | Local open-weight SLM for baseline tasks |
| Local GPU or CPU compute | Deployer-managed | Inference infrastructure for local SLM |
| Docker | Latest | Containerization for local model serving |
| Azure OpenAI Service | GPT-4o / GPT-4o-mini | Cloud LLM for complex reasoning tasks |
| vLLM or Ollama | TBD | Local model serving framework |

## Success Metrics (Definition of Done)

| Metric | Target |
|--------|--------|
| Router correctly classifies baseline vs complex tasks | 95%+ accuracy on test suite |
| Local SLM handles baseline tasks without Azure API call | Verified — zero cloud calls for extraction/classification |
| Token FinOps Tracker records local vs cloud cost split | Verified — routing_target field populated |
| No PHI appears in Azure OpenAI request logs for baseline tasks | Verified |
| Cost reduction measurable vs all-cloud baseline | Quantified in FinOps report |

## Open Questions / Known Gaps

1. **Not yet implemented — roadmap item.** This PRD describes planned v3.0 capabilities.
2. **Local model selection (Llama-3-8B vs alternatives) not yet evaluated.** Model choice depends on extraction accuracy benchmarks, licensing terms, and inference hardware requirements.
3. **GPU vs CPU inference tradeoff not yet modeled.** CPU inference eliminates GPU procurement but may introduce latency that affects workflow SLOs.
4. **Portability concern:** Local GPU dependency conflicts with the lightweight reference architecture positioning. The SDK must remain usable without GPU hardware — local SLM is an optional deployment mode, not a requirement.
5. **Routing accuracy threshold (95%) not yet validated.** Task-type classification accuracy depends on how clearly workflow nodes tag their requests — ambiguous task types may misroute.
6. **Model serving framework (vLLM vs Ollama) not yet decided.** Selection depends on performance requirements, deployment complexity, and community support.

## Related ADRs / Roadmap References

- ADR-024: Managed Inference vs Self-Hosted (SLM routing extends the managed vs self-hosted decision)
- ADR-025: Deterministic v1 vs Agentic v2 (routing layer integrates with v2 agentic runtime)
- COST_MODEL.md (FinOps split reporting extends existing cost model)
- Product Roadmap: v3.0 Priority 3

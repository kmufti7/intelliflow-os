# ADR: Managed Inference vs. Self-Hosted Inference

## Status

**Accepted** — February 2026

---

## Context

IntelliFlow OS targets regulated industries — healthcare, banking, insurance — where LLM inference carries compliance, data sovereignty, and operational risk implications that general-purpose AI platforms can ignore. The inference layer is a foundational architectural decision because it determines:

- **Data residency guarantees.** Where patient data, financial records, and policy documents are processed during inference.
- **Compliance posture.** Whether the platform can operate under BAA, HIPAA-aligned, and SOC 2-audited infrastructure without the operator building that posture from scratch.
- **Operational burden.** Who manages GPU provisioning, model serving, autoscaling, and inference reliability — the platform team or a cloud provider with enterprise SLAs.
- **FinOps predictability.** Whether inference costs are forecastable for enterprise procurement or variable based on GPU utilization and spot pricing.

Two broad approaches were evaluated: managed inference through cloud provider APIs with enterprise compliance coverage, and self-hosted inference on dedicated GPU infrastructure with full operational control.

---

## Decision

IntelliFlow OS uses **managed inference via Azure OpenAI Service** as the primary inference provider, accessed through private endpoints. AWS Bedrock via PrivateLink is the designated secondary provider for multi-cloud deployments. Self-hosted inference (vLLM, Triton Inference Server) was evaluated and rejected.

---

## Options Considered

### Option A: Azure OpenAI Service via Private Endpoint (Selected — Primary)

While foundational model providers (including direct OpenAI Enterprise) now offer BAA eligibility, Zero Data Retention (ZDR), and PrivateLink configurations, satisfying baseline compliance is only the first step in enterprise AI deployment.

IntelliFlow OS explicitly standardizes on Azure OpenAI Service to ensure deployments remain entirely within the organization's existing sovereign cloud perimeter. By leveraging Azure, IntelliFlow OS natively inherits the enterprise's pre-approved Virtual Networks (VNets), Microsoft Entra ID Role-Based Access Control (RBAC), Azure Key Vault Customer-Managed Keys (CMK), and existing Microsoft cloud billing commitments (MACC).

This architectural standard eliminates the immense InfoSec, Legal, and Procurement friction of onboarding a net-new Tier-1 data sub-processor, ensuring that AI workloads are governed by the exact same centralized security and identity policies as the rest of the enterprise infrastructure.

| Attribute | Detail |
|-----------|--------|
| **Data processing** | Within Azure region, operator's tenant. Microsoft does not use customer data for model training under enterprise agreement. |
| **Compliance coverage** | BAA-eligible, SOC 2 Type II, ISO 27001, HITRUST CSF. HIPAA-aligned when operator executes BAA with Microsoft. |
| **Network isolation** | Private endpoint binds to operator's VNet. DNS resolution routes to private IP. No public internet exposure. |
| **Model access** | GPT-4o, GPT-4o-mini, text-embedding-3-small, and future models as Microsoft releases them. |
| **Operational burden** | Zero GPU operations. Microsoft manages provisioning, scaling, patching, and availability. |
| **Billing model** | Token-based (pay-per-use) or Provisioned Throughput Units (PTUs) for reserved capacity. |

### Option B: AWS Bedrock via PrivateLink (Selected — Secondary)

AWS Bedrock provides managed access to Anthropic Claude, Amazon Titan, and other foundation models through AWS infrastructure. PrivateLink routes inference traffic through the operator's VPC without public internet exposure.

| Attribute | Detail |
|-----------|--------|
| **Data processing** | Within AWS region, operator's account. AWS does not use customer data for model training. |
| **Compliance coverage** | HIPAA-eligible (with BAA), SOC 2 Type II, ISO 27001, FedRAMP High (GovCloud). |
| **Network isolation** | PrivateLink creates VPC endpoint. Traffic stays within AWS backbone. |
| **Model access** | Claude (Anthropic), Titan (Amazon), Llama (Meta), Mistral, and others as AWS onboards them. |
| **Operational burden** | Zero GPU operations. AWS manages provisioning, scaling, and availability. |
| **Billing model** | On-demand token pricing or Provisioned Throughput for reserved capacity. |

### Option C: Self-Hosted vLLM on NVIDIA H100/H200 (Rejected)

vLLM is an open-source inference engine optimized for high-throughput LLM serving. It supports PagedAttention for efficient KV cache management, continuous batching, and quantization (FP8, INT4 via AWQ/GPTQ).

| Attribute | Detail |
|-----------|--------|
| **Data processing** | Fully on-premises or in operator's cloud tenancy. Complete data sovereignty. |
| **Compliance coverage** | None inherited. Operator must build full compliance stack (SOC 2, penetration testing, audit logging, encryption at rest/in transit). |
| **GPU requirements** | NVIDIA H100 (80GB HBM3) or H200 (141GB HBM3e). Minimum 2-node cluster for HA. |
| **Quantization control** | Full control over FP8/INT4/AWQ/GPTQ quantization. Operator tunes precision-performance tradeoff. |
| **KV cache control** | PagedAttention with configurable block size. Operator manages GPU memory allocation. |
| **Operational burden** | GPU procurement, driver management, CUDA versioning, model weight distribution, health monitoring, autoscaling, failover. |
| **Capital cost** | $30K–$40K per H100 GPU. Minimum viable cluster: 4–8 GPUs ($120K–$320K hardware). Full production: $500K–$2M+. |

### Option D: Self-Hosted Triton Inference Server (Rejected)

NVIDIA Triton Inference Server supports multi-model serving with model parallelism, dynamic batching, and ensemble pipelines. It is designed for high-throughput production inference across multiple framework backends (TensorRT-LLM, vLLM, ONNX).

| Attribute | Detail |
|-----------|--------|
| **Data processing** | Fully on-premises or in operator's cloud tenancy. Complete data sovereignty. |
| **Compliance coverage** | None inherited. Same compliance build-out required as Option C. |
| **GPU requirements** | Same as Option C. Triton adds orchestration overhead for multi-model serving. |
| **Model parallelism** | Tensor parallelism and pipeline parallelism across multi-GPU nodes. |
| **Operational burden** | Everything in Option C plus Triton server configuration, model repository management, ensemble pipeline debugging, and TensorRT-LLM compilation. |
| **Capital cost** | Same GPU costs as Option C, plus infrastructure engineering effort for Triton deployment and management. |

---

## Tradeoff Analysis

| Dimension | Azure OpenAI (Private Endpoint) | AWS Bedrock (PrivateLink) | Self-Hosted vLLM | Self-Hosted Triton |
|-----------|--------------------------------|--------------------------|-------------------|-------------------|
| **Data sovereignty** | Azure region, operator tenant. Microsoft enterprise data use terms. | AWS region, operator account. AWS data use terms. | Full on-premises control. | Full on-premises control. |
| **Compliance posture** | BAA-eligible, SOC 2 Type II, HITRUST CSF inherited. | HIPAA-eligible, SOC 2 Type II, FedRAMP High (GovCloud). | None inherited. Full build required. | None inherited. Full build required. |
| **FinOps model** | PTUs for predictable costs; token-based for variable workloads. | Provisioned Throughput or on-demand token pricing. | CapEx-heavy ($500K–$2M+ GPU). Variable OpEx (power, cooling, ops team). | Same as vLLM plus Triton ops overhead. |
| **Operational burden** | None. Microsoft SLA (99.9%+ for PTUs). | None. AWS SLA. | High. GPU ops team required (2–3 FTEs minimum). | Very high. GPU ops + Triton expertise required. |
| **Quantization control** | None. Microsoft manages model optimization. | None. AWS/model provider manages optimization. | Full. FP8, INT4, AWQ, GPTQ configurable per model. | Full. TensorRT-LLM compilation with custom precision. |
| **KV cache control** | None. Abstracted by provider. | None. Abstracted by provider. | Full. PagedAttention block size, GPU memory allocation. | Full. Plus multi-model memory partitioning. |
| **Time to production** | Days. Private endpoint + API key. | Days. PrivateLink + IAM configuration. | Months. GPU procurement, cluster build, model optimization, compliance build-out. | Months+. Everything in vLLM plus Triton pipeline setup. |
| **Model selection** | Microsoft-hosted models only (GPT-4o, GPT-4o-mini, embeddings). | Multi-provider (Claude, Titan, Llama, Mistral). | Any open-weight model (Llama, Mistral, Mixtral, Qwen). | Any model with TensorRT-LLM or vLLM backend. |

---

## Why Self-Hosted Was Rejected

Self-hosted inference (Options C and D) was rejected for four specific reasons, each independently sufficient:

### 1. Data Sovereignty Risk Without BAA

Self-hosting provides physical data control but does not provide compliance coverage. The operator must independently achieve SOC 2 Type II certification, execute their own BAA framework, conduct penetration testing, and maintain audit trails for inference operations. Azure OpenAI Service and AWS Bedrock provide these through their existing enterprise compliance programs — the operator inherits the posture rather than building it.

For regulated industries, the question is not "where is the data?" but "can you prove the data handling meets compliance requirements?" Managed providers answer this with existing certifications. Self-hosted requires the operator to build and maintain the evidence independently.

### 2. GPU Infrastructure Procurement ($2M+ (3-year TCO including ops team))

A production-grade self-hosted inference deployment for regulated industries requires:

| Component | Minimum Spec | Estimated Cost |
|-----------|-------------|----------------|
| GPU cluster (inference) | 4–8x NVIDIA H100 80GB | $120K–$320K |
| GPU cluster (redundancy) | Identical standby cluster for HA | $120K–$320K |
| Networking | 400Gbps InfiniBand for tensor parallelism | $50K–$100K |
| Storage | NVMe for model weights, checkpoint management | $20K–$50K |
| Power/cooling | Per-rack power delivery and thermal management | $30K–$80K/year |
| Monitoring/observability | GPU health, inference latency, queue depth | $20K–$40K/year |
| **Total (Year 1)** | | **$360K–$910K** |
| **3-year TCO** | Including refresh, power, and ops team | **$1.5M–$3M+** |

This capital expenditure is not justified when managed inference provides equivalent or better compliance posture at token-based or PTU pricing that scales with actual usage.

### 3. Inference Operations Team Required

Self-hosted inference requires dedicated operations expertise:

- **GPU operations:** Driver updates, CUDA version management, thermal monitoring, hardware failure response.
- **Model serving:** Weight distribution, quantization pipeline, KV cache tuning, continuous batching configuration.
- **Reliability:** Health checks, autoscaling, failover, load balancing across GPU nodes.
- **Security:** Network isolation, access control, encryption, audit logging at the inference layer.

Minimum staffing: 2–3 dedicated ML infrastructure engineers. Annual cost: $400K–$750K fully loaded. This team does not exist in most regulated industry IT organizations, and hiring for GPU operations expertise is competitive.

### 4. No Incremental Compliance Benefit

The compliance frameworks relevant to IntelliFlow OS (HIPAA, NIST AI RMF, OWASP LLM Top 10, EU AI Act) do not require self-hosted inference. They require:

- Data processing agreements (BAAs) — available from Azure and AWS.
- Audit trails for model inputs/outputs — implemented at the application layer regardless of inference provider.
- Network isolation — achieved through private endpoints and PrivateLink.
- Data residency within specified jurisdictions — configurable by Azure region and AWS region selection.

Self-hosting adds operational complexity without improving the compliance posture that regulators and auditors evaluate.

---

## FinOps Implications

### Provisioned Throughput Units (PTUs) vs. Token-Based Billing

| Model | Azure PTU (per unit/month) | Azure Token-Based (per 1M tokens) | Break-Even Point |
|-------|---------------------------|-----------------------------------|-----------------|
| GPT-4o | ~$3,600/PTU/month | $2.50 input / $10.00 output | ~1.4M output tokens/month per PTU |
| GPT-4o-mini | ~$900/PTU/month | $0.15 input / $0.60 output | ~1.5M output tokens/month per PTU |

**IntelliFlow OS cost posture:**

- **Regex-first extraction** reduces LLM calls by handling structured data extraction before LLM fallback. In CareFlow, regex extraction achieves 100% success rate on test patients — the LLM fallback is never triggered for extraction.
- **Structured outputs** (enum classification, typed fields) reduce output token count by constraining response format.
- **Model tiering** uses gpt-4o-mini (10x cheaper than gpt-4o) for all operations where reasoning capability is not the bottleneck.

These architectural decisions reduce per-interaction LLM cost, which shifts the FinOps calculus toward token-based billing for most deployments. PTUs become cost-effective only at sustained high-volume production workloads (thousands of interactions per hour).

### Enterprise Procurement Alignment

Managed inference pricing maps naturally to enterprise procurement:

- **Token-based billing** → OpEx, forecastable from historical usage.
- **PTU billing** → Reserved capacity, comparable to reserved instances. Predictable monthly spend for budgeting.
- **Self-hosted GPU** → CapEx procurement cycle (6–12 months for hardware, facilities, staffing). Does not align with agile deployment timelines.

---

## Consequences

### Positive

- **Middleware connectors target private endpoints only.** All inference integration code assumes Azure Private Endpoint or AWS PrivateLink. No public internet API calls in the inference path.
- **Quantization decisions delegated to provider.** Microsoft and AWS optimize model serving for their hardware. The platform does not need to manage FP8/INT4 tradeoffs, KV cache block sizing, or continuous batching configuration.
- **Operational burden eliminated.** Zero GPU procurement, zero driver management, zero inference scaling operations. The platform team focuses on application-layer governance, not infrastructure operations.
- **Compliance posture strengthened.** BAA eligibility, SOC 2 Type II, and HITRUST CSF coverage inherited from cloud provider certifications. The operator's compliance evidence includes provider audit reports rather than self-assessed infrastructure documentation.
- **Time to production measured in days, not months.** Private endpoint provisioning and API integration is a days-scale operation. Self-hosted GPU cluster build-out is a months-scale operation.

### Negative

- **No quantization control.** The platform cannot tune inference precision (FP8 vs. FP16) for specific use cases. If a future workload requires custom quantization for latency or cost reasons, self-hosted becomes necessary.
- **Model selection constrained to provider catalog.** Open-weight models (Llama 3, Mistral, Qwen) are available through Bedrock but not through Azure OpenAI. If a specific open-weight model is required, the architecture must accommodate Bedrock or introduce self-hosted serving for that model.
- **Provider lock-in at the inference layer.** While the platform abstracts the LLM call through middleware connectors, the private endpoint configuration is provider-specific. Switching from Azure to Bedrock (or vice versa) requires network reconfiguration, not just code changes.
- **Provider pricing changes pass through.** Token pricing and PTU costs are set by Microsoft and AWS. The platform has no leverage to negotiate inference costs beyond volume commitments.

---

## References

| Reference | Relevance |
|-----------|-----------|
| [Azure OpenAI Service BAA](https://learn.microsoft.com/en-us/azure/compliance/offerings/offering-hipaa-us) | BAA eligibility for HIPAA-aligned deployments. Azure OpenAI is a covered service under Microsoft's BAA. |
| [Azure OpenAI Private Endpoints](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/private-endpoints) | Network isolation configuration for VNet-integrated inference. |
| [Azure OpenAI Provisioned Throughput](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/provisioned-throughput) | PTU pricing model and capacity planning for reserved inference. |
| [AWS Bedrock HIPAA Eligibility](https://aws.amazon.com/bedrock/security-compliance/) | HIPAA-eligible service under AWS BAA. PrivateLink for VPC isolation. |
| [SR 11-7: Guidance on Model Risk Management](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm) | Federal Reserve guidance on model risk. Relevant to banking module inference decisions. |
| [NIST AI RMF](https://www.nist.gov/artificial-intelligence/risk-management-framework) | Risk management framework mapped in GOVERNANCE.md. Inference provider selection is a Govern function decision. |
| [vLLM Project](https://github.com/vllm-project/vllm) | Open-source inference engine evaluated as Option C. |
| [NVIDIA Triton Inference Server](https://developer.nvidia.com/triton-inference-server) | Multi-model serving platform evaluated as Option D. |

---

*Apache 2.0 — Copyright 2025-2026 Kaizen Works, LLC*

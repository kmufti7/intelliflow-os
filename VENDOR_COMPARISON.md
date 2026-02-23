# IntelliFlow OS — Vendor & Technology Decisions

This document explains the technology choices made for IntelliFlow OS and the rationale behind them.

## LLM Provider

| Option | Chosen | Rationale |
|--------|--------|-----------|
| Azure OpenAI Service | Yes | Enterprise compliance (BAA available for HIPAA), data residency controls, same models as OpenAI |
| OpenAI Direct API | No | BAA-eligible, but requires onboarding a separate sub-processor — no VNet, Entra ID, Key Vault, or MACC integration |
| Anthropic Claude | No | Strong alternative, but Azure relationship already established |
| Open Source (Llama, Mistral) | No | Self-hosting complexity, less suitable for production-grade reference architecture |

While foundational model providers (including direct OpenAI Enterprise) now offer BAA eligibility, Zero Data Retention (ZDR), and PrivateLink configurations, satisfying baseline compliance is only the first step in enterprise AI deployment.

IntelliFlow OS explicitly standardizes on Azure OpenAI Service to ensure deployments remain entirely within the organization's existing sovereign cloud perimeter. By leveraging Azure, IntelliFlow OS natively inherits the enterprise's pre-approved Virtual Networks (VNets), Microsoft Entra ID Role-Based Access Control (RBAC), Azure Key Vault Customer-Managed Keys (CMK), and existing Microsoft cloud billing commitments (MACC).

This architectural standard eliminates the immense InfoSec, Legal, and Procurement friction of onboarding a net-new Tier-1 data sub-processor, ensuring that AI workloads are governed by the exact same centralized security and identity policies as the rest of the enterprise infrastructure.

---

## Vector Database

| Option | Used For | Rationale |
|--------|----------|-----------|
| FAISS (Local) | Patient notes (PHI) | Zero network transmission, data stays on machine, no vendor dependency for sensitive data |
| Pinecone (Cloud) | Medical guidelines | Managed service, scalable, appropriate for public/non-PHI data |

**Architecture Decision:** Hybrid vector strategy. PHI stays local (FAISS), public knowledge goes to cloud (Pinecone). This demonstrates compliance-aware architecture without over-engineering.

**Alternatives Considered:**

| Option | Why Not |
|--------|---------|
| Pinecone for everything | PHI would leave the machine — compliance risk |
| FAISS for everything | Loses cloud scalability demonstration |
| Weaviate | Good option, but Pinecone is more widely adopted in enterprise |
| Chroma | Good for local, but FAISS is more battle-tested |

---

## Database

| Option | Chosen | Rationale |
|--------|--------|-----------|
| SQLite | Yes | Zero setup, file-based, sufficient for reference implementation scale, easy to inspect |
| PostgreSQL | No | Overkill for production-grade reference architecture, adds deployment complexity |
| MongoDB | No | Document store not needed for structured audit logs |

**Note:** SQLite is intentionally simple. Production deployment would likely use PostgreSQL with proper connection pooling.

---

## LLM Model

| Model | Used For | Rationale |
|-------|----------|-----------|
| gpt-4o-mini | All tasks | Cost-effective, fast, sufficient quality for classification/extraction/response |

**Alternatives Considered:**

| Model | Why Not |
|-------|---------|
| gpt-4o | Higher cost, not needed for reference implementation workloads |
| gpt-3.5-turbo | Lower quality, marginal cost savings |

**Future Consideration:** Tiered model selection — use smaller models for classification, larger for complex reasoning.

---

## Embedding Model

| Model | Chosen | Rationale |
|-------|--------|-----------|
| text-embedding-3-small | Yes | Good quality, low cost, sufficient for guideline retrieval |
| text-embedding-3-large | No | Higher cost, marginal quality improvement for this use case |
| OpenAI ada-002 | No | Older model, superseded by text-embedding-3 family |

---

## UI Framework

| Option | Chosen | Rationale |
|--------|--------|-----------|
| Streamlit | Yes | Rapid prototyping, built-in components, suitable for reference implementations |
| Gradio | No | Similar capability, less familiar |
| React | No | Overkill for production-grade reference architecture, adds frontend complexity |

---

## CI/CD

| Option | Chosen | Rationale |
|--------|--------|-----------|
| GitHub Actions | Yes | Native to GitHub, free tier sufficient, industry standard |
| Jenkins | No | Self-hosted complexity |
| CircleCI | No | Good option, but GitHub Actions is simpler for this scope |

---

## Summary

| Decision | Choice | Key Reason |
|----------|--------|------------|
| LLM Provider | Azure OpenAI | Enterprise compliance (BAA) |
| Vector DB (PHI) | FAISS | Local-only, no network transmission |
| Vector DB (Public) | Pinecone | Managed, scalable |
| Database | SQLite | Simplicity for reference implementation scope |
| Model | gpt-4o-mini | Cost-effective |
| Embeddings | text-embedding-3-small | Good quality, low cost |
| UI | Streamlit | Rapid prototyping |
| CI/CD | GitHub Actions | Industry standard |

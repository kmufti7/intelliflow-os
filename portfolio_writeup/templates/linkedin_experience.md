# LinkedIn Experience Entry

**Title:** Head of Product & Architect | IntelliFlow OS
**Company:** Kaizen Works, LLC
**Subtitle:** Governance-First AI for Regulated Industries

---

Governance-First AI for Regulated Industries

Designed and built IntelliFlow OS, a governance-first AI platform for regulated industries. Architected a shared SDK (intelliflow-core) enforcing Pydantic data contracts, audit logging, and cost tracking across modules.

Shipped SupportFlow (Banking): a multi-agent orchestrator that classifies customer intents via structured outputs and routes to specialized handlers grounded in {{sf_policies}} specific policies. Features deterministic routing and full audit trails.

Architected CareFlow (Healthcare): a clinical gap analysis engine where the LLM is the translator, not the decision-maker. Regex-first extraction handles structured data at zero API cost, feeding deterministic Python rules for gap detection. Every recommendation cites patient evidence against published guidelines.

Implemented PHI-aware data residency: patient data resides in local FAISS vector indexes (never leaves the machine), guidelines route to cloud. Dual-mode ingestion supports both legacy clinical notes and structured HL7 FHIR R4 bundles.

Built Chaos Engineering into both modules. Deterministic failure injection with safe clinical fallbacks. {{chaos_tests_total}} chaos tests, including integration tests that caught a real bypass bug.

Reduced LLM cost exposure through architecture, not negotiation: regex-first extraction, structured output schemas, model tier selection (gpt-4o-mini), and session cost tracking.

Created an Enterprise Evidence Pack ({{enterprise_docs}} docs) mapped to NIST AI RMF, OWASP LLM Top 10, and EU AI Act, with {{verification_checks}} automated verification checks.

Built an AI test generator that reads Pydantic schemas and produces edge-case pytest suites. {{total_tests}} tests ({{hand_written_tests}} hand-written + {{ai_generated_tests}} generated) across {{repos}} repos.

Technologies: Python, OpenAI API, Azure OpenAI, RAG, FAISS, Pinecone, Streamlit, Pydantic, FHIR R4, pytest, GitHub Actions, CI/CD, HIPAA, Model Risk Management, LangChain, LangGraph

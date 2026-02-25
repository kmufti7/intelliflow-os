# IntelliFlow OS — Enterprise Evidence Index

This repo is a governance-first AI platform reference implementation for regulated industries.
This index is the fastest way to review enterprise readiness signals.

## Overview

| Document | Purpose |
|----------|---------|
| [PRODUCT_BRIEF.md](PRODUCT_BRIEF.md) | 1-page buyer-facing summary: problem, solution, capabilities, deployment |

## Core Artifacts
| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Platform overview |
| [GOVERNANCE.md](GOVERNANCE.md) | Governance & NIST AI RMF + EU AI Act alignment |
| [SECURITY.md](SECURITY.md) | Security posture & OWASP LLM Top 10 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System diagrams (Mermaid) |
| [COST_MODEL.md](COST_MODEL.md) | Token economics & cost controls |
| [TEST_STRATEGY.md](TEST_STRATEGY.md) | Testing philosophy & coverage |
| [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | Data schemas & flows |
| [OBSERVABILITY.md](OBSERVABILITY.md) | Logging, monitoring & alerting |
| [VENDOR_COMPARISON.md](VENDOR_COMPARISON.md) | Technology decisions & rationale |
| [ETHICS.md](ETHICS.md) | Responsible AI considerations |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Enterprise Evidence Pack
| Document | Purpose |
|----------|---------|
| [SECURITY_PRIVACY_OVERVIEW.md](docs/enterprise/SECURITY_PRIVACY_OVERVIEW.md) | Security & privacy posture: data residency, compliance alignment, customer responsibility model |
| [SLO_SLA_STATEMENT.md](docs/enterprise/SLO_SLA_STATEMENT.md) | Service-level objectives, performance targets, customer responsibilities, measurement & reporting |
| [RELEASE_NOTES_VERSIONING.md](docs/enterprise/RELEASE_NOTES_VERSIONING.md) | Versioning policy, release cadence, deprecation process, customer communication |
| [PRODUCT_ROADMAP.md](docs/enterprise/PRODUCT_ROADMAP.md) | Product direction: current release, near-term priorities, strategic vision, guiding principles |
| [ADR_MANAGED_INFERENCE_VS_SELF_HOSTED.md](docs/enterprise/ADR_MANAGED_INFERENCE_VS_SELF_HOSTED.md) | Architecture decision record: managed inference (Azure OpenAI, AWS Bedrock) vs. self-hosted (vLLM, Triton), tradeoff analysis, FinOps implications |
| [ADR_DETERMINISTIC_V1_VS_AGENTIC_V2.md](docs/enterprise/ADR_DETERMINISTIC_V1_VS_AGENTIC_V2.md) | Architecture decision record: deterministic v1 vs. agentic v2, regulatory defensibility, kill-switch mandate, SR 11-7 alignment |
| [SR_11_7_MODEL_RISK_MANAGEMENT.md](docs/enterprise/SR_11_7_MODEL_RISK_MANAGEMENT.md) | SR 11-7 model risk management alignment: requirement mapping, module-specific controls, kill-switch mandate, deploying institution responsibilities |

## Strategy Documents
| Document | Purpose |
|----------|---------|
| [DEVELOPER_EXPERIENCE_STRATEGY.md](DEVELOPER_EXPERIENCE_STRATEGY.md) | AI-native developer experience: capability tiers, build vs. buy, and productivity measurement |

## Modules
| Module | Repository |
|--------|------------|
| SupportFlow (Banking) | [intelliflow-supportflow](https://github.com/kmufti7/intelliflow-supportflow) |
| CareFlow (Healthcare) | [intelliflow-careflow](https://github.com/kmufti7/intelliflow-careflow) |
| ClaimsFlow (Insurance) | [intelliflow-claimsflow](https://github.com/kmufti7/intelliflow-claimsflow) |

## SDK
| Component | Repository |
|-----------|------------|
| intelliflow-core | [intelliflow-core](https://github.com/kmufti7/intelliflow-core) |

### intelliflow-core v2 Runtime Files
| File | Purpose |
|------|---------|
| `v2/runtime/kill_switch.py` | KillSwitchGuard — deterministic governance enforcement interceptor (fail-closed, collect-all-failures) |
| `v2/runtime/contracts.py` | GovernanceRule (self-documenting rule struct), WorkflowResult (structured run() return) |
| `v2/runtime/exceptions.py` | KillSwitchTriggered (carries failed_rules + state_snapshot for audit) |
| `v2/tests/test_kill_switch.py` | 8 tests: pass, single failure, multi-failure, workflow integration, zero rules, state snapshot, fail-closed, immutability |
| `v2/runtime/tool_registry.py` | MCPRegistry (static catalog + dynamic scoping) + ToolSchema (Pydantic-validated tool definition) |
| `v2/tests/test_tool_registry.py` | 12 tests: registration, duplicate rejection, lock, post-lock rejection, scoped retrieval, unknown tool, full catalog, lock state, description required, input schema, scoped isolation, empty scope |
| `v2/storage/db.py` | DatabaseSessionManager — shared SQLite connection with WAL mode |
| `v2/storage/worm_logger.py` | WORMLogRepository — HMAC-SHA256 hash-chained WORM audit log, SQLite triggers |
| `v2/tests/test_worm_logger.py` | 12 tests: table creation, trigger enforcement, GENESIS, hash chain, verification, tamper detection, fail-closed, workflow integration, kill-switch logging, tool execution, trace_id propagation |

## Project Governance
| Document | Purpose |
|----------|---------|
| [LICENSE](LICENSE) | Apache License 2.0 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |

## Demos
| Module | Video |
|--------|-------|
| SupportFlow | [Watch Demo](https://youtu.be/7B6mBKlNL5k) |
| CareFlow | [Watch Demo](https://youtu.be/Ct9z91649kg) |

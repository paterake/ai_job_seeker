# Registries, Versioning & Lineage (Spoke)
> DAMA mapping: Metadata Management → Registries, Versioning & Lineage

## Governs

- Tool and model identity: a stable identifier, owned schema and version for each tool and MCP server, and an allowlist entry for each model
- Per-tool risk rating (`risk_tier`) and the approval flag a high-risk tool carries
- Versioning and pinning of shared surfaces and platform dependencies
- Run lineage and evidence for LLM-calling modules (coding-agent sessions are evidenced by git, capability-decision records and anchor docs)

## Enforced

- Tool and MCP registry shape (name, owner, evidence), `risk_tier` value, and `requires_approval: true` on a high-risk tool: validator, `governed-repo-validate` over [tool_registry.yaml](../master-data/tool_registry.yaml). Rule: [lineage.md](../ai_harness/rules/lineage.md) → Registries and Versioning.
- Model registry shape (name, owner, evidence): validator, `governed-repo-validate` over [model_registry.yaml](../master-data/model_registry.yaml).
- Research citations behind a governance change: human review at change approval. Rule: [security-threat-model.md](../ai_harness/rules/security-threat-model.md) → External Research.

## Not enforced

- Lineage manifest per run, approvals, exceptions and elevations bound to `run_id`, append-only evidence, recorded assumptions: required by [lineage.md](../ai_harness/rules/lineage.md) → Lineage and Evidence; no PCO check. The PCO has not audited `ai_agent_core` for a run-manifest implementation.
- Tool schema and version, model allowlist entries, and the ban on unregistered tools: required by [lineage.md](../ai_harness/rules/lineage.md) → Registries and Versioning; no PCO check (see [integration spoke](../integration/README.md) → Not enforced).
- Version pinning and semantic versioning of shared surfaces: required by [lineage.md](../ai_harness/rules/lineage.md) → Registries and Versioning; no PCO check (nothing reads consumers' pins).
- Retention schedule and legal hold on run evidence: required by [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md) → Records Retention & Legal Hold; no PCO check.

## Rules

- [lineage.md](../ai_harness/rules/lineage.md)
- Registry data: [master-data spoke](../master-data/README.md)

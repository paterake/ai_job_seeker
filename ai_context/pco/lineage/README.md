# Registries, Versioning & Lineage (Spoke)
> DAMA mapping: Metadata Management → Registries, Versioning & Lineage

## Governs

- Tool and model identity: a stable identifier, owned schema and version for each tool and MCP server, and an allowlist entry for each model
- Per-tool risk rating (`risk_tier`) and the approval flag a high-risk tool carries
- Versioning and pinning of shared surfaces and platform dependencies
- Run lineage and evidence for LLM-calling modules (coding-agent sessions are evidenced by git, capability-decision records and anchor docs)

## Enforced

- Tool and model registry shape, `risk_tier` and `requires_approval` on a high-risk tool: [master-data spoke](../master-data/README.md) → Enforced. Rule: [lineage.md](../ai_harness/rules/lineage.md) → Registries and Versioning.

## Not enforced

- Lineage manifest per run, approvals, exceptions and elevations bound to `run_id`, append-only evidence, recorded assumptions: required by [lineage.md](../ai_harness/rules/lineage.md) → Lineage and Evidence; no PCO check. What is known of `ai_agent_core`'s runtime: [assurance spoke](../assurance/README.md) → Declared Scope of Validation.
- Tool schema and version, model allowlist entries, and the ban on unregistered tools: required by [lineage.md](../ai_harness/rules/lineage.md) → Registries and Versioning; no PCO check. Tool calls are not checked against the registry: an unregistered tool or MCP server is not blocked, and risk tier is not checked before execution; the registry validator checks the file, not tool use.
- Version pinning and semantic versioning of shared surfaces: required by [lineage.md](../ai_harness/rules/lineage.md) → Registries and Versioning; no PCO check (nothing reads consumers' pins).
- Retention schedule and legal hold on run evidence: required by [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md) → Records Retention & Legal Hold; no PCO check.

## Rules

- [lineage.md](../ai_harness/rules/lineage.md)
- Registry data: [master-data spoke](../master-data/README.md)

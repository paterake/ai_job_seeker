# Identity, Policy & Configuration Master Data (Spoke)
> DAMA mapping: Reference & Master Data → Identity, Policy & Configuration Master Data

## Governs

- The registry files that hold the PCO's canonical identifiers, listed below
- Their minimum fields, which [CONTRACT.md](../governance/CONTRACT.md) and [lineage.md](../ai_harness/rules/lineage.md) define
- Additive-only project policy: a governed repo may strengthen platform policy, never weaken it

| Registry | Holds | Checked by |
|---|---|---|
| [tool_registry.yaml](tool_registry.yaml) | Tools and MCP servers: owner, evidence, `risk_tier`, `requires_approval` | `governed-repo-validate` |
| [model_registry.yaml](model_registry.yaml) | Model endpoints: owner, evidence | `governed-repo-validate` |
| [policy_pack_registry.yaml](../governance/policy_pack_registry.yaml) | Policy packs: id, version, owner, evidence, `rule_files` | `governed-repo-validate` (every rule file listed in a pack, every listed file present) |
| [exception_registry.yaml](../governance/exception_registry.yaml), and each repo's own (location: [CONTRACT.md](../governance/CONTRACT.md) → Exceptions) | Exceptions: id, expiry | `governed-repo-validate`, `exception-registry-validate`, `governance-audit` (unique non-empty `id`; a missing, invalid or past `expires` fails) |
| [capability_registry.yaml](../governance/capability_registry.yaml) | Capabilities: tier, lifecycle stage, owner, evidence | `capability-registry-validate`; with `--target`, and in `validate --scope governance\|full`, a consumer adopting a Tier 3/4 capability while `experimental` without an escalation record, or while `deprecated` ([CONTRACT.md](../governance/CONTRACT.md) → Capability Lifecycle) |
| [execution_limits.yaml](../governance/execution_limits.yaml) | Session limits read by `check_execution_limits.sh` | `governed-repo-validate` (positive integer, rationale) |

## Enforced

- Registry shape and the fields named in the "Checked by" column: validators named there (run from `ai_agent_pco`).
- A high-risk tool sets `requires_approval: true`: validator, `governed-repo-validate`. Rule: [lineage.md](../ai_harness/rules/lineage.md) → Registries and Versioning.
- An approval record in `audit/approvals/` for each repo-owned Tier 3/4 capability: `governance-audit` (fails with
  `--fail`; not applicable when the repo owns none). Rule: [CONTRACT.md](../governance/CONTRACT.md) → Change Control.
- A governed repo declares the Additive-Only Acknowledgment in `REPO_CONTRACT.md`: section presence is checked as in the [architecture spoke](../architecture/README.md) → Enforced; content is human review.

## Not enforced

- Exception minimum fields other than `id` and `expires`: required by [CONTRACT.md](../governance/CONTRACT.md) → Exceptions; no PCO check.
- Policy-pack applicability, rollout state and rollout verification plan: required by [CONTRACT.md](../governance/CONTRACT.md) → Policy Packs; no PCO check.
- Entitlements: [tool_registry.yaml](tool_registry.yaml) carries per-tool `entitlements.roles/environments`, but no validator reads them and no broker applies them; deny-by-default for side-effecting or network tools is target, not implemented.
- Registries for workflows, roles, agents and environment baselines, including per-workflow output schemas, risk tier and required sensors: target, not implemented.
- Stage progression in the capability lifecycle: nothing checks a stage against its criteria
  ([CONTRACT.md](../governance/CONTRACT.md) → Capability Lifecycle).

## Rules

- [lineage.md](../ai_harness/rules/lineage.md) (registry entries, run identity)
- Registry contracts: [CONTRACT.md](../governance/CONTRACT.md) → Exceptions, Capability Lifecycle, Policy Packs

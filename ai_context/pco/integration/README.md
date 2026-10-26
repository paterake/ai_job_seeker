# Tooling & Integration (Spoke)
> Area: Tooling & Integration

## Governs

- Which tools and MCP servers a governed repo may adopt, and how they are assessed first
- The tool and MCP registry: [master-data/tool_registry.yaml](../master-data/tool_registry.yaml)
- Harness switches, model upgrades and tool-interface changes (model-impact events), including the edit-tool format
- The gate hooks the PCO ships and their wiring into the agent's harness settings
- Native-first integration of vendors, models and tools

## Enforced

- A direct force-push command is denied: hook `check_guard.sh` (`force_push_refused`; what it matches:
  [hooks/README.md](../ai_harness/hooks/README.md)). The guard's other check, and the shell-call budget, are owned
  by the [knowledge](../knowledge/README.md) and [operations](../operations/README.md) spokes.
- Both PCO gates are run on the pre-tool-use event through current agent adapters: validator
  `validate_harness_wiring.py`, run from `ai_agent_pco`.
- `ai_context/` names no specific agent and does not refer back to the agent entrypoint or configuration folder
  ([CONTRACT.md](../governance/CONTRACT.md) → What a Target Repo Must Look Like): validator `governance-audit
  --fail` (agent neutrality scan, run from `ai_agent_pco`).
- Tool and MCP registry shape: [master-data spoke](../master-data/README.md) → Enforced.
- Tool and MCP trust assessment and the tool-selection test before adoption, native first, OSS preference,
  approval gates: human review ([security-threat-model.md](../ai_harness/rules/security-threat-model.md) §4,
  [code-architecture.md](../ai_harness/rules/code-architecture.md) → Native First, Low-Code / OSS Preference,
  [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) → Approval Gates).

## Not enforced

- Tool calls checked against the registry: [lineage spoke](../lineage/README.md) → Not enforced.
- Schema validation at tool invocation (target, not implemented; control plane,
  [governance/HUB.md](../governance/HUB.md) → Not enforced).
- Regression evidence before merge for a model-impacting tool change: required by Canonical below (delegated by
  [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)); no PCO check. The re-validation steps
  under Canonical are human review.
- A gate hook failing closed when the agent adapter that runs it is missing or crashes: required by
  [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) → Hooks: Guidance vs Enforcement; not
  met: per the harness's hook documentation (not tested here), a hook that cannot start does not block the call;
  no PCO check.
- Force push through indirection and other irreversible shell commands such as `rm -rf` or a hard reset: required
  by harness-tool-contract.md → Hooks: Guidance vs Enforcement; no PCO check. Only the direct force-push form is
  hooked ([hooks/README.md](../ai_harness/hooks/README.md)).
- Vendor third-party risk assessment before adoption: required by
  [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md) → Procurement & Access Lifecycle; no PCO
  check.
- Go-live effective oversight and segregation of duties (author ≠ approver): required by
  [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md) → Go-Live Approval Gates; no PCO check (the
  operator is the only approver today: [governance/HUB.md](../governance/HUB.md) → Not enforced).

## Rules

- [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)
- [security-threat-model.md](../ai_harness/rules/security-threat-model.md) §4
- [code-architecture.md](../ai_harness/rules/code-architecture.md) → Native First, Low-Code / OSS Preference
- [lineage.md](../ai_harness/rules/lineage.md) → Registries and Versioning
- [observability.md](../ai_harness/rules/observability.md) (telemetry for tool calls)
- Vendor third-party risk assessment: [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md)

## Canonical

[harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) cites this section for the edit-tool
format and model-impact events.

### Model–harness co-evolution (governed risk)

Models learn harness-specific behaviour through post-training and usage feedback, so tool and harness interfaces
can become implicit dependencies. A tool or harness change is a model-impact event, not only an engineering change: it
can degrade a capable model, and a harness tuned for one model may not transfer to another without regression
evidence.

- A change to a tool's schema, argument semantics, output format or default behaviour is model-impacting.
- A model-impacting change carries regression evidence (contract tests and eval runs) before merge, and ships with
  a rollback path.

### Edit-tool contract (capability floor)

The edit-tool format is a capability floor, not a configuration detail. A model can be post-trained against a
specific harness's edit dialect (e.g. unified diff vs. search-and-replace block). Governance transfers across
harnesses; the edit-tool contract may not. A mismatched dialect can collapse success rate and create retry loops
whatever the governance quality; restoring the expected format can recover it, with no model change.

- When switching harnesses, validate the edit-tool format before declaring the migration complete.
- When upgrading models, re-validate the edit-tool contract; forward compatibility is not guaranteed.
- Diagnose an unexplained success-rate drop after a harness or model change as a possible format mismatch before
  concluding model regression.

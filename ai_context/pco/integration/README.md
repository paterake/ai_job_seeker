# Tooling & Integration (Spoke)
> DAMA mapping: Data Integration & Interoperability → Tooling & Integration

## Governs

- Which tools and MCP servers a governed repo may adopt, and how they are assessed first
- The tool and MCP registry: [master-data/tool_registry.yaml](../master-data/tool_registry.yaml)
- Harness switches, model upgrades and tool-interface changes (model-impact events), including the edit-tool format
- The Claude Code hooks the PCO ships and their wiring into a repo's `settings.json`
- Native-first integration of vendors, models and tools

## Enforced

- A direct force-push command is denied (`force_push_refused`; matched on command text, so a quoted
  form (`bash -c "git push -f"`, `eval "git push -f"`) or a git alias is not caught); a file edit under `ai_context/pco/` in a consumer is denied
  (`synced_pco_edit_refused`; a shell command that writes there is not checked): hook `check_guard.sh`
  ([hooks/README.md](../ai_harness/hooks/README.md)).
- Shell calls per session are capped (`execution_limit_hit`): hook `check_execution_limits.sh`
  ([hooks/README.md](../ai_harness/hooks/README.md)).
- Both hooks are wired on PreToolUse in `settings.json`: validator `scripts/validate_harness_wiring.py`.
- Registry entries are well formed (each tool has `owner`, `evidence`, `risk_tier`; a `high` tool sets
  `requires_approval: true`; each MCP server has `owner` and `evidence`): validator `governed-repo-validate`
  ([lineage.md](../ai_harness/rules/lineage.md) → Registries and Versioning).
- Tool and MCP trust assessment and the tool-selection test before adoption, native first, OSS preference,
  approval gates: human review ([security-threat-model.md](../ai_harness/rules/security-threat-model.md) §4,
  [governance.md](../ai_harness/rules/governance.md) → Native First, Low-Code / OSS Preference,
  [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) → Approval Gates).

## Not enforced

- Tool calls are not checked against the registry: an unregistered tool or MCP server is not blocked, and risk
  tier is not checked before execution. Required by [lineage.md](../ai_harness/rules/lineage.md) → Registries and
  Versioning; no PCO check. The registry validator checks the file, not tool use.
- Schema validation at tool invocation (target, not implemented; control plane,
  [governance/HUB.md](../governance/HUB.md) → Not enforced).
- Regression evidence before merge for a model-impacting tool change: required by Canonical below (delegated by
  [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)); no PCO check. The re-validation steps
  under Canonical are human review.
- A gate hook failing closed when it crashes or its script is missing or not executable: required by
  [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) → Hooks: Guidance vs Enforcement; no
  PCO check. Per the hooks docs (not tested here), such a call passes.
- Force push through indirection (a quoted `bash -c` or `eval` form, a git alias) and other irreversible shell
  commands such as `rm -rf` or a hard reset: required by
  [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) → Hooks: Guidance vs Enforcement; no
  PCO check. Only the direct force-push form is hooked.
- Vendor third-party risk assessment before adoption: required by
  [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md) → Procurement & Access Lifecycle; no PCO
  check.

## Rules

- [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)
- [security-threat-model.md](../ai_harness/rules/security-threat-model.md) §4
- [governance.md](../ai_harness/rules/governance.md) → Native First, Low-Code / OSS Preference
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

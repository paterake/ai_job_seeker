# Operations (Spoke)
> DAMA mapping: Data Storage & Operations → Agent Runtime & Operations

## Governs

- Execution bounds for LLM-calling modules: timeouts, budgets, retries, loop stops, input caps
- Degrade modes on failure
- The defined evaluation path for an LLM-calling module
- The human checkpoint before a high-risk tool call
- Kill switches
- Bounds on a governed agent session

## Enforced

- Shell (Bash) calls per session are capped at `max_tool_calls`; further shell calls are denied: hook
  (`check_execution_limits.sh`, [hooks README](../ai_harness/hooks/README.md)). Every limit in
  [execution_limits.yaml](../governance/execution_limits.yaml) is a positive integer with a rationale: validator
  (`governed-repo-validate`).
- A `high` risk tool entry declares `requires_approval: true`: validator (`governed-repo-validate`). It checks the
  declaration, not the runtime stop.
- Execution bounds, degrade modes, the defined evaluation path (→ Non-Negotiable Baseline), the runtime human
  checkpoint and kill switches in LLM-calling modules: human review against
  [operations.md](../ai_harness/rules/operations.md).

## Not enforced

- Bounded execution in LLM-calling modules: required by operations.md → Non-Negotiable Baseline and Execution
  Bounds; no PCO check.
- Kill-switch activation evidence: required by operations.md → Human Checkpoint and Kill Switches; no PCO check.
- Regulatory incident notification: required by
  [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md) → Regulatory Notification & FinOps; no PCO
  check.

## Rules

- [operations.md](../ai_harness/rules/operations.md)
- Telemetry: [observability.md](../ai_harness/rules/observability.md); run identity and evidence:
  [lineage.md](../ai_harness/rules/lineage.md); incident capture: [assurance.md](../ai_harness/rules/assurance.md)
- [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md) → Regulatory Notification & FinOps

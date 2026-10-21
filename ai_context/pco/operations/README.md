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

- Shell calls per session are capped at `max_tool_calls` in
  [execution_limits.yaml](../governance/execution_limits.yaml); further shell calls are denied: hook
  `check_execution_limits.sh` (`execution_limit_hit`; behaviour: [hooks README](../ai_harness/hooks/README.md)).
  The limits file's shape and the `requires_approval` declaration on a high-risk tool: [master-data
  spoke](../master-data/README.md) → Enforced.
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

# Observability, Analytics & FinOps (Spoke)
> DAMA mapping: Data Warehousing & Business Intelligence → Observability, Analytics & FinOps

## Governs

- `run_id` propagation and tracing of LLM-calling modules
- The telemetry event contract for LLM and tool calls
- Privacy-safe telemetry: no raw prompts, payloads or retrieved content
- The post-run review artefact
- FinOps budget ownership

## Enforced

- Tracing Invariant, Telemetry Event Contract and Run Review: human review against
  [observability.md](../ai_harness/rules/observability.md).

## Not enforced

- LLM-calling modules emit the telemetry contract and keep raw text out of logs: required by observability.md →
  Tracing Invariant and Telemetry Event Contract; no PCO check.
- FinOps budget ownership and chargeback: required by
  [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md) → Regulatory Notification & FinOps; no PCO
  check.

## Rules

- [observability.md](../ai_harness/rules/observability.md)
- [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md) → Regulatory Notification & FinOps

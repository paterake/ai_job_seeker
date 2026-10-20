---
description: LLMOps runtime bounds — budgets, bounded loops and retries, input caps, degrade modes, kill switches. Loaded when editing Python, because model-calling modules carry no naming pattern.
globs:
  - "**/*.py"
basis: operational-experience
spoke: operations
paths:
  - "**/*.py"
applyTo: "**/*.py"
---

> Governance narrative: [operations spoke](../../operations/README.md). Tracing and telemetry: `observability.md`.
> Registries and lineage: `lineage.md`.

# Operational Rules — LLM-Calling Modules

## Non-Negotiable Baseline

- **Bounded execution**: timeouts and a token/cost budget for every LLM call. No unbounded loops.
- **Structured observability**: every call emits a correlation ID (`run_id`), latency, and token counts into structured telemetry.
- **Defined evaluation path**: an evaluation harness exists or is explicitly planned; quality is proven, not assumed.
- **Degrade mode**: failures/timeouts return a structured error, not silent empties.

## Execution Bounds (Required)

- Every workflow execution must be bounded by explicit limits: max wall-clock, max LLM calls, max tool calls, max retries, max retrieval attempts, and max output tokens per call.
- Every retry policy must be bounded and must declare a deterministic give-up condition; infinite retry loops are prohibited.
- Every agentic/tool loop must have a deterministic stop condition; reaching any bound must trigger a named degrade mode and a structured, non-empty response.
- Every externally invocable surface must enforce deterministic input caps (bytes/chars/array sizes) before calling tools or models.

## Human Checkpoint and Kill Switches

- A tool rated `risk_tier: high` in its registry (`lineage.md`) runs only after a human approves that call;
  the stop is enforced in the runtime, not requested in the prompt. **Consequence:** an irreversible or
  outbound action taken on an injected or mistaken instruction cannot be undone afterwards.
  *Source: GenAI research record (OpenAI practical guide to building agents); basis: research-derived.*
- The control plane must support kill-switches scoped at least to: per-run and per-workflow; kill-switch activation must be recorded as evidence.

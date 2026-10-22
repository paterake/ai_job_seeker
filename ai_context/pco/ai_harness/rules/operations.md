---
description: LLMOps runtime bounds — budgets, bounded loops and retries, input caps, degrade modes, kill switches. Loaded when editing Python, because model-calling modules carry no naming pattern.
basis: operational-experience
spoke: operations
paths:
  - "**/*.py"
---

> Governance narrative: [operations spoke](../../operations/README.md). Tracing and telemetry: `observability.md`.
> Registries and lineage: `lineage.md`.

# Operational Rules — LLM-Calling Modules

## Non-Negotiable Baseline

- **Bounded execution**: timeouts and a token/cost budget for every LLM call. No unbounded loops.
- **Structured observability**: per `observability.md` → Telemetry Event Contract.
- **Defined evaluation path**: an evaluation harness exists or is explicitly planned; quality is proven, not assumed (`assurance.md` → Error Analysis Before Gates).
- **Degrade mode**: failures/timeouts return a structured error, not silent empties.
- **Consequence:** an LLM-calling module missing any of these has unbounded cost, unattributable failures,
  unproven quality, or empty results read as valid answers.

## Execution Bounds (Required)

- Every workflow execution must be bounded by explicit limits: max wall-clock, max LLM calls, max tool calls, max retries, max retrieval attempts, and max output tokens per call.
- Every retry policy must be bounded and must declare a deterministic give-up condition; infinite retry loops are prohibited.
- Every agentic/tool loop must have a deterministic stop condition; reaching any bound must trigger a named degrade mode and a structured, non-empty response.
- Every externally invocable surface must enforce deterministic input caps (bytes/chars/array sizes) before calling tools or models.
- **Consequence:** one unbounded loop, retry or input turns a single fault into unbounded cost and a hung workflow,
  and a silent empty result is read as a valid answer.

## Human Checkpoint and Kill Switches

- A tool rated `risk_tier: high` in its registry (`lineage.md`) runs only after a human approves that call;
  the stop is enforced in the runtime, not requested in the prompt. **Consequence:** an irreversible or
  outbound action taken on an injected or mistaken instruction cannot be undone afterwards. Which content is
  untrusted and how to scope tools per task: `security-threat-model.md` → Required Controls §1-2.
- Kill switches scoped at least to per-run and per-workflow are required, and each activation must be recorded as
  evidence. Their intended host is the control plane ([HUB.md](../../governance/HUB.md) → Not enforced).
  **Consequence:** without a scoped stop, a misbehaving run can only be halted by killing everything around it,
  and an unrecorded activation leaves no evidence of why the run ended.

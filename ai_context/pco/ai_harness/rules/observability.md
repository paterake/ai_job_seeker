---
description: Tracing and privacy-safe telemetry for LLM-calling modules — run_id propagation, span hygiene, telemetry event contract, post-run review. Loaded when editing Python, because model-calling modules carry no naming pattern.
basis: operational-experience
spoke: observability
paths:
  - "**/*.py"
---

> Governance narrative: [observability spoke](../../observability/README.md)

# Observability Rules — LLM-Calling Modules

## Tracing Invariant

- `run_id` is propagated through every call chain; never generated mid-run.
- If spans are used, they must close in a `finally` block.
- Telemetry writes to a structured sink; avoid stdout in production paths.
- Tracing instrumentation must never attach raw text to span attributes; only identifiers, counts, and operational state.
- Workflows that perform multi-stage retrieval and synthesis must be traceable end-to-end (request → stages → tool calls → model calls).

## Telemetry Event Contract (Privacy-Safe by Default)

- Every LLM call must emit a structured telemetry event including: `run_id`, model identifier, input/output sizes, latency, and token counts when available.
- Every tool call must emit a structured telemetry event including: `run_id`, tool identifier (and schema version), input/output sizes, latency, and error/degrade fields when applicable.
- Input/output hashes are added to both events where the solution is High/Critical risk or declares an audit or
  replay need.
- Default operational logs and telemetry must not contain raw prompts, raw tool payloads, or raw retrieved content; only hashes, sizes, identifiers, and controlled metadata are permitted by default.

## Run Review

- Best-effort artefact writes must never fail silently; on write failure, emit a warning event visible in operational telemetry.
- A post-run review artefact must summarise: budget usage, anomalies, errors by type, degrade modes used, and whether verification completed.

---
description: LLMOps and operational discipline rules. Loaded when editing modules that call LLMs, use embeddings, or implement budgets/tracing/telemetry.
globs:
  - "**/*.py"
  - "**/*.yaml"
  - "**/*.yml"
basis: operational-experience
---

> Governance narrative: [operations spoke](../../operations/README.md)

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

## Tracing Invariant

- `run_id` is propagated through every call chain; never generated mid-run.
- If spans are used, they must close in a `finally` block.
- Telemetry writes to a structured sink; avoid stdout in production paths.
- Tracing instrumentation must never attach raw text to span attributes; only identifiers, counts, and operational state.
- Workflows that perform multi-stage retrieval and synthesis must be traceable end-to-end (request → stages → tool calls → model calls).

## Registries and Lineage

- Every tool must have a stable identifier, an owned schema, and a version. Unregistered tools are prohibited in governed execution.
- Every model endpoint must have a stable identifier and an allowlist entry; runs must record the model identifier used.
- Tools, workflows, and policy packs must use semantic versioning. Breaking changes must ship with a migration note and a compatibility window; changes without an upgrade path are prohibited for shared surfaces.
- Downstream repos must pin platform dependencies explicitly; "floating latest" is prohibited for governed execution surfaces.
- Every run must produce a lineage manifest recording: `run_id`, timestamps, project/workflow identity and versions, role/agent identity, tool versions, model identifier, policy versions, input/output fingerprints, and verification outcomes. Anonymous execution is prohibited.
- Any approval, exception, or elevation used by a run must be bound to the run identity and referenced by stable identifier in the lineage manifest.
- Evidence packages are append-only once a run is closed; rewriting or backfilling evidence after closure is prohibited.
- Best-effort artefact writes must never fail silently; on write failure, emit a warning event visible in operational telemetry.
- A post-run review artefact must summarise: budget usage, anomalies, errors by type, degrade modes used, and whether verification completed.
- The control plane must support kill-switches scoped at least to: per-run and per-workflow; kill-switch activation must be recorded as evidence.
- Assumptions used to proceed in the face of missing inputs must be recorded as evidence and linked to `run_id`.

## Telemetry Event Contract (Privacy-Safe by Default)

- Every LLM call must emit a structured telemetry event including: `run_id`, model identifier, input/output sizes, input/output hashes, latency, and token counts when available.
- Every tool call must emit a structured telemetry event including: `run_id`, tool identifier (and schema version), input/output sizes, input/output hashes, latency, and error/degrade fields when applicable.
- Default operational logs and telemetry must not contain raw prompts, raw tool payloads, or raw retrieved content; only hashes, sizes, identifiers, and controlled metadata are permitted by default.

## Regulatory Notification & FinOps

- **Regulatory notification.** The Incident Capture rule (`assurance.md`) is extended: an incident
  that crosses an external-notification threshold must record who notifies which authority, by when
  (the applicable statutory clock), and the notification sent — as run evidence. **Consequence:**
  internal incident capture with no notification trigger silently misses a statutory clock; the
  breach is contained technically but unreported legally.
- **FinOps chargeback & budget authority.** Beyond per-run cost, each solution/pod declares budget
  ownership, chargeback attribution, and a cost-dispute path. **Consequence:** cost with no named
  owner is cost nobody controls; federated spend fragments and no one is accountable for the total.

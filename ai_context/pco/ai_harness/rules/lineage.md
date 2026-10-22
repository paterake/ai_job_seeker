---
description: Registries, versioning and lineage for LLM-calling modules — tool and model identity, per-tool risk rating, version pinning, lineage manifest, append-only evidence. Loaded when editing Python, because model-calling modules carry no naming pattern.
basis: operational-experience
spoke: lineage
paths:
  - "**/*.py"
---

> Governance narrative: [lineage spoke](../../lineage/README.md). Registry data: [master-data spoke](../../master-data/README.md).

# Registries and Lineage — LLM-Calling Modules

## Registries and Versioning

- Every tool must have a stable identifier, an owned schema, and a version. Unregistered tools are prohibited in governed execution.
- Every tool carries `risk_tier` (`low`/`medium`/`high`), a rating of the tool's actions, distinct from a
  solution's risk tier. High is any irreversible, destructive, outbound or financial action; a high tool sets
  `requires_approval: true` and runs behind the human checkpoint in
  `operations.md`.
- Every model endpoint must have a stable identifier and an allowlist entry; runs must record the model identifier used.
- Tools, workflows, and policy packs shared across repos or teams use semantic versioning; breaking changes
  ship with a migration note and a compatibility window. A surface used in one repo needs only a stable version
  identifier.
- Downstream repos must pin platform dependencies and model snapshots explicitly; "floating latest" is prohibited for governed execution surfaces.
- **Consequence:** an unregistered tool or unpinned model cannot be traced from a run back to what executed, so a
  regression or incident cannot be attributed or reproduced; an unannounced breaking change fails every consumer
  at once.

## Lineage and Evidence

- Every run must produce a lineage manifest recording: `run_id`, timestamps, project/workflow identity and versions, role/agent identity, tool versions, model identifier, policy versions, and verification outcomes. Anonymous execution is prohibited. Input/output fingerprints are added under the same condition as the telemetry hashes (`observability.md`).
- Any approval, exception, or elevation used by a run must be bound to the run identity and referenced by stable identifier in the lineage manifest.
- Evidence packages are append-only once a run is closed; rewriting or backfilling evidence after closure is prohibited.
- These lineage and evidence obligations apply to runs of LLM-calling modules. Coding-agent sessions are evidenced by git commits, capability-decision records and anchor docs, not run records. **Consequence:** a per-session record duplicates git and goes unwritten, so a requirement nobody meets teaches that the rules are optional.
- Assumptions used to proceed in the face of missing inputs must be recorded as evidence and linked to `run_id`.

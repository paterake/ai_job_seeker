# Operations (Spoke)
> DAMA mapping: Data Storage & Operations → Agent Runtime & Operations

## Purpose

Operate the agent harness like production infrastructure: reliable, reproducible, recoverable, and controllable, even if the platform runs locally.

## PCO Emphasis

- Policy: defines run lifecycle policy, SLOs, and escalation rules
- Control plane: executes workflow routing, isolation, retries, and kill-switches
- Observability: captures operational telemetry and incident evidence

## Scope (what this spoke governs)

### Run lifecycle

- Admission → plan → execute → verify → record evidence → close
- Replayability (can the run be reproduced from recorded inputs)
- Deterministic handling of retries and partial failures

### Isolation and environments

- Separation of environments (dev/sandbox/prod-like constraints)
- Concurrency controls (rate limiting, queueing)
- State handling (run state, checkpoints, output artefacts)

### Reliability and incident response

- Failure classification (blocking vs retriable)
- Incident severity levels and runbooks
- Rollback and containment (kill-switches)

## Governance Controls (hub decisions)

### Reliability targets

Governance defines service expectations, such as:
- SLOs by workflow class (throughput, success rate, verification completion)
- Maximum retries, maximum loop iterations, and timeouts

### Operational risk tiers

Governance defines operational constraints per tier:
- Which tools are allowed
- Whether network egress is permitted
- Whether approvals are used for stateful or destructive actions

### Evidence completeness policy

Governance defines what a "complete run" includes:
- Logs/events
- Artefacts (trajectories, outputs, verification results)
- Retention requirements and redaction rules

## Artefacts and Surfaces (examples)

- Run lifecycle definition and state model
- Standard run metadata schema (project, workflow, policy versions, tool versions)
- Retry and idempotency policy for each workflow/tool
- Incident runbooks and containment steps
- SLO definitions and operational dashboards

## Canonical Operational Anchors

- Runtime execution invariants (run identity propagation, bounded budgets/retries/loops, input caps, telemetry/tracing posture, evidence artefacts, kill-switches): [operations.md](../ai_harness/rules/operations.md)
- Identity and entitlements surfaces referenced by runtime rules: [master-data/README.md](../master-data/README.md)
- Governance contract surfaces referenced by runtime rules: [CONTRACT.md](../governance/CONTRACT.md)

## Enforcement Rules

Canonical enforcement: [operations.md](../ai_harness/rules/operations.md)

Covers: bounded execution (timeouts, token/cost budgets), structured observability (run_id, latency, token counts), defined evaluation path, degrade mode on failure, run_id propagation through every call chain, spans closing in finally blocks, telemetry to structured sink, lineage manifest requirements, append-only evidence, kill-switch scoping, and post-run review artefact.

Regulatory notification: an incident crossing an external-notification threshold records who notifies
which authority, by when (the applicable statutory clock), and the notification sent — as run evidence,
extending the Incident Capture rule in [assurance.md](../ai_harness/rules/assurance.md).

## Enforcement Points (where the control plane enforces)

Canonical enforcement anchors: [operations.md](../ai_harness/rules/operations.md) and [CONTRACT.md](../governance/CONTRACT.md).

## Evidence and Metrics (what observability measures)

- Success rate by workflow and risk tier
- Verification completion rate (runs closed without full verification)
- Mean time to recovery and rerun rate
- Failure modes by phase (admission/execution/verification/evidence)
- Kill-switch activations and containment time

## Common Failure Modes

- Non-reproducible runs due to undeclared state and missing metadata
- Infinite loops or runaway retries creating cost blow-ups
- "Green" runs that skipped verification and only appear successful
- Evidence gaps: cannot answer what happened during an incident

## Maturity Model (pragmatic)

### Level 1: Controlled runs

- Standard workflow routing exists
- Basic timeouts and bounded retries exist
- Minimum evidence exists per run

### Level 2: Reliable operations

- SLOs exist and are measured
- Incidents have runbooks and are routinely closed with evidence
- Verification is mandatory before run completion

### Level 3: Resilient and efficient

- The harness adapts routing based on risk and cost signals
- Failures are predicted and prevented via trend detection
- Replayability and forensics are routine, not exceptional

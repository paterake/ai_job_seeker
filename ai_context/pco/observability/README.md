# Observability, Analytics & FinOps (Spoke)
> DAMA mapping: Data Warehousing & Business Intelligence → Observability, Analytics & FinOps

## Purpose

Make the harness measurable: quality, safety, cost, throughput, drift, and outcomes, so governance decisions are evidence-based rather than opinion-based.

## PCO Emphasis

- Policy: defines what "good" looks like (KPIs, thresholds, budgets) and how to act on signals
- Control plane: emits structured telemetry and enforces quotas and routing rules
- Observability: aggregates signals into dashboards, alerts, and improvement loops

## Scope (what this spoke governs)

### Observability

- Structured logs, traces, metrics for every workflow phase
- Tool-level telemetry (latency, errors, retries, denials)
- Evidence completeness telemetry

### Analytics

- Cross-run analysis: quality trends, failure trends, drift detection
- Cross-project analysis: adoption, exception concentration, risk exposure
- Incident analytics: recurrence, root cause patterns
- Unsupervised topic clustering on production traces to surface unknown-unknown failure modes

### FinOps

- Cost accounting by project/workflow/tool/model
- Budget controls (quotas, caps, rate limits)
- Cost-quality trade-off analysis and routing optimisation

## Governance Controls (hub decisions)

### Event taxonomy and minimum telemetry

Governance defines:
- Canonical event types and phases
- Mandatory fields for traceability (project, workflow, policy versions, tool versions)
- Severity levels and alerting thresholds

### Budgets and quotas

Governance defines:
- Budget envelopes by project and by workflow
- Limits on retries and loop iterations
- What happens when a budget is exceeded (block, degrade, require approval)

### Actioning signals

Governance defines decision rules:
- What signals trigger containment (kill-switch, approvals)
- What signals trigger improvement work (new evals, tool hardening, policy updates)

### Unknown-unknown anomaly detection (unsupervised clustering)

Governance defines a mechanism to surface emergent failure categories that no predefined rule or sensor would flag.

- Cluster production traces by semantic similarity and behavioural signatures
- Review top clusters on a named cadence; treat "new cluster emergence" as a governance signal
- Convert confirmed failure clusters into offline eval examples and regression suites
- Track cluster volume and trend as a leading indicator of drift and governance gaps

## Artefacts and Surfaces (examples)

- Event taxonomy and logging schema
- Dashboards for: quality, safety, cost, throughput, drift, exceptions
- Alert rules and incident response integration
- Cost model: attribution rules for each workflow/tool/model
- Quota and rate-limit policy by risk tier

## Enforcement Rules

Canonical enforcement: [operations.md](../ai_harness/rules/operations.md)

Covers: structured telemetry event contract (run_id, model identifier, input/output sizes/hashes, latency, token counts), tool call telemetry, privacy-safe defaults (no raw prompts/payloads/retrieved content in logs), and tracing invariants.

FinOps accountability: beyond per-run cost, each solution/pod declares budget ownership, chargeback
attribution, and a cost-dispute path — cost with no named owner is cost nobody controls
([operations.md](../ai_harness/rules/operations.md)).

## Enforcement Points (where the control plane enforces)

### Pre-run

- Budget checks and quota enforcement
- Selection of routing rules based on risk and cost constraints

### In-run

- Structured telemetry emitted for every phase and tool call
- Rate limiting and bounded retries enforced
- Budget-aware routing decisions applied (where allowed)

### Post-run

- Evidence completeness and verification outcomes recorded
- Cost reconciliation and anomaly detection performed

## Evidence and Metrics (what observability measures)

- Cost per successful run (and cost per verified outcome)
- Cost per defect prevented (proxy via review/eval catches)
- Rerun rate and cost of reruns
- Trend of quality scores vs cost (frontier curves)
- Drift indicators: sudden changes in tool usage, failures, or exceptions

## Common Failure Modes

- Measuring tokens/cost without tying to outcomes or verification
- Silent runaway loops causing cost spikes
- Telemetry that is too unstructured to support audit or trend analysis
- Optimising cost by weakening safety and quality gates

## Maturity Model (pragmatic)

### Level 1: Visible

- Minimum telemetry and dashboards exist
- Costs are attributable at least by workflow and project

### Level 2: Governed

- Budgets and rate limits are enforced
- Alerts trigger predictable containment and investigation paths
- Trend analysis drives targeted improvements

### Level 3: Optimised

- Routing decisions use risk and cost signals without weakening policy
- Continuous improvement demonstrably improves the cost-quality frontier
- Drift detection reduces incidents and exceptions over time

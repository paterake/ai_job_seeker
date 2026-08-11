# Registries, Versioning & Lineage (Spoke)
> DAMA mapping: Metadata Management → Registries, Versioning & Lineage

## Purpose

Provide traceability for every decision and action: who/what/when/why, with versioned artefacts and reproducible lineage.

## PCO Emphasis

- Policy: defines what is registered/versioned and what evidence is collected
- Control plane: enforces version negotiation, pins policy/tool/model versions, and records run context
- Observability: exposes lineage queries, audit trails, and drift detection over time

## Scope (what this spoke governs)

### Registries (canonical catalogues)

- Policy registry (pillars, security policy, workflow policy)
- Tool registry (schemas, versions, risk ratings)
- Model registry (allowed endpoints/configurations and safety posture)
- Agent/role registry (behaviour contracts and entitlements)
- Workflow registry (approved workflow types and versions)
- Source registry (external research sources → trust tier → owner → review cadence → claim summaries)

### Versioning rules

- Semantic versioning of policies and workflows where applicable
- Compatibility windows and deprecation timelines
- Pinning and negotiation for projects consuming the platform

### Lineage model

- Run identity: project, workflow, role, model, policy versions
- Inputs and sources: what data and content was used, with provenance
- Decisions and approvals: why the run was allowed, by what rule
- Actions and outputs: tool calls, changes made, verification results

## Governance Controls (hub decisions)

### What is registered

Governance defines the minimum set of registered objects and the non-compliance posture for "anonymous" tools, policies, or workflows.

### Evidence requirements by risk tier

Governance defines what lineage is captured per tier, including:
- Whether full trajectories are captured
- Whether approvals are linked to runs
- Whether outputs require additional attestation or review

### Compatibility and rollout rules

Governance defines:
- How projects pin minimum versions
- How breaking policy changes roll out
- How migrations are executed and verified

## Artefacts and Surfaces (examples)

- Registries for tools, policies, models, roles, and workflows
- A source registry for external research relied upon by governance decisions (trust tier, owner, review cadence, and claim summaries)
- Versioning and deprecation policy (including compatibility windows)
- Lineage schema for runs (fields, retention, access control)
- Query surfaces (how audit/forensics is performed)

## Enforcement Rules

Canonical enforcement:
- Tool/model/policy/workflow identity, semantic versioning, lineage/evidence invariants: [operations.md](../ai_harness/rules/operations.md)
- Assurance artefact provenance requirements: [assurance.md](../ai_harness/rules/assurance.md)
- Research citation requirements for governance changes: [agent-behavior.md](../ai_harness/rules/agent-behavior.md) and [CONTRACT.md](../governance/CONTRACT.md)

## Enforcement Points (where the control plane enforces)

Canonical enforcement anchors: [operations.md](../ai_harness/rules/operations.md) and [CONTRACT.md](../governance/CONTRACT.md).

## Evidence and Metrics (what observability measures)

- % runs with complete lineage captured
- Time to answer governance questions ("why did it do that?")
- Deprecated version usage rate and compliance with migration timelines
- Unregistered invocation attempts
- Incidents attributable to version drift or missing evidence

## Common Failure Modes

- Implicit versions: cannot reproduce behaviour because versions were not recorded
- Registry drift: tools/policies exist without ownership or lifecycle
- "He said / she said" post-mortems due to missing lineage
- Breaking changes shipped without compatibility and migration

## Maturity Model (pragmatic)

### Level 1: Registered and queryable

- Core registries exist and are used
- Runs record basic lineage (workflow, policy versions, tool versions)

### Level 2: Version-governed

- Deprecation and migration are real and enforced
- Projects pin and negotiate versions deliberately
- Evidence completeness is validated

### Level 3: Forensics-grade

- Full lineage supports reliable audits and reproductions
- Drift is detected early and corrected via controlled rollouts
- Governance decisions are demonstrably evidence-based

# Identity, Policy & Configuration Master Data (Spoke)
> DAMA mapping: Reference & Master Data → Identity, Policy & Configuration Master Data

## Purpose

Provide canonical identifiers, configurations, and entitlements so governance can be enforced consistently across projects without per-project reinvention.

## PCO Emphasis

- Policy: defines what master data exists and what is authoritative
- Control plane: enforces registration, entitlements, and version negotiation
- Observability: records lineage and drift across projects and time

## Scope (what this spoke governs)

### Canonical identities

- Projects, environments, workflows, roles, agents, models, tools, policies
- Ownership and accountability for each identity class

### Canonical entitlements

- Role × tool × environment × risk tier permissions
- Time-bounded elevations and exception grants

### Configuration baselines

- Defaults and mandatory constraints per environment and risk tier
- Version pinning and compatibility

## Canonical Registries (Master-Data Artefacts)

This spoke is substantiated by the first governance registries:
- Capability lifecycle registry: [capability_registry.yaml](../governance/capability_registry.yaml)
- Exception registry: [exception_registry.yaml](../governance/exception_registry.yaml)
- Tool + MCP inventory registry: [tool_registry.yaml](tool_registry.yaml)
- Model registry: [model_registry.yaml](model_registry.yaml)
- Policy pack registry: [policy_pack_registry.yaml](../governance/policy_pack_registry.yaml)

## Canonical Identity Classes

The platform defines stable identifiers (and registry entries) for:
- project
- environment
- workflow
- role
- agent
- tool
- model
- policy pack

Each identity class has an explicit owner and lifecycle policy (creation, modification, deprecation). Registry formats and enforcement live in `ai_agent_core`; this spoke is the canonical policy anchor.

## Entitlements (Policy Anchor)

Tool usage is governed by an explicit entitlement model: role × tool × environment × risk tier.

Elevations and exceptions are time-bounded, attributable (owner + justification), and recorded in run lineage when used.

Role must be assigned and entitled for the requested workflow and risk tier.

Default entitlement posture is deny-by-default for side-effecting tools and any tool with network egress.

## Workflow Declarations (Policy Anchor)

Workflow registry entries must declare required output schema identifiers per workflow version. Executions must select an output schema and record the selected schema identifier/version in run evidence.

## Environment Baselines (Policy Anchor)

Environment baselines must be explicit; "prod-like" constraints cannot be inferred implicitly from naming. Baselines are represented as registry/config entries with an owner and lifecycle policy.

## Governance Controls (hub decisions)

### Registration as the only onboarding path

Governance defines:
- What it means for a project to be "registered"
- What minimum metadata and policy binding is expected
- How registration changes are approved and audited

### Policy segmentation

Governance defines the policy segmentation model:
- Core policy (non-negotiable)
- Optional policy (explicit opt-in)
- Project-additive policy (allowed only if it strengthens constraints)

### Version negotiation

Governance defines:
- How platform versions are negotiated/pinned
- How breaking changes are rolled out
- What compatibility guarantees exist and how long they last

## Artefacts and Surfaces (examples)

- Project registry (project IDs, owners, bindings, opt-ins)
- Policy catalogue (IDs, versions, scope, enforcement semantics)
- Entitlement catalogue (role/tool/environment/risk tier)
- Environment configuration baselines (defaults + mandatory constraints)
- Exception register (owner, scope, expiry, justification, evidence)

## Enforcement Rules

Canonical enforcement:
- Run identity recording, anonymous execution posture: [operations.md](../ai_harness/rules/operations.md)
- Configuration non-compliance posture, additive-only strengthening: [CONTRACT.md](../governance/CONTRACT.md) and [governance.md](../ai_harness/rules/governance.md)

## Enforcement Points (where the control plane enforces)

Canonical enforcement anchors: [operations.md](../ai_harness/rules/operations.md) and [CONTRACT.md](../governance/CONTRACT.md).

## Evidence and Metrics (what observability measures)

- % projects registered and policy-bound
- % projects on compliant platform versions
- Policy override attempts (core overrides)
- Exception volume, expiry compliance, and repeat exceptions
- Entitlement denials and elevation frequency by tool/risk tier

## Common Failure Modes

- Identity sprawl: multiple names for the same thing across projects
- Permanent "temporary" exceptions that silently become policy
- Weak version discipline leading to irreproducible outcomes
- Entitlements stored informally rather than enforced structurally

## Maturity Model (pragmatic)

### Level 1: Canonical registries exist

- Projects and policies have canonical IDs and owners
- Entitlements exist for critical tools
- Version pinning exists for core workflows

### Level 2: Governed change and exceptions

- Exceptions are time-bounded and auditable
- Version negotiation supports controlled rollouts and migrations
- Entitlements are least-privilege and reviewed

### Level 3: Scalable governance

- Master data supports cross-project analytics and audit queries
- Policy and entitlements evolve safely with regression protection
- Drift is measurable and actively reduced over time

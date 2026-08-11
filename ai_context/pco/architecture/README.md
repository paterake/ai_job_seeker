# Architecture (Spoke)
> DAMA mapping: Data Architecture → Agent Architecture

## Purpose

Define the reference architectures, boundaries, and approved patterns that make agent behaviour composable, reviewable, and enforceable across projects.

## PCO Emphasis

- Policy: defines architecture standards and allowed patterns
- Control plane: enforces workflow routing, boundaries, and tool access
- Observability: provides evidence of adherence and drift

## Scope (what this spoke governs)

### Architecture boundaries

- Control plane vs execution plane separation
- Where policy lives (central), and where execution occurs (project scope)
- What a "workflow" is and how it may be composed

### Workflow taxonomy (named patterns)

Canonical approved pattern list and the "unapproved variant requires review" governance rule: [PCO_CONTRACT.md](../../../docs/concept/PCO_CONTRACT.md) §7 "Approved Workflow Patterns".

Pattern selection guidance (architecture-specific; not in the contract):

| Pattern | When to use |
|---|---|
| **Prompt chaining** | When steps can be pre-specified and controlled |
| **Routing** | When inputs vary but the set of workflows is fixed |
| **Parallelisation** | When sub-problems are separable and merge logic is clear |
| **Orchestrator–workers** | When decomposition is clear but workload is variable |
| **Evaluator–optimizer** | When quality is improved iteratively with bounded loops |

### "When not to use agents" decision gate

Canonical anchors: [agent-behavior.md](../ai_harness/rules/agent-behavior.md) (pre-implementation gate) and [CONTRACT.md](../governance/CONTRACT.md) (conformance boundaries).

### Reference patterns (approved building blocks)

- Planner/executor separation
- Multi-agent review loops (independence preserved)
- Tool-broker pattern (central tool registry + entitlements)
- Retrieval boundary (approved sources only; provenance maintained)
- Evidence boundary (every run produces a verifiable artefact set)

### Harness runtime context engineering patterns

These are runtime engineering mechanisms, distinct from session-level context minimisation rules.

- **Compaction**: summarise and offload context when approaching capacity limits, preserving decision-relevant facts and citations
- **Tool output offloading**: move large tool outputs to durable artefacts (filesystem/object store) and keep only minimal references in context
- **Progressive disclosure**: load tools/skills on demand rather than all at startup to reduce tool overload and accidental misuse

### Anti-patterns (examples)

Canonical anchors: [CONTRACT.md](../governance/CONTRACT.md) and [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)

- Agents directly calling each other outside orchestration
- Projects bypassing the harness to invoke agents/tools
- "Hidden policy" embedded in local prompts or ad-hoc scripts
- Architecture defined by chat history instead of versioned artefacts

## Governance Controls (hub decisions)

### Approved workflow catalogue

Governance defines a small set of approved workflow archetypes and their mandatory gates.

Examples of archetypes (illustrative):
- Debate (spec agreement) → Build (implementation) → Review (pillar + PRD compliance)
- Low-risk fast lane with reduced tool permissions and stronger output constraints
- High-risk lane requiring explicit approval and expanded eval coverage

### Architectural pillars (structural law)

Governance defines which architectural rules are non-negotiable (core pillars) vs opt-in (optional pillars) vs project-additive (local constraints that cannot weaken platform policy).

### Role catalogue

Governance defines:
- Roles (architect/reviewer/builder/etc.)
- Responsibilities and expected outputs per role
- Independence requirements (e.g., adversarial review cannot share synthesis context)

### Topology commitment (harness completeness prerequisite)

Harness completeness requires bounding the design space.

- Workflows are deployed into named service topologies (e.g., batch job, event processor, CRUD service, interactive CLI, data dashboard)
- Each topology has a harness template: pre-configured guide + sensor bundle designed for that topology
- A project commits to a topology as part of admission control; topology drift requires architecture review

### Poka-yoke tool design (mistakes impossible by construction)

When a tool interface can make a class of mistakes impossible, governance prefers interface design over documentation.

- Tool schemas encode validated fields and safe defaults
- Idempotency keys and dry-run options exist for high-impact tools
- Tool brokers enforce entitlements and block unsafe combinations, rather than relying on "remember not to do X"

## Artefacts and Surfaces (examples)

- Reference architecture (logical diagrams + text) for the harness
- Role catalogue (role → responsibilities → outputs → entitlements)
- Workflow catalogue (workflow → phases → gates → evidence requirements)
- Boundary definitions (what projects may and may not do)
- Exception policy for architecture deviations (time-bounded)

### Harness component taxonomy (what a harness contains)

- System policy prompts (core + optional + project-additive)
- Tool/skill/MCP catalogue (descriptions, schemas, versions, risk ratings)
- Bundled infrastructure (filesystem, sandbox, browser, secrets broker)
- Orchestration logic (routing, delegation, handoffs, model selection)
- Hooks/middleware for deterministic enforcement (pre/post checks, evidence capture)

## Enforcement Rules

Canonical enforcement:
- Pre-implementation gate, anti-patterns, and "when not to use agents": [agent-behavior.md](../ai_harness/rules/agent-behavior.md)
- Conformance boundaries, approved workflow catalogue, anti-patterns: [CONTRACT.md](../governance/CONTRACT.md)
- Edit-tool contract, approval gates, hooks vs guidance: [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)

## Enforcement Points (where the control plane enforces)

### Pre-run (admission control)

- Workflow type recognition and approval
- Project registration, version compatibility, and policy binding
- Tool entitlements checked for role and risk tier

### In-run (control-plane enforcement)

- Workflow steps executed only through the orchestrator
- Tool invocations mediated by the tool registry/broker
- Retrieval bounded to approved sources and policies

### Post-run (evidence and closure)

- Evidence package completeness checks
- Policy and version attribution recorded (what rules were applied)
- Drift signals emitted (non-standard paths attempted)

## Evidence and Metrics (what observability measures)

- Workflow conformity rate (% runs using approved workflow types)
- Policy bypass attempts
- Architecture drift rate (new patterns appearing without review)
- Exception volume and expiry compliance (% exceptions expired vs renewed vs removed)
- Reproducibility rate (can a run be replayed from evidence)

## Common Failure Modes

- Spaghetti orchestration: agents invoke each other ad-hoc, making auditing impossible
- Local optimisation: projects introduce "helpful" shortcuts that bypass governance
- Pattern proliferation: too many workflow variants to govern effectively
- Over-coupling: architecture assumes a specific vendor/agent/tool format

## Maturity Model (pragmatic)

### Level 1: Standardised

- A single reference workflow exists
- Roles and boundaries are explicit
- Basic admission control prevents bypass

### Level 2: Governed

- Multiple workflow archetypes exist with risk-based gating
- Exceptions are tracked with expiry and evidence
- Architecture drift is measurable and actively reduced

### Level 3: Adaptive

- Architecture supports safe substitution (models/agents/tools) without policy changes
- Policy changes roll out via version negotiation with regression protection
- Continuous improvement loop reduces cost and increases safety without degrading throughput

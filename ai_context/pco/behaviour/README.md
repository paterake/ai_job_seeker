# Behaviour Design (Spoke)
> DAMA mapping: Data Modelling & Design → Agent Behaviour Modelling & Design

## Purpose

Make agent behaviour specifiable, testable, and versioned, so "how the agent behaves" can be governed like an interface contract rather than folklore.

## PCO Emphasis

- Policy: defines behaviour contracts, policies, and safe defaults
- Control plane: injects/locks system policy; enforces schema contracts at runtime
- Observability: measures behaviour quality, drift, and policy compliance over time

## Scope (what this spoke governs)

### Behaviour as a contract

- Role definition (behaviour boundaries and prohibitions)
- Input/output contracts for each workflow step
- Uncertainty handling (escalation rules, safe refusal rules)

### Epistemic honesty (non-negotiable behaviour)

Agents must not present outputs as objective or infallible when they are not. When confidence is low or a request is outside reliable capability, signal uncertainty explicitly, surface ambiguity before proceeding, and return a structured low-confidence result rather than a confident wrong answer. Canonical anchor: [agent-behavior.md](../ai_harness/rules/agent-behavior.md)

### Specification ambiguity protocol

Agents must state assumptions explicitly before acting, present multiple interpretations when they exist, and stop to name what is unclear rather than filling gaps silently. Assumptions used to proceed must be recorded as evidence. Canonical anchors: [agent-behavior.md](../ai_harness/rules/agent-behavior.md) and [operations.md](../ai_harness/rules/operations.md)

### Tool contract design

- Tool schemas (types, validated fields, validation)
- Idempotency expectations (safe retries, deduplication)
- Error semantics (what is retriable vs blocking)

### Prompt and policy structure

- Separation of policy from task context
- System policy composition (core policy + optional policy + project-additive)
- Context boundaries (what retrieval is allowed and how it is attributed)

### Repo-wide engineering conventions

- Configuration drives code and Python tooling uses `uv` only: [governance.md](../ai_harness/rules/governance.md)

## Governance Controls (hub decisions)

### Role contracts

Governance defines, per role:
- Mandatory behaviours (e.g., produce artefact X, follow gate Y)
- Disallowed behaviours (e.g., bypass tool broker, expose secrets)
- Allowed tool set and risk-based escalation rules

### Autonomy spectrum behaviour rules

Canonical anchors: [governance/HUB.md](../governance/HUB.md) and [PCO_CONTRACT.md](../../../docs/concept/PCO_CONTRACT.md).

### Policy injection semantics

Core posture and security posture must be injected as non-conversational policy by the harness at session start — not as user-editable guidance. Canonical anchors: [core-posture.md](../ai_harness/rules/core-posture.md) and [CONTRACT.md](../governance/CONTRACT.md).

### Output formats and evidence requirements

Governance defines what "done" means per workflow step:
- Artefacts (PRD, feedback, trajectories, eval summaries)
- Metadata (policy versions, tool versions, model identifiers)

## Artefacts and Surfaces (planned)

- Behaviour specification per role (contract-style)
- Workflow step I/O schemas (including failure outputs)
- Tool schemas and validation rules
- Escalation playbooks (what to do when uncertain)
- Risk tiers and how they change behaviour (gating, approval, tool access)

## Enforcement Rules

Canonical enforcement:
- Pre-implementation gate, simplicity, surgical changes, verification: [agent-behavior.md](../ai_harness/rules/agent-behavior.md)
- Config drives code; no domain context in code; Python tooling uses `uv`: [governance.md](../ai_harness/rules/governance.md)
- Context minimisation, session boundaries, anchor doc pattern: [context-economy.md](../ai_harness/rules/context-economy.md)
- Guidance vs enforcement; edit-tool compatibility; approval gates: [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)

## Enforcement Points (where the control plane enforces)

### Pre-run

- Role assignment and entitlements: [master-data/README.md](../master-data/README.md)
- Output schema selection: [master-data/README.md](../master-data/README.md)
- Config purity and "no domain context in code" posture: [governance.md](../ai_harness/rules/governance.md)

### In-run

- System policy injection and locking (core cannot be overridden)
- Tool call schema validation (blocking on invalid structures)
- Context retrieval bounded and attributed (provenance enforced)

### Post-run

- Output artefact validation (schema + completeness checks)
- Behavioural evaluation runs (rubric scoring, safety checks, regressions)

### Hooks (lifecycle enforcement layer)

Guidance files (CLAUDE.md, governance docs) inform behaviour but cannot guarantee it — context saturation and instruction drift weaken prose rules over long sessions. Hooks execute at harness lifecycle points and are not subject to model behaviour.

Hard constraints — blocking destructive commands, enforcing typecheck/lint/tests after edits, requiring approvals before commits — are expressed as hooks in `settings.json` rather than prose guidance. See [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) for the enforcement anchor.

### Session Design and Token Economy

Canonical rules and enforcement model: [context-economy.md](../ai_harness/rules/context-economy.md).

## Evidence and Metrics (what observability measures)

- Schema contract violations (tool calls, outputs)
- Behaviour drift signals (changes in refusal/escalation rates)
- Uncertainty hygiene: escalation vs overconfident action in high-risk contexts
- Output quality scores from eval suites (trend, variance, regressions)
- Policy override attempts (core policy)

## Common Failure Modes

- Behaviour lives in chat history rather than versioned artefacts
- "Soft policy" that the agent can ignore under pressure
- Tool contracts are vague; downstream failures become hard to attribute
- Over-prescription: behaviour spec becomes so rigid it blocks legitimate work
- Hard constraints written as prose guidance rather than enforced by hooks — they erode as context fills
- Multi-task sessions rather than one session per task — context accumulates, earlier governance rules lose weight, and constraints erode without any visible signal
- Agent failures treated as one-off incidents rather than harvested into permanent rules (see Failure Harvest in [agent-behavior.md](../ai_harness/rules/agent-behavior.md))

## Maturity Model (pragmatic)

### Level 1: Contracted

- Role definitions exist
- Tool schemas exist for critical tools
- Outputs have minimum structure

### Level 2: Tested

- Behaviour is evaluated offline with regression gates
- High-risk paths require explicit escalation/approval
- Schema validation is blocking for key interfaces

### Level 3: Adaptively governed

- Policy and behaviour changes roll out with compatibility and eval coverage
- Online monitoring detects drift and triggers controlled responses
- Contracts support substitution of models/tools without weakening governance

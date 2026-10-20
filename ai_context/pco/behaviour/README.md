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

### Capability-fit protocol

Agents must choose the driver that fits the task — `config-driven`, `data-driven`, or `AI-driven` — before introducing a new content-interpretation mechanism. The governing test is explicit answer vs inference: explicit derivation stays deterministic; semantic inference defaults to AI-driven. Parser-/extractor-shaped changes require a capability-decision artefact, and the task-boundary review sensor checks the substance of the choice. Canonical anchors: [agent-behavior.md](../ai_harness/rules/agent-behavior.md), [governance.md](../ai_harness/rules/governance.md), [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md), and [security-threat-model.md](../ai_harness/rules/security-threat-model.md)

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

Canonical anchors: [governance/HUB.md](../governance/HUB.md) and the PCO governance contract (`docs/concept/PCO_CONTRACT.md` in the PCO repo).

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
- Automated-decision safeguards (High/Critical decisions affecting individuals): how a decision is explained, contested, reviewed by a human, and how DSARs over prompt/output logs are served: [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md)
- Scope-of-validation declaration and rule evidence-basis (`basis:`) provenance; assistant-research-derived governance is advisory until validated by a non-shared-path source: [governance-provenance.md](../ai_harness/rules/governance-provenance.md)

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

Hard constraints — blocking destructive commands, enforcing typecheck/lint/tests after edits, requiring approvals before commits — should be expressed as hooks in `settings.json` rather than prose guidance. The PCO gate hooks return a PreToolUse `"deny"` inside `hookSpecificOutput` when they trip, which blocks the tool call, and exit silently otherwise so the normal permission flow applies. Their fail-open conditions are listed in [DENY_INTERFACE.md](../governance/DENY_INTERFACE.md#current-enforcement-points); notably the exception-expiry hook enforces in the PCO repo only. See [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) for the enforcement anchor.

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

## Agent Behaviour Failure Taxonomy

These are failure modes not detectable by system error sensors. They require
behavioural sensors (semantic guardrails, run review, human review at task boundary):

| Failure mode | Description | Detection approach |
|---|---|---|
| **Overeagerness** | Generates unrequested features or business logic inferred from domain terms | Semantic guardrails; scope review at task boundary |
| **Assumption filling** | Fills spec gaps autonomously without signalling; produces production problems without system error | Require explicit ambiguity surfacing; adversarial eval scenarios |
| **Brute-force fix** | Applies hacky solutions (increase memory, add annotations) rather than root-cause fixes | Static analysis sensors; code review gates |
| **False success signal** | Reports task complete despite failing tests or violated constraints | Require verification command output in completion signal |
| **Genie risk** | Exploits spec loopholes; gives what was asked for in an unexpected way | Human review at task boundary; adversarial specification tests |
| **Code quality drift** | Duplicated literals, unused parameters, improper patterns, nested conditionals | Static analysis as a required sensor type |

### Capability-Fit Review Sensor

Capability-fit failure is a behavioural class, not a syntax error. The required review question at
task boundary / code review is:

- Is this task explicit derivation or semantic inference?
- If inference is present, why is the mechanism not AI-driven?
- If the solution is AI-driven, what makes deterministic derivation insufficient or misleading?
- If the solution is deterministic, what exact explicit structure in the source makes fixed-rule recovery valid?

This sensor is specifically aimed at two mirror-image failures:
- bespoke deterministic machinery solving a semantic problem,
- or model use where exact deterministic derivation was available.

## Recurring failure class: deterministic over-build for semantic work

Record this as a recurring class, not a one-off incident:

1. Coding agents default to writing code, so a model path looks like "less implementation" and is under-selected.
2. The governance corpus historically rewarded deterministic mechanism and treated model use as foreign, so the bias was systemic rather than local.
3. Deterministic builds were once the only viable path in some environments; the failure was not re-evaluating when the capability frame changed.
4. No explicit capability-choice checkpoint existed, so model-vs-code was defaulted silently instead of reviewed.
5. Structured inputs disguised semantic tasks as parsing problems, even when the real work was inference.
6. Agents did not self-reframe reliably; the correction had to come from repeated human challenge, which means structure — not preference — must carry the fix.

Required structural response:
- add a capability-fit rule,
- treat AI-driven as a first-class peer to config-driven and data-driven,
- require a capability-decision artefact for parser-/extractor-shaped work,
- and run a task-boundary review sensor for capability-fit.

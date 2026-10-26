# Agent Governance (Hub)

## Governs

- The platform pillars every governed repo follows
- Who may change a rule, and how a change is proposed, approved and synced
- Capability tiers and the supervision (autonomy) model
- The independent review pattern
- The spokes, one per area

## Enforced

Hub-owned controls only. Every other control is stated once, in the Enforced / Not enforced sections of the spoke
that owns it ([Spokes](#spokes)); what each hook blocks and misses: [hooks/README.md](../ai_harness/hooks/README.md).
Validators run when invoked; their commands are in the PCO repo's `docs/RUNBOOK.md` → Checks.

| Control | Mechanism |
|---|---|
| Tier 3/4 approval of a PCO-owned capability | Human review: operator review of its registry entry |
| Rule, hook, skill and settings changes | Human review: operator approval (see Decision rights) |
| Independent review (whoever dispatches it sets its independence) | Human review |

## Not enforced

Target, not implemented:
- A governance board, a standing red-team function, content safety oversight and transparency reporting. The
  operator is the only approver today.
- A periodic (quarterly) rule review cadence.
- Collection of enforcement signals (deny events, injection attempts, exception volume); review is ad hoc.
- A control plane (tool broker, secret brokering, admission control).
- Assignment or checking of a workflow's autonomy level.

## Rules

- Core: [AGENTS.md](../AGENTS.md); every rule file belongs to a spoke ([ASSISTANTS.md](../ASSISTANTS.md)).

## Platform Pillars

They apply to all governed repos. What is enforced for each: the [architecture](../architecture/README.md) and
[behaviour](../behaviour/README.md) spokes.

| # | Pillar | Rule | Consequence of violation |
|---|---|---|---|
| 1 | UV only for Python | `code-architecture.md` → Python Tooling | Environments diverge; no reproducible execution path |
| 2 | Config drives code: code is mechanism, domain context is config | `code-architecture.md` → Config Purity | Domain changes need code changes; near-identical implementations proliferate per domain |
| 3 | Low-code / OSS preference | `code-architecture.md` → Low-Code / OSS Preference | Custom code reimplements tested paths and accrues maintenance |
| 4 | Short sessions with durable state | `AGENTS.md` → Sessions and memory | Earlier constraints lose weight and cost grows non-linearly; work becomes non-resumable |

## Capability-Fit Governance

Governance does not privilege deterministic mechanism by default; it asks which of three peer drivers
(config-, data- or AI-driven) fits the task. The rule and the explicit-vs-inference test:
[code-architecture.md](../ai_harness/rules/code-architecture.md) → Driver Selection. The recurring failure class it answers
and the human review step (no hook): [behaviour spoke](../behaviour/README.md) → Capability-Fit Review.

## Governance Scope (what the hub owns)

### Decision rights

- Rule, hook, skill, settings and governance-contract changes: the operator, explicitly, in that session
  ([AGENTS.md](../AGENTS.md) → Governance changes).
- `ai_context/pco/` (the core included): changed only in the PCO. A consumer does not override or contradict a
  platform rule locally (its `REPO_CONTRACT.md` included); it reports the gap upstream.
- Exceptions: time-bounded registry entries ([CONTRACT.md](CONTRACT.md) → Exceptions).

### Autonomy placement (supervision model)

| Autonomy level | Meaning |
|---|---|
| **Fully supervised** | Human approves each high-impact step before it executes ([harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) → Approval Gates) |
| **Human-in-the-loop** | Agent acts within bounds; escalates for approval on defined conditions |
| **Human-on-the-loop** | Agent executes end-to-end; humans review sampled runs and intervene on alerts |
| **Fully autonomous** | No routine human review; only for narrow, well-characterised workflows |

Placement is a human decision, independent of security risk tier: a low-risk workflow may still need high
supervision when novelty or ambiguity is high.

### Capability-tiered governance (model/agent capability)

The tier is the `tier` field in [capability_registry.yaml](capability_registry.yaml).

| Capability tier | Typical characteristics | Control |
|---|---|---|
| **Tier 1** | Narrow scope, constrained tools, low autonomy | Human review |
| **Tier 2** | Broader toolset, works across domains | Human review |
| **Tier 3** | Strong general problem-solving, higher autonomy | Operator approval; adoption gate ([CONTRACT.md](CONTRACT.md) → Capability Lifecycle) |
| **Tier 4** | High-leverage tools, novel behaviour risk | As Tier 3 |

### Independent review pattern

When a workflow, risk tier, or change class requires independent review, the canonical pattern is fixed-role
separation:

- One agent executes/builds; a different agent judges/reviews.
- The judge/reviewer operates under the same repo contracts and behavioural rules as the executor.
- The judge/reviewer must not share the executor's synthesis context; review input is limited to
  the artefact, evidence, and explicit criteria required for review.
- Using different fixed models for executor and judge is the preferred implementation of this
  independence posture.
- Same-model self-review may be used as advisory signal only; it does not satisfy an independent
  review requirement.

## PCO Evolution Model

### What triggers a rule review

1. **Enforcement anomaly**: a rule fires on legitimate work (false positive) or misses a violation (false negative).
2. **New external research**: a credible source names a pattern or threat the rules do not cover.
3. **Downstream feedback**: a governed repo hits a rule that blocks legitimate work, or a risk the PCO misses.
4. **Sensor silence**: a rule that rarely fires is checked for whether it can detect what it claims.
5. **Capability change**: a new model class, tool access or deployment context changes the risk profile.

### Cadence and ownership

- **Accountable owner**: the operator.
- **Cadence**: reviews run on the triggers above (a periodic review: see Not enforced).

### Change process

1. **Propose**: state the change, its trigger and its source (URL + retrieval date for research). A change
   without a traceable source is not accepted. Provenance labels: [governance-provenance.md](../ai_harness/rules/governance-provenance.md).
2. **Review**: does it contradict an existing rule? Is it proportionate? A change that removes or weakens a control
   requires independent review (see Independent review pattern).
3. **Approve and record**: operator approval; the commit names the trigger and source. Breaking changes are
   marked `breaking:` in the commit.
4. **Communicate downstream**: sync to consumers (the PCO repo's sync tooling).

### Rollback procedure (governance-of-governance)

Human review; nothing triggers it automatically.
- Roll back a rule change that causes a safety regression, widespread false positives or blocked legitimate work.
- Restore the last known-good version of the changed files, sync it, and record the trigger and evidence in the
  commit.
- Forward-fix through the change process; when safety is at stake, never roll forward without the control.

### Enforcement feedback loop

The operator reviews these signals when they surface (collection: see Not enforced).

| Signal | Human action |
|---|---|
| Tool denial event | Was the denied action legitimate? False positive: loosen the rule. Correct block: keep it. |
| Sensor silence | Trigger 4 above. |
| High exception volume | The rule may be wrong; review it before escalating. |

### The AI's role in evolution

| Role | What the AI does | What the AI does not do |
|---|---|---|
| Sensor | Detects stale rules, enforcement anomalies, new research gaps | Decide whether a signal warrants a rule change |
| Proposer | Drafts the rule change with rationale and source tracing | Approve the change |
| Implementer | Writes the approved change, updates the anchor doc, syncs downstream | Determine the organisation's risk appetite |

## Capability Lifecycle

New capabilities are tracked in [capability_registry.yaml](capability_registry.yaml). Stages, progression criteria
and the registry contract: [CONTRACT.md](CONTRACT.md) → Capability Lifecycle; what is checked:
[master-data spoke](../master-data/README.md).

## `ai_agent_core` Relationship (Governed Implementation Substrate)

`ai_agent_core` is a governed repo and the shared implementation substrate that downstream repos pin as a
dependency, not vendor or modify. Because its changes reach every consumer, breaking changes need explicit
release signalling. Whether consumers use it: [architecture spoke](../architecture/README.md) → Not enforced.
Position and conformance declarations: [CONTRACT.md](CONTRACT.md) → Special Case: `ai_agent_core`.

## Harness Rule Enforcement Lifecycle (session-snapshot model)

### How rules are loaded

- The core (`ai_context/pco/AGENTS.md`) loads at session start through the repo's agent entrypoint.
  Every rule under `ai_harness/rules/` is `paths:`-scoped and loads when the agent first reads or edits a matching
  file. Docs that need an explicit read are listed in [ASSISTANTS.md](../ASSISTANTS.md).
- A rule written mid-session does not apply to the running session; it takes effect at the next session start.
- **Consequence:** an agent writing a weaker rule is not caught by the harness, only by human review. Automated
  checks cannot detect semantic contradictions between rules, so human review is the governance sensor.
- The PCO repo's sync propagates changes to consumers; they take effect at each consumer's next session start.

## Spokes

One spoke per area of the agent harness. Each spoke README opens with the area it governs, what is enforced and the named gaps. The list of spokes, with the
rules each one owns, is the spoke index: [ASSISTANTS.md](../ASSISTANTS.md).

# Agent Governance (Hub)

## Governs

- The platform pillars every governed repo follows
- Who may change a rule, and how a change is proposed, approved and synced
- Capability tiers and the supervision (autonomy) model
- The independent review pattern
- The spokes, one per DAMA knowledge area

## Enforced

| Control | Mechanism |
|---|---|
| No force push | Hook: `check_guard.sh` (`force_push_refused`) |
| No edit of `ai_context/pco/` in a consumer repo (shell writes not checked) | Hook: `check_guard.sh` (`synced_pco_edit_refused`) |
| Shell-call budget per session | Hook: `check_execution_limits.sh` (`execution_limit_hit`) |
| Expired exceptions | Validators: `exception-registry-validate`, `governed-repo-validate`, `governance-audit` |
| Tier 3/4 adoption while `experimental` without an escalation record, or `deprecated` | Validators: `capability-registry-validate --target`; `validate --scope governance\|full` ([CONTRACT.md](CONTRACT.md) → Capability Lifecycle) |
| Tier 3/4 approval of a PCO-owned capability | Human review: operator review of its registry entry |
| UV only: raw `python`/`python3` commands (pip, Poetry, Conda and venv use is not detected) | Validator: `governance-audit` (Python command scan) |
| Rule, hook, skill and settings changes | Human review: operator approval (see Decision rights) |
| Other pillars, driver choice, independent review | Human review |

Hook details: [hooks/README.md](../ai_harness/hooks/README.md). Validators run when invoked; their commands, and
what the Python command scan covers, are in the PCO repo's `docs/RUNBOOK.md` → Checks. Guidance vs enforcement:
[harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) → Hooks: Guidance vs Enforcement.

## Not enforced

Required by a rule or contract; no PCO check:
- Blocking of `rm -rf` and hard reset: required by [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)
  → Hooks: Guidance vs Enforcement (irreversible means a hook); no PCO check. Only force push is hooked.
- Reuse of the shared primitives layer (`ai_agent_core`) for LLM calls: required by
  [governance.md](../ai_harness/rules/governance.md) → AI Infrastructure Primitives; no PCO check.
- An approval record for a repo-owned Tier 3/4 capability: required by [CONTRACT.md](CONTRACT.md) → Change
  Control; no PCO check (the `governance-audit` check sees only PCO-owned entries).

Target, not implemented:
- A governance board, a standing red-team function, content safety oversight and transparency reporting. The
  operator is the only approver today.
- A periodic (quarterly) rule review cadence.
- Collection of enforcement signals (deny events, injection attempts, exception volume); review is ad hoc.
- A control plane (tool broker, secret brokering, admission control).
- Assignment or checking of a workflow's autonomy level, and capability stage progression.

## Rules

- Core: [AGENTS.md](../AGENTS.md)
- [governance.md](../ai_harness/rules/governance.md), [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md),
  [governance-provenance.md](../ai_harness/rules/governance-provenance.md)
- Per-spoke rules: [ASSISTANTS.md](../ASSISTANTS.md)

## Platform Pillars

They apply to all governed repos. Pillar 1 is partly checked by a validator (see Enforced); the others are
enforced by human review only.

| # | Pillar | Rule | Consequence of violation |
|---|---|---|---|
| 1 | UV only for Python | `governance.md` → Python Tooling | Environments diverge; no reproducible execution path |
| 2 | Config drives code | `governance.md` → Config Purity | Domain changes need code changes; code cannot be reused |
| 3 | Low-code / OSS preference | `governance.md` → Low-Code / OSS Preference | Custom code reimplements tested paths and accrues maintenance |
| 4 | Context minimisation | `AGENTS.md` → Sessions and memory | Earlier constraints lose weight; work becomes non-resumable |
| 5 | Token management | `AGENTS.md` → Sessions and memory | Cost grows non-linearly; regeneration replaces reuse |
| 6 | No domain context in code | `governance.md` → Config Purity | Near-identical implementations proliferate per domain |

Pillars 2 and 6 are one rule (code is mechanism; domain context is config); so are 4 and 5 (short sessions with
durable state).

## Capability-Fit Governance

Governance does not privilege deterministic mechanism by default; it asks which of three peer drivers
(config-, data- or AI-driven) fits the task. The rule and the explicit-vs-inference test:
[governance.md](../ai_harness/rules/governance.md) → Driver Selection. The recurring failure class it answers
and the human review step (no hook): [behaviour spoke](../behaviour/README.md) → Capability-Fit Review.

## Governance Scope (what the hub owns)

### Decision rights

- Rule, hook, skill, settings and governance-contract changes: the operator, explicitly, in that session
  ([AGENTS.md](../AGENTS.md) → Governance changes).
- `ai_context/pco/` and `AGENTS.md`: changed only in the PCO. A consumer does not override or contradict a
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
supervision when novelty or ambiguity is high. No mechanism assigns or checks it.

### Capability-tiered governance (model/agent capability)

The tier is the `tier` field in [capability_registry.yaml](capability_registry.yaml).

| Capability tier | Typical characteristics | Control |
|---|---|---|
| **Tier 1** | Narrow scope, constrained tools, low autonomy | Human review |
| **Tier 2** | Broader toolset, works across domains | Human review |
| **Tier 3** | Strong general problem-solving, higher autonomy | Operator approval and adoption gate (see Enforced) |
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

No hook or validator checks independence; whoever dispatches the review sets it.

## PCO Evolution Model

### What triggers a rule review

1. **Enforcement anomaly**: a rule fires on legitimate work (false positive) or misses a violation (false negative).
2. **New external research**: a credible source names a pattern or threat the rules do not cover.
3. **Downstream feedback**: a governed repo hits a rule that blocks legitimate work, or a risk the PCO misses.
4. **Sensor silence**: a rule that rarely fires is checked for whether it can detect what it claims.
5. **Capability change**: a new model class, tool access or deployment context changes the risk profile.

### Cadence and ownership

- **Accountable owner**: the operator.
- **Cadence**: a periodic review is target, not implemented; reviews run on the triggers above.

### Change process

1. **Propose**: state the change, its trigger and its source (URL + retrieval date for research). A change
   without a traceable source is not accepted. Provenance labels: [governance-provenance.md](../ai_harness/rules/governance-provenance.md).
2. **Review**: does it contradict an existing rule? Is it proportionate? A change that removes or weakens a control
   requires independent review (see Independent review pattern).
3. **Approve and record**: operator approval; the commit names the trigger and source. Breaking changes are
   marked `breaking:` in the commit.
4. **Communicate downstream**: `distill_harness.py sync` to consumers.

### Rollback procedure (governance-of-governance)

Human review; nothing triggers it automatically.
- Roll back a rule change that causes a safety regression, widespread false positives or blocked legitimate work.
- Restore the last known-good version of the changed files, sync it, and record the trigger and evidence in the
  commit.
- Forward-fix through the change process; when safety is at stake, never roll forward without the control.

### Enforcement feedback loop

No mechanism collects these signals; the operator reviews them when they surface.

| Signal | Human action |
|---|---|
| Tool denial event | Was the denied action legitimate? False positive: loosen the rule. Correct block: keep it. |
| Sensor silence | Check the sensor can detect what it claims; silence is not evidence of quality. |
| High exception volume | The rule may be wrong; review it before escalating. |

### The AI's role in evolution

| Role | What the AI does | What the AI does not do |
|---|---|---|
| Sensor | Detects stale rules, enforcement anomalies, new research gaps | Decide whether a signal warrants a rule change |
| Proposer | Drafts the rule change with rationale and source tracing | Approve the change |
| Implementer | Writes the approved change, updates the anchor doc, syncs downstream | Determine the organisation's risk appetite |

## Capability Lifecycle

New capabilities are tracked in [capability_registry.yaml](capability_registry.yaml); the registry contract and
what is checked: [CONTRACT.md](CONTRACT.md) → Capability Lifecycle.

| Stage | Meaning |
|---|---|
| **Experimental** | Exists; not yet governed. Anything not in the registry is treated as experimental. |
| **Emerging** | A provisional rule exists; not yet tested against adversarial cases |
| **Established** | A rule tested against adversarial cases covers it; available to all governed repos |
| **Deprecated** | Being retired; no new adoption; existing uses need a migration path and timeline ([CONTRACT.md](CONTRACT.md) → Capability Lifecycle) |

### Progression criteria

Human review; stage progression is not enforced.
- **Experimental → Emerging**: a rule exists and the risk is understood
- **Emerging → Established**: tested against adversarial cases; no open named gap for it in the covering spoke
- **Established → Deprecated**: superseded, unacceptable risk, or no longer used

## `ai_agent_core` Relationship (Governed Implementation Substrate)

`ai_agent_core` is a governed repo and the shared implementation substrate that downstream repos pin as a
dependency, not vendor or modify. Because its changes reach every consumer, breaking changes need explicit
release signalling. The PCO does not check that consumers use it (see Not enforced); position and conformance
declarations: [CONTRACT.md](CONTRACT.md) → Special Case: `ai_agent_core`.

## Harness Rule Enforcement Lifecycle (session-snapshot model)

### How rules are loaded

- The core (`AGENTS.md`, synced from `ai_context/pco/AGENTS.md`) loads at session start through `CLAUDE.md`.
  Every rule under `.claude/rules/` is `paths:`-scoped and loads when the agent first reads or edits a matching
  file. Docs that need an explicit read are listed in [ASSISTANTS.md](../ASSISTANTS.md).
- A rule written mid-session does not apply to the running session; it takes effect at the next session start.
- **Consequence:** an agent writing a weaker rule is not caught by the harness, only by human review. Automated
  checks cannot detect semantic contradictions between rules, so human review is the governance sensor.
- `distill_harness.py sync` propagates changes to consumers; they take effect at each consumer's next session start.

## Spokes

One spoke per DAMA knowledge area; each README states what the area governs, what is enforced and the named gaps:

| DAMA Knowledge Area | Agent Harness Equivalent | Canonical document |
|---|---|---|
| Data Architecture | Agent Architecture | [architecture/](../architecture/README.md) |
| Data Modelling & Design | Agent Behaviour Modelling & Design | [behaviour/](../behaviour/README.md) |
| Data Storage & Operations | Agent Runtime & Operations | [operations/](../operations/README.md) |
| Data Security | Agent Security & Safety | [security/](../security/README.md) |
| Data Integration & Interoperability | Tooling & Integration | [integration/](../integration/README.md) |
| Document & Content Management | Knowledge & Content Management | [knowledge/](../knowledge/README.md) |
| Reference & Master Data | Identity, Policy & Configuration Master Data | [master-data/](../master-data/README.md) |
| Data Warehousing & Business Intelligence | Observability, Analytics & FinOps | [observability/](../observability/README.md) |
| Metadata Management | Registries, Versioning & Lineage | [lineage/](../lineage/README.md) |
| Data Quality Management | Assurance, Evals & Continuous Improvement | [assurance/](../assurance/README.md) |

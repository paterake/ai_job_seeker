# Agent Governance (Hub)

## Purpose

Defines Agent Governance as the central hub of Agent Management: the strategy, oversight, decision rights, policies, and systemic accountability used to run agentic systems safely and repeatably at scale.

## Why this is the hub

Every spoke domain (security, operations, tooling, evals, etc.) can be implemented in isolation, but it will not be reliable unless governance defines:
- Global rules (pillars/policies) and what is non-negotiable
- Ownership and decision rights (who can change what)
- Risk tiers and approvals (what needs escalation)
- Evidence requirements (what is recorded into run artefacts)
- Enforcement semantics (what is blocking vs advisory)

Without this hub, the harness becomes a collection of capabilities rather than a governed system.

## Platform Pillars (Non-Negotiable — Blocking)

These pillars apply to all governed repos and all work performed within or by the harness.
They are not advisory. Any work that violates a pillar is non-conformant regardless of other correctness.

| # | Pillar | Consequence of violation |
|---|---|---|
| 1 | **UV only for Python** — all dependency management and script execution via `uv`; no `pip install` to OS, no Poetry/Conda/venv workarounds | Reproducibility breaks; environment state diverges; no consistent execution path |
| 2 | **Config drives code** — no domain strings, entity names, thresholds, file paths, or prompt text in `.py` files; all in YAML config | Code cannot be reused across domains; domain changes require code changes; config and code governance diverge |
| 3 | **Low-code / OSS preference** — prefer an existing OSS library over custom code when one covers the requirement adequately | Custom code accumulates maintenance liability; reimplements tested paths poorly; blocks reuse |
| 4 | **Context minimisation** — work spanning multiple sessions uses the anchor doc / backlog continuity pattern; sessions are scoped to one coherent slice | Context saturation erodes earlier constraints; invariants drift silently; work becomes non-resumable |
| 5 | **Token management** — long sessions resolving a single ask by accumulating large context are an anti-pattern; design in chapters | Cost grows non-linearly; earlier architectural rules lose weight; regeneration replaces reuse |
| 6 | **No domain context in code** — domain assumptions are not baked into implementations; domain context lives in config and context-layer inputs | Code cannot be reused across domain variations; triggers proliferation of near-identical implementations |

Pillars 2 and 6 are two faces of the same rule: code is reusable mechanism; domain context is configuration.
Pillars 4 and 5 are two faces of the same rule: long sessions accumulate noise; short sessions with durable state are the operating model.

---

## Governance Scope (what the hub owns)

### Decision rights

Agent Governance centralises decisions about:
- Core vs optional policy ("pillars" vs guidance)
- Tool availability and entitlements
- Allowed workflows and routing rules
- Risk tiers, approvals, and escalation paths
- Evaluation gates and pass/fail thresholds
- Exception policy (how exceptions are granted, time-bounded, and revoked)

### Autonomy placement (supervision model)

Governance owns the supervision model for workflows: how much human oversight is used and what triggers moving a workflow toward more supervision.

| Autonomy level | Meaning | Default controls |
|---|---|---|
| **Fully supervised** | Human approves each high-impact step before it executes | Strict tool entitlements, blocking review gates, minimal autonomy |
| **Human-in-the-loop** | Agent acts within bounds; escalates for approvals on defined conditions | Exception policy + escalation rules enforced as blocking gates |
| **Human-on-the-loop** | Agent executes end-to-end; humans review sampled runs and intervene on alerts | Strong telemetry, canarying, rollback readiness, online evaluation sampling |
| **Fully autonomous** | Agent executes without routine human review | Allowed only for narrow, well-characterised workflows with proven controls and monitoring |

Placement criteria are independent of security risk tier. A low-risk workflow may still require high supervision when novelty or ambiguity is high.

### Capability-tiered governance (model/agent capability)

| Capability tier | Typical characteristics | Governance strength |
|---|---|---|
| **Tier 1 (low)** | Narrow scope, constrained tools, low autonomy | Standard gates + baseline eval suites |
| **Tier 2 (moderate)** | Broader toolset, higher success rate across domains | Expanded eval coverage, stricter review for tool changes |
| **Tier 3 (high)** | Strong general problem-solving, higher autonomy pressure | Blocking adversarial testing, tighter entitlements, independent review requirements |
| **Tier 4 (frontier+)** | Rapid capability shifts, high leverage tools, novel behaviour risk | Governance-board approval for key changes, standing red-team capability, conservative rollout and monitoring |

### Policy taxonomy (what is governed)

| Policy type | What it controls | Enforcement semantics |
|---|---|---|
| Pillars | Architectural law and organisational non-negotiables | Blocking |
| Security policy | Data classes, secret handling, tool entitlements | Blocking |
| Workflow policy | Which workflows exist and when they may run | Blocking |
| Quality policy | Evals and thresholds by risk tier | Blocking |
| Operational policy | SLOs, incident response, rollbacks, kill-switch | Blocking where safety/reliability demands |
| Guidance | Preferred patterns and defaults | Advisory |

### Evidence and accountability

Governance is only real if outcomes are attributable and auditable:
- Every run has a traceable "why" (policy set, versions, approvals)
- Every action has accountable ownership (role, entitlement, execution record)
- Every exception is recorded (scope, owner, expiry, justification)

---

## Governance Operating Model

### Institutional oversight (named structures)

- **PCO owner**: accountable for the canonical PCO (this repo) and its change control
- **Governance board**: approves Tier 3/4 changes and any changes that materially alter risk appetite
- **Standing red-team function**: continuously tests adversarial behaviour; not a one-time deployment gate
- **Content safety oversight**: owns policies and response for harmful output risks (abuse, impersonation, unsafe content)
- **Transparency reporting**: periodic aggregated reporting across all governed agents (exceptions, incidents, drift, cost-quality frontier)

### The governance loop

Agent Governance is a continuous loop:
1. Define policies and standards
2. Enforce them structurally in the harness
3. Measure outcomes (quality, safety, cost, throughput)
4. Investigate incidents and near misses
5. Improve policies, tooling, and evals

### Change control principles

- Policies are versioned and rolled out deliberately.
- Breaking changes are deliberate: compatibility windows and migration paths exist.
- Exceptions are products: explicit owner, expiry, scope, and evidence.
- Advisory guidance is distinct from blocking law (enforcement semantics anchor: [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)).

---

## Governance Design Principle: Enable, Don't Constrain

Governance fails in two modes: too rigid (blocks legitimate work, gets bypassed) and too porous (rules exist on paper but aren't followed because compliance cost exceeds the cost of ignoring them).

The design intent is **enabling governance**:

- **Short, hard prohibition list** — a small set of non-negotiable controls (Lethal Trifecta mitigations, non-impersonation, pillar violations). These do not change with capability advancement; they become harder to satisfy as capability grows, not easier.
- **Long, growing approved-pattern list** — new capabilities, tools, and workflow patterns are added as they mature through the capability lifecycle. The approved list grows continuously; the disallowed list stays short and stable.
- **Certainty enables speed** — clear rules about what is permitted allow agents to act without escalating. Ambiguity forces constant approval requests, slowing work and incentivising workarounds.
- **Additive by default** — new capabilities extend the PCO; they do not require dismantling existing rules.

---

## PCO Evolution Model

The PCO is not frozen at authoring time. It is a living governance system that evolves as enforcement reveals miscalibrations, research identifies new gaps, and the capability of governed agents changes.

### What triggers a rule review

1. **Enforcement anomaly** — a rule fires unexpectedly (false positive) or fails to fire when a violation occurs (false negative). Both indicate miscalibration and trigger review, not just logging.
2. **New external research** — a credible source identifies a pattern or threat not covered by current rules. Record the source in the change proposal and queue the rule update.
3. **Downstream feedback** — a governed repo surfaces a conflict: a platform rule prevents legitimate work, or a downstream pattern reveals a class of risk the PCO does not cover.
4. **Sensor silence** — a rule that rarely fires is validated (can it detect what it claims to detect?) not assumed to be working.
5. **Capability change** — a new model class, expanded tool access, or new deployment context changes the risk profile and may require new or tightened rules.
6. **Periodic cadence** — rules are examined at a regular cadence regardless of triggers.

### Cadence and ownership

- **Cadence**: the PCO is reviewed on a named, recurring cadence (at minimum quarterly) regardless of incident triggers
- **Accountable owner**: a named human owner is accountable for running the cadence review and ensuring outcomes are recorded
- **Inputs**: enforcement anomalies, sensor silence checks, downstream feedback, red-team findings, and capability changes
- **Outputs**: approved changes, rejected proposals with rationale, and a prioritised backlog of enforcement work

### Change process

1. **Propose** — state the change, the trigger that caused it, and trace it to a source. A change without a traceable source is not accepted.

   **Change Proposal Evidence Block (PR description minimum):**
   - **Trigger**: enforcement anomaly | external research | downstream feedback | sensor silence | capability change | cadence review
   - **Decision**: what will change and what will not
   - **Sources (if any)**: URL + retrieval date
   - **Claims relied on**: short bullet list in your own words
   - **Controls impacted**: which rules/hooks/tests/sensors change; link to files
   - **Verification plan**: what proves this is correct; what failure would look like
   - **Rollout**: breaking/non-breaking; compatibility window if relevant

2. **Review** — assess: does it contradict an existing rule? Is it proportionate to the risk? HIGH or CRITICAL rule changes require independent review.
3. **Approve and record** — commit with a message that names the trigger and source. Breaking changes are marked `breaking:` in the commit.
4. **Communicate downstream** — governed repos are notified of any change that affects their conformance.

### Rollback procedure (governance-of-governance)

- Rollback criteria are defined (safety regression, widespread false positives, unacceptable throughput collapse)
- Rollback restores the last known-good policy version and records the trigger and evidence
- Forward-fix follows rollback; "roll forward without control" is not an acceptable response when safety is at stake

### Enforcement feedback loop

| Signal | Human action |
|---|---|
| Tool denial event | Periodic review: was the denied action legitimate? False positive → loosen rule. Correct block → confirm calibration. |
| Injection detection | Catalogue every detected attempt. Patterns trigger test suite updates. |
| Sensor silence | Validate the sensor can detect what it claims; do not assume silence means quality. |
| High exception volume | High rates for a rule indicate the rule may be wrong, not that teams are non-compliant. Review the rule before escalating. |
| Approval backlog | Elevated approval latency or volume signals a rule is too restrictive for the actual risk level. |

### The AI's role in evolution

| Role | What the AI does | What the AI does not do |
|---|---|---|
| Sensor | Detects stale rules, enforcement anomalies, new research gaps | Decide whether a signal warrants a rule change |
| Proposer | Drafts the rule change with full rationale and source tracing | Approve the change |
| Implementer | Writes the change into docs, updates the Gap Register, communicates downstream | Determine the organisation's risk appetite |

Human approval gates exist for every rule change (canonical anchor: [core-posture.md](../ai_harness/rules/core-posture.md)). A governance system where the governed entity approves its own rules is not governance.

### What a governed repo cannot do unilaterally

- Override or negate a platform rule in its local context
- Introduce a local rule that contradicts the hub
- Request a rule change by modifying its own `REPO_CONTRACT.md` without a formal change proposal to this repo

---

## Capability Lifecycle

New agent capabilities enter the PCO through a defined path. Without this, new capabilities are either blocked (not yet approved) or ungoverned (bypassing the PCO).

| Stage | Meaning | Monitoring | Downstream adoption |
|---|---|---|---|
| **Experimental** | Capability exists; not yet governed | Every use logged and reviewed | Requires platform awareness; not self-service |
| **Emerging** | Understood and governed at a basic level; adversarial testing in progress | Enhanced monitoring; provisional rule exists | Permitted with explicit acknowledgment |
| **Established** | Fully governed; guide/sensor coherence confirmed | Standard harness monitoring | Available to all governed repos as a standard pattern |
| **Deprecated** | Being retired; migration path defined | Tracked until removed | No new adoption; existing uses given a time-bounded migration window |

### Progression criteria

- **Experimental → Emerging**: a rule exists, monitoring is in place, risk is understood
- **Emerging → Established**: adversarial testing complete, guide/sensor coherence confirmed, no open HIGH gaps in the spoke doc covering this capability
- **Established → Deprecated**: capability is superseded, carries unacceptable risk, or is no longer used across governed repos

Anything not yet in the lifecycle is treated as **Experimental** — not blocked outright, but requiring explicit acknowledgment and enhanced monitoring.

Registry: [capability_registry.yaml](capability_registry.yaml)

---

## `ai_agent_core` Relationship (Governed Implementation Substrate)

`ai_agent_core` is both a governed repo conforming to `ai_agent_pco` structure and the shared implementation substrate that downstream repos pin to as a dependency. This separation enforces "consume as dependency, not source" for shared controls: downstream repos do not vendor or modify `ai_agent_core`. `ai_agent_pco` is guide-heavy by design; `ai_agent_core` is the shared sensor substrate.

Because changes to `ai_agent_core` affect all consumers, its change control is stricter than a typical downstream repo:
- Breaking changes require explicit release signalling and downstream communication
- Capability tier and autonomy implications are reviewed as part of `ai_agent_core` changes, not only local correctness

---

## Enforcement Model

| Layer (PCO) | Governance responsibility |
|---|---|
| Policy | Define policies, risk tiers, approvals; decide routing and gating |
| Control plane | Enforce policies at control points; broker secrets; block unsafe actions |
| Observability | Provide evidence: audit logs, trajectories, eval results, cost and drift signals |

## Harness Rule Enforcement Lifecycle (session-snapshot model)

### How rules are loaded

At session start, rule files under `.claude/rules/` are auto-loaded via their glob patterns (based on file types being touched). The agent then reads `CLAUDE.md` → `ai_context/ASSISTANTS.md`, which identifies which rules apply to the task and routes it to governance docs that require explicit reads (CONTRACT.md, ANTI_DRIFT.md, etc.). Rule files are already in context — the router does not re-read them. This creates a context snapshot. Mid-session writes to rule files do not retroactively apply to the running session — they take effect at the next session start.

### Within-session enforcement

- Platform pillars and agent-behavior rules are active from the first tool call.
- The deterministic router identifies which rules are most relevant and routes to governance docs that need explicit reads — it does not load rule files (those are already in context via globs).
- Computational sensors (tests, linters, structural validators) run within a session and report violations synchronously.

### Cross-session enforcement and the bootstrapping loop

- Governance doc changes are written in one session and loaded by the next — intentional. Governance quality compounds across sessions, but only if changes are correct.
- **Consequence:** governance doc changes require human review before acceptance. An agent writing a weaker rule within a session is not caught by the harness — only by the review layer.

### Human review as the governance sensor

Automated sensors cannot detect semantic contradictions between governance docs or rules that weaken controls. Human review is the primary sensor for governance doc changes (canonical anchor: [core-posture.md](../ai_harness/rules/core-posture.md)).

### Enforcement trigger summary

| Event | Effect |
|---|---|
| Session start | Rules snapshot loaded; constraints become active for that session |
| Mid-session rule write | No effect on current session; takes effect at next session start |
| Human acceptance of governance change | Change enters the operative rule set for subsequent sessions |
| `distill_harness.py sync` | Propagates rule changes to downstream repos; takes effect at their next session start |

## Spokes (the governed execution arms)

Each spoke is an execution domain controlled by this governance hub, mapped from the DAMA data management wheel:

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

## Definition of "Done" for Governance

Agent Governance is "done enough" for a real organisation when:
- Policies are centralised, versioned, and enforced structurally
- Tool access is least-privilege and auditable
- Runs are reproducible with full lineage and evidence
- Risk-tier gating exists (not everything is allowed by default)
- Evals/regressions protect the system from unsafe drift
- Incidents lead to measurable policy/tool/eval improvements

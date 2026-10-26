# Behaviour Design (Spoke)
> Area: Agent Behaviour Modelling & Design

## Governs

- How a coding agent works: assumptions stated, minimum code, surgical changes, proof of verification
- Driver choice (config-, data- or AI-driven) for code that interprets content
- Session scope and multi-session work through anchor docs
- Epistemic honesty: low confidence and ambiguity are surfaced, not filled
- Failure harvest: each agent failure becomes a structural fix

## Enforced

- The checked parts of the core are owned by other spokes: the shell-call budget ([operations](../operations/README.md)),
  the read-only synced core and its load by the agent entrypoint ([knowledge](../knowledge/README.md)), UV only
  ([architecture](../architecture/README.md)).
- Everything else in the core, including the driver choice and governance-change approval: human review (operator, at code review).

## Not enforced

- Evals of whether the rules change agent behaviour: no rule requires them; target, not implemented.

## Rules

- The always-loaded core: [AGENTS.md](../AGENTS.md)
- [code-architecture.md](../ai_harness/rules/code-architecture.md) (Config Purity, Driver Selection, Capability-Decision Record, Python Tooling)
- [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) (Capability Decisions Are Reviewed, Not Gated; Hooks: Guidance vs Enforcement)
- [security-threat-model.md](../ai_harness/rules/security-threat-model.md) §6 Epistemic honesty
- Anchor docs: [AI_ASSISTANT_BACKLOG_CONTINUITY.md](../governance/AI_ASSISTANT_BACKLOG_CONTINUITY.md); automated-decision safeguards: [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md)

## Canonical

### Session Design and Token Economy

Session boundaries are in the core ([AGENTS.md](../AGENTS.md) → Sessions and memory).
Config purity is the main token-economy lever: code reused through a config change is never regenerated
([code-architecture.md](../ai_harness/rules/code-architecture.md) → Config Purity).

### Failure Harvest

Every agent failure is a permanent signal, not a one-off incident. For each one:
1. Name the failure class (assumption filling, false success signal, scope creep, format mismatch, ...).
2. Engineer a structural fix: a rule, a hook or a verification step. A test only when the failure shows a delivered
   capability the test catalogue does not prove ([assurance.md](../ai_harness/rules/assurance.md) → Test Catalogue).
3. Record the fix in the governing file; if the constraint must hold unconditionally, wire it as a hook ([harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) → Hooks: Guidance vs Enforcement). When the governing file or hook is under `ai_context/pco/` and you are in a consumer, report the gap upstream instead ([AGENTS.md](../AGENTS.md) → Governance changes).
4. Remove a constraint only when the model demonstrably no longer triggers that failure class.

**The ratchet**: rules are added from evidence and removed by capability evidence, not by preference.
**Consequence**: failures treated as isolated incidents leave the harness with no memory, so the class recurs.

### Agent Behaviour Failure Taxonomy

The behaviour classes among the root causes the [incident template](../templates/incident_report.md) records. System error
sensors do not detect them; run review or human review at the task boundary does:

- **Overeagerness**: unrequested features, or business logic inferred from domain terms.
- **Assumption filling**: spec gaps filled without signalling, causing production problems with no system error.
- **Brute-force fix**: a hacky workaround (more memory, added annotations) instead of the root-cause fix.
- **False success signal**: the task reported complete despite failing tests or violated constraints.
- **Genie risk**: a spec loophole exploited (what was asked for, delivered in an unexpected way), or a confident wrong answer.
- **Code quality drift**: duplicated literals, unused parameters, improper patterns, nested conditionals.

### Capability-Fit Review (human, at code review)

A human review step; no automated sensor or gate exists. The questions:

- Is this task explicit derivation or semantic inference?
- If inference is present, why is the mechanism not AI-driven?
- If the solution is AI-driven, what makes deterministic derivation insufficient or misleading?
- If the solution is deterministic, what exact explicit structure in the source makes fixed-rule recovery valid?

It targets two mirror-image failures: bespoke deterministic machinery solving a semantic problem, and model use
where exact deterministic derivation was available.

### Recurring failure class: deterministic over-build for semantic work

A recurring class, not a one-off:

1. Coding agents default to writing code, so a model path looks like less implementation and is under-selected.
2. A governance corpus that rewards deterministic mechanism makes the bias systemic, not local.
3. A deterministic build chosen when it was the only viable path is not re-evaluated when capability changes.
4. With no capability-choice checkpoint, model-vs-code is defaulted silently instead of reviewed.
5. Structured inputs disguise semantic tasks as parsing problems.
6. Agents do not self-reframe; without structure the correction depends on repeated human challenge, so structure
   must carry the fix.

The structural response is Driver Selection and the Capability-Decision Record in
[code-architecture.md](../ai_harness/rules/code-architecture.md), screened by the review above.

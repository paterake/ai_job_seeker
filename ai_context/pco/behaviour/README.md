# Behaviour Design (Spoke)
> DAMA mapping: Data Modelling & Design → Agent Behaviour Modelling & Design

## Governs

- How a coding agent works: assumptions stated, minimum code, surgical changes, proof of verification
- Driver choice (config-, data- or AI-driven) for code that interprets content
- Session scope and multi-session work through anchor docs
- Epistemic honesty: low confidence and ambiguity are surfaced, not filled
- Failure harvest: each agent failure becomes a structural fix

## Enforced

- Bash calls per session are capped: hook, `check_execution_limits.sh`, limit in [execution_limits.yaml](../governance/execution_limits.yaml) ([hooks/README.md](../ai_harness/hooks/README.md)).
- The synced core is read-only in a consumer: hook, `check_guard.sh` denies a file edit under `ai_context/pco/` outside the PCO; a shell write is not checked ([hooks/README.md](../ai_harness/hooks/README.md)).
- Root `AGENTS.md` is an exact copy of the core: `wire`/`sync` write it and `validate` reports drift ([CONTRACT.md](../governance/CONTRACT.md)).
- UV only, for raw `python`/`python3` commands: validator, `governance-audit` (Python command scan; [HUB.md](../governance/HUB.md) → Enforced).
- Everything else in the core, including the driver choice and governance-change approval: human review (operator, at code review).

## Not enforced

- No `pip`, Poetry, Pipenv, Conda or ad-hoc virtualenv workflows: required by [code-architecture.md](../ai_harness/rules/code-architecture.md) → Python Tooling (UV Only); no PCO check.
- Evals of whether the rules change agent behaviour: no rule requires them; target, not implemented.

## Rules

- The always-loaded core: [AGENTS.md](../AGENTS.md)
- [code-architecture.md](../ai_harness/rules/code-architecture.md) (Config Purity, Driver Selection, Capability-Decision Record, Python Tooling)
- [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) (Capability Decisions Are Reviewed, Not Gated; Hooks: Guidance vs Enforcement)
- [security-threat-model.md](../ai_harness/rules/security-threat-model.md) §6 Epistemic honesty
- Anchor docs: [AI_ASSISTANT_BACKLOG_CONTINUITY.md](../governance/AI_ASSISTANT_BACKLOG_CONTINUITY.md); automated-decision safeguards: [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md)

## Canonical

### Session Design and Token Economy

Session boundaries are in the core ([AGENTS.md](../AGENTS.md) → Sessions and memory). A long session that
resolves one ask by accumulating context is an anti-pattern: work in chapters, one anchor-doc item per session.
Config purity is the main token-economy lever: code reused through a config change is never regenerated
([code-architecture.md](../ai_harness/rules/code-architecture.md) → Config Purity).

### Failure Harvest

Every agent failure is a permanent signal, not a one-off incident. For each one:
1. Name the failure class (assumption filling, false success signal, scope creep, format mismatch, ...).
2. Engineer a structural fix: a rule, a hook, a test or a verification step.
3. Record the fix in the governing file; if the constraint must hold unconditionally, wire it as a hook in settings.json ([harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md) → Hooks: Guidance vs Enforcement).
4. Remove a constraint only when the model demonstrably no longer triggers that failure class.

**The ratchet**: rules are added from evidence and removed by capability evidence, not by preference.
**Consequence**: failures treated as isolated incidents leave the harness with no memory, so the class recurs.

### Agent Behaviour Failure Taxonomy

The root-cause classes that the [incident template](../templates/incident_report.md) records. System error
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
2. The governance corpus once rewarded deterministic mechanism, so the bias was systemic, not local.
3. Deterministic builds were once the only viable path and were not re-evaluated when capability changed.
4. With no capability-choice checkpoint, model-vs-code was defaulted silently instead of reviewed.
5. Structured inputs disguised semantic tasks as parsing problems.
6. Agents did not self-reframe; the correction came from repeated human challenge, so structure must carry the fix.

The structural response is Driver Selection and the Capability-Decision Record in
[code-architecture.md](../ai_harness/rules/code-architecture.md), screened by the review above.

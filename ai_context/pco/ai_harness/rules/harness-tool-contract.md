---
description: Harness tool contract — approval gates, capability decisions reviewed rather than gated, hooks versus guidance (gates fail closed). Loaded when changing ai_context or audit records; edit-tool format and model-impact events are in the integration spoke.
basis: operational-experience
spoke: integration
paths:
  - "ai_context/**"
  - "audit/**"
---

> Governance narrative: [integration spoke](../../integration/README.md)

# Harness Tool Contract

Edit-tool format, harness switches, model upgrades and tool-interface changes (model-impact events)
are governed in the [integration spoke](../../integration/README.md).

## Approval Gates (Policy Anchor)

In fully supervised workflows (and whenever a policy requires approval), the assistant must stop at explicit approval gates and request a decision before proceeding.

- Approval gates are named and must present explicit options and consequences.
- Proceeding past an approval gate without an approval record is prohibited.
- The approval record must have a stable identifier; its binding to the run: `lineage.md` → Lineage and Evidence.
- Go-live gates for High/Critical solutions add effective-oversight and segregation-of-duties
  obligations: [ENTERPRISE_OBLIGATIONS.md](../../governance/ENTERPRISE_OBLIGATIONS.md).

## Capability Decisions Are Reviewed, Not Gated

The driver choice for a new content-interpretation mechanism (`code-architecture.md` → Driver Selection) is checked at
task boundary / code review, where the reviewer screens the substance: bespoke
deterministic machinery solving a semantic problem, or a model used where exact derivation was available.
No hook gates it. **Consequence:** a commit gate can prove only that a record exists, not that the choice is
right, so it adds a step to every commit without catching a wrong driver.

## Hooks: Guidance vs Enforcement

Always-loaded instructions and governance docs are guidance — they inform agent behaviour but cannot guarantee it under context saturation or instruction drift. Hooks are enforcement — they run deterministically at harness lifecycle points.

| Constraint type | Correct mechanism |
|---|---|
| Soft defaults, style, preferences | Always-loaded instructions / governance docs |
| Hard constraints that must hold unconditionally | Hooks in the harness settings |

Use a hook, not docs, for any constraint where a single violation has irreversible consequences (e.g. force push, `rm -rf`, hard reset).

**The test**: if the constraint must hold even at the end of a long, saturated session — wire it as a hook.
A constraint whose violation is reversible and caught by a validator (e.g. exception expiry) stays a validator check.

The hooks the PCO ships, what each blocks and misses, and what each does when a tool is missing:
[hooks/README.md](../hooks/README.md).
- A gate hook fails closed when it cannot run: it blocks a call it governs, never passes it silently. Where the
  PCO hooks fall short: [integration spoke](../../integration/README.md) → Not enforced.
  **Consequence:** a gate that passes when it cannot run is enforcement that silently does not happen.
- The context reaches every session as committed files; the PCO adds no session-environment setup.

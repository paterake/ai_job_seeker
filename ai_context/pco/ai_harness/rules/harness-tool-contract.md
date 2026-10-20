---
description: Harness tool contract — edit-tool format as a capability floor, not a config detail. Loaded when changing harness, switching models, or modifying tool interfaces.
globs:
  - ".claude/**"
  - ".trae/**"
  - ".github/**"
  - "ai_context/**"
  - "audit/**"
  - "**/settings.json"
basis: operational-experience
spoke: integration
paths:
  - ".claude/**"
  - ".trae/**"
  - ".github/**"
  - "ai_context/**"
  - "audit/**"
  - "**/settings.json"
applyTo: ".claude/**,.trae/**,.github/**,ai_context/**,audit/**,**/settings.json"
---

> Governance narrative: [integration spoke](../../integration/README.md)

# Harness Tool Contract

Edit-tool format, harness switches, model upgrades and tool-interface changes (model-impact events)
are governed in the [integration spoke](../../integration/README.md).

## Approval Gates (Policy Anchor)

In fully supervised workflows (and whenever a policy requires approval), the assistant must stop at explicit approval gates and request a decision before proceeding.

- Approval gates are named and must present explicit options and consequences.
- Proceeding past an approval gate without an approval record is prohibited.
- The approval record must have a stable identifier and be bound to `run_id` (and referenced in run lineage when used).
- Go-live gates for High/Critical solutions add effective-oversight and segregation-of-duties
  obligations: [ENTERPRISE_OBLIGATIONS.md](../../governance/ENTERPRISE_OBLIGATIONS.md).

## Capability-Decision Enforcement

Prose guidance is not enough for recurring capability-fit failures. When a change introduces a new
parser-/extractor-shaped mechanism, or a comparable content-interpretation surface, the harness must
enforce that a capability-decision artefact exists before commit / PR creation.

Required record shape: `governance.md` → Capability-Decision Record (template:
`audit/templates/capability_decision_record.md`).

Enforcement semantics:
- The hook enforces that a decision record exists — it denies the commit / PR command otherwise — in repos
  whose settings wire it; it fails open when its path/keyword heuristic does not recognise the change as
  content-interpretation-shaped. It does **not** prove the decision is correct.
- The corresponding behavioural sensor is a required task-boundary / code-review step that screens for
  the substance of the decision: bespoke deterministic machinery solving a semantic problem, or a model
  being used where exact derivation was available.
- Consumer repos own their `settings.json`, so the platform distributes the hook script and the
  baseline settings template; conformance requires the project-owned settings to wire it.

## Hooks: Guidance vs Enforcement

CLAUDE.md and governance docs are guidance — they inform agent behaviour but cannot guarantee it under context saturation or instruction drift. Hooks are enforcement — they execute at harness lifecycle points and cannot be overridden by model behaviour.

| Constraint type | Correct mechanism |
|---|---|
| Soft defaults, style, preferences | CLAUDE.md / governance docs |
| Hard constraints that must hold unconditionally | Hooks in `settings.json` |

Use a hook, not docs, for:
- Blocking destructive bash commands (force push, `rm -rf`, hard reset)
- Running typecheck / lint / tests after file edits
- Requiring approvals before commits or PRs are created
- Requiring a capability-decision artefact before parser-/extractor-shaped content-interpretation changes are committed
- Any constraint where a single violation has irreversible consequences

**The test**: if the constraint must hold even at the end of a long, saturated session — wire it as a hook.
A constraint whose violation is reversible and caught by a validator (e.g. exception expiry) stays a validator check.

The hooks the PCO ships, what each needs and what it does when a tool is missing: [hooks/README.md](../hooks/README.md).
- A gate hook fails closed when it cannot run: it blocks a call it governs with a one-line reason (exit 2),
  and never passes that call silently.
  **Consequence:** a gate that passes when `jq` or `ruby` is missing is enforcement that silently does not
  happen (observed 2026-10-20: every gate failed open with a tool off PATH).
- Cloud sessions provision the gates' tools through the `setup_cloud_session.sh` SessionStart hook, which
  every `.claude/settings.json` wires (`validate_harness_wiring.py` fails otherwise).

**Consequence**: hard constraints that live only in guidance text are subject to context saturation. As sessions grow, earlier rules lose weight. A constraint that must hold unconditionally must be enforced by the harness, not stated in prose.

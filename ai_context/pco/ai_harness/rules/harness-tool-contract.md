---
description: Harness tool contract — edit-tool format as a capability floor, not a config detail. Loaded when changing harness, switching models, or modifying tool interfaces.
globs:
  - ".claude/**"
  - ".qwen/**"
  - ".trae/**"
  - "ai_context/**"
basis: operational-experience
---

> Governance narrative: [integration spoke](../../integration/README.md)

# Harness Tool Contract

## The Portability Distinction

Governance transfers across harnesses. The edit-tool contract does not transfer automatically.

The governance layer (rules, posture, context routing) is portable by design — the same rules are symlinked into `.claude/`, `.qwen/`, and `.trae/`. The tool format layer is not governed by the same mechanism: models are post-trained and RL'd against a specific harness's tool conventions (e.g. unified diff vs. search-and-replace block). This calibration is implicit and not visible in any config file.

**Consequence**: even with a clean, portable governance layer, a mismatched edit dialect collapses success rate and creates retry loops regardless of how well the harness routes context. Governance directs; the edit-tool contract still has to fit.

## Edit-Tool Format as a Capability Variable

The edit-tool format a harness uses is a capability variable, not a configuration detail.

- A model calibrated to one edit dialect may emit structurally valid but unparseable output when the expected format changes.
- Success rate collapse from format mismatch is indistinguishable from model capability failure without explicit diagnosis.
- Recovery is complete when the expected format is restored — with no model change. This confirms the root cause is the tool format, not the model.

**Consequence**: treating the edit-tool contract as a neutral detail leads to silent capability degradation that is misdiagnosed as model regression.

## Required Controls

### When switching harnesses

Before migrating governance to a new harness (e.g. Claude Code → Qwen Coder):
- Identify the edit-tool format each harness emits and expects.
- Confirm the target model was post-trained or evaluated against that format.
- Run a capability regression suite before declaring the migration complete — clean governance is a necessary but not sufficient condition.

### When changing a tool interface

Any change to tool schema, argument semantics, output format, or default behaviour is a model-impact event (not just an engineering change). Treat it as such:
- Flag the change as model-impacting before merging.
- Require regression evidence from a representative workflow eval, not just unit tests.
- Apply a compatibility window if the change affects the edit tool specifically.

### When upgrading models

A model upgrade may shift the post-training distribution for tool format expectations. Do not assume forward compatibility:
- Re-validate the edit-tool contract for the new model version.
- Treat unexplained success rate drops after a model upgrade as a potential format mismatch before assuming model regression.

## Approval Gates (Policy Anchor)

In fully supervised workflows (and whenever a policy requires approval), the assistant must stop at explicit approval gates and request a decision before proceeding.

- Approval gates are named and must present explicit options and consequences.
- Proceeding past an approval gate without an approval record is prohibited.
- The approval record must have a stable identifier and be bound to `run_id` (and referenced in run lineage when used).
- **Effective oversight (not nominal).** For a gate on a High/Critical solution, the named overseer
  must be competent for that risk tier and the gate must be designed to resist automation bias — the
  approval record captures a substantive decision, not a rubber-stamp. **Consequence:** a signature
  box is not oversight; nominal sign-off fails the AI Act's effectiveness bar while appearing compliant.
- **Segregation of duties at go-live.** At the go-live gate, the approver must not be the author of
  the change; author ≠ approver is enforced, not advisory. **Consequence:** self-approval at go-live
  defeats the conformance gate — the one control the gate exists to provide is bypassed by one person.

## Hooks: Guidance vs Enforcement

CLAUDE.md and governance docs are guidance — they inform agent behaviour but cannot guarantee it under context saturation or instruction drift. Hooks are enforcement — they execute at harness lifecycle points and cannot be overridden by model behaviour.

| Constraint type | Correct mechanism |
|---|---|
| Soft defaults, style, preferences | CLAUDE.md / governance docs |
| Hard constraints that must hold unconditionally | Hooks in `settings.json` |

Hooks are required (not docs) for:
- Blocking destructive bash commands (force push, `rm -rf`, hard reset)
- Running typecheck / lint / tests after file edits
- Requiring approvals before commits or PRs are created
- Any constraint where a single violation has irreversible consequences

**The test**: if the constraint must hold even at the end of a long, saturated session — wire it as a hook.

**Consequence**: hard constraints that live only in guidance text are subject to context saturation. As sessions grow, earlier rules lose weight. A constraint that must hold unconditionally must be enforced by the harness, not stated in prose.

---
name: "backlog-continuity"
description: "Creates/updates anchor-doc checkpoints for backlog continuity. Invoke when starting/continuing a backlog item or creating a TODO anchor doc."
---

# Skill: Backlog Continuity

## Goal

Maintain durable backlog state so each backlog item can be executed in a fresh session without losing constraints, verification steps, or discovered gotchas.

## When to Invoke

- The user asks to create a TODO/anchor doc for a backlog.
- The user asks to continue/progress a backlog item across sessions.
- The user asks for a checkpoint update (Done/Still Todo/Constraints/Verification/Gotchas).

## Inputs (Ask Only If Missing)

- Anchor doc path (e.g., `docs/TODO_PCO_MATURITY.md`)
- Backlog item name (exact heading or label)
- What changed (files + summary)
- Verification command(s) actually run (or to be run)
- New constraints established by this item
- New gotchas discovered

## Procedure

1. Read the anchor doc.
2. Locate the top-of-doc `## Resume (start here)` section and the backlog item checkpoint sections:
   - Resume (start here)
   - Done
   - Still Todo
   - Accumulated Active Constraints
   - Verification
   - Gotchas
3. Update the checkpoint using the template below:
   - Record concrete file-level changes and outcomes.
   - Move completed steps from Still Todo to Done.
   - Forward prior constraints and append any new invariants.
   - Record exact verification commands.
   - Append any gotchas discovered.
4. Update the top-of-doc resume pointer to the next unfinished item + step (so it is correct for handover).
5. Output the next resume prompt:
   - `From <anchor doc>: Continue <item name> → “Still todo” step <n>`

## Checkpoint Template

```text
Backlog Item: <name>

Done
- <specific change + file(s) + verification result>

Still todo (next actions)
1) <next action>

Accumulated Active Constraints (active for all remaining items)
- <invariant — forward from prior items + any new ones this item established>

Verification
- <exact command>

Gotchas
- <environment/tooling/dependency note>
```

## Reference

- Continuity contract: `ai_context/pco/governance/AI_ASSISTANT_BACKLOG_CONTINUITY.md`

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

- Anchor doc path (e.g., `docs/todo/TODO_<NAME>.md`)
- Backlog item name (exact heading or label)
- What changed (files + summary)
- Verification command(s) actually run (or to be run)
- New constraints established by this item
- New gotchas discovered

## Procedure

1. Read the anchor doc.
2. Locate the sections the continuity contract requires (§ What the Anchor Doc Must Contain).
3. Update the checkpoint in the shape of the contract's § Checkpoint Template:
   - Record concrete file-level changes and outcomes.
   - Move completed steps from Still Todo to Done.
   - Forward prior constraints and append any new invariants.
   - Record exact verification commands.
   - Append any gotchas discovered.
4. Update the Resume (start here) line to the next unfinished item + step, and make sure the Session start prompt
   section holds the prompt built as in the contract's § Resume Prompt (One Line).
5. Run the contract's § Session-Close Self-Check.
6. Output the Session start prompt for the operator to paste into the next session.

## Reference

- Continuity contract: `ai_context/pco/governance/AI_ASSISTANT_BACKLOG_CONTINUITY.md`

# AI Assistant Backlog Continuity Contract

## Operating Model

Use a **new chat session per backlog item**. Each session reads the anchor doc to start warm.
This is the primary model, not a fallback — it prevents context saturation and ensures
accumulated constraints are loaded at full precision rather than competing with task noise.

## Resume Prompt (One Line)

> `load the use-context skill, and from: <anchor-doc-path>, continue`

**How to construct it when creating a new anchor doc:**

1. Check whether a `use-context` skill is available in this environment (repo-local skills directory and/or the agent UI’s available skills list).
2. If the skill exists: `load the use-context skill, and from: <anchor-doc-path>, continue`
3. If no skill: `from: <anchor-doc-path>, continue`
4. `<anchor-doc-path>` is the path of the anchor doc being created, relative to the repo root.

Store the constructed prompt verbatim in the anchor doc's `## Session start prompt` section so the operator pastes it without reconstructing the formula each time.

## Anchor Doc Resume Section (Required)

The anchor doc must include a top-of-document resume pointer so a fresh session or a new agent can open the file and immediately know what to do next.

Use this exact structure at the top of the anchor doc:

```text
## Resume (start here)

- From `docs/<anchor-doc>.md`: Continue <item name> → “Still todo” step <n>
```

This resume line must be updated whenever the “Still todo” next step changes.

## What the Anchor Doc Must Contain

| Section | Purpose |
|---|---|
| **Resume (start here)** | One-line pointer to the next item + next step for handover |
| **Session start prompt** | Exact prompt to paste at session start (including skill invocations) — stored so the operator never reconstructs the formula |
| **Done** | What changed, where, and verification result — file-level references |
| **Still Todo** | Remaining ordered actions |
| **Accumulated Active Constraints** | Invariants established by completed items — grows as work progresses; never shrinks |
| **Verification** | Exact command(s) — "should work" is not a check |
| **Gotchas** | Discovered friction that a fresh session would otherwise re-learn |

An anchor doc may also be a **hybrid**: the checkpoint sections above plus per-item
descriptive/spec sections (e.g. one `### Item N` per module) for a full backlog spec. See
"Single Source of Truth for Status" below for the constraint this hybrid shape must follow.

## Anchor Doc Selection

| Work type | Anchor doc location |
|---|---|
| Cross-repo or cross-module work | `docs/<tracker>.md` in the affected root repo |
| Single-module backlog | `<module>/docs/TODO.md` (delete when exhausted) |
| Contract/maturity gaps | module `PRD.md` |

## Constraint Inheritance Rule

Every completed item establishes constraints that all subsequent items must honour.
The Accumulated Active Constraints section must be updated after each item — forward
new constraints explicitly; do not assume the next session will re-derive them.

## Single Source of Truth for Status

Some anchor docs embed per-item descriptive/spec sections (e.g. a full backlog spec with one
`### Item N` section per module) in addition to the Resume/Done/Still-Todo block. This is a
hybrid shape: "checkpoint anchor doc" + "full backlog spec" in one file.

When this hybrid shape is used, the per-item spec sections must not restate completion status
in prose. They reference the Resume/Accumulated-Constraints section instead (e.g. "see Resume"
or a bare ✅/⏳ marker on the heading only).

Before closing any session that changes an item's status, grep the full anchor doc for every
other mention of that item's name/number and confirm no other location contradicts the new
status.

**Consequence**: status duplicated across a Resume line and a per-item prose section drifts the
moment one is updated and the other isn't — a fresh session reading the per-item section sees a
stale status and re-derives wrong assumptions about what's left to do.

## Session-Close Self-Check (Required, Proactive)

Before ending any session that closes or advances a backlog item, perform this check
without waiting to be asked:

1. Grep the full anchor doc for every mention of the item's name/number.
2. For each hit, confirm it agrees with the new status — including the item's own
   descriptive body, not just the Resume/heading line.
3. Re-run every command in that item's Verification block and replace any recorded
   output (counts, pass/fail text) with the actual current output — a stale recorded
   output is itself a contradiction, not just a stale status sentence.
4. Confirm Gotchas and Accumulated Active Constraints reflect this item's outcome.
5. If this session wrote or updated a memory file (or a memory index such as `MEMORY.md`)
   about this item, confirm it agrees with the anchor doc's new status — memory is a second
   persistent surface outside the anchor doc, and the same drift this contract guards against
   inside one file can also open up between the anchor doc and memory.

**Consequence**: a status check that only looks at the intro sentence misses stale
verification output and stale next-step instructions embedded deeper in the item body —
the gap a single status-prose rule does not catch, and that otherwise requires the operator
to manually request a handover check after every single item. A memory file that contradicts
the anchor doc is the same failure one layer up: a fresh session that trusts memory over a
correctly-updated anchor doc (or vice versa) inherits whichever one is wrong.

## Blocked Item Marker (Required When Applicable)

An item that ends a session genuinely unresolved — blocked on an ambiguity, a missing
decision, or external input — is not the same state as an item with ordinary next steps.
Mark it explicitly rather than letting it read like a normal in-progress item:

- Prefix the item's status with `BLOCKED:` (in the Resume line and the item heading/marker),
  followed by the specific open question or missing decision in one sentence.
- State explicitly what must NOT be assumed: if there is more than one plausible
  interpretation, list them rather than picking one silently.
- Do not advance "Still Todo" past the blocking step. The next action for a blocked item is
  always "resolve the blocker," not the step that would follow if it were resolved.

**Consequence**: an unresolved ambiguity that reads like a normal next-step invites a cold
session to silently pick an interpretation and proceed — assumption filling (see
`ai_context/pco/ai_harness/rules/agent-behavior.md` § Pre-Implementation Gate) is the documented
failure mode this produces, and it is harder to catch after the fact than before a session ends.

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

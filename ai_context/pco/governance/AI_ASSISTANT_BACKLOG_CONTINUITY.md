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
6. **Secret/redaction-signature self-check (cfg repos that declare `redaction.patterns[i]`).** Run the repo's boundary/secret gate against ALL text files this session touched in the cfg repo (anchor doc TODO.md, RUNBOOK.md, ORIENTATION.md, EXECUTE.md, acceptance-report JSON, any changed catalogue YAML). Confirm `check_boundary.py --staged` rc=0, or — if the project has no such script yet — manually grep every changed cfg file for a literal substring match against each `redaction.patterns[i]` regex from the catalogue. The only permitted exceptions are: (a) `catalogue.yaml` itself (it is the pattern source and contains the definition), and (b) the boundary-gate check script (it names patterns in comments). Everywhere else, including checkpoint crumbs, gotchas, and lesson-learned prose: replace the literal matched text with either (i) the pattern index pointer `redaction.patterns[N]` or (ii) the sanitised replacement token (e.g. `[REDACTED_TEST_ACCOUNT]`). DO NOT rely on your own reading of the prose to decide "this is obviously documentation not a secret" — the pre-commit gate regex cannot distinguish and will fail the commit regardless of intent.

**Consequence**: a status check that only looks at the intro sentence misses stale
verification output and stale next-step instructions embedded deeper in the item body —
the gap a single status-prose rule does not catch, and that otherwise requires the operator
to manually request a handover check after every single item. A memory file that contradicts
the anchor doc is the same failure one layer up: a fresh session that trusts memory over a
correctly-updated anchor doc (or vice versa) inherits whichever one is wrong. A cold-start
session that inherits an anchor doc containing a bare redaction signature then writes a
second unrelated checkpoint crumb → `git commit` fails on the unrelated commit because the
boundary gate scans ALL staged files, not just the ones changed that session, and the bare
signature was never cleaned from the anchor doc.

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

### Checkpoint Crumbs — Non-Negotiable Hygiene

The Done block, Constraints, and Gotchas are written into git-tracked text files in the repo
(anchor doc TODO.md, RUNBOOK.md, etc.). Two rules prevent recurring pre-commit boundary
failures when the repo declares `redaction.patterns[i]` regexes:

1. **Never embed a bare redaction signature in prose.** If the just-completed item
   scrubbed a secret or discussed redaction output integrity, reference the pattern by
   its catalogue index (e.g. `redaction.patterns[2]`) and/or by the sanitised replacement
   token the writer emits (e.g. `[REDACTED_VENDOR_DOMAIN]`). NEVER paste the actual matched
   substring into a checkpoint just to be concrete about what was scrubbed — the
   boundary-gate regex cannot tell documentation of a secret apart from the secret itself,
   and the next `git commit` (possibly for an unrelated item in a cold session) will fail
   with `BOUNDARY GATE FAILED`.
2. **Session-close step #6 (gate re-run) is mandatory.** After writing checkpoint crumbs,
   actually run `scripts/check_boundary.py --staged` (or the repo's equivalent) as the
   final act of the session and confirm rc=0 before declaring the item finished. Do not
   assume "it was clean last session" — crumbs written in *this* session are the highest-
   probability source of a regression.

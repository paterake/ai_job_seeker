# Documentation Contract

## Why This Matters

The reader of these docs is an agent, and it reads code directly. A doc that restates code drifts and is
then trusted over the code, by agents and by publication, which reads the implementation and config for
what they show. Docs hold what code cannot show ([Derivability Test](#derivability-test)); without it an
agent guesses, and breaks invariants it could not see.

This contract is the whole doc set, not a floor. Invoke `docs-alignment` to validate a repo or implementation
against it.

---

## Required Set (Every Repo and Implementation)

Missing any of these is a blocker, not a backlog item.

| File | Owns | Consequence if absent |
|-----|------|-----------------------|
| `ai_context/project/INTENT.md` | Purpose, scope and non-goals; guarantees the code must meet; decisions with rejected alternatives; constraints from outside the code; known limitations. Shape: `ai_context/pco/templates/INTENT_TEMPLATE.md` | The code cannot be checked against intent; rejected alternatives are re-proposed; invariants are broken unseen |
| `docs/RUNBOOK.md` ‡ | Prerequisites and environment; which entry point serves which task and when; what a failure means and the recovery the code cannot show. Commands and flags come from each tool's `--help` | An agent cannot set up, sequence or recover the module; failures are fixed by guesswork |
| `docs/CONFIGURATION.md` | Config keys, defaults, rationale — [code-blind](#configurationmd-code-blind-definition) | Domain values leak into code; reuse across datasets requires code changes |
| `docs/TODO.md` † | Project backlog index — open initiatives with pointers to anchor docs, completed section | Backlog continuity breaks; completed items re-enter scope; sessions re-derive state |

† **`docs/TODO.md` is required only while the module (or repo) has open backlog.** Once
the backlog is closed and `docs/TODO.md` removed, its absence is permitted and must not be treated
as a blocker. A missing `docs/TODO.md` is a violation only when the module still has open backlog
items (e.g. an Alpha module with open maturity gaps); otherwise an intentional retirement and a
drift defect are indistinguishable to `docs-alignment`.

‡ **`docs/RUNBOOK.md` is required only when the module (or repo) is set up and run from its own checkout.** A
library that runs only inside its consumers has no operations of its own: each consumer's runbook owns the
workflows that use it, and the library's `INTENT.md` → Delegates names those consumers. Its absence is then
permitted and must not be treated as a blocker. A missing runbook is a violation when the module is run from its
own checkout or `INTENT.md` names no consumer runbook; otherwise `docs-alignment` reports a blocker no fix can
clear, or a runbook is written with nothing to run.

A root `README.md` is not required; a repo may keep one as a pointer to its entrypoint.

**`INTENT.md`, not `PRD.md`.** A PRD is a build input: before code exists it holds everything, and once the
code exists most of it restates the code. Modules here are built by agents from anchor docs and the session, so
a `PRD.md` would be written after the code to fit convention: a second copy from its first line. `INTENT.md`
keeps only what survives the build. The name is deliberate: an agent given a `PRD.md` fills it from the common
template (features, stack, file layout). A build spec written before code is a temporary input, like an anchor
doc: when the code lands, move what passes the Derivability Test into `INTENT.md` and delete the spec.
Rejected: keeping the name `PRD.md` for familiarity.

**Any other doc is a finding.** `PRD.md`, `docs/ARCHITECTURE.md`, `docs/AI.md`, `docs/EXECUTIVE-SUMMARY.md`,
`docs/use-cases/`, extension docs, legacy command docs (`docs/RUNNERS.md`, `docs/ops/CLI.md`) and a `README.md`
inside a code module or package directory are retired:
apply the [Derivability Test](#derivability-test), move what remains to its owner in this set, then delete the
doc ([Retrospective Refactor Safety](#retrospective-refactor-safety)). Until migrated, it is a finding, not a
blocker.

### TODO File Structure

`docs/TODO.md` is the single project backlog index — the only TODO file in the `docs/` root.
All other TODO files are filed under `docs/todo/`.

| Location | Purpose |
|----------|---------|
| `docs/TODO.md` | Open initiatives (pointer + status) and completed section. One file, root only. |
| `docs/todo/<initiative>.md` | Active anchor docs for named multi-session initiatives. Session continuity artefacts. |
| (no archive) | A completed anchor doc is deleted once its durable facts are moved into code or docs; its Completed row in `docs/TODO.md` cites the deleting commit (recover with `git show <hash>^:<path>`). |

**Consequence**: named `TODO_<X>.md` files in the docs root make it impossible to distinguish the
live backlog from session artefacts and historical records at a glance.

**Implementation-level TODOs** belong within the implementation's own directory (`<implementation>/docs/TODO.md`), never in the project root.

---

## Multi-Implementation Repos

When a repo contains multiple named implementations (e.g., `impl_a/`, `impl_b/`), each implementation owns
`<implementation>/docs/RUNBOOK.md` (‡), `<implementation>/docs/CONFIGURATION.md` and
`ai_context/project/<implementation>/INTENT.md`. The root `docs/RUNBOOK.md` and `docs/CONFIGURATION.md` are
routing surfaces: they route to the implementation docs and hold no implementation-specific install steps,
commands, recovery, keys, defaults or rationale.

**Consequence of violation**: a root doc that accumulates implementation detail drifts independently of each
implementation's own docs, and an agent cannot tell which is authoritative.

**The test**: does the root doc contain content a reader could only answer by reading a specific
implementation? If yes, it has become a duplicate, not a routing surface.

---

## Segregation Rules (What Each File Owns)

Hard boundaries. Content in the wrong file forces readers to search several files for one answer
and produces invisible duplication that drifts independently.

- **When to run what, failure meaning and recovery** → `docs/RUNBOOK.md` only, each entry point once, under its task.
- **Config keys and their rationale** → `docs/CONFIGURATION.md` only. Never inline in code comments.
- **Intent, guarantees, decisions, outside constraints, limitations** → `INTENT.md` only. AI tuning rationale
  and degrade modes are decisions; their values are config.
- **Dataset and domain specifics** → config only. Never in framework-level files.

**The test**: can a reader answer their question from exactly one file? If not, the segregation is broken.

---

## Derivability Test

A line that an agent could answer correctly from the code, config or a tool's `--help` does not belong in
docs or `INTENT.md`. They hold only what code cannot show:

- intent, scope and non-goals;
- guarantees the code must meet;
- decisions with their rejected alternatives;
- constraints from outside the code: operator decisions, obligations, external systems, environment;
- known limitations;
- the backlog.

**Consequence if violated**: a line that restates code drifts the next time the code changes, and a reader
who trusts it over the code acts on the stale copy.

---

## INTENT.md Is Code-Blind

`INTENT.md` states what must be true, not how the code achieves it, so the code can be checked against it.
It names no source file paths, functions or tests. Guarantees are falsifiable: each names an input, an output
and a verifiable constraint. A claim states its conditions ("deterministic" names the inputs, config and
environment under which it holds).

**Consequence if violated**: intent that names code drifts with every refactor and stops being a standard the
code can be checked against.

---

## CONFIGURATION.md Code-Blind Definition

`CONFIGURATION.md` may reference config/data file paths (YAML, XLSX, config directories) and the
config keys themselves. It must not reference source-code file paths, script names,
function/method/macro names, or CLI flags — the code shows those, and `RUNBOOK.md` owns when to run what.

**Consequence if violated**: implementation detail embedded in the config doc drifts independently
of the code it names.

---

## Config Master-Data Is Referenced, Never Copied

A doc must not enumerate facts owned by a config or SQL file that change with data/extract — ingest
tabs/sheets, per-stage source-table lists, thresholds. Reference the owning file by relative link
instead. A doc that copies such a list is a defect: it drifts silently the next time the config
changes, and a consolidation from an already-stale doc propagates the stale copy.

Stable contract identifiers (output table names, validator names, workflow names) **may** be named
inline — they are the contract, not volatile data. Point-in-time measurements (row counts, reconcile
buckets) **may** be stated if dated and paired with the command that regenerates them. The target of
this rule is copied config **structure**, not stable identifiers or dated measurements.

**Consequence if violated**: refactor/consolidation sessions keep copying volatile lists; every
extract or config change silently re-opens the same drift, undetected until a manual data check.

---

## Retrospective Refactor Safety

Applying this contract to existing docs (retrospective alignment) is a content operation, not a
structural tidy. Existing docs contain information that must not be lost. The process is strictly
ordered — deviation produces silent information loss.

### Required sequence (non-negotiable)

1. **Inventory first.** Read every doc being changed in full before any file operation. List what
   information each doc contains — not its title, its actual content.

2. **Map every item.** For each piece of information in the inventory, identify the destination
   per the segregation rules. If no clear destination exists, flag it for operator review — do not
   decide unilaterally and do not drop it.

3. **Move, never drop.** Content in the wrong place is moved to the correct one. It is never deleted
   because it is in the wrong place. The one exception is content that fails the
   [Derivability Test](#derivability-test): it may be dropped, but only after confirming the code, config or
   `--help` actually shows it. If it does not, it is a constraint and is moved.

4. **Distill, never rewrite.** Preserve existing content; adapt the framing if needed. Do not
   rewrite from scratch — the existing text carries decisions and constraints that may not be
   visible on the surface.

5. **One home.** After moving, the information exists in exactly one place. Remove it from the
   source. Never duplicate.

6. **Verify completeness.** After restructuring, step through the inventory and confirm every item
   landed in a destination or was confirmed derivable. An item with no destination is a gap to surface to
   the operator, not a reason to proceed.

**Consequence**: an agent that restructures docs without completing the inventory step first cannot
guarantee that no information was lost. Silent information loss is not detectable after the fact
without reading git history — and the next agent session will derive from the restructured docs,
not from what was dropped.

### What this means for specific operations

| Operation | Risk | Required step before proceeding |
|-----------|------|--------------------------------|
| Retiring a doc outside the required set | High — content may still be unique | Read in full; confirm every section is moved to its owner or confirmed derivable |
| Moving a TODO file | Low — structural only | Confirm the file is moving intact; verify links from docs/TODO.md index |
| Reshaping a mixed-concern doc | High — content splits across destinations | Full inventory; map each section to destination before touching the file |
| Renaming a doc to match contract path | Low — structural only | Update all links to the old path |

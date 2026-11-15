---
name: "retire-backlog"
description: "Retires a completed backlog anchor doc: folds its durable content into the owning doc, then archives or purges it with its docs/TODO.md row, as the operator decides. Invoke when the operator says retire/close/clean up a backlog, or when no open item remains in an anchor doc. SKIP: any open item remains."
---

# Skill: Retire Backlog

## Goal

Close a backlog that is fully complete, so spent tracking artefacts do not persist as dead weight that later sessions load and re-work.

## When to Invoke

- The operator says "retire `<doc>`", "close the backlog" or "clean up `<doc>`".
- The last open item of an anchor doc closes (continuity contract § Backlog Lifecycle).

## Procedure

1. **Verify completion.** Read the anchor doc. If any item is open or in progress, or waits on the operator, stop and report which; do not retire. Deferred or parked items are re-homed into another backlog as agreed with the operator (`DOCS_CONTRACT.md` → TODO File Structure).
2. **Fold durable content.** Move every decision, invariant or gotcha that lives only in the anchor doc into its owning doc (code, `docs/` or `ai_context/project/`). Dropped items are not folded.
3. **Archive or purge.** Ask the operator to choose archive or purge (`DOCS_CONTRACT.md` → TODO File Structure), then apply that choice to the anchor doc and its `docs/TODO.md` row.
4. **Repoint references.** For each inbound reference (`git grep -n <basename>`), repoint it: on archive, to the new path; on purge, to plain text "`<basename>` (retired; git `<hash>`)", where `<hash>` is the last commit that contains the file.
5. **Update indexes.** On purge, remove the doc from any other docs index that lists it (for example the root `README.md`); on archive, step 4 has already repointed it. `docs/TODO.md` is handled in step 3. A publication doc is not a tracker: leave it.
6. **Report.** Doc retired, git hash cited, what was folded and where, index changes, and that no open item was left behind.

## Reference

- Continuity contract: `ai_context/pco/governance/AI_ASSISTANT_BACKLOG_CONTINUITY.md`
- Backlog file structure: `ai_context/pco/governance/DOCS_CONTRACT.md` → TODO File Structure

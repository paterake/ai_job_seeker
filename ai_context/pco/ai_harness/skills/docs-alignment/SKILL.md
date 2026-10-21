---
name: "docs-alignment"
description: "Validates and fixes a repo or implementation's docs against the platform documentation contract. Invoke when creating a new repo/implementation, before publishing, or when docs may have drifted."
---

# Docs Alignment

This skill validates documentation against the platform contract,
`ai_context/pco/governance/DOCS_CONTRACT.md`. The contract owns every requirement; this skill only orders the
checks and the fixes.

## When to Invoke

- When creating a new governed repo or implementation (validate before first commit)
- When a significant refactor may have drifted docs from the contract
- Before publishing or sharing docs externally
- When asked to review whether a repo's docs are complete

## Validation Checklist

Check the repo against each DOCS_CONTRACT.md section in this order. A failure is a blocker.

1. **Core Doc Set**, including the † rule (`docs/TODO.md` may be absent once the backlog is closed) and the
   legacy command docs (`docs/RUNNERS.md`, `docs/ops/CLI.md`): a finding, not a blocker.
2. **Conditional Required**: check each trigger.
3. **TODO File Structure**.
4. **Segregation Rules**: apply "the test" to each doc.
5. **PRD Authoring Contract**: the shape is `ai_context/pco/governance/templates/PRD_TEMPLATE.md`.
6. **CONFIGURATION.md Code-Blind Definition**.
7. **Config Master-Data Is Referenced, Never Copied**.
8. **Extension Contract**: the discoverability rule.
9. **Multi-Implementation Repos** (if applicable): root RUNBOOK and CONFIGURATION are routing surfaces.

## Fix Strategy

**Before any file operation on an existing doc, inventory its content in full** (DOCS_CONTRACT.md →
Retrospective Refactor Safety). Skipping the inventory step produces silent information loss.

For each failing check:

1. **Required doc missing (greenfield)**: create it from the template shape. No inventory is needed.
2. **Required doc missing, but its content is in the wrong doc**: inventory the source doc, move the content
   to the new doc, and remove it from the source.
3. **Content in the wrong doc**: inventory, map each section to its destination, move one section at a time,
   and confirm the source no longer holds misplaced content.
4. **Superseded doc to retire**: read it in full, and confirm every section is in the canonical source or
   explicitly redundant. Then delete it; the commit history keeps it.
5. **TODO file misplaced or completed**: apply TODO File Structure, and update the `docs/TODO.md` index.
6. **PRD references implementation files**: rewrite those references as contract language.
7. **Extension doc undiscoverable**: link it from `ARCHITECTURE.md` or `README.md`; do not move the doc.
8. **Multi-implementation root docs too detailed**: move the implementation detail into each
   implementation's own docs, and leave pointers at the root.
9. **CONFIGURATION.md names code or CLI flags**: move the detail to its owning doc first if it exists nowhere
   else, then reduce the CONFIGURATION.md reference to a behavioural description.
10. **A doc copies a config-owned list**: replace the list with a link to its owning file.
11. **Legacy command doc present** (`docs/RUNNERS.md` or `docs/ops/CLI.md`): inventory it, move each command
    into `docs/RUNBOOK.md` under the task it serves (merging with any RUNBOOK text that already explains it),
    drop flag listings that `--help` already gives, then delete the legacy doc.

**Surface to the human (do not resolve unilaterally):**
- Content that does not clearly belong in any contract doc
- Content in a superseded doc that has no obvious canonical counterpart
- Any section where the right destination is ambiguous

## Suggested Commands

```bash
ls docs/
ls docs/todo/ 2>/dev/null
find . -name "TODO*.md" -not -path "*/todo/*" -not -path "*/.venv/*"
find . -name "PRD.md" -not -path "*/.venv/*"
```

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
- Before publishing
- When asked to review whether a repo's docs are complete

## Validation Checklist

Check the repo against each DOCS_CONTRACT.md section in this order. A failure is a blocker.

1. **Required Set**, including its † and ‡ rules, and any doc outside the set: a finding, not a blocker.
2. **TODO File Structure**.
3. **Multi-Implementation Repos** (if applicable): each implementation's files; root RUNBOOK and CONFIGURATION
   are routing surfaces.
4. **Segregation Rules**: apply "the test" to each file.
5. **Derivability Test**: apply it to each line of each file.
6. **INTENT.md Is Code-Blind**: the shape is `ai_context/pco/templates/INTENT_TEMPLATE.md`.
7. **CONFIGURATION.md Code-Blind Definition**.
8. **Config Master-Data Is Referenced, Never Copied**.

## Fix Strategy

**Before any file operation on an existing doc, inventory its content in full** (DOCS_CONTRACT.md →
Retrospective Refactor Safety). Skipping the inventory step produces silent information loss.

For each failing check:

1. **Required file missing (greenfield)**: create it; `INTENT.md` from the template shape. No inventory is needed.
2. **Doc outside the required set**: inventory it; for each item, confirm the code, config or `--help` shows it
   and drop it, or move it to its owner per DOCS_CONTRACT.md → Segregation Rules; fix links to it; then delete
   it. The commit history keeps it.
3. **Content in the wrong file**: inventory, map each section to its destination, move one section at a time,
   and confirm the source no longer holds misplaced content.
4. **A line restates what code shows** (fails the Derivability Test): confirm the code, config or `--help`
   actually shows it, then drop it. A line the code does not show is a constraint: keep it, or move it to its
   owner.
5. **TODO file misplaced or completed**: apply TODO File Structure, and update the `docs/TODO.md` index.
6. **INTENT.md names code**: rewrite those references as guarantees.
7. **Multi-implementation root docs too detailed**: move the implementation detail into each
   implementation's own files, and leave pointers at the root.
8. **CONFIGURATION.md names code or CLI flags**: move the detail to its owning file first if the code does not
   show it, then reduce the CONFIGURATION.md reference to a behavioural description.
9. **A doc copies a config-owned list**: replace the list with a link to its owning file.

**Surface to the operator (do not resolve unilaterally):**
- Content that does not clearly belong in any required file and is not derivable
- Any section where the right destination is ambiguous

## Suggested Commands

```bash
ls docs/ ai_context/project/
ls docs/todo/ 2>/dev/null
find . -name "TODO*.md" -not -path "*/todo/*" -not -path "*/.venv/*"
find . \( -name "PRD.md" -o -name "ARCHITECTURE.md" -o -name "AI.md" -o -name "EXECUTIVE-SUMMARY.md" \) -not -path "*/.venv/*"
git ls-files '*README.md' | grep -v -e '^README.md$' -e '^ai_context/'
```

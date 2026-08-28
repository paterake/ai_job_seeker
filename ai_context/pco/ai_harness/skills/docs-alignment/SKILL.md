---
name: "docs-alignment"
description: "Validates and fixes a repo or implementation's docs against the platform documentation contract. Invoke when creating a new repo/implementation, before publishing, or when docs may have drifted."
---

# Docs Alignment

This skill validates documentation against the platform contract at:

- `ai_context/pco/governance/DOCS_CONTRACT.md` — required doc set, segregation rules, PRD authoring standard, extension contract, TODO structure

## When to Invoke

- When creating a new governed repo or implementation (validate before first commit)
- When a significant refactor may have drifted docs from the contract
- Before publishing or sharing docs externally
- When asked to review whether a repo's docs are complete

## Validation Checklist

### 1) Core Doc Set

Confirm each required doc exists. Missing = blocker.

- [ ] `README.md`
- [ ] `PRD.md`
- [ ] `docs/ARCHITECTURE.md`
- [ ] `docs/RUNBOOK.md`
- [ ] `docs/CONFIGURATION.md`
- [ ] `docs/TODO.md` — required only while the module/repo has **open backlog**; permitted absent once `retire-backlog` has closed it (do not flag as a blocker in that case)
- [ ] `docs/RUNNERS.md` (accepts `docs/ops/CLI.md` as a legacy alias)

### 2) Conditional Required

Check each trigger. If trigger is true and doc is absent = blocker.

- [ ] Module owns AI-adjacent behaviour → `docs/AI.md` present?
- [ ] Implementation is product/stakeholder-facing → `docs/EXECUTIVE-SUMMARY.md` present?

### 3) TODO Structure

- [ ] `docs/TODO.md` is the only TODO file in the docs root
- [ ] Active initiative anchor docs are under `docs/todo/`
- [ ] Closed initiative docs are under `docs/todo/archive/` or deleted
- [ ] No `TODO_<X>.md` files sitting in the docs root

### 4) Segregation

For each doc, verify content is in the right place:

- [ ] Operational commands only in `docs/RUNNERS.md` (`docs/ops/CLI.md` accepted as a legacy alias; not inline in README or ARCHITECTURE)
- [ ] Run/recovery steps only in `docs/RUNBOOK.md` (not in README or ARCHITECTURE)
- [ ] Config keys only in `docs/CONFIGURATION.md` (not inline in code comments or ARCHITECTURE)
- [ ] Design and boundaries only in `docs/ARCHITECTURE.md`
- [ ] AI behaviour only in `docs/AI.md`
- [ ] Dataset/domain specifics only in `docs/use-cases/`
- [ ] Requirements and acceptance criteria only in `PRD.md`

### 5) PRD Contract

- [ ] PRD describes behaviours and contracts — not files, classes, or tests
- [ ] PRD contains no implementation file paths or function names
- [ ] PRD states what the module owns vs what it delegates
- [ ] PRD follows the template shape (`ai_context/pco/governance/templates/PRD_TEMPLATE.md`)
- [ ] Any determinism claims have explicit conditions stated
- [ ] Trust posture is stated (caps, rejection, degrade, retry bounds)

### 5b) CONFIGURATION.md Code-Blind

- [ ] CONFIGURATION.md contains no script/tool file paths, function/method/macro names, or CLI flags — only config/data file paths, key names, and their meaning/rationale

### 5c) Config Master-Data Referenced, Not Copied

- [ ] Docs reference config-owned lists by link (ingest tabs/sheets, per-stage source-table lists, thresholds) rather than enumerating them as prose — only stable contract identifiers and dated snapshots are named inline

### 6) Extension Docs

- [ ] Every extension doc (`SOURCE_HANDLING.md`, `LINEAGE.md`, etc.) is linked from `docs/ARCHITECTURE.md` or `README.md`
- [ ] No extension docs exist that are not reachable from an entry point

### 7) Multi-Implementation Repos (if applicable)

If the repo contains multiple named implementations:

- [ ] Root `docs/RUNBOOK.md` is a routing surface — no implementation-specific run steps
- [ ] Root `docs/CONFIGURATION.md` is a routing surface — no implementation-specific config keys
- [ ] Each implementation has its own `<implementation>/docs/RUNBOOK.md` and `<implementation>/docs/CONFIGURATION.md`

## Fix Strategy

**Before any file operation on an existing doc: inventory its content in full.**
See the Retrospective Refactor Safety section in `ai_context/pco/governance/DOCS_CONTRACT.md` for
the required sequence. Skipping the inventory step produces silent information loss.

For each failing check:

1. **Required doc missing (greenfield)** — create using the template shape (PRD: `ai_context/pco/governance/templates/PRD_TEMPLATE.md`; others: follow segregation rules). No inventory needed.
2. **Required doc missing (content exists elsewhere in wrong doc)** — inventory the source doc first; extract and move the relevant content to the new doc; remove it from the source. Do not duplicate.
3. **Content in the wrong doc** — inventory the doc; map each section to its correct destination; move sections one at a time; verify the source doc is empty of misplaced content before closing.
4. **Superseded doc to retire** — read in full; confirm every section is either present in the canonical source or explicitly redundant. Only then delete or archive.
5. **TODO file misplaced** — move intact to `docs/todo/` or `docs/todo/archive/`; update `docs/TODO.md` index. Structural move — no inventory needed.
6. **PRD references implementation files** — rewrite those references to contract language; preserve all non-implementation content.
7. **Extension doc undiscoverable** — add a link from `ARCHITECTURE.md` or `README.md`; do not move the doc.

8. **Multi-implementation repo — root RUNBOOK/CONFIGURATION too detailed** — convert to routing surfaces: strip implementation-specific content from root docs; confirm that content exists in (or move it to) each implementation's own `docs/RUNBOOK.md` and `docs/CONFIGURATION.md`. Root docs may only contain pointers and brief routing context.
9. **CONFIGURATION.md references script paths, function/method/macro names, or CLI flags** — distill the violating reference to a behavioural description, or replace it with a pointer to the doc that already owns that implementation detail (`ARCHITECTURE.md` for code structure, `RUNBOOK.md` for run/recovery steps, `RUNNERS.md` for CLI flags). Never delete the detail if it exists nowhere else — move it to its owning doc first, then distill the CONFIGURATION.md reference.
10. **Doc copies a config-owned list instead of linking it** — replace the enumerated list (ingest tabs/sheets, per-stage source-table lists, thresholds) with a one-line relative link to its owning file (ingest JSON / `*_base.sql`); keep only the stable model description inline. Leave stable contract identifiers and dated point-in-time snapshots (paired with their regeneration command) as-is.

**Surface to human (do not resolve unilaterally):**
- Content that does not clearly belong in any contract doc
- Content that appears in a superseded doc and has no obvious canonical counterpart
- Any section where the right destination is ambiguous

## Suggested Commands

```bash
ls docs/
ls docs/todo/ 2>/dev/null
ls docs/todo/archive/ 2>/dev/null
find . -name "TODO*.md" -not -path "*/todo/*" -not -path "*/.venv/*"
find . -name "PRD.md" -not -path "*/.venv/*"
```

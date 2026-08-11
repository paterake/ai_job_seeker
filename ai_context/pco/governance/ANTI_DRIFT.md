# Anti-Drift Contract (Single Source of Truth)

## Purpose

Prevent documentation drift and stale duplication across:
- assistant-facing context (`ai_context/`)
- human-facing docs (`docs/`)
- operational scripts (`scripts/`)

This is a governance contract for the agent harness.

## Canonical Sources (what is authoritative)

### Operational semantics

- `ai_context/pco/governance/CONTRACT.md` is the canonical source for:
  - what the harness manages
  - what “sync” means (scope, non-destructive defaults, pruning)
  - what a target repo must look like to be harness-wired

### Commands

- `docs/ops/CLI.md` is the canonical source for commands a human should run.
- `docs/ops/CLI.md` must not restate behavioural semantics; it links to `ai_context/pco/governance/CONTRACT.md`.

### Documentation contract

- `ai_context/pco/governance/DOCS_CONTRACT.md` is the canonical source for:
  - the required doc set per repo/implementation
  - segregation rules (what each doc owns)
  - PRD authoring standard
  - extension contract (when and how to add docs beyond the core set)
  - TODO file structure
- `ai_context/pco/governance/templates/PRD_TEMPLATE.md` is the canonical PRD shape — referenced by `DOCS_CONTRACT.md`.
- Temporal currency (keep docs in sync with code changes) is a thin ambient rule in `ai_context/pco/ai_harness/rules/governance.md`.
- `ai_context/pco/ai_harness/skills/docs-alignment/SKILL.md` is the procedural skill for validating a repo against this contract.

### Human model

- `ai_context/pco/` contains the canonical governance narratives: spoke READMEs per domain + hub at `ai_context/pco/governance/HUB.md`.
- `docs/README.md` is an index; it must not duplicate the operating model.

### Assistant-facing posture

- `ai_context/ASSISTANTS.md` is the canonical assistant entrypoint (what to read first, what matters).
- It should link to deeper files rather than duplicating their contents.

## Edit Rules (what must update together)

### If you change a script under `scripts/`

- If the change affects how a human runs the system, update `docs/ops/CLI.md` in the same change set.
- If the change affects sync semantics or target repo shape, update `ai_context/pco/governance/CONTRACT.md` in the same change set.

### If you change `ai_context/pco/governance/CONTRACT.md`

- Update `docs/ops/CLI.md` only if commands or flags changed.
- Otherwise keep `docs/ops/CLI.md` unchanged and rely on linking to avoid drift.

### If you change `ai_context/pco/governance/DOCS_CONTRACT.md`

- If the PRD template shape changes, update `ai_context/pco/governance/templates/PRD_TEMPLATE.md` in the same change.
- If validation steps change, update `ai_context/pco/ai_harness/skills/docs-alignment/SKILL.md` in the same change.

### If you change anything under `ai_context/`

- `ai_context/` is prescriptive and assistant-facing. `docs/` is narrative and human-facing. A rule change with no corresponding doc update leaves humans and assistants out of sync.
- Identify which governance area the change impacts (Agent Management wheel domain).
- Update the corresponding spoke narrative under `ai_context/pco/<spoke>/README.md` to reflect the change.
- If the change alters posture or operating model, also update `docs/PRD.md` in the same response.

## Drift Tests

Before considering a change “done”:
- There is exactly one canonical place that defines each behavioural contract.
- Any other place that mentions it is either a link or a one-line pointer.

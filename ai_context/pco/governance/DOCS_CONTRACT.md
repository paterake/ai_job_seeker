# Documentation Contract

## Why This Matters

Inconsistent documentation is a navigation failure, not a style problem. An agent or engineer
entering an unfamiliar repo cannot determine scope, run the module, understand design decisions, or
identify what is still planned without reading source code. The consequence is re-derivation: the
agent reconstructs context from code instead of reading a stated contract, burning tokens, introducing
drift, and producing implementations that do not honour existing invariants.

This contract defines the floor. Implementations must meet it before adding further docs.

Invoke `docs-alignment` to validate a repo or implementation against this contract.

---

## Core Doc Set (Required — Every Repo and Implementation)

Missing any of these is a blocker, not a backlog item.

| Doc | Owns | Consequence if absent |
|-----|------|-----------------------|
| `README.md` | Navigation and 2-minute orientation | No canonical entry point; agent reads code instead of contracts |
| `PRD.md` | Intent, scope, contracts, acceptance criteria | No verifiable success criteria; implementation rework is undetectable |
| `docs/ARCHITECTURE.md` | Components, data flow, design decisions, responsibility boundaries | Agent cannot rebuild functionality without reading source; boundaries become implicit |
| `docs/RUNBOOK.md` | Installation, commands, diagnosis, recovery | Operator cannot run or recover the module without reading code |
| `docs/CONFIGURATION.md` | Config keys, defaults, rationale — [code-blind](#configurationmd-code-blind-definition) | Domain values leak into code; reuse across datasets requires code changes |
| `docs/TODO.md` † | Project backlog index — open initiatives with pointers to anchor docs, completed section | Backlog continuity breaks; completed items re-enter scope; sessions re-derive state |
| `docs/RUNNERS.md` | Operational command reference — install, run, diagnose, utility commands (accepts `docs/ops/CLI.md` as a legacy alias) | No canonical command surface; humans and assistants derive commands from code or scattered notes, producing drift and support burden |

† **`docs/TODO.md` is required only while the module (or repo) has open backlog.** Once
`retire-backlog` has closed the backlog and removed the file, its absence is permitted and must not
be treated as a blocker. A missing `docs/TODO.md` is a violation only when the module still has open
backlog items (e.g. an Alpha module with open maturity gaps). This reconciles the contract with the
`retire-backlog` skill, which deletes `docs/TODO.md` on completion — an intentional retirement and a
drift defect are otherwise indistinguishable to `docs-alignment`.

### Conditional Required

Create these when the trigger applies. If the trigger is true and the doc is absent, treat it as a blocker.

| Doc | Trigger | Consequence if absent |
|-----|---------|----------------------|
| `docs/AI.md` | Module owns AI-adjacent behaviour (LLM calls, RAG pipelines, embeddings, degrade modes, eval hooks, similarity thresholds) | Tuning surface is invisible and ungoverned; an agent cannot reason about quality, cost, or degrade modes |
| `docs/EXECUTIVE-SUMMARY.md` | Implementation is product-facing or stakeholder-facing | Non-technical readers have no entry point; value and differentiators are buried in spec language; stakeholder alignment depends on reading the PRD |

### TODO File Structure

`docs/TODO.md` is the single project backlog index — the only TODO file in the `docs/` root.
All other TODO files are filed under `docs/todo/`.

| Location | Purpose |
|----------|---------|
| `docs/TODO.md` | Open initiatives (pointer + status) and completed section. One file, root only. |
| `docs/todo/<initiative>.md` | Active anchor docs for named multi-session initiatives. Session continuity artefacts. |
| `docs/todo/archive/` | Closed initiative anchor docs. Retained briefly for reference; delete when no longer needed — git holds the history. |

**Consequence**: named `TODO_<X>.md` files in the docs root make it impossible to distinguish the
live backlog from session artefacts and historical records at a glance.

**Implementation-level TODOs** belong within the implementation's own directory (`<implementation>/docs/TODO.md`), never in the project root.

---

## Multi-Implementation Repos (Root Docs Posture)

When a repo contains multiple named implementations (e.g., `impl_a/`, `impl_b/`), the root core doc
set still applies — but `docs/RUNBOOK.md` and `docs/CONFIGURATION.md` at the root are routing surfaces,
not implementation docs.

**Routing surface rule (non-negotiable):**
- Root `docs/RUNBOOK.md` — routes to implementation-level runbooks. Contains no implementation-specific
  install steps, commands, or recovery procedures.
- Root `docs/CONFIGURATION.md` — routes to implementation-level config docs. Contains no
  implementation-specific keys, defaults, or rationale.

Implementation detail belongs in `<implementation>/docs/RUNBOOK.md` and
`<implementation>/docs/CONFIGURATION.md` — these are the canonical locations for that implementation's
run and config content.

**Consequence of violation**: a root doc that accumulates implementation detail becomes a god-doc. It
drifts independently of each implementation's own docs and no single source of truth exists — an operator
cannot determine whether the root doc or the implementation doc is authoritative.

**The test**: does the root doc contain content a reader could only answer by reading a specific
implementation? If yes, it has become a duplicate, not a routing surface.

---

## Segregation Rules (What Each Doc Owns)

Hard boundaries. Content in the wrong doc forces readers to search multiple files for a single answer
and produces invisible duplication that drifts independently.

- **Operational commands** (install, run, diagnose, utility) → `docs/RUNNERS.md` only (`docs/ops/CLI.md` accepted as a legacy alias). Never inline in README or ARCHITECTURE.
- **Run and recovery** → `docs/RUNBOOK.md` only. Never in README or ARCHITECTURE.
- **Config keys and their rationale** → `docs/CONFIGURATION.md` only. Never inline in code comments or ARCHITECTURE.
- **Technical design and module boundaries** → `docs/ARCHITECTURE.md` only. Never in README or RUNBOOK.
- **AI behaviour** (LLM tuning, degrade modes, eval hooks, thresholds) → `docs/AI.md` only.
- **Dataset and domain specifics** → `docs/use-cases/` only. Never in framework-level docs.
- **Requirements and acceptance criteria** → `PRD.md` only. Never in ARCHITECTURE or README.

**The test**: can a reader answer their question from exactly one doc? If not, the segregation is broken.

---

## PRD Authoring Contract

A PRD is not documentation about code. It is a contract — it defines what must exist and what must
be true, independent of how the implementation achieves it. An agent building a module must be able
to reconstruct the module's behaviour from the PRD alone, without reading source files.

### Non-Negotiables

- **Contract-first**: describe what the module guarantees (inputs/outputs, invariants, constraints),
  not how it is implemented.
- **Code-blind**: do not reference implementation file paths, function names, or test file names.
  PRDs are the spec; code is one possible realisation.
- **Boundary-explicit**: state what the module owns vs what it delegates to other modules or shared
  platform primitives. Unowned behaviour silently becomes undefined behaviour.
- **Determinism where promised**: if the module claims deterministic outputs, state the conditions
  under which determinism holds (same inputs + config + environment ⇒ same outputs).
- **Trust posture**: state caps, safety boundaries, and failure behaviour. What is rejected? What is
  degraded? What is retried, and how many times?

### Shape

Follow the template at `ai_context/pco/governance/templates/PRD_TEMPLATE.md`. The template is the canonical shape;
inline variations accumulate inconsistency.

### Common PRD Failure Modes (Prohibited)

- Listing files, classes, or tests instead of describing behaviours and contracts.
- Duplicating shared platform primitives (AIOps/LLMOps plumbing) inside module PRDs — inherit and reference.
- Making claims without their conditions ("deterministic" without defining the determinism conditions).
- Mixing dataset or use-case specifics into domain-neutral module PRDs.
- "Verified against code" language — PRDs state intent; code is the verification.

---

## CONFIGURATION.md Code-Blind Definition

`CONFIGURATION.md` may reference config/data file paths (YAML, XLSX, config directories) and the
config keys themselves. It must not reference source-code file paths, script names,
function/method/macro names, or CLI flags — those belong in `ARCHITECTURE.md`, `RUNBOOK.md`, or
`RUNNERS.md` respectively.

**Consequence if violated**: implementation detail embedded in the config doc drifts independently
of the code it names, and the same detail duplicates across `CONFIGURATION.md` and its actual
owning doc — the two copies silently disagree the next time either one changes.

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

## Extension Contract (Beyond the Core Set)

The core set is the floor, not the ceiling. Create a supporting doc when any trigger is true:

| Trigger | Supporting doc |
|---------|---------------|
| Module handles multiple source types with different parsing strategies | `docs/SOURCE_HANDLING.md` |
| Module owns lineage or versioning rules with complex re-run conditions | `docs/LINEAGE.md` |
| Module has a high deterministic failure surface (schema drift, parsing quirks, corrupted caches) | `docs/TROUBLESHOOTING.md` |
| Module owns input/output schemas and compatibility guarantees | `docs/DATA_CONTRACTS.md` |

**Discoverability rule**: every extension doc must be linked from `docs/ARCHITECTURE.md` (or
`README.md` if it is operator-first). A doc that exists but is not reachable from an entry point is
treated as missing — an agent will not find it and will re-derive its contents.

---

## Retrospective Refactor Safety

Applying this contract to existing docs (retrospective alignment) is a content operation, not a
structural tidy. Existing docs contain information that must not be lost. The process is strictly
ordered — deviation produces silent information loss.

### Required sequence (non-negotiable)

1. **Inventory first.** Read every doc being changed in full before any file operation. List what
   information each doc contains — not its title, its actual content.

2. **Map every item.** For each piece of information in the inventory, identify the destination doc
   per the segregation rules. If no clear destination exists, flag it for human review — do not
   decide unilaterally and do not drop it.

3. **Move, never drop.** Content in the wrong doc is moved to the correct doc. It is never deleted
   because it is in the wrong place.

4. **Distill, never rewrite.** Preserve existing content; adapt the framing if needed. Do not
   rewrite from scratch — the existing text carries decisions and constraints that may not be
   visible on the surface.

5. **One home.** After moving, the information exists in exactly one place. Remove it from the
   source. Never duplicate.

6. **Verify completeness.** After restructuring, step through the inventory and confirm every item
   landed in a destination. An item with no destination is a gap to surface to the human, not a
   reason to proceed.

**Consequence**: an agent that restructures docs without completing the inventory step first cannot
guarantee that no information was lost. Silent information loss is not detectable after the fact
without reading git history — and the next agent session will derive from the restructured docs,
not from what was dropped.

### What this means for specific operations

| Operation | Risk | Required step before proceeding |
|-----------|------|--------------------------------|
| Retiring a superseded doc | High — content may still be unique | Read in full; confirm every section is either duplicated in the canonical source or explicitly redundant |
| Moving a TODO file | Low — structural only | Confirm the file is moving intact; verify links from docs/TODO.md index |
| Creating a pointer doc | Low — additive only | No inventory needed; pointer docs contain no original content |
| Reshaping a mixed-concern doc | High — content splits across destinations | Full inventory; map each section to destination before touching the file |
| Renaming a doc to match contract path | Low — structural only | Update all links to the old path |

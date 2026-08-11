# ai_context Contract — ai_agent_pco

## Purpose

`ai_context/` is the canonical, versioned context layer for all assistants (Claude, Qwen, Trae) operating in this repository, and the **superset** that can be synced into other repositories.

This is an operational surface, not “documentation”. It is the continuity layer that governs assistant behaviour and makes runs reproducible.

## Anti-Drift (Single Source of Truth)

This repo explicitly avoids duplicating “the same truth” across multiple files.

- The anti-drift rules live in [ANTI_DRIFT.md](ANTI_DRIFT.md).
- When behaviour changes, update the canonical source and keep other references as links/pointers.

## What is Managed Here

- Shared assistant entrypoint: `ai_context/ASSISTANTS.md` (dispatcher) → `ai_context/pco/ASSISTANTS.md` + `ai_context/project/ASSISTANTS.md`
- Concern framing: `ai_context/pco/governance/CONCERNS.md`
- Shared harness tooling: `ai_context/pco/ai_harness/`
  - `hooks/` deterministic guardrails
  - `rules/` rule files and posture constraints
  - `skills/` procedural skills and tooling definitions (PCO-universal skills only; PCO-specific skills live in `project/`)

## What a Target Repo Must Look Like

For a target repo to be “harness-wired”, it must have a **two-layer `ai_context/`** structure:

```
<repo>/ai_context/
  ASSISTANTS.md          ← repo-specific router and active backlog (repo-owned, never synced)
  pco/                   ← synced wholesale from ai_agent_pco/ai_context/ (platform-owned, read-only)
    ai_harness/          ← platform hooks, rules, skills
    governance/          ← platform governance contracts
    ...                  ← all other platform spokes
  project/               ← this repo’s additions only (mirrors spoke structure)
    ai_harness/          ← repo-specific skills (additive; no overrides)
    governance/          ← REPO_CONTRACT.md and repo-specific governance docs
    ...                  ← any spoke with repo-specific content
```

Additionally:

- `.claude/{hooks,rules}` symlinked to `../ai_context/pco/ai_harness/{hooks,rules}`
- `.claude/skills/` is a **real directory** of per-skill symlinks — managed by `distill_harness.py wire`. PCO skills point into `pco/ai_harness/skills/`; project skills point into `project/ai_harness/skills/`. Project skills override PCO skills on name collision.
- Same wiring applies to `.qwen/` and `.trae/`
- Root entrypoints `CLAUDE.md`, `QWEN.md`, `TRAE.md` pointing to `ai_context/ASSISTANTS.md`

**Why two layers:** `pco/` is a clean platform namespace that can be blown away and resynced without risk. `project/` is repo-owned and a sync never touches it. This eliminates namespace collision and makes the `PROTECTED_FILES` exclusion mechanism unnecessary.

## Conformance (Strict Structural Parity)

To prevent interpretive “mapping” and drift, governed repos must match the **ai_agent_pco `ai_context/` structure**, not just the intent.

Within `ai_context/pco/`, the allowed entries are:

- `ASSISTANTS.md`
- `ai_harness/`
- `governance/`
- `architecture/`
- `assurance/`
- `behaviour/`
- `integration/`
- `knowledge/`
- `lineage/`
- `master-data/`
- `observability/`
- `operations/`
- `security/`

Spoke folders may be empty or pointer-only, but they must exist so that project context can be filed deterministically.

Objective test:
- A repo is conformant when `distill_harness.py validate --scope full` reports zero differences.

Refactor rule:
- If a project needs context that does not fit an existing spoke, that is a platform gap. Add/rename a spoke in `ai_agent_pco` first, then refactor projects to match.

## Downstream Conformance Contract (Semantic)

Structural parity is necessary but not sufficient. Every downstream governed repo must also declare semantic conformance in:

- `ai_context/project/governance/REPO_CONTRACT.md`

Minimum required sections:

- `## Additive Content Map`
- `## Additive-Only Acknowledgment`
- `## Sensor Layer Declaration`
- `## Guide/Sensor Coherence Map`

The Additive Content Map must include a markdown table whose first column is `Spoke`. Each `Spoke` value must map to a canonical platform spoke (one of the `ai_context/` spoke folder names) or `harness`.

## Sync Behaviour

The sync tool is [distill_harness.py](../../../scripts/distill_harness.py).

Key principles:
- Prune is **on by default**: within the selected scope, target-only files under `ai_context/pco/` are removed so the platform namespace is deterministic. Use `--no-prune` to disable pruning when explicitly instructed.
- Sync target is `<repo>/ai_context/pco/` — the platform namespace only. `ai_context/project/` and `ai_context/ASSISTANTS.md` are repo-owned and are never touched by sync.
- Sync is **scoped**:
  - `--scope harness` syncs only `ai_context/pco/ai_harness/`
  - `--scope governance` syncs `ai_context/pco/governance/`
  - `--scope full` syncs the full `ai_context/pco/` tree

## How This Applies Across Repos

The harness is shared and `ai_context/` structure is fixed. Repo differences exist as content within the same spoke folders (and are explained by `ai_context/pco/governance/CONCERNS.md`), not as ad-hoc structure changes.

## Special Case: `ai_agent_core`

`ai_agent_core` is a governed repo and must be harness-wired exactly like other governed repos.

Its position is distinct:

- It **conforms** to `ai_agent_pco` structure and hub/spoke policy
- It **implements** the shared sensor substrate that downstream repos consume as a pinned dependency

As a result, its conformance declarations are not “additive only”. It must declare what platform contracts it implements and how those implementations are regression-protected and rolled out without breaking downstream consumers unexpectedly.

## Change Control (Policy Anchor)

- A governance change without a traceable source is not accepted.
- If external research justifies a governance change, the change proposal must record sources (URL + retrieval date) and claim summaries being relied on.
- Enforcement anomalies (false positive/false negative) trigger review and an explicit governance decision, not just logging.
- Rules are examined at a regular cadence regardless of triggers; the cadence record is part of governance evidence.
- Policies are versioned and rolled out deliberately; unreviewed or “floating” governance changes are prohibited.
- Tier 3/4 capability changes require a traceable approval record artefact; the record is stored in `audit/approvals/` (using `audit/templates/approval_record.md`) and referenced from the change evidence (e.g., capability registry `evidence` field or the change proposal).

## Exceptions (Registry Contract; Pending Enforcement)

- Exceptions are time-bounded, attributable (owner + justification), and scoped; informal exceptions are prohibited.
- Each governed repo maintains an exception registry at `ai_context/project/governance/exception_registry.yaml`.
- Any exception used by a run is referenced by stable identifier in the run lineage manifest.

Minimum registry fields:

- `id`
- `rule` (canonical reference to the rule/contract being excepted)
- `justification`
- `owner`
- `granted_by`
- `granted` (date)
- `expires` (date)
- `scope` (explicit boundary)
- `status` (`active` | `expired` | `revoked`)
- `evidence` (link or pointer to the approval/evidence record)

## Capability Lifecycle (Registry Contract; Pending Enforcement)

- New agent capabilities (new tool classes, new model capabilities, new harness patterns) enter the platform through a defined lifecycle.
- Capabilities are tracked in a registry with lifecycle stage and supporting evidence.
- Tier 3/4 capabilities must not be adopted while `stage` is `experimental` unless the adopting repo records a capability adoption escalation in `ai_context/project/governance/REPO_CONTRACT.md` under `## Capability Adoption Escalations`.
- Deprecated capabilities must not be newly adopted; existing uses must be paired with an explicit migration path and timeline in `ai_context/project/governance/REPO_CONTRACT.md`.

Minimum registry fields:

- `name`
- `tier`
- `stage` (`experimental` | `emerging` | `established` | `deprecated`)
- `stage_since` (date)
- `owner`
- `evidence`

## Policy Packs (Registry and Rollout Contract; Pending Enforcement)

- Policy packs have stable identifiers and semantic versions; changes without an upgrade path are prohibited for shared surfaces.
- A policy pack registry records policy pack identity, versions, ownership, applicability, and rollout state.
- Rollouts include a verification plan (rule, hook, test, eval, sensor) and an explicit change source.

Intended storage (platform-owned):

- `ai_context/pco/governance/policy_pack_registry.yaml`

## Conformance Declarations (ai_agent_core; Pending Enforcement)

`ai_agent_core` must declare which platform contracts it implements and how conformance is continuously validated.

Minimum required declaration shape (in `ai_context/project/governance/REPO_CONTRACT.md`):

- `## Platform Contract Implementations`
- A table with: `Contract`, `Implementation`, `Continuous Validation`, `Rollout/Compatibility`

# ai_context Contract

## Purpose

`ai_context/` is the canonical, versioned context layer for the agent working in a governed repo. Its `pco/` layer is
authored once in `ai_agent_pco` (the **superset**) and synced into every governed repo.

This is an operational surface, not “documentation”. It is the continuity layer that governs assistant behaviour and makes runs reproducible.

## Anti-Drift (Single Source of Truth)

A governed repo avoids duplicating “the same truth” across multiple files.

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
  ASSISTANTS.md          ← router to the pco/ and project/ indexes (repo-owned, never synced)
  pco/                   ← synced wholesale from ai_agent_pco/ai_context/pco/ (platform-owned, read-only)
    ai_harness/          ← platform hooks, rules, skills
    governance/          ← platform governance contracts
    ...                  ← all other platform spokes
  project/               ← this repo’s additions only (mirrors spoke structure)
    ai_harness/skills/   ← repo-specific skills (additive: never reuse a PCO skill's name)
    governance/          ← REPO_CONTRACT.md and repo-specific governance docs
    ...                  ← any spoke with repo-specific content
```

Additionally:

- The agent's configuration links its rules to `ai_context/pco/ai_harness/rules`, and its skills one by one: PCO
  skills into `pco/ai_harness/skills/`, project skills into `project/ai_harness/skills/`. A project skill that
  reuses a PCO skill's name shadows it (the project link wins), which overrides a platform skill locally: name it
  differently. Only skills are wired from the project layer; its rules and hooks are not. Its pre-tool-use hooks run the agent-neutral gates in
  `ai_context/pco/ai_harness/hooks/` through an agent adapter kept in the agent's configuration, outside
  `ai_context/`. The PCO repo's sync tooling manages the links and installs the adapter.
- The repo's agent entrypoint loads the always-loaded core from the synced layer (`ai_context/pco/AGENTS.md`) and
  routes to `ai_context/ASSISTANTS.md`; there is no root copy of the core. The entrypoint is repo-owned and sync
  never writes it.
- One agent is wired; which entrypoint and configuration folder it uses is set in `ai_agent_pco`'s wiring
  configuration, never in `ai_context/`. Other agents read the committed context their own way; the PCO does not
  wire or validate them.
- Content under `ai_context/` is agent-agnostic: it names no specific agent and never refers back to the agent
  entrypoint or configuration folder. **Consequence:** governance that names one agent is coupled to that vendor,
  and a consumer that runs a different agent reads instructions that do not apply to it.

**Why two layers:** `pco/` is a clean platform namespace that can be blown away and resynced without risk. `project/` is repo-owned and a sync never touches it. This eliminates namespace collision, so no protected-file list is needed.

## Conformance (Strict Structural Parity)

To prevent interpretive “mapping” and drift, governed repos must match the **ai_agent_pco `ai_context/` structure**, not just the intent.

Within `ai_context/pco/`, the allowed entries are `ASSISTANTS.md`, `AGENTS.md`, `ai_harness/`, `governance/`,
`templates/`, and one folder per spoke, as listed in the spoke index ([ASSISTANTS.md](../ASSISTANTS.md)). The
index, the spoke folders and the rules' `spoke:` frontmatter must agree.

Spoke folders may be empty or pointer-only, but they must exist so that project context can be filed deterministically.

Objective test:
- A repo is conformant when the PCO repo's `validate --scope full` reports zero differences for it.

Refactor rule:
- If a project needs context that does not fit an existing spoke, that is a platform gap. The spoke is added or renamed in `ai_agent_pco` first (from a consumer: report the gap upstream, [AGENTS.md](../AGENTS.md) → Governance changes), then projects are refactored to match.

## Downstream Conformance Contract (Semantic)

Structural parity is necessary but not sufficient. Every downstream governed repo must also declare semantic conformance in:

- `ai_context/project/governance/REPO_CONTRACT.md`

Minimum required sections:

- `## Additive Content Map`
- `## Additive-Only Acknowledgment`
- `## Sensor Layer Declaration`
- `## Guide/Sensor Coherence Map`

The Additive Content Map must include a markdown table whose first column is `Spoke`. Each `Spoke` value must map to a canonical platform spoke (one of the `ai_context/` spoke folder names) or `harness`.

A consumer references the PCO only from its agent layer, in three ways:
- Load: the agent entrypoint loads the core (`ai_context/pco/AGENTS.md`).
- Navigation: entrypoint → `ai_context/ASSISTANTS.md` → `pco/ASSISTANTS.md` or `project/ASSISTANTS.md`; a file under
  `ai_context/project/` may name the PCO doc its task needs.
- Wiring: the agent configuration's links into `ai_context/pco/ai_harness/`.

Product artefacts (code, config, tests, implementation docs, PRDs, `docs/TODO.md`) state their own reasoning and
do not cite PCO paths. Exempt: dated audit and decision records; an upstream gap report until it is lodged; and
anchor docs under `docs/todo/`, which are session records of agent work and are deleted when their initiative
closes.
**Consequence:** a PCO rename or restructure breaks every consumer doc that cites it (dozens of consumer files on 2026-10-21).

## Sync Behaviour

The sync tool is `scripts/distill_harness.py` in the PCO repo.

Key principles:
- Prune is **on by default**: within the selected scope, target-only files under `ai_context/pco/` are removed so the platform namespace is deterministic. Use `--no-prune` to disable pruning when explicitly instructed.
- Sync target is `<repo>/ai_context/pco/` — the platform namespace only. `ai_context/project/` and `ai_context/ASSISTANTS.md` are repo-owned and are never touched by sync.
- Sync is **scoped**:
  - `--scope harness` syncs `ai_context/pco/ASSISTANTS.md`, `AGENTS.md` and `ai_harness/`
  - `--scope governance` syncs `ai_context/pco/ASSISTANTS.md`, `AGENTS.md` and `governance/` (the `master-data/` registries are not in this scope; use `--scope full`)
  - `--scope full` syncs the full `ai_context/pco/` tree

## How This Applies Across Repos

The harness is shared and `ai_context/` structure is fixed. Repo differences exist as content within the same spoke folders (and are explained by `ai_context/pco/governance/CONCERNS.md`), not as ad-hoc structure changes.

## Special Case: `ai_agent_core`

`ai_agent_core` is a governed repo and must be harness-wired exactly like other governed repos.

Its position is distinct:

- It **conforms** to `ai_agent_pco` structure and hub/spoke policy
- It **implements** the shared sensor substrate that downstream repos consume as a pinned dependency

As a result, its conformance declarations are not “additive only”. It must declare what platform contracts it implements and how those implementations are regression-protected and rolled out without breaking downstream consumers unexpectedly, in its `ai_context/project/governance/REPO_CONTRACT.md` under `## Platform Contract Implementations`: a table with `Contract`, `Implementation`, `Continuous Validation`, `Rollout/Compatibility`.

## Change Control (Policy Anchor)

- Traceable sources, review triggers, cadence and the change process: [HUB.md](HUB.md) → PCO Evolution Model.
- Tier 3/4 capability changes require a traceable approval. A PCO-owned capability is approved by its entry in the PCO capability registry. A repo-owned one needs an approval record in that repo's `audit/approvals/` (template `ai_context/pco/templates/approval_record.md`), referenced from the change evidence.

## Exceptions (Registry Contract)

- Exceptions are time-bounded, attributable (owner + justification), and scoped; informal exceptions are prohibited.
- Each governed repo maintains an exception registry at `ai_context/project/governance/exception_registry.yaml`.
- An exception used by a run is bound to it as `lineage.md` → Lineage and Evidence requires.

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

## Capability Lifecycle (Registry Contract)

- New agent capabilities (new tool classes, new model capabilities, new harness patterns) enter the platform through a defined lifecycle.
- Capabilities are tracked in a registry with lifecycle stage and supporting evidence.
- Tier 3/4 capabilities must not be adopted while `stage` is `experimental` unless the adopting repo records a capability adoption escalation in `ai_context/project/governance/REPO_CONTRACT.md` under `## Capability Adoption Escalations`.
- Deprecated capabilities must not be newly adopted; existing uses must be paired with an explicit migration path and timeline in `ai_context/project/governance/REPO_CONTRACT.md`.

| Stage | Meaning |
|---|---|
| **Experimental** | Exists; not yet governed. Anything not in the registry is treated as experimental. |
| **Emerging** | A provisional rule exists; not yet tested against adversarial cases |
| **Established** | A rule tested against adversarial cases covers it; available to all governed repos |
| **Deprecated** | Being retired; no new adoption; existing uses need a migration path and timeline |

Progression is by human review.
- **Experimental → Emerging**: a rule exists and the risk is understood
- **Emerging → Established**: tested against adversarial cases; no open named gap for it in the covering spoke
- **Established → Deprecated**: superseded, unacceptable risk, or no longer used

Minimum registry fields:

- `name`
- `tier`
- `stage` (`experimental` | `emerging` | `established` | `deprecated`)
- `stage_since` (date)
- `owner`
- `evidence`

## Policy Packs (Registry and Rollout Contract)

- Policy packs have stable identifiers and semantic versions; changes without an upgrade path are prohibited for shared surfaces.
- A policy pack registry records policy pack identity, versions, ownership, applicability, and rollout state.
- Rollouts include a verification plan (rule, hook, test, eval, sensor) and an explicit change source.

Storage (platform-owned): `ai_context/pco/governance/policy_pack_registry.yaml`.

What each registry contract checks, and what it does not: [master-data spoke](../master-data/README.md).

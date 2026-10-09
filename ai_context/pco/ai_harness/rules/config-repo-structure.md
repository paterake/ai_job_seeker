---
description: Structure discipline for configuration / use-case-realization repos — fixed homes for config, docs, backlog, and glue; no haphazard root accumulation. Loaded when creating or moving files in a config/use-case repo.
globs:
  - "**/*"
basis: operational-experience
---

# Config-Repo Structure

A configuration / use-case-realization repo — a downstream repo that holds config, prompts, docs,
and glue for the platform, **not** mechanism code — must be organised to a fixed structure, not
filled by whatever path is convenient in the moment.

## Fixed Homes (Required)

- `cfg/` — runtime configuration the platform reads (config files and config trees).
- `docs/` — human-facing docs. `docs/todo/` holds active backlog anchors; `docs/todo/archive/`
  holds completed ones.
- `scripts/` — project glue only. Mechanism code lives in the platform repo, never here.
- Root holds **only** `README.md` plus these folders. No loose config, docs, or backlog files at
  the root.

## Placement Discipline

- Decide a new file's home from this structure **before** creating it. If none fits, stop and ask —
  do not drop it at the root.
- **One operator manual per use case.** Do not create a second runbook / command sheet that competes
  with it; extend the one that exists.
- **No data-plane or rebuildable artefacts in git** — they live in the data plane and are
  regenerated, never committed.
- **Deprecated material is removed** (or quarantined for an operator to delete), never left in place
  beside live material.

**Consequence:** an agent that takes the convenient path and dumps files at the root produces a repo
that is unnavigable, hides deprecated material behind live material, and defeats the config-driven
reuse the platform exists for. Observed in the 2026-09 MOAS config-repo cleanup, where an accreted
root of loose config, backlog, and retired-pipeline artefacts had to be reorganised wholesale.

Downstream repos own their own layout, but this structure is the default a coding agent must apply
and preserve; a deviation requires an explicit, recorded decision. This is the repo-level companion
to Config Purity and One-Responsibility-Per-File in `governance.md`.

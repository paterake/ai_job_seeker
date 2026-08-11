---
description: Governance rules for config purity, reuse, and safe publishing posture. Loaded when editing code or configuration.
globs:
  - "**/*.py"
  - "**/*.yaml"
  - "**/*.yml"
---

> Governance narrative: [integration spoke](../../integration/README.md)

# Governance Rules — Config Purity and Reuse

## Config Purity

- Domain strings, entity names, dataset identifiers, thresholds, and prompt text must not be hard-coded in source code.
- If a string would change when adopting a new dataset or domain, it belongs in configuration, not code.
- Treat code as reusable mechanism. Treat domain context as configuration and context-layer inputs; do not bake domain assumptions into implementations.

**Config directory structure:**
- `config/` — runtime config YAMLs (entity lists, thresholds, data paths, tuning params)
- `config/prompts/` — LLM prompt YAMLs (one file per prompt, named by purpose)

## Python Tooling (UV Only)

- For Python dependency and environment management, use `uv`.
- Do not introduce `pip`/`requirements.txt`, Poetry, Pipenv, Conda, or ad-hoc virtualenv workflows.
- If Python tooling is required for a repo, represent it via `pyproject.toml` + `uv.lock` and keep commands in `docs/ops/CLI.md` (do not duplicate runbooks across multiple docs).

## Code Reuse Gate

- Before writing new infrastructure code, check whether a shared utility already exists.
- If a utility would benefit multiple modules/projects, elevate it to the shared layer instead of duplicating it.
- Shared utilities, models, and infrastructure belong in a shared package, not duplicated across consumer modules.
- New shared functionality → extend or create a shared package, not copy-paste.

### AI Infrastructure Primitives (extends Code Reuse Gate)

Before implementing any of the following from scratch in an AI module, check whether
a shared AI primitives layer already provides it:

- LLM call surfaces: provider wiring, model selection, tuning key normalisation
- Config loading: YAML schema, deep-merge baseline, provider-agnostic runtime view
- Vector store wiring: client creation, storage context, collection management
- Retrieval defaults: top-k, hybrid search flags, reranking, semantic cache
- CLI argument contracts: spec-driven runner args
- AIOps substrate: telemetry events, tracing spans, budget guardrails, circuit breaker, run manifests, eval runner

How to check quickly:
- Prefer a dedicated “primitives index” for your shared AI primitives layer (project-owned routing usually points to it).
- If your repo uses `ai-agent-core`, print the packaged primitives index with `ai-agent-primitives-index`.

**Why this rule must be explicit:** agent-driven development reproduces these from scratch
in every module, because sessions are stateless — each session starts from the domain
problem with no visibility into what prior sessions built in other modules. Assuming the
agent knows a shared primitives layer exists is not a safe assumption. The rule must name
the categories.

**Consequence of violation:** each module independently derives the same infrastructure
with slightly different defaults. Quiet drift — the kind that survives code review —
accumulates until a single shared config change requires edits across multiple modules.

## One Responsibility Per File

- Major classes get their own `.py` file.
- For function modules (no class), one concern per file: config resolution, file reading, and routing logic are separate files, never mixed.
- No file should grow beyond ~300 lines with multiple unrelated concerns.
- File name mirrors the primary class or concern (`retriever.py` for `Retriever`, `_config.py` for config helpers).
- Anti-pattern: a single `orchestrator.py` that resolves config, reads files, lazy-loads graphs, and routes requests.

**Consequence**: monolithic files block independent import, slow review, and make responsibility boundaries invisible.

## Modular Entry Points

- Code is structured so classes can be imported independently of the entry point.
- Avoid procedural scripts that can only be run top-to-bottom.
- Entry points (`main()`) are thin wrappers over importable classes.

## Docs Currency

Any code or config change must be reflected in the affected docs in the same response — do not wait to be asked.

- **README.md** — reflect current commands; remove stale ones
- **ARCHITECTURE.md** — reflect current design, config values, file names, and behaviour
- **CONFIGURATION.md** — every key used in code must be documented; no undocumented keys, no stale defaults
- **TODO.md** — mark completed items done and move them to the Completed section
- **PRD.md** — update acceptance criteria and contracts when the module's obligations change

**Stale documentation is a bug in the change, not a backlog item.**

For the full documentation contract (required doc set, segregation rules, PRD authoring standard, extension contract, TODO structure) see `ai_context/pco/governance/DOCS_CONTRACT.md` or invoke `/docs-alignment`.

**Before writing any new `.py` file, confirm:**
- Does this contain strings/values a user might want to change without touching code? → YAML config
- Is this a second major class in an existing file? → new file
- Is this a second distinct concern in an existing file? → new file
- Is this duplicating logic from another module? → extract to shared package

## Low-Code / OSS Preference

- Prefer an existing OSS library over custom code when one covers the requirement adequately.
- Custom code requires justification: the OSS option does not exist, is too heavy for the task, or
  requires more wiring than the problem warrants.
- Balanced decision rule: a small in-line parser or test utility may be faster than wiring a library.
  The test is: "does this custom code become a maintenance liability or block reuse?" If yes, find the library.
- Custom code that reimplements something an OSS library already provides well is a governance violation,
  not just a style preference.

## Tool Selection Discipline

Fewer, focused tools outperform a large overlapping toolset.

- Every tool description populates every prompt; each additional tool adds cognitive load and increases the probability of tool confusion or misuse.
- Before adding a new tool, confirm it is not a near-duplicate of an existing one.
- Each MCP server is trusted text in the agent's execution context — a compromised or malicious MCP server is a prompt injection vector (see `security-threat-model.md`).

**The test**: can you name the specific failure mode this tool prevents, and does no existing tool already cover it? If not, do not add it.

**Consequence**: tool proliferation degrades prompt quality, expands MCP supply-chain attack surface, and makes tool schemas harder to reason about in long sessions.

## Publication Safety (when content is publishable)

- Do not include client/company identifiers or internal programme names in publishable content.
- Avoid repository-internal file paths in publishable narrative content; describe mechanisms in plain language.

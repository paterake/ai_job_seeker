---
description: Governance rules for config purity, reuse, and safe publishing posture. Loaded when editing code or configuration.
globs:
  - "**/*.py"
  - "**/*.yaml"
  - "**/*.yml"
basis: operational-experience
---

> Governance narrative: [integration spoke](../../integration/README.md)

# Governance Rules — Config Purity, Driver Selection, and Reuse

## Config Purity

- Domain strings, entity names, dataset identifiers, thresholds, and prompt text must not be hard-coded in source code.
- If a string would change when adopting a new dataset or domain, it belongs in configuration, not code.
- Treat code as reusable mechanism. Treat domain context as configuration and context-layer inputs; do not bake domain assumptions into implementations.

**Config directory structure:**
- `config/` — runtime config YAMLs (entity lists, thresholds, data paths, tuning params)
- `config/prompts/` — LLM prompt YAMLs (one file per prompt, named by purpose)

## Driver Selection: Config-Driven, Data-Driven, AI-Driven

The platform recognises three peer solution drivers:
- **Config-driven** — variability is carried in configuration rather than code.
- **Data-driven** — the answer is explicit in the data and recoverable by fixed rules.
- **AI-driven** — the mechanism must infer meaning that is not explicit in the input.

Choose the driver that fits the task:
- Acquisition, bookkeeping, reconciliation, parsing of known syntactic structures, validation, hashing, and bounded transforms default to deterministic mechanism (`config-driven` or `data-driven`).
- Semantic interpretation of content defaults to `AI-driven`.
- AI-driven solutions still honour config purity: prompts, schemas, taxonomies, thresholds, and routing belong in configuration rather than code.
- AI-driven is a governed peer, not a foreign exception. It carries its own obligations: evaluation, provenance, recorded non-determinism, and explicit review of model use.

### Explicit Answer vs Inference Test

- **Derivation**: the answer is already explicit and fixed rules can recover it. Example: parse JSON, join on a key, compute a hash, apply a threshold from config.
- **Inference**: producing the answer requires judgment, interpretation, or latent structure not explicit in the source. Example: infer entity relationships, interpret intent in prose, classify a diagram by meaning rather than syntax.

Any task with a material inference step is AI-driven by default. Do not call a semantic task "parsing" just because the carrier format is structured. Do not call a deterministic parse "inference" to justify a model when fixed rules are exact.

### Capability-Decision Record

Before introducing a new parser-/extractor-shaped mechanism, or a comparable content-interpretation surface, record:
- task type,
- chosen driver,
- why the other driver was not chosen,
- and whether a config/prompt solution was considered.

The hook only proves the decision was recorded; it does not prove the decision is correct. Correctness is screened by the capability-fit review sensor at task boundary / code review.

## Python Tooling (UV Only)

- For Python dependency management, environments, and script execution, use `uv` only.
- Never invoke raw `python` or `python3` in this governed workspace. Use `uv run python3 ...` instead.
- This applies to every Python execution path: scripts, validators, one-liners, tests, and ad-hoc local commands.
- Do not introduce `pip`/`requirements.txt`, Poetry, Pipenv, Conda, or ad-hoc virtualenv workflows.
- If Python tooling is required for a repo, represent it via `pyproject.toml` + `uv.lock` and keep commands in `docs/ops/CLI.md` (do not duplicate runbooks across multiple docs).

## Code Reuse Gate

- Before writing new infrastructure code, check whether a shared utility already exists.
- If a utility would benefit multiple modules/projects, elevate it to the **least-general shared home that covers its consumers** (see *Shared-Code Home Selection*), not automatically to the platform-wide core.
- Shared utilities, models, and infrastructure belong in a shared package, not duplicated across consumer modules.
- New shared functionality → extend or create a shared package, not copy-paste.

### Shared-Code Home Selection

"Shared by more than one module" answers *whether* to extract, not *where* it lands. Choose the home explicitly:

- **Least-general shared home.** Place shared code in the most-specific module that covers its *actual* consumers. Code shared by two sibling implementation modules belongs with the more-specific owner of that capability (the module whose domain it serves), not the platform-wide core. Two modules happening to use a utility is not by itself grounds for promotion to the generic core — the test is whether the capability is needed **platform-wide**, not whether two modules touch it.
- **Generic-core purity.** The generic primitives layer (`ai_agent_core`) holds **generic** AI/AIOps primitives only — the categories in *AI Infrastructure Primitives* below (LLM call surfaces, config loading, vector-store wiring, retrieval defaults, telemetry/tracing, CLI contracts, AIOps substrate). Domain- or source-specific capability (a source connector, a facet parser, a domain client) must **not** enter the generic core even when shared — route it to the owning domain module. This is the Config Purity principle applied to module placement: domain context does not belong in the reusable core.
- **Adding to the core is a versioned change.** Adding a new module/package to `ai_agent_core` is a versioned change — a semver bump on the shared package plus a dependency re-sync in consumers — never an untracked drop into the shared tree. An untracked addition leaves consumers building against a stale pinned dependency (the path-dependency stale-build trap).

**Consequence:** without a home-selection rule, every utility shared by two modules defaults into the generic core — an agent following "elevate to the shared layer" as written is routed there by the contract, not by misjudgement. The core then accretes domain-specific code (e.g. a source connector or a duplicated file-hash helper), consumers weld to it, and each untracked addition trips the stale-build trap. Naming the least-general home converts "shared → promote to core" into "shared → place with the nearest owner," which is the same systemic-routing failure config-purity exists to prevent.

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

### Capability-Fit extension

- Do not build bespoke deterministic machinery for a task that is materially better served by an AI-driven mechanism.
- Do not reach for a model where a deterministic mechanism is exact, cheaper, and auditable.
- The design review question is not "can code do this?" but "which driver best fits the goal and evidence obligations?"

## Tool Selection Discipline

Fewer, focused tools outperform a large overlapping toolset.

- Every tool description populates every prompt; each additional tool adds cognitive load and increases the probability of tool confusion or misuse.
- Before adding a new tool, confirm it is not a near-duplicate of an existing one.
- Each MCP server is trusted text in the agent's execution context — a compromised or malicious MCP server is a prompt injection vector (see `security-threat-model.md`).

**The test**: can you name the specific failure mode this tool prevents, and does no existing tool already cover it? If not, do not add it.

**Consequence**: tool proliferation degrades prompt quality, expands MCP supply-chain attack surface, and makes tool schemas harder to reason about in long sessions.

## Procurement & Access Lifecycle

- **Vendor procurement / TPRM.** A model or tool vendor must carry a completed third-party risk
  assessment covering data handling, contractual liability, and exit terms before adoption —
  `vendor_assessment_ref` is a pointer to that completed process, not a substitute for it.
  **Consequence:** a vendor field with no assessment behind it is due-diligence theatre; the
  liability and exit exposure it was meant to control is unmanaged.
- **Access recertification.** Human and agent access to a solution is provisioned by named identity
  and recertified on a schedule; joiner/mover/leaver changes are applied. **Consequence:** access
  granted once and never reviewed is how orphaned privilege accumulates across hundreds of
  solutions — the standing exposure no runtime control detects.

## Publication Safety (when content is publishable)

- Do not include client/company identifiers or internal programme names in publishable content.
- Avoid repository-internal file paths in publishable narrative content; describe mechanisms in plain language.

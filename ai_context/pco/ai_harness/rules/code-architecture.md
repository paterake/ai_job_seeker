---
description: Architecture rules for code — config purity, driver selection, simplest pattern first, reuse and shared-code homes, file structure, native-first integration. Loaded when editing code or configuration.
basis: operational-experience
spoke: architecture
paths:
  - "**/*.py"
  - "**/*.sh"
  - "**/*.js"
  - "**/*.ts"
  - "**/*.yaml"
  - "**/*.yml"
  - "**/*.toml"
---

> Governance narrative: [architecture spoke](../../architecture/README.md)

# Code Architecture Rules — Config Purity, Driver Selection, and Reuse

## Config Purity

- Domain strings, entity names, dataset identifiers, thresholds, file paths, and prompt text must not be hard-coded in source code.
- If a string would change when adopting a new dataset or domain, it belongs in configuration, not code.
- Treat code as reusable mechanism. Treat domain context as configuration and context-layer inputs; do not bake domain assumptions into implementations.
- Runtime inputs come from config files (YAML, JSON) and command-line arguments. Environment variables carry secrets only, read at point of use and never written to config, logs or evidence. Any other value read from the environment is a defect: move it to config. Variables the operating system provides (`HOME`, `PATH`) are not configuration and may be read.

**Consequence:** an environment value is invisible in the repo and in the run evidence, differs silently between shells, agents and machines, and cannot be reviewed or reproduced; config is committed, diffable and recorded with the run.

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
- **Simplest pattern first.** An AI-driven solution starts as a single model call; it becomes a fixed workflow,
  then an agent, only when evidence shows the simpler pattern fails the task. **Consequence:** an agent where a
  call would do adds loops, cost and failure surface that its evals and bounds must then cover.

### Explicit Answer vs Inference Test

- **Derivation**: the answer is already explicit and fixed rules can recover it. Example: parse JSON, join on a key, compute a hash, apply a threshold from config.
- **Inference**: producing the answer requires judgment, interpretation, or latent structure not explicit in the source. Example: infer entity relationships, interpret intent in prose, classify a diagram by meaning rather than syntax.

Any task with a material inference step is AI-driven by default. Do not call a semantic task "parsing" just because the carrier format is structured. Do not call a deterministic parse "inference" to justify a model when fixed rules are exact.

### Capability-Decision Record

When a new parser-/extractor-shaped mechanism, or a comparable content-interpretation surface, involves a real
choice between drivers, record it in the commit message or PR description (fields: `ai_context/pco/templates/capability_decision_record.md`):
- task type,
- chosen driver,
- why the other driver was not chosen,
- and whether a config/prompt solution was considered.

The reviewer checks the driver choice at code review ([harness-tool-contract.md](harness-tool-contract.md) →
Capability Decisions Are Reviewed, Not Gated). A path or wiring change is not a driver decision and needs no record.

## Python Tooling (UV Only)

The core states the rule ([AGENTS.md](../../AGENTS.md) → While you work). Its scope:
- This applies to every Python execution path: scripts, validators, one-liners, tests, and ad-hoc local commands.
- Do not introduce `pip`/`requirements.txt`, Poetry, Pipenv, Conda, or ad-hoc virtualenv workflows.
- If Python tooling is required for a repo, represent it via `pyproject.toml` + `uv.lock`.

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

Any code or config change must be reflected, in the same change and without being asked, in every doc that owns
a fact the change alters: a command, a design decision, a config key or default, a backlog item, an obligation.
Which doc owns which fact: `ai_context/pco/governance/DOCS_CONTRACT.md` → Segregation Rules (validate with the
`docs-alignment` skill).

**Stale documentation is a bug in the change, not a backlog item.**

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

## Native First

- Integrate any vendor, model, tool or platform through its native integration: its own plugin or
  skill, SDK, API, or the host platform's extension points (for example the agent harness's skills,
  hooks and MCP). Do not build or maintain wrapper CLIs, adapter skills or glue layers to integrate it.
- Use what the native integration offers; scope its use through the vendor's approval record, not
  through extra layers. Platform controls (`operations.md`, `observability.md`, `lineage.md`,
  `security-threat-model.md`) still apply.
- If no native path exists for a use, that use is not integrated: say so; do not build a bridge.
- This does not ban the one shared, governed call surface per vendor that *AI Infrastructure
  Primitives* and `operations.md` require for product mechanism. Behaviour changes there are config,
  not new layers.
- **Consequence:** a wrapper is a second integration to maintain and creates friction; it drifts from
  the vendor and duplicates what already exists.

Adding a tool or MCP server: `security-threat-model.md` §4 (trust assessment and tool-selection test).

---
description: Architecture rules for code — config purity, driver selection, simplest pattern first, reuse and shared-code homes, variant contracts, duplicate-code ratchet, file structure, module boundaries, dependency updates, native-first integration. Loaded when editing code or configuration.
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

- Config the project owns is declared and enforced: its loader names the key surface and fails on an undeclared key or a missing required key. A vendor or API payload the project consumes, and whose schema it does not own, is not owned config: document it as a consumed contract, pin its version where one exists, and read it defensively; never re-declare it as owned config.

**Consequence:** an owned key that loads without a declaration is dead or mistyped config nobody notices; a vendor payload absorbed into owned config bloats the contract and turns every upstream API change into a config migration.

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
- **Consequence:** one execution path outside UV resolves different versions, so a result cannot be reproduced.

## Dependency Updates

- Dependencies resolve from a committed lockfile (`uv.lock` for Python). Moving a pinned version is a deliberate
  change, named in its commit message, never done in passing; only code the new version requires moves with it.
- A standard dependency-update tool watches the pinned dependencies and opens one change per upgrade, so a release,
  deprecation or security fix is seen when it ships. No custom watcher is built (Low-Code / OSS Preference).
- An upgrade is accepted when the repo's pipelines run end to end on it and its authorisation, secrets and redaction
  and provenance tests pass unchanged; tests the upgrade makes stale follow `assurance.md` → Test Catalogue.
- A dependency pinned in more than one place (for example a git revision in the workspace sources and an exact
  version in each package) moves in one change, in every place.

**Known gap:** the PCO ships no update-tool configuration and names no tool as verified. On 2026-11-15 none of the
eight governed repos had a pipeline definition or an update-tool configuration committed in the repo, and five pinned
the shared-code home by git revision. Whether a candidate tool (Renovate, Dependabot) updates `uv.lock` and a
git-revision pin is UNVERIFIED; until a consumer wires one and records the result, no tool watches the pins.

**Consequence:** pins nobody watches fall behind silently: a security fix is missed, and the eventual upgrade spans
several versions at once, the costly migration the OSS preference is meant to avoid.

## Code Reuse Gate

- Before writing new infrastructure code, check whether a shared utility already exists.
- If a utility would benefit multiple modules/projects, elevate it to the **least-general shared home that covers its consumers** (see *Shared-Code Home Selection*), not automatically to the platform-wide core.
- Shared utilities, models, and infrastructure belong in a shared package: extend an existing one or create one,
  never duplicate or copy-paste across consumer modules.

### Shared-Code Home Selection

"Shared by more than one module" answers *whether* to extract, not *where* it lands. Choose the home explicitly:

- **Least-general shared home.** Place shared code in the most-specific module that covers its *actual* consumers. Code shared by two sibling implementation modules belongs with the more-specific owner of that capability (the module whose domain it serves), not the platform-wide core. Two modules happening to use a utility is not by itself grounds for promotion to the generic core — the test is whether the capability is needed **platform-wide**, not whether two modules touch it.
- **Generic-core purity.** The generic primitives layer (the shared-code home) holds **generic** AI/AIOps primitives only — the categories in *AI Infrastructure Primitives* below (LLM call surfaces, config loading, vector-store wiring, retrieval defaults, telemetry/tracing, CLI contracts, AIOps substrate). Domain- or source-specific capability (a source connector, a facet parser, a domain client) must **not** enter the generic core even when shared — route it to the owning domain module. This is the Config Purity principle applied to module placement: domain context does not belong in the reusable core.
- **Adding to the core is a versioned change.** Adding a new module/package to the shared-code home is a versioned change — a semver bump on the shared package plus a dependency re-sync in consumers — never an untracked drop into the shared tree. An untracked addition leaves consumers building against a stale pinned dependency (the path-dependency stale-build trap).

**Consequence:** without a home-selection rule, every utility shared by two modules defaults into the generic core — an agent following "elevate to the shared layer" as written is routed there by the contract, not by misjudgement. The core then accretes domain-specific code (e.g. a source connector or a duplicated file-hash helper), consumers weld to it, and each untracked addition trips the stale-build trap. Naming the least-general home converts "shared → promote to core" into "shared → place with the nearest owner," which is the same systemic-routing failure config-purity exists to prevent.

### Variant Capabilities (extends Code Reuse Gate)

When one capability has more than one variant (a language, a source, a store):

- Define one input contract and one facade; every later step calls the facade, never a variant.
- The contract is documented where the facade is owned: what goes in, what comes out, what policy it enforces, and
  where an external component would bind. A facade whose contract is not documented does not meet the first bullet.
- Each variant is an adapter registered by config. No variant name appears in a code path after extraction.
- A second variant may not be added until the contract and the facade exist.

**Consequence:** one module per variant duplicates the same logic in each and leaks variant shapes into every later
step, so each new language or source multiplies the code and each fix is made several times. Evidence (reported by a
consumer's director session, not verified in this repo): a six-key provenance dict repeated 23 times across sibling
reader modules with no shared base, while Code Reuse Gate covered only a shared utility.
An undocumented contract cannot be bound, reviewed or described in an architecture document without reading its code.

### Duplicate-Code Ratchet (extends Code Reuse Gate)

A repo keeps a duplicate-code count that may only fall: the count is a committed baseline integer, the gate fails when
the count rises, and a zero threshold is not used while clones exist.

The ratchet's scope is the code that ships. Code whose only purpose is to guard, measure or prove a change (checkers,
parity or comparison harnesses, migration gates) is declared build-time scaffolding when it is created, with a
retirement condition recorded next to it. Scaffolding is excluded from quality ratchets and clean-up passes
(duplicate-code count, refactors), is not refactored, and is retired when its condition is met. The first step of
driving a count down is to measure where the count sits and drop what is not retained.

**Known gap:** this is a requirement only. The PCO ships no check; each consumer wires the count into its own gate
script. The record names jscpd (PMD CPD as the Java fallback) and marks its flags, the count field and the
determinism of the count as UNVERIFIED, so no tool settings are given here.
The scaffolding exclusion is likewise unenforced: no PCO check reads a declaration or a retirement condition.

**Consequence:** without a count that cannot rise, duplication grows with every addition and is found only after the
fact, when a matrix, library research and a refactor must come before any other work.
A ratchet that includes scaffolding turns clean-up effort into work on code about to be deleted, and a guard rewritten
for tidiness is no longer the independent check it was.

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
- If your repo uses the shared-code home's package, print its packaged primitives index with the package's index command.

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
- **Consequence:** logic that lives only in a script cannot be tested in isolation or reused by another module,
  so it is copied instead.

## Module Boundaries

For a repo with more than one module:

- Dependencies run one way, with no cycles. The repo records its module layers; a module imports only from layers
  below its own, and modules in one layer do not import each other's code: one consumes another's outputs as data.
- Across modules, import public names only, never an underscore module or name. A need for private code means the
  owner exposes it, the code moves to its real owner, or the consumer is restructured to sit downstream of the owner.
- Every config file has one owning module. Another module gets a value through the owner's public API, or the run
  passes it the location; it never reads the owner's config folder by path.
- A module with no consumer and no entry point in use is retired or recorded as parked with the trigger that brings
  it back; no new dependency on a parked module is added. A retirement is its own decided change, never a side effect
  of other work (the core: mention unrelated dead code; don't delete it).

**Consequence:** an upward or sideways import welds two modules and becomes a cycle the first time the lower one needs
the upper one; a private import blocks every rename in its owner; a config file read by two modules drifts, and a path
into another module's folder breaks silently when the owner moves it; a dead module is still maintained and built on.
Evidence (reported by a consumer's director session, not verified in this repo): about 20 private cross-module imports
found and removed in one consumer, each of which blocked a rename in its owner.

## Docs Currency

Any code or config change must be reflected, in the same change and without being asked, in every doc that owns
a fact the change alters: a command, a design decision, a config key or default, a backlog item, an obligation.
Which doc owns which fact: `ai_context/pco/governance/DOCS_CONTRACT.md` → Segregation Rules (validate with the
`docs-alignment` skill).

**Stale documentation is a bug in the change, not a backlog item.** **Consequence:** the next agent acts on the
stale fact, and a deferred doc fix is never made.

## Low-Code / OSS Preference

- Prefer an existing OSS library over custom code when one covers the requirement adequately.
- Preference order: a standard or protocol, then a widely used maintained library (pinned, behind an interface the
  repo owns), then custom code as glue only.
- Adopt a library when it keeps the guarantees, not the features: authorisation (who may see which data), secrets
  and redaction (nothing sensitive reaches outputs, logs or traces) and provenance (every answer traces to its
  source) are kept regardless; every other feature of the replaced code that the library lacks is listed and
  dropped, not rebuilt. Byte-identical output is not required: the change records the output before and after and
  classifies every difference.
- A guarantee is enforced through the library's own mechanism first (filter, hook, middleware, callback); custom code
  covers only what the library cannot do, as a thin check before or after the call, never a parallel implementation.
- Custom code is justified only when no standard or maintained library covers the requirement, or none can keep the
  three guarantees above. A library being heavier than the task, or needing more wiring than the problem seems to
  warrant, is not a reason; neither is custom code being faster to write.
- Custom code that reimplements something an OSS library already provides well is a governance violation,
  not just a style preference.
- **Consequence:** custom code reimplements tested paths with fewer users finding its bugs, and its maintenance
  is paid forever; an adoption that rebuilds every feature of the code it replaces keeps that maintenance.
  Evidence (reported by the operator, not verified in this repo): custom code accumulated across three incarnations
  of one consumer repo. The exceptions removed here ("too heavy", "more wiring", "a small in-line parser is faster")
  were the openings the old rule text left for it.

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

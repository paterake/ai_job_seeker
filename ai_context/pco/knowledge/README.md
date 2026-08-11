# Knowledge & Content (Spoke)
> DAMA mapping: Document & Content Management → Knowledge & Content Management

## Purpose

Ensure the harness uses controlled, trustworthy knowledge sources and policy content, rather than stale, duplicated, or accidental context.

## PCO Emphasis

- Policy: defines authoritative content, provenance rules, and freshness requirements
- Control plane: enforces retrieval boundaries, whitelists, and policy precedence
- Observability: records retrieval lineage and detects staleness/drift

## Scope (what this spoke governs)

### Policy content

- Pillars, standards, and guardrails as authoritative content
- Runbooks and playbooks for workflows and incidents
- Templates for outputs (PRDs, feedback, evidence packs)

### Prompts as governed engineering artefacts

Prompts are treated as versioned artefacts with owners, tests, and refactoring cycles.

- Prompt libraries and priming packs (role/system policy, workflow prompts, templates)
- Prompt refactoring cycle (red–green–refactor backed by automated evals)
- Model-switch risk management (regression evidence and rollout semantics anchor: [assurance.md](../ai_harness/rules/assurance.md) and [CONTRACT.md](../governance/CONTRACT.md))

### Knowledge sources for task execution

- Curated corpora (docs, specs, ADRs, runbooks, domain knowledge)
- Allowed vs disallowed sources and trust tiers
- Provenance, attribution, and freshness signalling

### Content lifecycle

- Ownership, review cadence, and deprecation
- Retention rules and controlled deletion
- Duplication avoidance (single source of truth)

### Retrieval decision hierarchy (governed choices)

Retrieval mechanisms are chosen using a declared hierarchy:

1. Prompt optimisation (first)
2. RAG over authoritative sources
3. Hybrid retrieval (structured + semantic) where appropriate
4. Query rewriting (bounded, cost-accounted)
5. Reranking (with monitored quality)
6. Fine-tuning (last resort; requires significant data curation governance)

## Governance Controls (hub decisions)

### Authority and precedence

Governance defines the precedence model:
- Core policy outranks optional policy
- Policy outranks project-local preferences
- Authoritative sources outrank untrusted notes

### Source whitelisting and trust tiers

Governance assigns every content source the agent can read to an explicit trust tier. Canonical 4-tier model (Trusted / Internal / Untrusted / Prohibited) and per-tier permitted agent actions: [security-threat-model.md](../ai_harness/rules/security-threat-model.md).

What governance must decide per knowledge domain:
- Which repositories/paths/systems fall in each tier
- Separation of Untrusted sources from any context with credential access or write capability (required by canonical model)

### Freshness and deprecation

Governance defines:
- Minimum review cadence for critical runbooks and policies
- What "deprecated" means and how it is enforced (warnings vs blocking)

### Prompt lifecycle governance

Governance defines:
- Ownership and review cadence for prompts that carry policy or high-risk behaviour
- Eval coverage for prompt changes that affect safety, tool access, or output schemas (anchor: [assurance.md](../ai_harness/rules/assurance.md))
- Quality metrics: first-pass acceptance rate and iteration-to-acceptance, tracked per workflow
- Knowledge priming expectations: structured pre-run priming distinct from runtime retrieval

### Query rewriting and reranking governance

Governance defines:
- Query rewriting limits (generate 3–5 alternatives max) and token budget accounting
- When NOT to use vector retrieval (embeddings are lossy; disallow for exact-match structured/relational needs)
- Reranker fallback rule: monitored quality gates and containment plan when reranking degrades results

### Fine-tuning gate (last resort)

Governance defines:
- Preconditions for adopting fine-tuning (stable task definition, sufficient curated data, inability of prompt/RAG to meet thresholds)
- Data curation standards (privacy, provenance, splits, versioning, red-team cases included)
- Post-tune regression obligations (offline evals + online monitoring for degradation)

## Artefacts and Surfaces (examples)

- Authoritative policy library and templates
- Source registry (source → trust tier → owner → review cadence)
- Content provenance model (source, owner, date, version)
- Deprecation policy and migration guidance
- Retrieval and citation rules (how evidence references sources)
- Prompt registry (prompt ID, purpose, owner, model compatibility, last eval version)
- Priming packs (structured tech stack, directory structure, naming conventions, pattern examples)
- Retrieval policy decision tree (what method is allowed for what data class)
- Fine-tuning data curation standard (used only if fine-tuning is adopted)

## External Research Intake (Bounded)

External research can inform governance, but it is not itself a control. Canonical intake rules (treat as untrusted input, prefer primary sources, record evidence, distill don't copy, require a verification plan for any governance change): [agent-behavior.md](../ai_harness/rules/agent-behavior.md) and [assurance.md](../ai_harness/rules/assurance.md)

## Enforcement Rules

Canonical enforcement: [retrieval.md](../ai_harness/rules/retrieval.md)

Covers: chunking parameters in config (not code), hybrid search as a first-class contract (sparse + dense legs, merged and reranked), quality gate (results carry provenance; no silent empty returns), and unit test isolation (no live vector DBs or model servers).

## Enforcement Points (where the control plane enforces)

### Pre-run

- Retrieval configuration is selected and recorded (sources + trust rules)
- Disallowed sources are excluded by construction

### In-run

- Retrieval is constrained to approved sources and bounded by policy
- Provenance is attached to retrieved content and carried into evidence
- Unsafe mixing of sources is prevented (e.g., policy + random notes)

### Post-run

- Retrieval lineage is stored with the run evidence
- Staleness signals trigger updates or deprecations

## Evidence and Metrics (what observability measures)

- Retrieval hit-rate from authoritative sources
- Citation/provenance completeness rate
- Staleness rate (% runs using deprecated content)
- Policy duplication occurrences (same rule defined in multiple places)
- Content update effectiveness (incident recurrence after content updates)

## Common Failure Modes

- Policy drift caused by duplicate documents with conflicting guidance
- Stale runbooks that remain "official" because nothing tracks review cadence
- Retrieval that mixes authoritative policy with casual notes and treats both equally
- Hidden dependency on internal tribal knowledge not captured as artefacts
- Context monoliths: a single ai_context blob applied to every repo regardless of its dominant risk surface

## Concern Profiles (Applied Context)

The same harness wiring can support different repos, but the context reflects the dominant concern to avoid mis-governance (anchor: [CONCERNS.md](../governance/CONCERNS.md)).

- LLM system repos emphasise bounded execution, evals, retrieval correctness, and tracing
- Publishing repos emphasise leakage prevention, evidence discipline, and avoiding drift across packs
- Data/document repos emphasise determinism, schema/format correctness, and repeatable transformations

## Maturity Model (pragmatic)

### Level 1: Curated and referenced

- Policy and runbooks are centralised
- Retrieval sources are whitelisted
- Provenance is recorded for retrieved content

### Level 2: Lifecycle-governed

- Deprecation exists and is enforced
- Review cadence is tracked for critical content
- Duplication is actively removed and prevented

### Level 3: Evidence-driven knowledge

- Content changes are driven by telemetry and incident learnings
- Retrieval policies adapt by risk tier (stricter for high-risk workflows)
- Provenance supports reliable forensics and audit queries

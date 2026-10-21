# Knowledge & Content (Spoke)
> DAMA mapping: Document & Content Management → Knowledge & Content Management

## Governs

- Policy content as a single source of truth: the PCO owns `ai_context/pco/`, consumers receive it by sync
- Keeping human docs in step with `ai_context/`
- Retrieval and RAG in governed repos, chosen by the hierarchy below
- Publishing: safety gates and claim scoping; output ownership and source licensing
- Concern profiles: a repo's context reflects its dominant concern ([CONCERNS.md](../governance/CONCERNS.md))

## Enforced

- A consumer's synced `ai_context/pco/` matches the PCO within the checked scope, and the agent entrypoint loads the
  core from it with no root copy: validators `validate` and `validate_harness_wiring.py`, run from the PCO; they
  report drift after the fact (scopes: [CONTRACT.md](../governance/CONTRACT.md) → Sync Behaviour).
- A file edit under `ai_context/pco/` in a consumer, the core included, is denied: hook `check_guard.sh`
  (`synced_pco_edit_refused`; what it misses: [hooks/README.md](../ai_harness/hooks/README.md)).
- Relative Markdown links in tracked `ai_context/`, `docs/` and README files point to existing files: validator
  `governed-repo-validate`, run from `ai_agent_pco` (in a consumer, a broken link in the synced layer is a warning).
- The spoke index ([ASSISTANTS.md](../ASSISTANTS.md)), the spoke folders and the rules' `spoke:` frontmatter agree, and
  `ai_context/pco/` holds only the allowed entries ([CONTRACT.md](../governance/CONTRACT.md) → Conformance):
  validator `governance-audit --fail` (index consistency), run from `ai_agent_pco`.
- Publication safety gates, the PCO repo's circulatable doc (`docs/enterprise/FEDERATED_AI_GOVERNANCE.md`) only: validator
  `governance-audit --fail` flags links, URLs and repo path segments. Client, company and programme names, other absolute paths, and all other publishable
  content: human review ([publication.md](../ai_harness/rules/publication.md) → Safety Gates).
- Contradicting rules across `ai_context/`: validator `governance-audit --fail`, run from `ai_agent_pco` (a heuristic token-overlap check;
  it finds some contradictions, not all).
- Retrieval rules, claim scoping, output ownership, source licensing and concern profiles: human review.
- Human docs kept in step with `ai_context/` ([ai_context_sync.md](../ai_harness/rules/ai_context_sync.md)), and
  the Rule Authoring Standard and Workflow Gates ([publication.md](../ai_harness/rules/publication.md)): human
  review.

## Not enforced

- Provenance on retrieval results and end-to-end retrieval traces at run time: required by
  [retrieval.md](../ai_harness/rules/retrieval.md) → Quality Gate and
  [observability.md](../ai_harness/rules/observability.md); no PCO check. Restriction to approved sources:
  [security spoke](../security/README.md) → Not enforced. What is known of `ai_agent_core`'s
  runtime: [assurance spoke](../assurance/README.md) → Declared Scope of Validation.
- Stale docs, runbooks included: required by [code-architecture.md](../ai_harness/rules/code-architecture.md) → Docs Currency; no
  PCO check.

## Rules

- [retrieval.md](../ai_harness/rules/retrieval.md)
- [publication.md](../ai_harness/rules/publication.md)
- [ai_context_sync.md](../ai_harness/rules/ai_context_sync.md)
- [security-threat-model.md](../ai_harness/rules/security-threat-model.md) §1 (trust of retrieved content)
- Output ownership and source licensing: [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md)

## Canonical

### Retrieval decision hierarchy (governed choices)

Retrieval mechanisms are chosen simplest first:

1. Prompt optimisation (first)
2. RAG over authoritative sources
3. Hybrid retrieval (structured + semantic) where appropriate
4. Query rewriting (bounded, cost-accounted)
5. Reranking (with monitored quality)
6. Fine-tuning (last resort)

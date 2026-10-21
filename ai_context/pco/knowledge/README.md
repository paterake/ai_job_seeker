# Knowledge & Content (Spoke)
> DAMA mapping: Document & Content Management → Knowledge & Content Management

## Governs

- Policy content as a single source of truth: the PCO owns `ai_context/pco/`, consumers receive it by sync
- Keeping human docs in step with `ai_context/`
- Retrieval and RAG in governed repos, chosen by the hierarchy below
- Trust tiers for content an agent reads, and bounded external research
- Publishing: safety gates and claim scoping; output ownership and source licensing
- Concern profiles: a repo's context reflects its dominant concern ([CONCERNS.md](../governance/CONCERNS.md))

## Enforced

- A consumer's synced `ai_context/pco/` and root `AGENTS.md` match the PCO: validator `validate` (reports drift
  after the fact; root `AGENTS.md` in every scope, the default `--scope harness` covers `ASSISTANTS.md`,
  `AGENTS.md` and `ai_harness/`, and only `--scope full` covers the whole synced tree).
- A file edit under `ai_context/pco/` in a consumer is denied: hook `check_guard.sh` (root `AGENTS.md` and shell
  writes are not hooked) ([hooks/README.md](../ai_harness/hooks/README.md)).
- Relative Markdown links in tracked `ai_context/`, `docs/` and README files point to existing files: validator
  `governed-repo-validate` (in a consumer, a broken link in the synced layer is a warning; heading references are
  not checked).
- Publication safety gates, circulatable doc (`docs/enterprise/FEDERATED_AI_GOVERNANCE.md`) only: validator
  `governance-audit --fail` flags seven literal tokens (`http://`, `https://`, `file://`, `](`, `ai_context`,
  `.claude`, `scripts/`). Client, company and programme names, other absolute paths, and all other publishable
  content: human review ([publication.md](../ai_harness/rules/publication.md) → Safety Gates).
- Contradicting rules across `ai_context/`: validator `governance-audit --fail` (a heuristic token-overlap check;
  it finds some contradictions, not all).
- Retrieval rules, trust tiers, bounded external research, claim scoping, output ownership, source licensing and
  concern profiles: human review.
- Human docs kept in step with `ai_context/` ([ai_context_sync.md](../ai_harness/rules/ai_context_sync.md)), and
  the Rule Authoring Standard and Workflow Gates ([publication.md](../ai_harness/rules/publication.md)): human
  review.

## Not enforced

- Nothing bounds retrieval at run time: restriction to approved sources, provenance on results and end-to-end
  retrieval traces are required by [security-threat-model.md](../ai_harness/rules/security-threat-model.md) §1,
  [retrieval.md](../ai_harness/rules/retrieval.md) → Quality Gate and
  [observability.md](../ai_harness/rules/observability.md); no PCO check. The PCO has not audited the retrieval
  defaults in `ai_agent_core`.
- Stale docs, runbooks included: required by [governance.md](../ai_harness/rules/governance.md) → Docs Currency; no
  PCO check.
- A periodic review cadence for policy content (target, not implemented;
  [governance/HUB.md](../governance/HUB.md) → Cadence and ownership).

## Rules

- [retrieval.md](../ai_harness/rules/retrieval.md)
- [publication.md](../ai_harness/rules/publication.md)
- [ai_context_sync.md](../ai_harness/rules/ai_context_sync.md)
- [security-threat-model.md](../ai_harness/rules/security-threat-model.md) §1 and → External Research (Bounded)
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

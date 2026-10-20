# Spoke Index — Platform (PCO)

**Read on demand.** The always-loaded core is the root `AGENTS.md` (source: [AGENTS.md](AGENTS.md)).
Rules under `ai_harness/rules/` are all path-scoped: the harness loads each one when you read or edit
a matching file, so do not read them pre-emptively. Use this index when a task needs a spoke's
narrative or a governance doc.

## Spokes (DAMA-DMBOK wheel → agent harness)

The model and the reason each spoke exists: [governance/HUB.md](governance/HUB.md).

| Spoke | Read when the task touches | Path-scoped rules |
|---|---|---|
| [architecture/](architecture/README.md) | Repo layout, module boundaries, config placement | `governance.md`, `config-repo-structure.md` |
| [behaviour/](behaviour/README.md) | Agent behaviour, sessions, token economy, Failure Harvest | — (core: `AGENTS.md`) |
| [operations/](operations/README.md) | LLM-calling modules: bounds, budgets, degrade modes, human checkpoint, kill switches | `operations.md` |
| [security/](security/README.md) | Untrusted content, tools/MCP, agents | `security-threat-model.md` |
| [integration/](integration/README.md) | Harness switch, model upgrade, hooks, edit-tool format | `harness-tool-contract.md` |
| [knowledge/](knowledge/README.md) | Retrieval/RAG, docs, publishing, anti-drift | `retrieval.md`, `publication.md`, `ai_context_sync.md` |
| [master-data/](master-data/README.md) | Model/tool registries, policy packs, exceptions | — (registry data; checked by `governed-repo-validate`) |
| [observability/](observability/README.md) | Tracing, telemetry, run review, FinOps | `observability.md` |
| [lineage/](lineage/README.md) | Tool/model registration, risk rating, versioning, run lineage | `lineage.md` |
| [assurance/](assurance/README.md) | Evals, datasets, incidents, rule provenance | `assurance.md`, `governance-provenance.md` |

## Governance docs (explicit read)

| Task | Read |
|---|---|
| `ai_context/` structure, sync scope, what is authoritative | [CONTRACT.md](governance/CONTRACT.md) |
| Anti-drift / "no duplication" questions | [ANTI_DRIFT.md](governance/ANTI_DRIFT.md) |
| Repo concern profile / what belongs in ai_context | [CONCERNS.md](governance/CONCERNS.md) |
| Backlog / multi-session work (anchor docs) | [AI_ASSISTANT_BACKLOG_CONTINUITY.md](governance/AI_ASSISTANT_BACKLOG_CONTINUITY.md) |
| Module docs and PRDs | [DOCS_CONTRACT.md](governance/DOCS_CONTRACT.md) |
| Enterprise go-live (residency, data-subject rights, vendors, retention, FinOps, oversight) | [ENTERPRISE_OBLIGATIONS.md](governance/ENTERPRISE_OBLIGATIONS.md) |

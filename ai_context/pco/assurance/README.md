# Assurance & Evals (Spoke)
> DAMA mapping: Data Quality Management → Assurance, Evals & Continuous Improvement

## Governs

- Eval gates for LLM-calling modules: error analysis first, explicit thresholds, regression protection
- Eval datasets: versions, provenance, named splits
- Evaluator calibration (independence: [HUB.md](../governance/HUB.md) → Independent review pattern)
- Incident capture and the link from an incident to the governance change it causes
- Rule provenance (`basis:`) and the declared scope of validation
- The enterprise-grade bar for work

## Enforced

- A governed repo declares its sensors in `REPO_CONTRACT.md` (Sensor Layer Declaration, Guide/Sensor Coherence Map): section presence is checked as in the [architecture spoke](../architecture/README.md) → Enforced; content is human review.
- Error analysis, eval levels, dataset provenance and splits, evaluator calibration and required-suite records: human review against [assurance.md](../ai_harness/rules/assurance.md) (no check).
- Rule provenance tag on each rule file, the declared validated scope, and independent validation of `research-derived` content: human review at change approval. Rule: [governance-provenance.md](../ai_harness/rules/governance-provenance.md) → Scope of Validation, Rule Provenance, Independent Validation.

## Not enforced

- Evals as blocking gates, threshold changes backed by regression evidence, pinned dataset versions: required by [assurance.md](../ai_harness/rules/assurance.md) → Eval as a Gate, Dataset Governance; no PCO check. A consumer's gates are its own, declared in its `REPO_CONTRACT.md`.
- Online-to-offline loop (production failures become regression cases): required by [assurance.md](../ai_harness/rules/assurance.md) → Online-to-Offline Loop; no PCO check.
- Incident reports in `audit/incidents/` from the [incident template](../templates/incident_report.md): required by [assurance.md](../ai_harness/rules/assurance.md) → Incident Capture; no PCO check.

## Rules

- [assurance.md](../ai_harness/rules/assurance.md)
- [governance-provenance.md](../ai_harness/rules/governance-provenance.md)

## Canonical

### Enterprise Grade

Enterprise grade is not a fixed checklist or a label: the agent doing the work sets it for each task, because
what the work needs moves with the work. Before starting, it states the bar: each criterion below that the work
touches, plus any the task itself needs, each as a check it will run. It finishes by reporting each criterion with
its evidence. Repos coin no grade names, tiers or status labels. **Consequence:** a self-coined grade measures
against a label instead of criteria, cannot be compared across repos, and drifts from what the work actually needs.

The floor, by what the work touches (each rule owns its criteria; this list only points):
- Any code: guarantees and error envelope ([INTENT_TEMPLATE.md](../templates/INTENT_TEMPLATE.md)), config purity
  and driver selection ([code-architecture.md](../ai_harness/rules/code-architecture.md))
- Docs: [DOCS_CONTRACT.md](../governance/DOCS_CONTRACT.md)
- LLM-calling modules: [operations.md](../ai_harness/rules/operations.md),
  [observability.md](../ai_harness/rules/observability.md), [lineage.md](../ai_harness/rules/lineage.md),
  [assurance.md](../ai_harness/rules/assurance.md)
- Untrusted content, tools or MCP servers: [security-threat-model.md](../ai_harness/rules/security-threat-model.md)
- High/Critical solutions at go-live: [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md)

### Declared Scope of Validation

As of 2026-10-21 ([governance-provenance.md](../ai_harness/rules/governance-provenance.md) → Scope of Validation):

| Axis | Status | Evidence |
|---|---|---|
| Runtime governance: source trust, lineage, bounded execution, eval gates, multi-agent trust | Declared validated by the operator through production use | Production use, not an independent audit. The PCO checks no runtime conformance. A name-level read of `ai_agent_core` (2026-10-21, not a full audit) found bounds, `run_id`, degrade paths, input caps and run manifests, and no kill switch or per-call human approval; its retrieval defaults were not read |
| Legal, procurement, organisational | Workstream, not independently validated | Wording advisory until Legal/DPO sign-off ([ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md)) |

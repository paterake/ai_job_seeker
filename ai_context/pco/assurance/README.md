# Assurance & Evals (Spoke)
> DAMA mapping: Data Quality Management → Assurance, Evals & Continuous Improvement

## Governs

- Eval gates for LLM-calling modules: error analysis first, explicit thresholds, regression protection
- Eval datasets: versions, provenance, named splits
- Evaluator calibration and independence ([HUB.md](../governance/HUB.md) → Independent review pattern)
- Incident capture and the link from an incident to the governance change it causes
- Rule provenance (`basis:`) and the declared scope of validation

## Enforced

- A governed repo declares its sensors in `REPO_CONTRACT.md`: validator, `validate --scope governance|full` checks that the Sensor Layer Declaration and Guide/Sensor Coherence Map sections exist, not their content ([CONTRACT.md](../governance/CONTRACT.md) → Downstream Conformance Contract).
- Error analysis, eval levels, dataset provenance and splits, evaluator calibration and required-suite records: human review against [assurance.md](../ai_harness/rules/assurance.md) (no check).
- Rule provenance tag on each rule file, the declared validated scope, and independent validation of `research-derived` content: human review at change approval. Rule: [governance-provenance.md](../ai_harness/rules/governance-provenance.md) → Scope of Validation, Rule Provenance, Independent Validation.

## Not enforced

- Evals as blocking gates, threshold changes backed by regression evidence, pinned dataset versions: required by [assurance.md](../ai_harness/rules/assurance.md) → Eval as a Gate, Dataset Governance; no PCO check. A consumer's gates are its own, declared in its `REPO_CONTRACT.md`.
- Online-to-offline loop (production failures become regression cases): required by [assurance.md](../ai_harness/rules/assurance.md) → Online-to-Offline Loop; no PCO check.
- Incident reports in `audit/incidents/` from the [incident template](../templates/incident_report.md): required by [assurance.md](../ai_harness/rules/assurance.md) → Incident Capture; no PCO check.

## Rules

- [assurance.md](../ai_harness/rules/assurance.md)
- [governance-provenance.md](../ai_harness/rules/governance-provenance.md)

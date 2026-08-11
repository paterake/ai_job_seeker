---
description: Assurance and eval governance rules. Loaded when editing Python or YAML in any governed repo.
globs:
  - "**/*.py"
  - "**/*.yaml"
  - "**/*.yml"
---

> Governance narrative: [assurance spoke](../../assurance/README.md)

# Assurance and Evaluation Rules

## Eval as a Gate (Non-Negotiable)

- Evals are blocking gates, not advisory reporting. Metrics that do not gate real outcomes are metrics theatre.
- "Should work" is not a threshold. The measurable property and the minimum acceptable score must be explicit and versioned.
- Any threshold change is a governance change — it requires regression evidence before taking effect.
- Self-evaluation (same model evaluating itself) is high-risk; permitted only as advisory. Known failure modes must be documented before use.

## Evaluation Units

A passing output-level eval while taking an unsafe or wasteful tool trajectory is a failure mode, not a pass. Evaluation is required at three levels:

- **Output-level**: score the final artefact against explicit criteria
- **Trajectory-level**: score the sequence of tool calls and decisions, not just the final output
- **Thread-level**: score multi-turn coherence, not only individual turns

## Dataset Governance

- Eval datasets are versioned artefacts. CI must pin to a specific dataset version; floating latest is prohibited.
- Named splits must be explicit (e.g. `ci_smoke`, `ci_regression`, `nightly`, `red_team`).
- Production failures become permanent regression cases — never discarded.

## Workflow Plan and Required Suites

- Required eval suites are declared and scheduled as part of the workflow plan.
- The run evidence records which suites were required, which were executed, and the dataset versions/splits used.

## Evaluator Calibration

- Evaluators are sensors. Sensor silence is not evidence of correctness — validate periodically that a sensor can detect what it claims to cover.
- For adversarial review loops: evaluator context must not share the same synthesis path as the primary agent output.
- If the evaluator model or rubric changes, re-baseline against pinned historical results before treating new scores as comparable.

## Online-to-Offline Loop (Required)

- Offline eval gates changes. Online eval monitors production. Production failures must become offline regression cases — validated offline, then confirmed by online monitoring.
- A system that detects production failures but does not convert them into regression cases has a broken improvement mechanism.

## Incident Capture (Required)

- When an incident or near miss occurs, file an incident report in `audit/incidents/` using `audit/templates/incident_report.md`.
- If the incident produces a governance change, the incident report must cross-reference the affected governance surface(s): rule file(s) under `ai_context/pco/ai_harness/rules/` and/or registry entry IDs in `ai_context/pco/governance/*_registry.yaml`.
- If a governance change is justified by an incident, the change record (approval, PR, or run evidence) must link back to the incident report.

**Canonical reference:** [assurance spoke](../../assurance/README.md)

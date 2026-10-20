---
description: Assurance and eval governance rules. Loaded when editing eval code, eval datasets or audit records.
globs:
  - "**/eval*/**"
  - "**/*eval*.py"
  - "**/*eval*.yaml"
  - "audit/**"
basis: operational-experience
spoke: assurance
paths:
  - "**/eval*/**"
  - "**/*eval*.py"
  - "**/*eval*.yaml"
  - "audit/**"
applyTo: "**/eval*/**,**/*eval*.py,**/*eval*.yaml,audit/**"
---

> Governance narrative: [assurance spoke](../../assurance/README.md)

# Assurance and Evaluation Rules

## Error Analysis Before Gates

- Before building an eval gate, read real traces and failures and name the failure modes. The first suite is
  20–50 tasks drawn from those failures, scored by explicit pass/fail checks, not generic metrics.
- Keep capability evals (new behaviour, expected to start low) separate from regression evals (expected to stay
  passing). An LLM judge is validated against human labels before it gates.
- **Consequence:** a suite built before any failure is seen measures guesses, so it passes while real failures ship.

## Eval as a Gate (Non-Negotiable)

- Evals are blocking gates, not advisory reporting. Metrics that do not gate real outcomes are metrics theatre.
- "Should work" is not a threshold. The measurable property and the minimum acceptable score must be explicit and versioned.
- Any threshold change is a governance change — it requires regression evidence before taking effect.
- Self-evaluation (same model evaluating itself) is high-risk; permitted only as advisory. Known failure modes must be documented before use.

## Evaluation Units

A passing output-level eval while taking an unsafe or wasteful tool trajectory is a failure mode, not a pass. Evaluation is required at each level that applies:

- **Output-level** (always): score the final artefact against explicit criteria
- **Trajectory-level** (agents and tool loops): score the sequence of tool calls and decisions, not just the final output
- **Thread-level** (multi-turn products only): score multi-turn coherence, not only individual turns.

## Dataset Governance

- Eval datasets are versioned artefacts. CI must pin to a specific dataset version; floating latest is prohibited.
- Each dataset version that gates or scores behaviour declares its provenance: source, how cases were produced, and owner.
  **Consequence:** a gold set of unknown origin cannot be checked for leakage or for sharing the evaluated output's synthesis path, so the gate it drives proves nothing.
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

- When an incident or near miss occurs, file an incident report in `audit/incidents/` using `ai_context/pco/templates/incident_report.md`.
- If the incident produces a governance change, the incident report must cross-reference the affected governance surface(s): rule file(s) under `ai_context/pco/ai_harness/rules/` and/or registry entry IDs in `ai_context/pco/governance/*_registry.yaml`.
- If a governance change is justified by an incident, the change record (approval, PR, or run evidence) must link back to the incident report.

**Canonical reference:** [assurance spoke](../../assurance/README.md)

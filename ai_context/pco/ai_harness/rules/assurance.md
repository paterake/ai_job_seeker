---
description: Assurance and eval governance rules. Loaded when editing eval code, eval datasets or audit records.
basis: operational-experience
spoke: assurance
paths:
  - "**/eval*/**"
  - "**/*eval*.py"
  - "**/*eval*.yaml"
  - "audit/**"
  - "**/test_*.py"
  - "**/test_catalogue.yaml"
---

> Governance narrative: [assurance spoke](../../assurance/README.md)

# Assurance and Evaluation Rules

## Test Catalogue (Required)

- A repo's tests are a fixed catalogue: every test file is listed under the delivered feature it proves (each served
  surface end to end, its safety invariants, the goldens consumers depend on, the eval gates CI runs), with its test
  count, and a gate fails on an unlisted file, a gone file or a changed count.
- A change keeps the catalogued tests passing and adds none: no test for a fix, a review finding, a historical item,
  a library swap or an agent task. A new test is added only for a newly delivered capability, through a catalogue
  edit below.
- Agents own every catalogue edit, each gated by an independent reviewer's PASS ([HUB.md](../../governance/HUB.md) →
  Independent review pattern); the reviewer is trusted with this because it judges in a fresh context, so the
  "self-evaluation is advisory only" limit (Eval as a Gate) does not apply to it. The operator is involved only when
  the reviewer returns ESCALATE. The catalogue edits are: a new test for a newly delivered capability (the reviewer
  checks it proves a capability and is not a fix, a finding or a task in disguise); a change to a test's setup only,
  its assertions unchanged; test names and docstrings; moving tests between files or features, with the counts
  adjusted; lowering an eval floor when its cases go with a dropped feature; dropping a stale or wrong test (below).
- A failing catalogue test is classified as regression, stale or wrong. Regression: fix the product. Stale (the
  behaviour changed by a recorded decision, such as a library adoption or version change or a dropped feature) or
  wrong (it pins layout, private internals or one library version, or forces a workaround in the product): fix its
  setup or drop it, with the catalogue count lowered, when the change shows all of: the cause (the decision, or the
  defect in the test); what the test checked, what happens now, and why that difference is intended, not a
  regression; and the authorisation, secrets and redaction and provenance tests passing unchanged. The reviewer
  checks each drop against these and returns REVISE when one is missing, when the product was bent to satisfy a
  test, or when a test was bent or dropped to hide a regression; an agent that cannot make the case stops and
  reports; the commit message lists every test dropped. If the dropped test's behaviour still matters, the agent adds
  a fresh capability test as a catalogue edit above.
  Never: dropping or weakening a test of authorisation, secrets and redaction or provenance; re-aiming a dropped test
  at the new behaviour; rewriting an assertion to get green; dropping a test whose failure the cause does not explain
  (that is a regression, and it is fixed).
- **Consequence:** without a fixed catalogue every change adds tests (one consumer repo grew to about 4,500 tests,
  a third of its commits adding some, and kept about 760 after a purge); the suite then measures change history, not
  intent, costs more effort than the work, and hides which tests prove what the repo delivers.
  A test that pins the code an adoption replaces, or one library version, blocks the adoption the OSS preference
  asks for (`code-architecture.md` → Low-Code / OSS Preference) and turns every upgrade into a test rewrite.
  Routing catalogue edits to the operator burned delivery cycles on test shaping and kept the operator in test
  management; a test an agent must work around is itself likely wrong.

## Error Analysis Before Gates

- Before building an eval gate, read real traces and failures and name the failure modes. The first suite is
  20–50 tasks drawn from those failures, scored by explicit pass/fail checks, not generic metrics.
- Keep capability evals (new behaviour, expected to start low) separate from regression evals (expected to stay
  passing). An LLM judge is validated against human labels before it gates.
- **Consequence:** a suite built before any failure is seen measures guesses, so it passes while real failures ship.

## Eval as a Gate (Non-Negotiable)

- Evals are blocking gates, not advisory reporting. Metrics that do not gate real outcomes are metrics theatre.
- "Should work" is not a threshold. The measurable property and the minimum acceptable score must be explicit and versioned.
- Any threshold change is a governance change — it requires regression evidence before taking effect. The one
  exception is lowering a floor whose cases go with a dropped feature, which is a catalogue edit (Test Catalogue).
- Self-evaluation is advisory only ([HUB.md](../../governance/HUB.md) → Independent review pattern); its known failure modes must be documented before use.
- **Consequence:** an advisory eval or an unstated threshold lets a regression ship with a passing report, and a
  threshold lowered without evidence hides the regression it was set to catch.

## Evaluation Units

A passing output-level eval while taking an unsafe or wasteful tool trajectory is a failure mode, not a pass. Evaluation is required at each level that applies:

- **Output-level** (always): score the final artefact against explicit criteria
- **Trajectory-level** (agents and tool loops): check the tool calls for safety violations and waste; do not require a particular path, because the outcome is what is graded
- **Thread-level** (multi-turn products only): score multi-turn coherence, not only individual turns.
- Where a task is run k times, reliability is pass^k: all k trials succeed; a pass@k (any-success) score hides flaky behaviour that fails in production.
- **Consequence:** an output-only eval passes an agent that reached the right answer through an unsafe or wasteful
  path, and that path is what runs in production.

## Dataset Governance

- Eval datasets are versioned artefacts. The eval runner must pin to a specific dataset version; floating latest is prohibited.
- Each dataset version that gates or scores behaviour declares its provenance: source, how cases were produced, and owner.
  **Consequence:** a gold set of unknown origin cannot be checked for leakage or for sharing the evaluated output's synthesis path, so the gate it drives proves nothing.
- Named splits must be explicit (e.g. `ci_smoke`, `ci_regression`, `nightly`, `red_team`).

## Workflow Plan and Required Suites

- Required eval suites are declared and scheduled as part of the workflow plan.
- The run evidence records which suites were required, which were executed, and the dataset versions/splits used.
- **Consequence:** without the required set on record, a skipped suite is indistinguishable from a passed one.

## Evaluator Calibration

- Evaluators are sensors. Sensor silence is not evidence of correctness — validate periodically that a sensor can detect what it claims to cover.
- Adversarial review loops follow the independence pattern ([HUB.md](../../governance/HUB.md) → Independent review pattern).
- If the evaluator model or rubric changes, re-baseline against pinned historical results before treating new scores as comparable.
- **Consequence:** an uncalibrated evaluator reports silence as correctness, and a score from a changed evaluator
  is read as a change in the system under test.

## Online-to-Offline Loop (Required)

- Offline eval gates changes. Online eval monitors production. Production failures must become permanent offline regression cases — validated offline, then confirmed by online monitoring.
- **Consequence:** a system that detects production failures but does not convert them into regression cases has a
  broken improvement mechanism: the same failure ships again.

## Incident Capture (Required)

- When an incident or near miss occurs, file an incident report in `audit/incidents/` (created with the first record) using `ai_context/pco/templates/incident_report.md`.
- If the incident produces a governance change, the incident report must cross-reference the affected governance surface(s): rule file(s) and/or registry entry IDs (where each registry lives: [CONTRACT.md](../../governance/CONTRACT.md) → Exceptions, Capability Lifecycle, Policy Packs).
- If a governance change is justified by an incident, the change record (approval, PR, or run evidence) must link back to the incident report.
- **Consequence:** an unrecorded incident recurs as a one-off, and a rule with no link to its incident cannot be
  re-validated or retired on evidence.

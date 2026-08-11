# Assurance & Evals (Spoke)
> DAMA mapping: Data Quality Management → Assurance, Evals & Continuous Improvement

## Purpose

Ensure agent behaviour and outputs are correct, safe, and improving over time through measurable gates (evals), regression protection, and disciplined post-incident learning.

## PCO Emphasis

- Policy: defines what "correct and safe" means, sets thresholds, and decides gating strength by risk tier
- Control plane: enforces blocking gates and release constraints; routes work through review and verification
- Observability: records eval outcomes, regressions, incidents, and trend signals to drive improvement

## Scope (what this spoke governs)

### Evaluation taxonomy

- Behavioural evals (role adherence, instruction following under constraints)
- Safety evals (injection resilience, data handling, tool misuse resistance)
- Quality evals (correctness, completeness, maintainability proxies)
- Operational evals (reliability of workflows, loop stability)

### Evaluation units (what an eval measures)

Evaluation is governed at three distinct units. A mature programme uses all three.

- **Output-level**: score the final artefact (answer, patch, report) against criteria
- **Trajectory-level**: score the sequence of tool calls and decisions (the path), not just the output
- **Thread-level**: score multi-turn coherence across a conversation, not only individual turns

### Gating and regression

- Blocking gates vs advisory scoring
- Regression protection for policy/tool/model changes
- Release gating and staged rollouts

### Continuous improvement loop

- Incident → root cause → corrective actions (policy/tool/eval updates)
- Calibration of rubrics and thresholds
- Reduction of false positives/negatives over time

### Evaluation patterns (named)

Governance recognises these patterns explicitly so projects do not invent inconsistent "testing" semantics.

- **Human evaluation**: structured review against a rubric; used for ambiguous or high-impact judgement calls
- **LLM-as-judge**: a separate model evaluates against explicit criteria; evaluator is treated as a governed component
- **Self-evaluation** (high risk): the same model evaluates itself; allowed only as advisory and only with known failure modes documented

## Governance Controls (hub decisions)

### Risk-tiered gating policy

Governance defines, per risk tier:
- Mandatory eval suites and thresholds
- When human review is used
- Which failures are blocking vs advisory

### Threshold governance (what "passing" means)

Blocking evals require explicit, versioned thresholds.

- Thresholds are declared per suite and risk tier and are treated as policy
- Any threshold change is a governance change and is rolled out with regression evidence
- "Should work" is not a threshold; the measurable property and the minimum acceptable score are stated explicitly

### Release policy for changes

Governance defines:
- What constitutes a breaking change (policy/tool/workflow/model)
- Eval coverage before rollout
- Compatibility expectations and rollback rules

### Evaluator governance and calibration

Evaluators are sensors. Sensor claims are validated.

- **Sensor silence ambiguity**: a rarely-firing sensor is validated periodically; silence is not evidence of correctness
- **Evaluator drift**: if the evaluator model or rubric changes, re-baseline and compare against pinned historical results
- **Independence**: for adversarial review loops, evaluator context does not share the same synthesis path as the primary agent output

### Evidence standards

Governance defines what is recorded:
- Eval run identifiers and versions
- Thresholds applied and outcomes
- Links between incidents and the corrective actions taken

## Artefacts and Surfaces (examples)

- Eval catalogue (ID, purpose, unit, method, owner, thresholds, scope)
- Regression suites tied to policy/tool/workflow/model versions
- Review rubrics and calibration guidance (including "sensor silence" validation approach)
- Eval datasets as governance contracts (splits, versions, pinned baselines)
- Incident post-mortem template and improvement backlog
- Rollout playbooks (staged rollout, canary, rollback)

### Dataset governance (splits, versions, pinning)

Eval datasets are versioned artefacts with explicit structure.

- Named splits (e.g., `ci_smoke`, `ci_regression`, `nightly`, `red_team`)
- Snapshotting/versioning when examples change, with CI pinned to a specific dataset version
- Promotion path for new examples: curated intake, de-duplication, and threat/quality tagging

### Test design patterns

- **Property-based evaluation**: define quality as explicit properties; use an evaluator to score properties; validate the evaluator itself
- **Example-based tests (open–closed)**: add new cases via data files, keep test logic stable so "CI passed" has consistent meaning
- **Adversarial dataset growth**: expand datasets iteratively using a structured threat taxonomy; failures become permanent regression cases

### Online-to-offline feedback loop (named lifecycle pattern)

- Offline eval during development gates changes
- Online evaluation in production monitors for degradation and emergent failures
- Production anomalies are converted into offline regression examples, validated, and then confirmed by online monitoring

## Enforcement Rules

Canonical enforcement: [assurance.md](../ai_harness/rules/assurance.md) and [operations.md](../ai_harness/rules/operations.md)

Covers: eval as a blocking gate (not advisory), three evaluation units (output/trajectory/thread), dataset governance (versioned artefacts, named splits, CI-pinned), evaluator calibration, online-to-offline feedback loop, and incident capture requirements.

## Enforcement Points (where the control plane enforces)

### Pre-run

- Risk tier is determined and gating policy selected
- Dataset version and split are selected and recorded per suite

### In-run

- Blocking gates enforced before high-impact actions complete
- Review loops enforced (adversarial review independence preserved)

### Post-run

- Verification results and eval outcomes recorded into evidence
- Regression dashboards updated and alerts triggered on failures
- Improvement actions created when failures or incidents occur
- Offline-to-online linkage recorded (which production failure became which regression case)

## Evidence and Metrics (what observability measures)

- Eval pass rate by suite and risk tier (trend and variance)
- Pass rate by evaluation unit (output vs trajectory vs thread)
- Regression incidents after policy/tool/model changes
- False positive/negative rates for key safety and quality gates
- Evaluator agreement and calibration metrics (human–judge, judge–judge where applicable)
- Mean time to detect and contain unsafe behaviour
- Repeat incident rate (did improvements actually reduce recurrence)
- Online evaluator sampling rate and cost per monitored run

## Common Failure Modes

- One-off evaluation: tests are run once, not maintained
- Metrics theatre: scores exist but do not gate real outcomes
- Over-gating: too many blocking checks slow delivery without improving safety
- Under-gating: unsafe behaviours escape because gates are advisory or absent
- Output-only evaluation: the agent "passes" while taking unsafe or wasteful tool trajectories
- Dataset drift: "CI passed" meaning changes silently because examples changed without pinning

## Maturity Model (pragmatic)

### Level 1: Basic assurance

- Some blocking gates exist for critical safety/correctness
- Review loop exists for high-impact workflows
- Eval outcomes are recorded

### Level 2: Regression-protected governance

- Policy/tool/workflow changes require eval coverage
- Regressions trigger rollbacks or controlled containment
- Rubrics and thresholds are calibrated over time

### Level 3: Continuous improvement system

- Incident learnings systematically produce policy/tool/eval improvements
- Drift is detected early and corrected with minimal disruption
- The harness improves measurably without weakening governance

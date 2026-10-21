# Architecture (Spoke)
> DAMA mapping: Data Architecture → Agent Architecture

## Governs

- Driver and pattern choice, simplest first ([code-architecture.md](../ai_harness/rules/code-architecture.md) → Driver Selection)
- Workflow patterns: prompt chaining, routing, parallelisation, orchestrator–workers and evaluator–optimizer are
  common patterns, not a closed list; autonomous agents are within Driver Selection
- Code structure: config purity, reuse and shared-code home, one responsibility per file, modular entry points,
  UV-only Python
- The boundary between the synced PCO layer and a repo's project-additive content
- Independent review ([governance/HUB.md](../governance/HUB.md) → Independent review pattern)

## Enforced

- No raw Python commands (UV only): validator `governance-audit --fail`, scope as in
  [governance/HUB.md](../governance/HUB.md) → Enforced ([code-architecture.md](../ai_harness/rules/code-architecture.md) →
  Python Tooling (UV Only)); pip, Poetry, Pipenv, Conda and venv use is not detected (human review).
- A consumer's `REPO_CONTRACT.md` exists, has the required sections and maps only real spokes: validator
  `validate --scope governance|full` ([CONTRACT.md](../governance/CONTRACT.md)).
- The synced PCO layer is not edited in a consumer: hook `check_guard.sh` (file-edit tools only) and validator
  `validate` (reports drift after the fact; the default `--scope harness` covers `ASSISTANTS.md`, `AGENTS.md` and
  `ai_harness/`, and only `--scope full` covers the whole synced tree)
  ([hooks/README.md](../ai_harness/hooks/README.md)).
- Driver choice: human review at code review ([harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)
  → Capability Decisions Are Reviewed, Not Gated).
- Config purity, code reuse gate and shared-code home, one responsibility per file, modular entry points: human
  review ([code-architecture.md](../ai_harness/rules/code-architecture.md) → Config Purity, Code Reuse Gate, One Responsibility
  Per File, Modular Entry Points; [governance/HUB.md](../governance/HUB.md) → Platform Pillars).
- Independent review: human review; no hook or validator checks independence
  ([governance/HUB.md](../governance/HUB.md) → Independent review pattern).

## Not enforced

- There is no orchestrator, tool broker or admission control: workflow pattern, topology and tool entitlements
  are not checked before or during a run (target, not implemented).
- Hard-coded domain strings and oversized multi-concern files: required by
  [code-architecture.md](../ai_harness/rules/code-architecture.md) → Config Purity, One Responsibility Per File; no PCO check.

## Rules

- [code-architecture.md](../ai_harness/rules/code-architecture.md)
- [AGENTS.md](../AGENTS.md) → Before you start
- [CONTRACT.md](../governance/CONTRACT.md)
- [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)

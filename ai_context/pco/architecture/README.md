# Architecture (Spoke)
> Area: Agent Architecture

## Governs

- Driver and pattern choice, simplest first ([code-architecture.md](../ai_harness/rules/code-architecture.md) → Driver Selection)
- Workflow patterns: prompt chaining, routing, parallelisation, orchestrator–workers and evaluator–optimizer are
  common patterns, not a closed list; autonomous agents are within Driver Selection
- Code structure: config purity, reuse and shared-code home, one responsibility per file, modular entry points,
  UV-only Python
- The boundary between the synced PCO layer and a repo's project-additive content

## Enforced

- No raw `python`/`python3` commands (UV only): validator `governance-audit --fail` (Python command scan, run from
  `ai_agent_pco`) ([code-architecture.md](../ai_harness/rules/code-architecture.md) → Python Tooling (UV Only)).
- A consumer's `REPO_CONTRACT.md` exists, has the required sections and maps only real spokes: validator
  `validate --scope governance|full` ([CONTRACT.md](../governance/CONTRACT.md)).
- The synced PCO layer is not edited in a consumer: [knowledge spoke](../knowledge/README.md) → Enforced.
- Driver choice: human review at code review ([harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)
  → Capability Decisions Are Reviewed, Not Gated).
- Config purity, code reuse gate and shared-code home, one responsibility per file, modular entry points: human
  review ([code-architecture.md](../ai_harness/rules/code-architecture.md) → Config Purity, Code Reuse Gate, One Responsibility
  Per File, Modular Entry Points; [governance/HUB.md](../governance/HUB.md) → Platform Pillars).

## Not enforced

- Workflow pattern and topology are not checked before or during a run; no PCO check (the control plane that would
  host such checks: [governance/HUB.md](../governance/HUB.md) → Not enforced).
- Hard-coded domain strings and oversized multi-concern files: required by
  [code-architecture.md](../ai_harness/rules/code-architecture.md) → Config Purity, One Responsibility Per File; no PCO check.
- No `pip`, Poetry, Pipenv, Conda or ad-hoc virtualenv workflows: required by code-architecture.md → Python Tooling
  (UV Only); no PCO check (the scan sees raw `python` commands only).
- Reuse of the shared primitives layer (`ai_agent_core`) for LLM calls: required by code-architecture.md → AI
  Infrastructure Primitives; no PCO check.
- `ai_agent_core`'s Platform Contract Implementations declaration: required by
  [CONTRACT.md](../governance/CONTRACT.md) → Special Case: `ai_agent_core`; no PCO check.

## Rules

- [code-architecture.md](../ai_harness/rules/code-architecture.md)
- [AGENTS.md](../AGENTS.md) → Before you start
- [CONTRACT.md](../governance/CONTRACT.md)
- [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)

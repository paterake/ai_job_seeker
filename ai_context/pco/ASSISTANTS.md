# AI Assistant Guide — Platform (PCO)

**Shared context for all coding assistants (Claude, Qwen, Trae, GitHub Copilot).**

**Read this BEFORE starting any work.**

> **Copilot note**: Copilot has no hook-execution lifecycle equivalent to Claude Code's `settings.json` `PreToolUse`/`Stop` hooks. Rules and skills are enforced the same way as the other three (auto-discovered from `.claude/rules/` and `.claude/skills/`), but the git-push gate, exception-expiry check, and execution-limits check in `.claude/hooks/` are not enforced for Copilot sessions. Treat this as a known limitation, not a silent gap — see `harness-tool-contract.md`.

## Platform Pillars (Non-Negotiable — Apply to All Work)

Six blocking pillars apply to all work in all governed repos. Violating any one is
non-conformant regardless of other correctness.

> **Intentional duplication note**: the pillar definitions also appear in [governance/HUB.md](governance/HUB.md) (canonical narrative source) and in `docs/concept/PCO_CONTRACT.md` (stakeholder-facing declaration). This copy is kept here deliberately — ASSISTANTS.md loads at every session start, so agents need the pillars in context without reading HUB.md. The "Rule file" column is additive content not present in HUB.md. Do not deduplicate this table away.

| Pillar | Consequence of violation | Rule file |
|---|---|---|
| **UV only** | Introduces competing env/dep toolchains; reproducibility breaks; onboarding forks | `governance.md` — Python Tooling |
| **Config drives code** | Domain strings baked into source; code cannot be reused across datasets without rewrite | `governance.md` — Config Purity |
| **Low-code/OSS preference** | Custom re-implementations of solved problems accumulate as maintenance debt | `governance.md` — Low-Code/OSS Preference |
| **Context minimisation** | Earlier rules lose weight as session grows; constraints silently stop holding | `context-economy.md` — Context Minimisation |
| **Token management** | Long sessions regenerate instead of reusing; cost scales with domain churn | `context-economy.md` — Token Management |
| **No domain context in code** | Same as Config drives code — these are one rule stated twice for emphasis | `governance.md` — Config Purity |

Pillars 2+6 = one rule (code is mechanism; domain context is config).
Pillars 4+5 = one rule (long sessions accumulate noise; short sessions with durable state are the model).

---

## Deterministic Router (Task → Required Reads)

Rule files under `.claude/rules/` are **already in your context** via auto-loaded globs — do not re-read them. Use the two tables below: the first identifies which rules apply to your task; the second lists governance docs that need an explicit read.

### Rule files — already in context (identify and apply, no read needed)

| Task type | Relevant rule |
|---|---|
| Any code change | `agent-behavior.md` — pre-implementation gate, simplicity, surgical changes, verification · `governance.md` — UV-only, config drives code, file structure, OSS preference, docs currency |
| LLM-calling modules (timeouts, budgets, tracing) | `operations.md` |
| Retrieval / RAG changes | `retrieval.md` |
| Publishing / disclosure risk | `publication.md` |
| Harness switch / model upgrade / edit-tool format | `harness-tool-contract.md` |
| Security / sensitive tooling | `security-threat-model.md` |
| Evaluations / assurance changes | `assurance.md` |
| Authoring/changing governance rules; scope-of-validation or rule provenance | `governance-provenance.md` |
| Data residency, data-subject rights, IP/output ownership, retention/legal hold | `compliance-lifecycle.md` |

### Governance docs — read explicitly (not auto-loaded)

| Task type | Read explicitly |
|---|---|
| `ai_context/` structure or anti-drift | [CONTRACT.md](governance/CONTRACT.md) |
| Anti-drift / "no duplication" questions | [ANTI_DRIFT.md](governance/ANTI_DRIFT.md) |
| Repo concern profile / what belongs in ai_context | [CONCERNS.md](governance/CONCERNS.md) |
| Backlog / multi-session work | [AI_ASSISTANT_BACKLOG_CONTINUITY.md](governance/AI_ASSISTANT_BACKLOG_CONTINUITY.md) |
| Domain-specific implementation notes for this repo | `project/{domain}/README.md` |

## After Reading This File

Read **[../project/ASSISTANTS.md](../project/ASSISTANTS.md)** — repo-specific posture, local task routing, and active backlog.
Then follow the routing table above for any task-specific reads.

## Anti-Drift Contract

Documentation drift is a governance failure. Canonical rules live in [ANTI_DRIFT.md](governance/ANTI_DRIFT.md).

## Concern Profiles

Concern profiles and their rationale live in [CONCERNS.md](governance/CONCERNS.md).

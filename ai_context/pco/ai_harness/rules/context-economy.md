---
description: Context economy rules — context minimisation and token management. Applies to all sessions and agentic work in governed repos.
globs:
  - "**/*.md"
  - "**/*.py"
  - "**/*.yaml"
---

> Governance narrative: [behaviour spoke](../../behaviour/README.md)

# Context Economy Rules

## Why This Matters

Long sessions accumulate context noise. Earlier constraints, architectural rules, and style
invariants compete with growing task-specific signals. They are not ignored — they are lower-weight
signals in a saturated context. This is not a model failure; it is a structural problem with how
work is organised. These rules address it structurally.

## Context Minimisation

- Prefer durable documents over long sessions. Work that spans multiple sessions must use an
  anchor doc (backlog continuity pattern — see `ai_context/pco/governance/AI_ASSISTANT_BACKLOG_CONTINUITY.md`) so each
  session starts warm from recorded state, not transcript archaeology. One session per task is
  the primary model, not a fallback — see [behaviour/README.md](../../behaviour/README.md)
  (Session Design and Token Economy) for the full operator pattern.
- **Anchor doc structural requirement (non-negotiable):** any TODO file serving as an anchor
  document is incomplete without all four of these sections:
  1. Continuity header — states current status, next item, and "read X before touching code"
  2. `## Accumulated Active Constraints` — placeholder if no items complete yet; grows as each
     item establishes new invariants that subsequent sessions must honour
  3. Per-item verification commands — exact commands, not "should work"
  4. `## Gotchas` — placeholder if empty; fills as friction is discovered
  A missing `Accumulated Active Constraints` section is the most common failure: constraints
  established by early items silently disappear from later sessions.

  **Consequence:** an anchor doc without these sections is a handoff that will fail — the next
  session re-derives constraints from context (expensive, unreliable) rather than reading them
  as stated facts.
- Do not re-derive what is already recorded. If a decision, constraint, or plan exists in a
  durable document, load it — do not reconstruct it from memory or prior chat.
- Scope each session to one coherent slice. Do not accumulate multiple unrelated concerns in a
  single session — earlier constraints fade under the weight of later task-specific signals.
- Prefer targeted reads (specific file, specific section) over broad reads of entire file trees
  to answer a focused question.

## Token Management

- Long-running sessions that resolve a single ask by accumulating large context are an anti-pattern.
  Design work in chapters: one anchor doc item per session.
- Config-driven code directly reduces token burn: an existing piece of code reused via config change
  eliminates the probability of re-implementation. This is a consequence of the Config Purity rule
  (see `governance.md`), not an independent rule.
- Domain context in code forces regeneration. When the domain changes, code with baked-in domain
  assumptions cannot be reused — a new implementation is triggered. Keep domain context in config
  so the same mechanism is reused across runs and domains.
- Proliferation of near-identical implementations is a token economy failure: multiple files
  performing similar operations on slight domain variations is the symptom of domain context leaking
  into code. Treat it as a governance violation, not just a code smell.

## The Connection Between Rules

These rules are not independent. They form a reinforcing set:

- Config purity → code is reusable → fewer reimplementations → fewer token-intensive sessions
- Anchor doc pattern → each session starts warm → no context saturation → constraints hold
- OSS preference → less custom code → less maintenance surface → less regeneration pressure
- No domain context in code → same mechanism runs across domains → no "create new version for X" asks

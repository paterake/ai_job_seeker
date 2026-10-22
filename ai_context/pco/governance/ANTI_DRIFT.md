# Anti-Drift Contract (Single Source of Truth)

## Purpose

Prevent documentation drift and stale duplication in a governed repo, across:
- assistant-facing context (`ai_context/`)
- human-facing docs (`docs/`)
- operational scripts (`scripts/`)

## Rules

- Each behavioural contract has exactly one canonical home. Every other mention is a link or a one-line pointer.
- Where each related rule lives:
  - an `ai_context/` change that alters a doc: `ai_harness/rules/ai_context_sync.md`;
  - a code or config change that alters a doc: `ai_harness/rules/code-architecture.md` → Docs Currency;
  - which doc owns which kind of fact: [DOCS_CONTRACT.md](DOCS_CONTRACT.md) → Segregation Rules;
  - product artefacts never cite PCO paths: [CONTRACT.md](CONTRACT.md) → Downstream Conformance Contract;
  - `ai_context/pco/` is read-only in a consumer: [AGENTS.md](../AGENTS.md) → Governance changes.

**Consequence:** a second copy of a contract drifts the next time either copy changes, and an agent reading the
stale one acts on it.

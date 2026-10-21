---
description: Retrieval and RAG rules. Loaded when editing retrieval, query, or ingestion code.
basis: operational-experience
spoke: knowledge
paths:
  - "**/retriev*/**"
  - "**/ingest*/**"
  - "**/query*/**"
---

> Governance narrative: [knowledge spoke](../../knowledge/README.md)

# Retrieval Rules

## Chunking

- Do not introduce multiple chunkers without an explicit design decision recorded in `INTENT.md` → Decisions.
- Keep chunking parameters in configuration, not code.
- **Consequence:** a second chunker splits the same corpus two ways, so retrieval quality changes with no recorded
  decision to explain it.

## Hybrid Search Contract

- Use the simplest retrieval that meets the task (simplest-first; order: [knowledge spoke](../../knowledge/README.md)
  → Retrieval decision hierarchy). Hybrid search is added only where the task needs it.
- Where hybrid search is used, its legs are merged, and reranking is a later step of the same hierarchy; any leg
  bypass requires an explicit config flag and a rationale.
- **Consequence:** an unneeded or silently bypassed leg adds cost and failure surface, or drops recall, with no
  trace of why.

## Quality Gate

- Results must carry provenance (citation IDs); never return raw text without traceability.
- If the quality gate fails: return a structured low-confidence result; do not silently return empty.
- **Consequence:** an untraceable or silently empty result looks like a valid answer, so retrieval failures reach
  users unseen.

## Tests

- Unit tests must not require live vector DBs or live model servers; use fixtures/fakes.
- Integration tests must be explicitly gated and opt-in.
- **Consequence:** tests that need live services fail for reasons unrelated to the code, and get skipped.


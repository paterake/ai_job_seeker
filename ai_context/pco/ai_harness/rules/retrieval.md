---
description: Retrieval and RAG rules. Loaded when editing retrieval, query, or ingestion code.
globs:
  - "**/retriev*/**"
  - "**/ingest*/**"
  - "**/query*/**"
---

> Governance narrative: [knowledge spoke](../../knowledge/README.md)

# Retrieval Rules

## Chunking

- Do not introduce multiple chunkers without an explicit design decision recorded in the human docs.
- Keep chunking parameters in configuration, not code.

## Hybrid Search Contract

- Treat hybrid search as a first-class contract: sparse + dense legs, merged and reranked.
- Any leg bypass requires an explicit config flag and a rationale.

## Quality Gate

- Results must carry provenance (citation IDs); never return raw text without traceability.
- If the quality gate fails: return a structured low-confidence result; do not silently return empty.

## Tests

- Unit tests must not require live vector DBs or live model servers; use fixtures/fakes.
- Integration tests must be explicitly gated and opt-in.


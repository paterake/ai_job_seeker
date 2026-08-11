---
description: Sync trigger fired when any ai_context/ file is edited. Ensures prescriptive AI-facing changes propagate to human-facing documentation.
globs:
  - "ai_context/**"
---

# ai_context → Human Docs Sync

Any change to a file in `ai_context/` must be reflected in the appropriate human-facing documentation under `docs/`.

See `ai_context/pco/governance/ANTI_DRIFT.md` for the canonical edit rules and action steps.

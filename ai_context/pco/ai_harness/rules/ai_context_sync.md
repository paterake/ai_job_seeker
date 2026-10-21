---
description: Sync trigger fired when any ai_context/ file is edited. Keeps the repo's human docs in step with its assistant-facing context.
basis: operational-experience
spoke: knowledge
paths:
  - "ai_context/**"
---

> Governance narrative: [knowledge spoke](../../knowledge/README.md)

# ai_context → Human Docs Sync

When a change in `ai_context/` alters what a human doc under `docs/` states, update that doc in the same change, in
the repo's own words (product docs cite no PCO paths: `ai_context/pco/governance/CONTRACT.md` → Downstream
Conformance Contract). A change that arrives by sync needs no `docs/` change unless the repo's own docs describe the
changed behaviour.

**Consequence:** a rule change with no matching doc update leaves humans and assistants working from different
facts.

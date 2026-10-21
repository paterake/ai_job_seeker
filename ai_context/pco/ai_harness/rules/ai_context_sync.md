---
description: Sync trigger fired when any ai_context/ file is edited. Keeps the repo's docs in step with its agent context.
basis: operational-experience
spoke: knowledge
paths:
  - "ai_context/**"
---

> Governance narrative: [knowledge spoke](../../knowledge/README.md)

# ai_context → Docs Sync

When a change in `ai_context/` alters what a doc under `docs/` states, update that doc in the same change, in
the repo's own words (product docs cite no PCO paths: `ai_context/pco/governance/CONTRACT.md` → Downstream
Conformance Contract). A change that arrives by sync needs no `docs/` change unless the repo's own docs describe the
changed behaviour.

**Consequence:** a context change with no matching doc update leaves an agent running the module from the docs
and an agent reading the context working from different facts.

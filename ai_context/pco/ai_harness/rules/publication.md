---
description: Publishing safety and workflow rules. Loaded when editing publishing docs, harness rules/skills, or publishing automation.
globs:
  - "publication/**/*.md"
  - "ai_context/**/*.md"
  - "ai_context/**/*.json"
  - "scripts/**/*.py"
  - "scripts/**/*.md"
basis: operational-experience
---

# Publishing Rules

## Rule Authoring Standard

Every rule must include:
- The rule (what to do or not do)
- The consequence (what risk materialises or what goal is blocked if violated)

A rule without a stated consequence is routinely overridden under pressure.

## Safety Gates

- Do not add absolute file paths or internal tooling paths to publishable content.
- Do not name the client/company or internal programme names in publishable content.
- Keep use-case-specific material in use-case-specific areas; keep framework-level context generic.

## Claim Scoping (No Overclaiming Coverage)

- A publishable governance claim must be scoped to the axis actually evidenced. "This model
  covers / answers for X" is permitted only where runtime or documented evidence for X exists.
- Where an obligation class is not yet covered, name it explicitly as a known gap or workstream.
  Do not let coverage be inferred by omission — silence that reads as completeness is an overclaim.
- **Consequence:** an artefact that implies coverage it cannot evidence falsifies the governance
  posture. One uncovered obligation found by a reviewer discredits the whole stance. Naming the
  uncovered axis is required, not optional — it converts a hidden overclaim into a credible boundary.

Downstream framework layers (e.g. a federated governance model) inherit this rule; their scope-of-claim
statements are applications of it, not independent authoring. This keeps the source, not the reflection,
as the owner of claim discipline.

## Workflow Gates

- Skills under `ai_context/pco/ai_harness/skills/` remain orchestration-only: reference canonical standards instead of restating them.
- Avoid duplicating status/todo metadata across multiple files; prefer a single source of truth and pointers.


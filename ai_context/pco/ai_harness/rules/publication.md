---
description: Publishing safety and workflow rules. Loaded when editing publishing docs, harness rules/skills, or publishing automation.
globs:
  - "publication/**/*.md"
  - "ai_context/**/*.md"
  - "ai_context/**/*.json"
  - "scripts/**/*.py"
  - "scripts/**/*.md"
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

## Workflow Gates

- Skills under `ai_context/pco/ai_harness/skills/` remain orchestration-only: reference canonical standards instead of restating them.
- Avoid duplicating status/todo metadata across multiple files; prefer a single source of truth and pointers.


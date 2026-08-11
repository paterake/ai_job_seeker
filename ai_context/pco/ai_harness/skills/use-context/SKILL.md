---
name: "use-context"
description: "Use AI context before starting tasks."
---

# Skill: Use AI Context

**Purpose:** Ensure assistants load the correct context before starting work.

## Process

- Read `ai_context/ASSISTANTS.md` first — it routes to `pco/ASSISTANTS.md` (platform router) and `project/ASSISTANTS.md` (repo-specific).
- Use the routing table in `ai_context/pco/ASSISTANTS.md` to identify which rule files apply to the task at hand.
- Load only those files. Do not read entire directories when a specific rule file is named.


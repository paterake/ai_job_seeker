---
name: "use-context"
description: "Use AI context before starting tasks."
---

# Skill: Use AI Context

**Purpose:** Ensure assistants load the correct context before starting work.

## Process

- Read `ai_context/ASSISTANTS.md` first — it routes to `pco/ASSISTANTS.md` (platform router) and `project/ASSISTANTS.md` (repo-specific).
- Rule files are already loaded in context; use the routing table in `ai_context/pco/ASSISTANTS.md` to identify which apply to the task at hand — do not re-read them.
- Read only the governance docs the router names for the task. Do not read entire directories when a specific file is named.


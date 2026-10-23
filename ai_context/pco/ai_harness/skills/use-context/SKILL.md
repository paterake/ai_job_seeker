---
name: "use-context"
description: "Loads the repo's AI context: reads ai_context/project/ASSISTANTS.md, then only the project and platform docs it routes to for the task. Use at the start of a session or task, before reading code or making changes, or when a session prompt says to load use-context."
---

# Skill: Use AI Context

**Purpose:** Ensure assistants load the correct context before starting work.

## Process

- Read `ai_context/project/ASSISTANTS.md` first (the repo's router), then the files its "Start any work" row (where present) and the task's row name.
- Rules load with the files they match; use the spoke index in `ai_context/pco/ASSISTANTS.md` to find the narrative or governance doc the task needs.
- Read only the governance docs the router names for the task. Do not read entire directories when a specific file is named.


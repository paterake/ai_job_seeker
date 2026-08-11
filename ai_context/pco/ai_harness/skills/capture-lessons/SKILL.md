---
name: "capture-lessons"
description: "Capture lessons from implementation work into ai_context/ before they are lost. Enforces selectivity: most fixes do not belong here."
---

# Skill: Capture Lessons

**Purpose:** Capture selectively. Most implementation work produces nothing that belongs in durable reference material.

## When to Invoke

- After meaningful implementation work, especially before commits that change behaviour.

## Selectivity Gate

Add something only if at least one is true:

1. Understanding changed: the work shifted how we approach a class of problems.
2. A repeatable trap exists: future work in the same area is likely to hit the same failure mode.

If neither is true, do not add anything.

## What to Capture

- A durable rule (with a consequence) that will matter again.
- A precise trap + symptom + fix that is actionable.

## Where to Add It

| Content type | Target file |
|---|---|
| A governance rule (what must hold and why) | `ai_context/pco/ai_harness/rules/<domain>.md` — add to the relevant rule file |
| A non-obvious gotcha for a specific spoke | `ai_context/pco/<spoke>/README.md` — append to the `Non-Obvious Gotchas` section |
| A repeatable trap in this repo's own operations | `ai_context/project/ASSISTANTS.md` — add to the Gotchas section |

Do not add to `ai_context/pco/ASSISTANTS.md` — it is a static router; it must not accumulate lessons.

## Report

State concisely:
- What was added (or “none”)
- Where it was added
- Why it met the selectivity gate


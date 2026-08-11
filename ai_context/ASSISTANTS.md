# AI Assistant Entry Point — ai_job_seeker

**Start here. Read both files below before doing any work.**

## Two-layer structure

`ai_context/` is split into two distinct layers with different ownership:

| Layer | Path | Owned by | Synced? |
|---|---|---|---|
| Platform (PCO) | `pco/` | The PCO — synced from ai_agent_pco | Yes |
| Project | `project/` | This repo | Never synced |

## Read order (required)

1. **[pco/ASSISTANTS.md](pco/ASSISTANTS.md)** — platform pillars, universal routing table, governance rules. Apply to all work in all governed repos.
2. **[project/ASSISTANTS.md](project/ASSISTANTS.md)** — repo-specific posture, task routing, active backlog. Apply when working in this repo specifically.

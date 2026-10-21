# AI Assistant Entry Point — ai_job_seeker

**Read on demand.** The always-loaded core is `pco/AGENTS.md`; this index routes to the rest.

## Two-layer structure

`ai_context/` is split into two distinct layers with different ownership:

| Layer | Path | Owned by | Synced? |
|---|---|---|---|
| Platform (PCO) | `pco/` | The PCO — synced from ai_agent_pco | Yes |
| Project | `project/` | This repo | Never synced |

## Where to look

1. **[pco/ASSISTANTS.md](pco/ASSISTANTS.md)** — spoke index: which DMBOK spoke and governance doc a task needs.
2. **[project/ASSISTANTS.md](project/ASSISTANTS.md)** — repo-specific posture, task routing, active backlog. Apply when working in this repo specifically.

# ai_job_seeker

An AI-assisted job-search pipeline that works on behalf of one real candidate. It turns the
candidate's CV into a structured profile, pulls live postings from public job boards, filters out
roles the candidate cannot or should not apply for, and ranks the rest into a two-section HTML
shortlist for a human to review. It never sends anything: drafting and application packets are
planned, not built, and any future submission sits behind a human approval gate.

## Status (2026-10-11)

| Stage | State |
|---|---|
| Profile (CV to structured profile) | Built |
| Ingest (live job boards, dedupe, age filter) | Built |
| Match (hard-block filter, deterministic scorer, two cohorts, HTML/MD/JSON shortlist) | Built. The optional LLM judge exists but is off by default |
| Applied-jobs tracking (local store that removes already-applied roles) | Built |
| Draft (tailored cover letter / CV) | Not built. A placeholder command only reports the backend mode |
| Packet (ready-to-send folder, human approval gate) | Not built |

The backlog and the next step are in [docs/TODO.md](docs/TODO.md).

## Repo shape

- A uv workspace with one implementation, `implementation/job_seeker/`. The canonical docs live
  at the repo root because there is only one implementation.
- Runtime config is in `implementation/job_seeker/config/`. Candidate profiles and all generated
  output sit under gitignored folders inside it.
- The LLM substrate (backend-mode switch, JSON generation, agent handoff) comes from the
  `ai_agent_core` repo, pinned to a release tag as a git dependency.
- `ai_context/` holds AI-assistant governance: `pco/` is a read-only synced platform copy and
  `project/` is owned by this repo.

## Entry chain for AI agents

1. This README.
2. [CLAUDE.md](CLAUDE.md), or [TRAE.md](TRAE.md) for Trae. Each one points to step 3.
3. [ai_context/ASSISTANTS.md](ai_context/ASSISTANTS.md): explains the two-layer context and the read order.
4. [ai_context/pco/ASSISTANTS.md](ai_context/pco/ASSISTANTS.md) (platform rules), then
   [ai_context/project/ASSISTANTS.md](ai_context/project/ASSISTANTS.md) (repo posture and non-negotiables).
5. The doc set below, read for the task in hand.

## Documentation

| Doc | Read it for |
|---|---|
| [PRD.md](PRD.md) | What the system must do: scope, contracts, trust posture, acceptance criteria |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Components, data flow, scorer design, output layout, design decisions |
| [docs/AI.md](docs/AI.md) | The optional LLM judge: backend modes, prompt layout, validation, handoff |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Every config file and key, defaults, and where secrets live |
| [docs/RUNNERS.md](docs/RUNNERS.md) | Every command, with its real flags |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | The default run, and how to recover when something fails |
| [docs/TODO.md](docs/TODO.md) | Backlog anchor |

Skills that run the pipeline from a chat prompt:
[kiera-job-search](ai_context/project/ai_harness/skills/kiera-job-search/SKILL.md) (the full run)
and [log-applied-jobs](ai_context/project/ai_harness/skills/log-applied-jobs/SKILL.md) (records
roles the candidate has applied for).

## Non-negotiables

No fabricated experience. No auto-send. No impersonation. Untrusted posting text is kept apart
from instructions. PII stays out of git. [PRD.md](PRD.md) states each one as a requirement.

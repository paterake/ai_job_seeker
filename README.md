# ai_job_seeker

An AI-assisted job-search pipeline: CV to profile, live job-board ingest, and a ranked shortlist for human review.
It has two separate components, a graduate pipeline (`implementation/job_seeker`) and a contract-role search
(`implementation/contract_search`), each with its own profile and results. It never sends anything.

- Intent, guarantees and limitations: [ai_context/project/INTENT.md](ai_context/project/INTENT.md)
- Running and recovery: [docs/RUNBOOK.md](docs/RUNBOOK.md)
- Configuration and secrets: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
- Backlog: [docs/TODO.md](docs/TODO.md)
- AI agents start at [ai_context/ASSISTANTS.md](ai_context/ASSISTANTS.md)

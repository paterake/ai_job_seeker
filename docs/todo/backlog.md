# ai_job_seeker — Backlog

Repo backlog (anchor doc). Intent and guarantees live in
[INTENT.md](../../ai_context/project/INTENT.md), operation in [RUNBOOK](../RUNBOOK.md) and config in
[CONFIGURATION](../CONFIGURATION.md); this file holds only open work, constraints, and verification.

---

## Resume (start here)

- **Status:** Profile, live ingest (Adzuna, Reed, The Muse), and dual-cohort match + rank are
  built and in use. Draft and Packet are not built.
- **Next:** none for the contract search. Open follow-ups are item 6. Stage 4 (Draft) is parked until the operator asks for it (operator 2026-10-25).
- **Before touching code, read:** [ai_context/project/ASSISTANTS.md](../../ai_context/project/ASSISTANTS.md),
  [REPO_CONTRACT.md](../../ai_context/project/governance/REPO_CONTRACT.md),
  [INTENT.md](../../ai_context/project/INTENT.md), and `## Accumulated Active Constraints` below. Stage 4 builds
  on the phase-2 judge call pattern (its guarantees are in INTENT.md).

---

## Items

| # | Item | Status | Pointer |
|---|---|---|---|
| 1 | Stage 4 — Draft: tailored cover letter + CV per shortlisted job; every claim traces to the profile | parked (operator 2026-10-25: until asked) | [INTENT → Acceptance](../../ai_context/project/INTENT.md#acceptance) |
| 2 | Stage 5 — Packet: ready-to-send folder per job; submission is a human-approval gate, no auto-send | ⬜ open | [INTENT → Acceptance](../../ai_context/project/INTENT.md#acceptance) |
| 3 | User action: review the candidate profile with Kiera — confirm `target.roles` / `remote` and the audit-role end date | ⬜ open (user) | [CONFIGURATION → Candidate profile](../CONFIGURATION.md#candidate-profile-profilecandidateyaml) |
| 4 | Defects and gaps found in the 2026-10-11 docs audit (salary key mismatch, empty shortlist exits 0, silent exclusions disable, hard-coded cohort keywords, `cli.py` size, no capability-decision record for the CV extractor, no phase-2 eval, whole profile incl. contact details in the phase-2 prompt; since core 0.13 `backend.yaml` `cloud` has no `base_url` key, so cloud mode set there fails without `--llm-base-url`, found 2026-10-25) | ⬜ open — triage | [INTENT → Known Limitations](../../ai_context/project/INTENT.md#known-limitations) |
| 5 | Exception `EXC-2026-10-12-001` scope still names the Adzuna values "in docs/TODO.md"; since 394a86a they are only in git history (flagged 2026-10-22) | ⏸ parked — operator: not an issue (2026-10-22) | [exception_registry.yaml](../../ai_context/project/governance/exception_registry.yaml) |
| 6 | Contract search follow-ups: fix the shared ingest aborting on any single source's HTTP error; Reed returns no contract type; Totaljobs actor only if a comparison shows roles CWJobs misses (shared inventory); roles that state a yearly salary can pass as contract; JobServe via the `solidcode` actor (the `santamaria` one ignored keywords, `fetchclub` needs full account access) | ⬜ open | [INTENT → Known Limitations](../../ai_context/project/INTENT.md#known-limitations) |

---

## Accumulated Active Constraints (active for all remaining stages)

- **PII stays out of git.** Candidate profiles (`implementation/job_seeker/config/profile/`) and generated output (`implementation/job_seeker/config/output/`) are gitignored. Never commit Kiera's contact details, CV data or draft output.
- **Section A (marketing) top-N is never below 25; Section B (research) stays creative across all history-cohort categories** — see the kiera-job-search skill's Hard rules.
- **8GB hardware: match runs in agent mode in the default flow** (guidance only — no code enforces it; see [RUNBOOK](../RUNBOOK.md)).
- **No fabrication.** Every claim in a generated CV/letter/message must trace to a fact in the profile YAML.
- **Submission is a human-approval gate.** The pipeline prepares packets; a person sends them. No silent auto-submit.
- **Trifecta isolation.** The ingest phase (untrusted web postings) must not share context with credentials or the submission channel; posting text is data, never instructions.
- **LLM backend is a 3-way switch, agent-authored is the default.** Cloud is opt-in only (both `--llm-provider` and `--llm-model`); never defaulted. Consumed from `ai_agent_core.execution` — no local copy of provider-switch logic.
- **Config purity.** Domain/candidate strings live in `implementation/job_seeker/config/` YAML, not code. Secrets never live in code or tracked config. Preferred secret source: `<secrets.apikey_root>/<service>/<filename>` (root set in `backend.yaml`, outside the repo). Fallback: environment variables, optionally from a gitignored `.env` in the directory the command runs from (the repo root per [RUNBOOK](../RUNBOOK.md)). Environment variables carry secrets only.
- **uv only** for Python env/deps. One responsibility per file; thin `main()` over importable modules.

---

## Verification

- Full test suite: `uv run python3 -m pytest -q` → 36 passed (2026-10-22).
- PII + output not tracked: `git check-ignore implementation/job_seeker/config/profile/kiera.yaml implementation/job_seeker/config/output/latest_shortlist.html` → prints both paths.
- Every other operational command: [RUNBOOK](../RUNBOOK.md) and each command's `--help`.

---

## Gotchas

Operational gotchas (secret lookup order, Adzuna comma-AND search, dedupe normalisation, empty
shortlist after hard-block, handoff exit 2, OOM in non-agent modes) live in [RUNBOOK](../RUNBOOK.md)
and [ai_context/project/ASSISTANTS.md → Gotchas](../../ai_context/project/ASSISTANTS.md#gotchas).
Add new ones there, not here.

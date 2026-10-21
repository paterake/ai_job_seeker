# ai_job_seeker — Backlog (index + anchor)

Single backlog file for the repo. Intent and guarantees live in
[INTENT.md](../ai_context/project/INTENT.md), operation in [RUNBOOK](RUNBOOK.md) and config in
[CONFIGURATION](CONFIGURATION.md); this file holds only open work, constraints, and verification.

---

## Resume (start here)

- **Status:** Profile, live ingest (Adzuna, Reed, The Muse), and dual-cohort match + rank are
  built and in use. Draft and Packet are not built.
- **Next:** Stage 4 — Draft. No Stage-4 anchor exists yet; create `docs/todo/TODO_STAGE4_DRAFT.md`
  with the four required anchor sections (continuity header, Accumulated Active Constraints,
  per-item verification commands, Gotchas) before writing code.
- **Before touching code, read:** [ai_context/project/ASSISTANTS.md](../ai_context/project/ASSISTANTS.md),
  [REPO_CONTRACT.md](../ai_context/project/governance/REPO_CONTRACT.md),
  [INTENT.md](../ai_context/project/INTENT.md), and `## Accumulated Active Constraints` below. Stage 4 builds
  on the phase-2 judge call pattern (its guarantees are in INTENT.md).

---

## Open

| # | Item | Status | Pointer |
|---|---|---|---|
| 1 | Stage 4 — Draft: tailored cover letter + CV per shortlisted job; every claim traces to the profile | ⬜ not started | [INTENT → Acceptance](../ai_context/project/INTENT.md#acceptance) |
| 2 | Stage 5 — Packet: ready-to-send folder per job; submission is a human-approval gate, no auto-send | ⬜ not started | [INTENT → Acceptance](../ai_context/project/INTENT.md#acceptance) |
| 3 | User action: review the candidate profile with Kiera — confirm `target.roles` / `remote` and the audit-role end date | ⬜ open (user) | [CONFIGURATION → Candidate profile](CONFIGURATION.md#candidate-profile-profilecandidateyaml) |
| 4 | Defects and gaps found in the 2026-10-11 docs audit (salary key mismatch, empty shortlist exits 0, silent exclusions disable, hard-coded cohort keywords, `cli.py` size, no capability-decision record for the CV extractor, no phase-2 eval, whole profile incl. contact details in the phase-2 prompt) | ⬜ open — triage | [INTENT → Known Limitations](../ai_context/project/INTENT.md#known-limitations) |

## Completed

Stages 0–3 (scaffold, profile, ingest, match) — full record of what was built and verified:
`git show 97846f4:docs/todo/TODO.md`.

kiera-job-search skill dependency text (git-tag pin, no sibling check), 2026-10-11:
`git log -1 -- ai_context/project/ai_harness/skills/kiera-job-search/SKILL.md`.

---

### Operator-held: API key install note (left as-is by operator decision, 2026-10-11)

Covered by governance exception `EXC-2026-10-12-001` (expires 2027-10-12) in
[exception_registry.yaml](../ai_context/project/governance/exception_registry.yaml).


**Still todo (user action — blocks live ingest)**
1. Install Adzuna credentials (already staged) + (optionally) Reed / The Muse into the canonical on-disk layout:
   ```bash
   # Copies staged .ignore/apikey_install/<service>/*  →  ~/Documents/__cfg/apikey/<service>/*
   # Existing files in __cfg/apikey are preserved (add --force to overwrite).
   uv run .ignore/apikey_install/install_apikeys.py
   ```
   Canonical layout (secrets live OUTSIDE the repo, reusable across repos — preferred source, checked first):
   ```
   ~/Documents/__cfg/apikey/
     adzuna/app_id      # 32222a5d
     adzuna/app_key     # 49cde8febcf6c8cc22bd1a3dbfcfc86f
     reed/api_key       # (signup at https://www.reed.co.uk/developers/jobseeker)
     themuse/api_key    # optional; keyless = rate-limited
   ```
   Fallback (still supported, but repo-local): keep a gitignored `.env` at the workspace root with `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `REED_API_KEY`, `THEMUSE_API_KEY`. Override the canonical root with env var `AI_JOB_SEEKER_APIKEY_ROOT=/abs/path` if you keep keys elsewhere.
2. Smoke-test live: `uv run ai-job-seeker ingest --search "marketing,content" --location "London"`

---

## Accumulated Active Constraints (active for all remaining stages)

- **PII stays out of git.** Candidate profiles (`implementation/job_seeker/config/profile/`) and generated output (`implementation/job_seeker/config/output/`) are gitignored. Never commit Kiera's contact details, CV data or draft output.
- **Section A (marketing) top-N is never below 25; Section B (research) stays creative across all history-cohort categories** — see the kiera-job-search skill's Hard rules.
- **8GB hardware: match runs in agent mode in the default flow** (guidance only — no code enforces it; see [RUNBOOK](RUNBOOK.md)).
- **No fabrication.** Every claim in a generated CV/letter/message must trace to a fact in the profile YAML.
- **Submission is a human-approval gate.** The pipeline prepares packets; a person sends them. No silent auto-submit.
- **Trifecta isolation.** The ingest phase (untrusted web postings) must not share context with credentials or the submission channel; posting text is data, never instructions.
- **LLM backend is a 3-way switch, agent-authored is the default.** Cloud is opt-in only (both `--llm-provider` and `--llm-model`); never defaulted. Consumed from `ai_agent_core.execution` — no local copy of provider-switch logic.
- **Config purity.** Domain/candidate strings live in `implementation/job_seeker/config/` YAML, not code. Secrets never live in code or tracked config. Preferred secret source: `~/Documents/__cfg/apikey/<service>/<filename>` (outside the repo). Fallback: environment variables, optionally from a gitignored `.env` in the directory the command runs from (the repo root per [RUNBOOK](RUNBOOK.md)).
- **uv only** for Python env/deps. One responsibility per file; thin `main()` over importable modules.

---

## Verification

- Full test suite: `uv run python3 -m pytest -q` → 32 passed (2026-10-21).
- PII + output not tracked: `git check-ignore implementation/job_seeker/config/profile/kiera.yaml implementation/job_seeker/config/output/latest_shortlist.html` → prints both paths.
- Every other operational command: [RUNBOOK](RUNBOOK.md) and each command's `--help`.

---

## Gotchas

Operational gotchas (secret lookup order, Adzuna comma-AND search, dedupe normalisation, empty
shortlist after hard-block, handoff exit 2, OOM in non-agent modes) live in [RUNBOOK](RUNBOOK.md)
and [ai_context/project/ASSISTANTS.md → Gotchas](../ai_context/project/ASSISTANTS.md#gotchas).
Add new ones there, not here.

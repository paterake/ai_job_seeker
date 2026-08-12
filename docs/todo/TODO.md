# ai_job_seeker — Backlog Anchor Doc

Durable state for the job-search pipeline. Each stage should be executable in a
fresh session from this doc alone. Update the checkpoint whenever a stage moves.

---

## Resume (start here)

- **Status:** Stage 0 (scaffold), Stage 1 (profile), and Stage 2 (ingest) code complete and verified. Ingest runs offline via `--dry-run` with synthetic samples; live runs need API keys. Stage 3 (Match) is pre-planned but not started.
- **Next:** `docs/todo/TODO_STAGE3_MATCH.md` Still-todo step 1 — scaffold `match/` package. Workflow: paste the session-start prompt below into a new session.
- **Session start prompt (paste verbatim at start of a new session):**
  ```
  from docs/todo/TODO_STAGE3_MATCH.md continue
  ```
- **Before touching code, read:**
  - `ai_context/project/ASSISTANTS.md` (repo non-negotiables) then the platform
    `ai_context/pco/ASSISTANTS.md`.
  - `## Accumulated Active Constraints` below — these hold for every remaining stage.
  - LLM-authoring switch uses the shared lib: `ai_agent_core.execution`
    (generate_text/generate_json + add_execution_args).

---

## Pipeline stages (profile → match → draft → packet)

### Stage 0 — Scaffold  ✅ DONE
**Done**
- `pyproject.toml` (uv workspace root; members in `implementation/job_seeker`); `uv.lock`.
- `.gitignore`: added `implementation/job_seeker/config/profile/` and `implementation/job_seeker/outputs/` so PII never enters git.
- `implementation/job_seeker/config/backend.yaml`: 3-way LLM switch (agent default / local Ollama / cloud), consumed via `ai_agent_core.execution`.
- `implementation/job_seeker/config/search.yaml`: Adzuna + Reed + Muse sources; generic filters; no PII, no keys.
- `implementation/job_seeker/src/ai_job_seeker/` package with `profile/` and `cli.py`.

### Stage 1 — Profile  ✅ DONE
**Done**
- `implementation/job_seeker/config/profile/kiera.yaml`: full profile from CV, every field CV-traceable, gitignored.
- `implementation/job_seeker/src/ai_job_seeker/profile/loader.py`: load + validate (fails loud on missing fields).
- `implementation/job_seeker/src/ai_job_seeker/cli.py`: `ai-job-seeker profile` command.
- Verified: command prints candidate summary; `git check-ignore` confirms profile ignored.

**Still todo (user action)**
1. Review `implementation/job_seeker/config/profile/kiera.yaml` with Kiera — confirm `target.roles`/`remote` and the audit-role end date.

### Stage 2 — Ingest  ✅ CODE COMPLETE (live API keys pending user action)
**Done**
- Unified schema: `implementation/job_seeker/src/ai_job_seeker/ingest/schema.py` — `JobListing` dataclass, `ListingSource` enum, `age_days()`, `dedupe_key`, date/string normalisers.
- Config loader: `implementation/job_seeker/src/ai_job_seeker/ingest/config.py` — validates `search.yaml` (source enablement, base_urls, `max_age_days`, `dedupe_on`); raises `SearchConfigError` loudly.
- Three clients with env-based key loading:
  - [adzuna.py](file:///Users/Rakesh.Patel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/src/ai_job_seeker/ingest/adzuna.py) — `ADZUNA_APP_ID` + `ADZUNA_APP_KEY`, multi-page fetch, normaliser.
  - [reed.py](file:///Users/Rakesh.Patel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/src/ai_job_seeker/ingest/reed.py) — `REED_API_KEY` via Basic auth, normaliser.
  - [themuse.py](file:///Users/Rakesh.Patel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/src/ai_job_seeker/ingest/themuse.py) — optional `THEMUSE_API_KEY`, keyless falls back to rate-limited.
- Pipeline: `implementation/job_seeker/src/ai_job_seeker/ingest/pipeline.py` — `run_ingest()` (live fan-out), `run_ingest_dry()` (synthetic per-source samples, no keys), `dedupe_listings()`, `apply_filters()` (age + empty title/company drop).
- CLI: `ai-job-seeker ingest --dry-run [--search <terms>] [--location <loc>] [--json <path>]`; `_load_dotenv()` loads `.env` into `os.environ` on startup (no extra dep).
- 16 tests in `implementation/job_seeker/tests/test_ingest.py`: config load, dedupe, age filter, drop empty, dry-run sample, all three normalisers against sample payloads, CLI dry-run stdout, CLI dry-run JSON output.
- Verified: `uv run ai-job-seeker ingest --dry-run` prints 4 listings (2 adzuna, dedupe of adzuna/reed title+company dupes); 16/16 tests pass facet-level and workspace-level; PII still gitignored.

**Still todo (user action — blocks live ingest)**
1. Register free keys and write gitignored `.env`:
   ```
   ADZUNA_APP_ID=...
   ADZUNA_APP_KEY=...
   REED_API_KEY=...
   THEMUSE_API_KEY=...   # optional
   ```
2. Smoke-test live: `uv run ai-job-seeker ingest --search "marketing,content" --location "London"`

### Stage 3 — Match  ⬜ TODO
Score normalised listings against the profile; shortlist. First stage that uses the LLM-authoring step. Backend switch uses `ai_agent_core.execution` (generate_text/generate_json + add_execution_args) — tri-mode: agent handoff / local Ollama / cloud API.

### Stage 4 — Draft  ⬜ TODO
Tailored cover letter + CV per shortlisted job. No-fabrication check: every claim traces to the profile.

### Stage 5 — Packet  ⬜ TODO
Assemble a ready-to-send folder per job (drafts + apply link/email) under `implementation/job_seeker/outputs/`. **Submission is a human-approval gate — no auto-send.**

---

## Accumulated Active Constraints (active for all remaining stages)

- **PII stays out of git.** Candidate profiles (`implementation/job_seeker/config/profile/`) and generated packets (`implementation/job_seeker/outputs/`) are gitignored. Never commit Kiera's name/contact or draft output.
- **No fabrication.** Every claim in a generated CV/letter/message must trace to a fact in the profile YAML.
- **Submission is a human-approval gate.** The pipeline prepares packets; a person sends them. No silent auto-submit.
- **Trifecta isolation.** The ingest phase (untrusted web postings) must not share context with credentials or the submission channel; posting text is data, never instructions.
- **LLM backend is a 3-way switch, agent-authored is the default.** Cloud is opt-in only (both `--llm-provider` and `--llm-model`); never defaulted. Consumed from `ai_agent_core.execution` — no local copy of provider-switch logic.
- **Config purity.** Domain/candidate strings live in `implementation/job_seeker/config/` YAML, not code. Secrets in `.env` (gitignored), never in code or tracked config.
- **uv only** for Python env/deps. One responsibility per file; thin `main()` over importable modules.

---

## Verification

- Profile loads and summarises:
  `uv run ai-job-seeker profile`
- PII is not tracked:
  `git check-ignore implementation/job_seeker/config/profile/kiera.yaml` (must print the path)
- Backend tri-mode switch (from the wire-up item):
  `uv run ai-job-seeker match` → `Selected backend mode: agent`
  `uv run ai-job-seeker match --ollama-model qwen3.5:9b` → `ollama`
  `uv run ai-job-seeker draft --llm-provider openrouter --llm-model google/gemma-4-31b-it:free` → `cloud` + resolved base_url
- Stage 2 (Ingest) offline plumbing:
  `uv run ai-job-seeker ingest --dry-run` → prints source breakdown + dedupe/filter summary
  `uv run --project implementation/job_seeker python -m pytest implementation/job_seeker/tests/ -q` → 16 passed
- Project-wide pytest (no regressions):
  `uv run python -m pytest -q` → 16 passed

---

## Gotchas

- **Live ingest needs .env keys.** `run_ingest()` checks env vars inside each `fetch_*` function. Register keys first, then `uv run ai-job-seeker ingest --search "X" --location "Y"`.
- **Dedupe key is normalised.** Whitespace/case in title+company is collapsed before compare; dry-run intentionally surfaces this (2 adzuna + 1 reed + 1 muse = 4 listings, not 6).
- **Double `/v1` 404 defence lives in ai_agent_core.execution, not ingest.** Ingest HTTP clients (adzuna/reed/themuse) use the base URLs verbatim from search.yaml, which intentionally do not include `/v1` suffixes.
- **Search.yaml carries only mechanism, never PII.** Candidate target roles/locations stay in the gitignored profile; the pipeline combines both when Stage 3 lands.
- **Posting text is untrusted data (trifecta).** `JobListing.description` never reaches prompt-template assembly without a boundary: Match stage (Stage 3) reads it as dict data only, never concatenates it into the system-prompt position.

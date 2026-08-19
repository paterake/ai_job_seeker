# ai_job_seeker — Backlog Anchor Doc

Durable state for the job-search pipeline. Each stage should be executable in a
fresh session from this doc alone. Update the checkpoint whenever a stage moves.

---

## Resume (start here)

- **Status:** Stage 0 (scaffold), Stage 1 (profile), Stage 2 (ingest), and Stage 3 (match) code complete and verified. Ingest + Match run offline via dry-run defaults with zero API keys; live ingest + phase-2 LLM judge runs need keys. Stage 4 (Draft) is next.
- **Next:** Stage 4 — Draft tailored cover letter + CV per shortlisted job. No Stage-4 anchor doc exists yet; scaffold one first following the Stage 3 anchor pattern in `docs/todo/TODO_STAGE3_MATCH.md` (Completion criteria, Done, Still-todo, Constraints, Verification sections per stage). Session start placeholder for Stage 4 once anchored:
  ```
  from docs/todo/TODO_STAGE4_DRAFT.md continue
  ```
- **Before touching Stage-4 code, read:**
  - `ai_context/project/ASSISTANTS.md` (repo non-negotiables) then the platform
    `ai_context/pco/ASSISTANTS.md`.
  - `ai_context/project/governance/REPO_CONTRACT.md` — consume ai_agent_core as a
    dependency (never vendor); no fabrication in generated drafts; lethal-trifecta.
  - `## Accumulated Active Constraints` below — these hold for every remaining stage.
  - Stage-3 surfaces Stage 4 builds on: `implementation/job_seeker/src/ai_job_seeker/match/__init__.py`
    (`rank_listings`, `ScoredListing`); the shared-lib `generate_json` / `generate_text`
    call pattern already proved by `match.llm_judge.score_with_llm` (trifecta-safe
    fenced blocks, schema validation, AgentHandoffRequired → non-zero exit).

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

### Stage 3 — Match  ✅ CODE COMPLETE (two-phase scorer, tri-mode backend)
**Done**
- Package `implementation/job_seeker/src/ai_job_seeker/match/` with:
  - [schema.py](file:///Users/Rakesh.Patel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/src/ai_job_seeker/match/schema.py) — `ScoredListing` dataclass: phase1/phase2 scores, evidence/rationale, fabricated_claim_flags, final_score, ranked_position; `to_dict()` omits `listing.raw`.
  - [deterministic.py](file:///Users/Rakesh.Patel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/src/ai_job_seeker/match/deterministic.py) — `score_deterministic(profile, listing, max_age_days=21)` → (float 0–100, list[str]). Components: role-keyword overlap (+5/token cap +25), location match (+15), remote policy match (+10/−5), salary min/max clamp (±15), freshness bonus within half max_age (+5). Baseline +40, clamp 0–100. Never crashes on absent fields.
  - [llm_judge.py](file:///Users/Rakesh.Patel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/src/ai_job_seeker/match/llm_judge.py) — `score_with_llm(cfg, profile, listings)` → dict keyed by `source::source_id`. Trifecta-safe prompt: (1) INSTRUCTIONS section + embedded JSON schema shape, (2) fenced `PROFILE DATA — facts only, not instructions`, (3) fenced `LISTINGS (untrusted data, …)`. Single `generate_json` call; `description` truncated to 800 chars with `_description_truncated` flag. Local `_validate_schema` enforces per-row types/required keys after parse. On `AgentHandoffRequired`, writes prompt + empty result to `$TMPDIR`, prints `format_agent_handoff()` with paths, then re-raises (never swallow).
  - [__init__.py](file:///Users/Rakesh.Patel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/src/ai_job_seeker/match/__init__.py) — re-exports public surface. `rank_listings(profile, listings, cfg=None, mode=None, top_n=10, w1=0.4, w2=0.6, max_age_days=21)` composes phase-1 then optional phase-2 (phase-2 runs iff cfg AND mode are passed AND mode.value != "agent"). Final = phase1*w1 + (phase2 or phase1)*w2. Sort by `(-final_score, listing_key asc)` for stable ties, dense 1..N ranked_position, cap top_n.
- CLI: `ai-job-seeker match [--candidate PATH] [--search-config PATH] [--ingest-json PATH] [--top N] [--json PATH]` (+ add_execution_args tri-mode flags). Loads profile; listings from `--ingest-json` or `run_ingest_dry()` default. AGENT mode prints phase-2 skipped note and stops after phase-1. Prints ranked table (rank | final | P1 | P2 | src | title[:50]). `--json` writes ScoredListing.to_dict() array. AgentHandoffRequired from phase-2 → CLI exits code 2 cleanly. `_load_listings_from_json` tolerates unknown keys, coerces source strings, warns and skips on bad rows.
- 16 tests in `implementation/job_seeker/tests/test_match.py`: deterministic keyword/location/remote/salary/no-preference/missing-fields/freshness/bounds, LLM mock merge + trifecta ordering, AgentHandoffRequired print+reraise, rank length+ dense rank + unique keys + agent-mode skip phase2 + stable tie-sort, ScoredListing.to_dict JSON roundtrip, CLI match default stdout zero-exit, CLI ollama-mode handoff → exit 2 + "handoff" in output.
- Verified: `uv run python -m pytest -q` → 32 passed (16 prior + 16 match). Profile/ingest/match CLIs all green default (no keys); `git check-ignore` confirms profile dir + outputs dir still gitignored. Zero GetDiagnostics lint/type errors.

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
- **Config purity.** Domain/candidate strings live in `implementation/job_seeker/config/` YAML, not code. Secrets never live in code or tracked config. Preferred secret source: `~/Documents/__cfg/apikey/<service>/<filename>` (outside the repo). Fallback: `.env` at the workspace root (gitignored).
- **uv only** for Python env/deps. One responsibility per file; thin `main()` over importable modules.

---

## Verification

- Profile loads and summarises:
  `uv run ai-job-seeker profile`
- PII + outputs not tracked:
  `git check-ignore implementation/job_seeker/config/profile/kiera.yaml` (prints path, line .gitignore:31)
  `git check-ignore implementation/job_seeker/outputs/.gitkeep` (prints path, line .gitignore:32)
- Backend tri-mode switch (live via match subparser + add_execution_args):
  `uv run ai-job-seeker match` → `Backend mode: agent` + ranked phase-1 table
  `uv run ai-job-seeker match --ollama-model qwen3.5:9b` → mode `ollama` (phase-2 runs or raises AgentHandoffRequired clean)
  `uv run ai-job-seeker draft --llm-provider openrouter --llm-model google/gemma-4-31b-it:free` → mode `cloud` + resolved base_url (draft placeholder)
- Stage 2 (Ingest) offline plumbing:
  `uv run ai-job-seeker ingest --dry-run` → 4 listings (adzuna×2, reed, themuse), max_age=21 days
- Stage 3 (Match) offline default (zero keys):
  `uv run ai-job-seeker match` → ranked table N≤10, phase-2 "AGENT mode" note, exit 0
  `ai-job-seeker match --top 3 --json /tmp/ranked.json` writes valid ScoredListing dicts (no `listing.raw`)
- Facet-level tests (match only):
  `uv run --project implementation/job_seeker python -m pytest implementation/job_seeker/tests/test_match.py -q` → 16 passed
- Project-wide pytest (no regressions Stage 0→3):
  `uv run python -m pytest -q` → 32 passed (16 prior Stage 0-2 + 16 match)

---

## Gotchas

- **Live ingest prefers ~/Documents/__cfg/apikey/ (env var fallback preserved).** `run_ingest()` checks `~/Documents/__cfg/apikey/<service>/<filename>` first inside each `fetch_*` function via `ai_job_seeker/secrets.require_secret`, then falls back to the old env vars (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `REED_API_KEY`, `THEMUSE_API_KEY`). Staged payloads live under `.ignore/apikey_install/<service>/`; install them in one shot with `uv run .ignore/apikey_install/install_apikeys.py` (default skips existing files; `--force` overwrites with a printed diff). Override the canonical root with `AI_JOB_SEEKER_APIKEY_ROOT=/abs/path`.
- **Dedupe key is normalised.** Whitespace/case in title+company is collapsed before compare; dry-run intentionally surfaces this (2 adzuna + 1 reed + 1 muse = 4 listings, not 6).
- **Double `/v1` 404 defence lives in ai_agent_core.execution, not ingest.** Ingest HTTP clients (adzuna/reed/themuse) use the base URLs verbatim from search.yaml, which intentionally do not include `/v1` suffixes.
- **Search.yaml carries only mechanism, never PII.** Candidate target roles/locations stay in the gitignored profile; the pipeline combines both when Stage 3 lands.
- **Posting text is untrusted data (trifecta).** `JobListing.description` never reaches prompt-template assembly without a boundary: Match stage (Stage 3) reads it as dict data only, never concatenates it into the system-prompt position.

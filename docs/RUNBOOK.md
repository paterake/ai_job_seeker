# Runbook: ai_job_seeker

This covers running and recovering the pipeline. Exact commands and flags are in
[RUNNERS.md](RUNNERS.md), config keys in [CONFIGURATION.md](CONFIGURATION.md), and design in
[ARCHITECTURE.md](ARCHITECTURE.md).

## Prerequisites

1. This repo, synced with `uv sync`, which fetches the pinned `ai_agent_core` git tag (network
   access to the `ai_agent_core` repo is needed on first sync). **Every subcommand needs
   `ai_agent_core` installed**, profile and ingest included (see
   [Missing ai_agent_core](#missing-ai_agent_core)).
2. `uv` installed. Run everything through `uv run` from the repo root. Never install into the
   system Python.
3. Board API keys installed (see [Installing API keys](#installing-api-keys)).
4. The candidate's CV `.docx` at the location set in the backend config, outside the repo.

## Default run (the job-search skill)

The canonical flow is the
[kiera-job-search skill](../ai_context/project/ai_harness/skills/kiera-job-search/SKILL.md),
which any harness triggers from a chat request. It runs these steps:

1. **Sync dependencies** with `uv sync` (fetches the pinned `ai_agent_core` git tag).
2. **Re-extract the profile** from the CV, with forced overwrite.
3. **Restore the target fields** that extraction left for review. Extraction clears
   `target.roles` and `target.locations` every time, so the skill writes back the
   operator-confirmed role list (it is kept in the skill) and the location. If you skip this,
   role overlap and location score zero for every listing.
4. **Ingest two pools.** The marketing pool uses the search term `marketing`; the research pool
   uses `graduate research`. Both run against all three boards and are written under
   `output/_pools/`. If any source prints `SKIP`, tell the operator; do not carry on silently.
5. **Match in dual-cohort mode** in agent mode: Section A top 25 from the marketing pool only,
   Section B top 25 from the marketing and research pools merged. The applied-jobs store is
   passed explicitly. This writes the JSON/MD files to `output/_pipeline/` and
   `latest_shortlist.html` to `output/`.
6. **Open the output folder and the HTML shortlist** for the candidate, then report the paths in
   plain language.

**Section A source pool.** The skill passes `output/_pipeline/latest_listings.json` as the
Section A pool, so that a same-day re-run reproduces an earlier Section A exactly. **None of
the skill's own steps writes that file.** It only exists if an earlier run wrote it with an
ingest `--json` pointing there. If it is missing, match exits 1 with "ingest JSON not found".
In that case use this run's fresh marketing pool instead, as [RUNNERS.md](RUNNERS.md) shows.
Expect at most a tie-band swap compared with an earlier run.

**Recording applications.** When the candidate says which roles she has applied for (by section
and position), use the
[log-applied-jobs skill](../ai_context/project/ai_harness/skills/log-applied-jobs/SKILL.md). It
writes to the local store, which the next match run filters on, and it mirrors the rows to the
tracker sheet through the browser.

## Installing API keys

- Put one file per key under `~/Documents/__cfg/apikey/<service>/`, or under whatever folder
  `AI_JOB_SEEKER_APIKEY_ROOT` names. The file names are in [CONFIGURATION.md](CONFIGURATION.md#secrets).
  Each file holds the bare key value. Leading and trailing whitespace is ignored.
- Fallback: environment variables, or a gitignored `.env` in the directory you run from.
- Staged keys may sit under `.ignore/apikey_install/` (gitignored) with an install script. That
  folder is local-only. Its contents and the script are not in git and are unverified here.
- Check: run a live ingest. Every source should report a count, not `SKIP`.
- Never paste key values into docs, commits, issue text or chat logs.

## Recovery

### A source shows `SKIP — …`
Its credentials were not found in either the key file or the environment variable. Install the
key and re-run. The other sources' results are still valid.

### `error: ingest failed: … HTTP <code>`
Any non-200 response from any board aborts the whole ingest, with no partial output and no
retry. Re-run later. To isolate a broken board, set it to `enabled: false` in the search
config. A 400/401 from Adzuna or Reed usually means a bad key.

### Zero listings from Adzuna
The search terms were probably comma-separated, which produces a single query that must match
every word. Use one concept, or a space-joined phrase.

### Empty or very short shortlist after the hard-block filter
Match prints a `[hard-block]` line per pool, with counts by reason.

- If everything was removed, check the reasons. Engineering-title or location blocks against a
  live pool usually mean the search terms or location are wrong. **The command still exits 0
  with empty sections**, so always read the summary lines.
- A match run with no pool falls back to synthetic "Data Engineer" samples. All of them are
  hard-blocked, so an empty shortlist from a bare `match` is expected.
- If the exclusion config is missing or malformed, **nothing** is blocked and no error is shown.
  A shortlist full of engineering or overseas roles means the exclusion config failed to load.
- An oversized `[applied-filter]` removal count can mean the applied store holds title-only
  records. These remove every listing with that title, whatever the company.

### `AgentHandoffRequired` (match exits 2)
This happens only outside agent mode. The prompt and an empty result file are in the system
temp directory; the paths are printed. Two ways out:

- Re-run in agent mode (no LLM flags) to get a phase-1-only shortlist. This is the default and
  the only safe option on 8 GB.
- Author the JSON as instructed. There is currently no match option that reads the result file
  back in (see [AI.md](AI.md#agent-handoff)), so this path is incomplete.

### Out of memory, or the machine freezes during match
A local model was used on the 8 GB machine. Kill it, stop the local model server, and re-run
**without** any `--ollama-*` or `--llm-*` flags. Check that `backend.yaml` still has
`default_mode: agent`, an empty `local.model`, and an empty cloud section.

### Missing ai_agent_core
Symptoms: `uv sync` cannot fetch the pinned `ai_agent_core` git tag, or any command fails with an
`ai_agent_core` import error. That includes `profile` and `ingest`, because the CLI imports the LLM judge at
load time (verified 2026-10-11). The CLI's error message gives the same `uv sync` fix. Fix: check network/GitHub access to the
`ai_agent_core` repo and that the pinned tag exists, then run `uv sync`.

### Profile errors
- `Profile not found` / `missing required fields`: re-run the extraction, or fix the YAML. The
  required keys are in [CONFIGURATION.md](CONFIGURATION.md#candidate-profile-profilecandidateyaml).
- `Refusing to overwrite existing profile`: add the force flag, but only if hand edits can be
  lost. Step 3 above restores the target fields.
- `--extract requires a CV .docx path`: check `profile.cv_dir` and the stems in the backend
  config, or pass the CV path explicitly.

### Old shortlist needed
Timestamped copies sit in the `_archive/` folder next to each output, for 7 days. Older copies
are deleted automatically the next time that folder is written to.

## Health checks

- The test suite passes (32 tests, 2026-10-11).
- `git check-ignore` confirms that the profile and output folders are ignored.
- The governance validators run clean.

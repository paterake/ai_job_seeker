# Configuration: ai_job_seeker

This doc covers config files, keys, defaults and rationale only. When to run what is in
[RUNBOOK.md](RUNBOOK.md); intent and limitations are in [INTENT.md](../ai_context/project/INTENT.md). Every
config file lives in `implementation/job_seeker/config/`, except the contract search's, which are listed under
[Contract search](#contract-search).

| File | Tracked in git | Owns |
|---|---|---|
| [backend.yaml](../implementation/job_seeker/config/backend.yaml) | yes | LLM backend mode, the default CV location and the secret lookup root |
| [search.yaml](../implementation/job_seeker/config/search.yaml) | yes | Job sources and generic ingest filters |
| [exclusions.yaml](../implementation/job_seeker/config/exclusions.yaml) | yes | Hard-block policy for match |
| `profile/<candidate>.yaml` | **no** (gitignored PII) | The candidate profile |
| `output/` | **no** (gitignored) | Every generated artefact, plus the applied-jobs store |

Tracked config never contains secrets or candidate facts. `backend.yaml` does carry an absolute
CV folder path and CV file stems, which identify the candidate. That is a known exposure.

## backend.yaml

| Key | Default if absent | Meaning and rationale |
|---|---|---|
| `default_mode` | `agent` | `agent` / `local` / `cloud`. Keep it at `agent`: the reference machine has 8 GB of RAM and local models can run it out of memory. |
| `local.model` | empty | Used only when `default_mode: local`. Fills in the local model if none was requested at run time. |
| `local.base_url` | the substrate's default | Endpoint of the local model server. |
| `local.timeout_s` | the substrate's default | Request timeout for the local model, in seconds. |
| `cloud.provider`, `cloud.model` | empty | Opt-in only. Set **both** or **neither**: setting just one is rejected. Setting both enables cloud whatever `default_mode` says. API keys never go here. |
| `profile.cv_dir` | `implementation/job_seeker/config/profile` | Folder holding the source CV. Absolute paths are used verbatim; relative paths are resolved from the workspace root. Keep the CV outside the repo. |
| `profile.cv_docx_stem`, `profile.cv_pdf_stem` | `CV` | Expected file names, without extension. If the named file is missing, the first `*.docx` / `*.pdf` in `cv_dir` is used. |
| `secrets.apikey_root` | none (required) | Folder holding one file per API key ([Secrets](#secrets)). `~` is expanded. Keep it outside the repo. |

## search.yaml

| Key | Default if absent | Meaning and rationale |
|---|---|---|
| `sources.<name>` | — | One block per known source: `adzuna`, `reed`, `themuse`. Any other source name is ignored. |
| `sources.<name>.enabled` | `false` | Whether ingest calls this source. |
| `sources.<name>.base_url` | **required** | API endpoint, used exactly as written (with no `/v1` suffix added). If missing, config load fails. |
| `sources.adzuna.country` | `gb` | Country segment of the Adzuna URL. |
| `sources.adzuna.results_per_page` | `50` | Page size. |
| `sources.adzuna.max_pages` | `1` | Maximum pages per ingest run. The file sets 3. |
| `sources.reed.results_to_take` | `100` | Reed returns one page of this size. |
| `filters.max_age_days` | `21` | Postings older than this are dropped. Must be greater than 0. Half this value is the "fresh posting" threshold the scorer uses. |
| `filters.dedupe_on` | `["title", "company"]` | Cross-source dedupe fields. Only `title` and `company` are recognised. |

The Muse's page count (3) and every request timeout (30 s) are code constants, not config.

## exclusions.yaml

The hard-block policy. Edit this file, not code, when the candidate rules out a kind of role.
Matching is case-insensitive and word-bounded, and the file is read once per process. **A
missing or malformed file disables every exclusion without any error.**

| Key | Applied to |
|---|---|
| `blocked_language_tokens` | Single words in the title. Ignored when the title contains "english". |
| `blocked_language_phrases` | The title, and the first 1500 characters of the description |
| `blocked_engineering_phrases` | The title |
| `blocked_senior_phrases` | The title |
| `blocked_construction_phrases` | The title |
| `blocked_teaching_subjects_phrases` | The title |
| `geo_allow_prefixes` | Location substring that marks a role as allowed |
| `geo_allow_postcode_prefixes` | Location prefix (UK outward code) that marks a role as allowed |
| `blocked_geo_tokens` | Location, checked only when neither allow list matched |
| `blocked_geo_countries` | Location, checked only when neither allow list matched |

The current list contents are in [exclusions.yaml](../implementation/job_seeker/config/exclusions.yaml).
The catch-all title tokens (engineer, engineering, architect, tester, devops, sre) and both
cohort keyword sets are code constants, not config (gap, see
[INTENT.md → Known Limitations](../ai_context/project/INTENT.md#known-limitations)).

## Candidate profile (`profile/<candidate>.yaml`)

The default file is `profile/kiera.yaml`. It is PII, gitignored, and written with owner-only
permissions. Top-level keys `identity`, `target`, `summary`, `skills` and `experience` are
required and must be non-empty. `education` and `achievements_and_awards` are optional.

| `target.*` key | Used by | Notes |
|---|---|---|
| `roles` | Scorer role overlap | Extraction leaves it empty or puts in a hint, flagged for review. The job-search skill fills it with the confirmed role list. |
| `locations` | Scorer location bonus | Substring match against the listing location. |
| `remote` | Scorer remote component | Takes `remote_only`, `hybrid_or_remote_ok` or `onsite_only`. Any other value is neutral; extraction writes `any`. |
| `expected_salary_min` | Scorer salary component | **Extraction does not write this key**, so salary scoring is neutral unless it is added by hand. |
| `salary_min_gbp`, `salary_max_gbp` | Profile summary only | Written by extraction. **Not read by the scorer.** |
| `contract_types`, `seniority` | Nothing yet | Required-review fields. |

## Secrets

**No secret values in any file in this repo.** Secrets are looked up in this order, and the
first non-empty value wins:

1. A file at `<root>/<service>/<file>`. `<root>` is `secrets.apikey_root` in
   [backend.yaml](#backendyaml) (committed value `~/Documents/__cfg/apikey`).
2. An environment variable. Variables can come from a gitignored `.env` file in the directory
   the command runs from. Variables that are already set are not overwritten.

| Service | File under the root | Environment variable | Required |
|---|---|---|---|
| Adzuna | `adzuna/app_id`, `adzuna/app_key` | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | yes, otherwise the source is skipped |
| Reed | `reed/api_key` | `REED_API_KEY` | yes, otherwise the source is skipped |
| The Muse | `themuse/api_key` | `THEMUSE_API_KEY` | no; it works keyless at a lower rate limit |

Cloud-LLM API keys are resolved by `ai_agent_core`, not by this repo, and never from the environment or `.env`
(core 0.14.0): see [Core configuration](#core-configuration).

## Core configuration

`ai_agent_core` reads no environment variable (core 0.14.0). `match` and `draft` take `--config-dir`, a
use-case folder outside the repo; without it the core runs unconfigured, which is enough for the default
agent mode.

| File in `--config-dir` | Effect |
|---|---|
| `layout.yaml` | `roots.output` is the core's output root (`paths.output_dir`); no default, absolute and outside any repository. Needed only when the core writes (for example `telemetry_jsonl` in `run.yaml`). |
| `process.yaml` (optional) | The core's process keys, for example `paths.api_key_dir` or `providers.anthropic.api_key_file` / `providers.openai.api_key_file` (cloud keys, by file, never the value). |
| `run.yaml` (optional) | The core's run keys (budgets, guardrails, telemetry sink). |

Cloud mode also needs `--llm-base-url`: the core has no default endpoint (0.13.0).

## Output locations

- Output root: `implementation/job_seeker/config/output/` (gitignored).
- Applied-jobs store default: `output/_pipeline/applied_jobs.json`.
- Archive retention is 7 days. That is a code constant, not config.
- The full layout convention is in [RUNBOOK.md → Output folders](RUNBOOK.md#output-folders).

## Contract search

Config for `implementation/contract_search/config/`. Each file declares its keys, and the loader fails on an
undeclared or missing key.

| File | Tracked in git | Owns |
|---|---|---|
| `search.yaml` | yes | Job sources (Adzuna, Reed; The Muse is disabled because it returns 403 without a key) and the age filter (14 days) |
| `scoring.yaml` | yes | Contract, day-rate, IR35 and remote patterns (case-insensitive regexes over title and description), the valid `target.remote` modes (`remote_modes`) and which of them skip the location-free query pass (`remote_modes_without_location_pass`), blocked title phrases, and the score weights |
| `profile/<candidate>.yaml` | **no** (gitignored PII) | Identity, `skills`, and `target`: `queries` (one ingest pass each), `title_weights` (best phrase found in the title sets the title score, 1-100), `locations`, `remote` |
| `apify.yaml` | yes | Opt-in Apify actors for CWJobs and JobServe: actor ids, input templates, the output-field mapping, `max_queries`, polling and wait limits |
| `output/` | **no** (gitignored) | `latest_shortlist.{md,json}` plus a timestamped copy in `_archive/` |

Keys come from the same environment variables as above (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `REED_API_KEY`).
A listing is dropped when its title is outside `title_weights`, matches a blocked phrase, is permanent or has no
contract signal (`require_contract`), or is neither in a target location nor remote. IR35 changes the score
(outside +20, inside -30) and is `unstated` when the advert does not say.

`--apify` adds CWJobs and JobServe through Apify. It needs `APIFY_API_TOKEN` in the environment (set with
`secret-set`) and spends Apify credit: the free plan has $5 a month, and a run with three queries costs about
$0.25-0.30. Without the token, or if Apify refuses a call, each actor is recorded as a skip and the run goes on. A run
that outlives `max_wait_s` is aborted. Use only actors with limited permissions: an actor that asks for full access
to the Apify account does not belong in `apify.yaml`. CWJobs adverts apply through Totaljobs (one shared inventory),
so the CWJobs actor's apply link is the listing URL and no separate Totaljobs actor is configured.

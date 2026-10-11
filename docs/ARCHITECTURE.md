# Architecture: ai_job_seeker

What the system must guarantee is in [PRD.md](../PRD.md). Config keys are in
[CONFIGURATION.md](CONFIGURATION.md), commands in [RUNNERS.md](RUNNERS.md), and LLM-judge
behaviour in [AI.md](AI.md).

## Workspace layout

- Root `pyproject.toml`: a uv workspace with a single member, `implementation/job_seeker`. It
  declares `ai-agent-core` as a path source at `../ai_agent_core/implementation/ai_agent_core`.
  Pytest settings also live here: `--import-mode=importlib`, the `src` path, and a cache under `.ignore/`.
- `implementation/job_seeker/pyproject.toml`: the `ai-job-seeker` package. It provides the
  `ai-job-seeker` console script and depends on `ai-agent-core>=0.5.0`, `pyyaml`, `python-docx` and `requests`.
  The `>=` constraint is a floor, not a pin. The workspace path source overrides it, so the
  version used is whatever is checked out in the sibling repo.
- `implementation/job_seeker/config/`: the YAML config, plus the gitignored `profile/` and `output/` folders.
- `implementation/job_seeker/src/ai_job_seeker/`: the package (described below).
- `implementation/job_seeker/tests/`: 32 tests across ingest, match and backend modes.
- `_build_7_section_shortlist.py` at the repo root: a stray one-off script that merges seven
  per-section shortlist JSONs (A–G). Nothing in the docs or skills calls it. Its `sys.path` insert
  resolves outside the repo, and it sits outside the config-repo structure. Its status is
  unverified, so treat it as not part of the pipeline.

## Components

| Package / module | Responsibility |
|---|---|
| `cli.py` | Argparse entry point and every subcommand handler. Also holds the applied-jobs store helpers, pool loading and merging, the hard-block and applied filters, the shortlist writers (MD/HTML/JSON), and the timestamp/archive writer. About 2.4k lines, so it breaks the one-responsibility-per-file rule (backlog). |
| `backend.py` | Bridge from `backend.yaml` to `ai_agent_core.execution`: parser defaults, overrides from the YAML, and profile CV-location defaults. Imports `ai_agent_core` lazily. |
| `secrets.py` | Secret lookup: a per-service file first, then an environment variable. Raises a typed `SecretNotFound` that names the file and variable but never the value. |
| `profile/extractor.py` | Deterministic CV `.docx` paragraph parser. Section headers are recognised by ALL-CAPS keyword sets. No LLM is used. |
| `profile/loader.py` | Loads and validates a profile (required top-level keys). Writes profiles with 0600/0700 permissions and refuses to overwrite unless asked. |
| `ingest/schema.py` | The `JobListing` dataclass, the `ListingSource` enum and date parsing. `to_dict()` drops `raw`. |
| `ingest/config.py` | Loads and validates `search.yaml` (`SearchConfigError`). |
| `ingest/adzuna.py`, `reed.py`, `themuse.py` | One HTTP client per board, plus a normaliser to `JobListing`. |
| `ingest/pipeline.py` | Fans out to enabled sources, records per-source skips (`IngestSourceSkip`), dedupes, filters, and provides the dry-run sample generator. |
| `match/deterministic.py` | Phase-1 scorer, the cohort keyword sets, and `hard_blocked()`, driven by `exclusions.yaml`. |
| `match/llm_judge.py` | Phase-2 judge. See [AI.md](AI.md). |
| `match/__init__.py` | `rank_listings()`: runs phase 1, runs phase 2 if enabled, blends the scores, sorts, caps and ranks. |
| `match/schema.py` | The `ScoredListing` dataclass and `to_dict()`. |

## Data flow

```
CV .docx ──profile --extract──▶ profile YAML (gitignored, human-reviewed)
                                     │
board APIs ──ingest (per pool)──▶ pool JSON (normalise → dedupe → age/empty filter)
                                     │
                     match ◀─────────┘
                       1. load pools (per cohort; multiple pools merged + deduped)
                       2. applied-jobs filter
                       3. hard-block filter (reasons reported)
                       4. rank: phase-1 (+ phase-2 if non-agent mode)
                       5. Section B minus Section A, re-rank 1..N
                       6. write JSON / MD / HTML (timestamped + latest alias)
                                     │
                       human review ─┴─▶ applied add ──▶ applied-jobs store (feeds step 2 next run)
```

Ingest and match are separate processes connected only by JSON files. Match never calls the
boards. With no pool supplied, it falls back to synthetic dry-run listings.

## Ingest details

- Search terms: the CLI splits `--search` on commas, and the Adzuna and Reed clients join the
  terms with spaces into a single keyword query. A comma-separated list therefore becomes one
  query that must match every word, which is why the skills tell you not to comma-separate.
  The Muse client ignores search terms and filters by location only.
- Pagination: Adzuna fetches up to `max_pages` (falling back to 1 if the key is unset). The Muse
  always fetches up to 3 pages (hard-coded). Reed makes a single request. Paging stops early on
  an empty page.
- Every request has a hard-coded 30-second timeout. A non-200 response raises a client error
  that aborts the whole ingest; there is no retry. A row that fails normalisation is dropped
  silently.
- Credentials: Adzuna and Reed raise `IngestSourceSkip` when a key is missing, so the source is
  skipped and reported. The Muse key is optional and is sent as a query parameter.
- **Dedupe key.** Ingest uses the configured `dedupe_on` fields, but only `title` and `company`
  are honoured, each lowercased and whitespace-collapsed. The first listing seen wins. Merging
  pools inside match uses `(title.strip().lower(), company.strip().lower())`, which does not
  collapse internal whitespace, and again the first pool given wins. Put the pool with the
  richer descriptions first.

## Hard-block filter

`hard_blocked(listing)` returns a reason string or `None`. Checks run in order, and the first
hit wins:

1. Non-English language phrase in the title.
2. Non-English language token in the title, unless the title also contains "english".
3. Non-English language phrase in the first 1500 characters of the description.
4. Engineering phrase in the title.
5. The token engineer/engineering/architect/tester/devops/sre in the title. This list is
   hard-coded in the scorer module, not in config.
6. Senior or executive phrase.
7. Construction phrase.
8. Specialist teaching-subject phrase.
9. Location. If the location is non-empty and matches neither an allow-prefix substring nor an
   allow-postcode prefix, it is blocked when it matches a foreign city/region token or a
   country name.

Phrase matching is case-insensitive and word-bounded. It tolerates hyphens and slashes between
tokens, and also matches hyphen-joined and fully joined variants. The lists are loaded once, on
import, from `exclusions.yaml`. If that file is missing or unparseable, every list is empty and
nothing is blocked (fails open).

## Phase-1 deterministic scorer

`score_deterministic(profile, listing, max_age_days, cohort)` starts from a baseline of 40,
adds the components below, and clamps the result to 0–100. Every component that fires adds an
evidence line.

| Component | Rule |
|---|---|
| Role overlap | Tokens from `target.roles` that appear in the title score +5 each (cap +25). Tokens that appear only in the description score +1 each (cap +8). |
| Marketing cohort bonus (`cohort="marketing"`) | +0.75 per marketing-keyword token found in the title or description (cap +6). |
| History cohort bonus (`cohort="history"`) | Band 1: +2 per cohort token in the title (cap 10). Band 2: +0.9 per cohort token found only in the description (cap 7). Band 3: +0.6 per CV-strength synonym (cap 5). Maximum +22. |
| Location | +15 if any `target.locations` entry is a substring of the listing location. |
| Remote | `remote_only`: +10 if the listing is remote, −5 if not. `hybrid_or_remote_ok`: +7 if remote. `onsite_only`: −5 if remote. Any other value, `any` included, is neutral. |
| Salary | Reads `target.expected_salary_min`. If the listing maximum is below it: −min(15, gap/1000). If the listing minimum is at or above it: +min(15, excess/2000). Profile extraction writes `salary_min_gbp`, not this key, so the component stays neutral unless the profile is edited by hand. |
| Freshness | +5 if the posting is at most `max_age_days // 2` days old (age is measured against the current clock). |

**History-cohort augmentation.** For `cohort="history"` only, the role-overlap token set is
widened with every token in `HISTORY_COHORT_KEYWORDS` before overlap is computed. Without
this, the marketing-heavy `target.roles` list scores genuine research, policy and archive roles
at zero overlap, and the +22 cohort bonus alone cannot lift them into the top 25. The guard
never runs for Section A, so Section A's ordering is unaffected. Multi-word keywords such as
"civil service" are tokenised into their single words.

The cohort keyword sets (`MARKETING_COHORT_KEYWORDS`, `HISTORY_COHORT_KEYWORDS`) and the
band-3 strength synonyms are **hard-coded in the scorer module**, not loaded from config. This
breaks config purity (backlog). The keyword categories are listed in the
[kiera-job-search skill](../ai_context/project/ai_harness/skills/kiera-job-search/SKILL.md).

## Ranking and dual cohort

- `rank_listings()` computes final = phase1 × 0.4 + (phase2 or phase1) × 0.6. With no phase 2,
  final therefore equals phase 1. Results are sorted by (−final, `source::source_id`), cut to
  `top_n` (0 means no cut), and numbered 1..N in sorted order.
- **Dual-cohort mode** is switched on by a research-top value above 0:
  - Section A uses the marketing pool (or the shared pool). Its cohort is `marketing` unless a
    dedicated Section A pool is passed, in which case it is `None` (vanilla). Vanilla scoring
    keeps Section A identical to a single-cohort baseline on that pool.
  - Section B ranks its whole pool with `cohort="history"`. It then drops any entry whose exact,
    case-sensitive `(title, company)` is in Section A, takes the top N, and re-ranks them from 1.
    No role ever appears in both sections.
  - If a cohort has no pool, it uses the synthetic dry-run listings for that cohort.
- Single-cohort mode (no research-top) ranks one shared pool with `cohort=None`.

## Applied-jobs store

The store is a JSON list in `output/_pipeline/applied_jobs.json` by default. Its key is
`(title.strip().lower(), company.strip().lower())`. Adding a record never overwrites an existing
key. The filter matches the exact key, or, for records with an empty company, the title alone.
Syncing to the external sheet is done by the
[log-applied-jobs skill](../ai_context/project/ai_harness/skills/log-applied-jobs/SKILL.md)
through browser tools. The CLI's `sync-from-sheet` only prints instructions.

## Output folder layout

The default output root is `implementation/job_seeker/config/output/`, which is gitignored. The
code creates `_pipeline/` there when the CLI is imported and defaults the applied store into
it. **Every other output path is chosen by the caller.** The layout below is a convention that
the skill sets by passing explicit paths:

| Location | Contents |
|---|---|
| `output/` (top level) | Human-facing `.html` only, e.g. `latest_shortlist.html` |
| `output/_pipeline/` | JSON/MD caches: `latest_shortlist{,_marketing,_history}.json`, `latest_shortlist.md`, `latest_listings.json`, `applied_jobs.json` |
| `output/_pools/` | Raw ingest pools: `pool_marketing.json`, `pool_research.json`, plus exploration pools |
| `<parent>/_archive/` | Timestamped copies `<stem>_YYYYMMDD_HHMM<ext>` |

The writer saves to `<parent of target>/_archive/<stem>_<stamp><ext>`, copies that file to the
target path (the stable "latest" alias), and then prunes files older than 7 days (by mtime)
from **that same `_archive/`**. So each folder gets its own archive: `output/_archive/`,
`output/_pipeline/_archive/` and `output/_pools/_archive/`. All artefacts from one match run
share a single timestamp. The applied store is written directly, with no archive copy.

HTML output is self-contained, with inline CSS. All listing text is HTML-escaped, and links open
with `rel="noopener nofollow"`.

## Lazy `ai_agent_core` import and `--help`

`main()` takes the first non-flag argument and registers only the subparsers that argument
needs. `profile` and `ingest` are always registered. `applied` is registered only when it is the
first argument. `match` and `draft` are registered only when named, and only then are the
LLM-mode flags from `ai_agent_core.execution.add_execution_args` added. This is why
`ai-job-seeker --help` lists only `profile` and `ingest`.

**This does not make profile or ingest independent of `ai_agent_core`** (verified 2026-10-11).
`cli.py` imports the `match` package at module load. That package imports `match/llm_judge.py`,
and `llm_judge.py` imports `ai_agent_core.execution` at its top level. With `ai_agent_core`
unimportable, importing the CLI fails, so every subcommand needs the sibling checkout. The
docstrings that say otherwise are stale.

## Design decisions

- **Deterministic first, model optional.** Phase 1 is cheap, explainable, runs on an 8 GB
  machine, and needs no keys. Phase 2 is an additive judge behind a backend switch.
- **Exclusions in YAML.** The candidate's "never show me X" feedback changes the data, not the
  code.
- **Two independent cohorts, one HTML file.** Section A is preserved exactly at the operator's
  request. Section B widens discovery without disturbing it.
- **Stable alias plus a 7-day archive.** A re-run never destroys the previous deliverable, and
  the folder the candidate opens stays clean.
- **Deterministic CV extractor.** The extractor parses one graduate-CV layout by section
  headers. No capability-decision record exists for it, so it is a candidate for capability-fit
  review.
- **Trifecta boundary.** Postings are data only. Ingest never interprets them, and the phase-2
  prompt puts them in a labelled untrusted block after the instructions. Ingest does read board
  credentials in the same process that fetches postings. That is a mechanical HTTP call, not an
  LLM context, and no LLM call exists in ingest.

## Tests

- `test_ingest.py` (13): config load, dedupe, age filter, dry run, normalisers, CLI JSON output.
- `test_match.py` (16): scorer components, the LLM-merge and trifecta ordering, handoff
  re-raise, ranking stability, and the CLI.
- `test_backend_modes.py` (3): the backend-mode switch.

All synthetic dry-run listings ("Data Engineer") are hard-blocked, so a CLI test that must reach
phase 2 supplies its own non-engineering listing as ingest JSON. Some tests create a stub profile
at the default profile path if none exists.

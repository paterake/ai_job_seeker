# Runners: ai_job_seeker

These are all the operational commands. Run them **from the repo root** and always through `uv`.
Never use bare `python` or `pip`. What each one does in the full pipeline is in
[RUNBOOK.md](RUNBOOK.md). Flags were checked against the argparse code on 2026-10-11.

## Setup

```bash
# sibling checkouts must exist: ../ai_agent_core (required) and ../ai_agent_pco (validators only)
uv sync                       # resolve the workspace incl. the ai_agent_core path dependency
uv run ai-job-seeker --help   # lists only profile + ingest (match/applied/draft register on demand)
```

## profile

```bash
uv run ai-job-seeker profile                       # load + summarise the default profile
uv run ai-job-seeker profile --extract             # CV .docx -> profile YAML (refuses to overwrite)
uv run ai-job-seeker profile --extract --force     # re-extract, overwriting the YAML
```

| Flag | Default | Meaning |
|---|---|---|
| `--candidate PATH` | `implementation/job_seeker/config/profile/kiera.yaml` | Profile YAML to load (and the `--extract` target) |
| `--extract` | off | Extract a profile from the CV `.docx` |
| `--cv-docx PATH` | from backend config | CV to extract from |
| `--output PATH` | the `--candidate` path | Where `--extract` writes |
| `--force` | off | Allow `--extract` to overwrite |

## ingest

```bash
uv run ai-job-seeker ingest --dry-run                                  # synthetic listings, no keys
uv run ai-job-seeker ingest --search "marketing" --location "London" \
  --json implementation/job_seeker/config/output/_pools/pool_marketing.json
uv run ai-job-seeker ingest --search "graduate research" --location "London" \
  --json implementation/job_seeker/config/output/_pools/pool_research.json
```

| Flag | Default | Meaning |
|---|---|---|
| `--search-config PATH` | `implementation/job_seeker/config/search.yaml` | Source and filter config |
| `--dry-run` | off | Use synthetic samples instead of the APIs |
| `--search TEXT` | empty | Search terms. Commas split terms, which are then space-joined into one query that must match every word, so do **not** comma-separate concepts. The Muse ignores this flag. |
| `--location TEXT` | empty | Location passed to every source |
| `--json PATH` | none | Write the listings: a timestamped copy goes to `<dir>/_archive/`, plus the alias at PATH |

## match

```bash
# default dual-cohort run (agent mode, phase-1 only)
uv run ai-job-seeker match \
  --marketing-ingest-json implementation/job_seeker/config/output/_pools/pool_marketing.json \
  --history-ingest-json   implementation/job_seeker/config/output/_pools/pool_marketing.json \
  --history-ingest-json   implementation/job_seeker/config/output/_pools/pool_research.json \
  --top 25 --research-top 25 \
  --applied-json   implementation/job_seeker/config/output/_pipeline/applied_jobs.json \
  --json-marketing implementation/job_seeker/config/output/_pipeline/latest_shortlist_marketing.json \
  --json-history   implementation/job_seeker/config/output/_pipeline/latest_shortlist_history.json \
  --json           implementation/job_seeker/config/output/_pipeline/latest_shortlist.json \
  --md             implementation/job_seeker/config/output/_pipeline/latest_shortlist.md \
  --html           implementation/job_seeker/config/output/latest_shortlist.html

uv run ai-job-seeker match            # single cohort over dry-run samples (currently all hard-blocked, empty result)
```

| Flag | Default | Meaning |
|---|---|---|
| `--candidate PATH` | default profile | Profile YAML |
| `--search-config PATH` | default `search.yaml` | Used for `max_age_days` and the dry-run fallback |
| `--ingest-json PATH` | none | Shared pool. Repeatable or comma-separated; multiple pools are merged and deduped, with the first pool winning |
| `--marketing-ingest-json PATH` | none | Section A pool only. Repeatable. Its presence switches Section A to vanilla scoring |
| `--history-ingest-json PATH` | none | Section B pool only. Repeatable |
| `--top N` | `25` | Section A cap (the single-cohort cap too). The skill rule is never below 25 |
| `--research-top N` | `0` | Above 0 turns on dual-cohort mode and caps Section B |
| `--applied-json PATH` | `output/_pipeline/applied_jobs.json` | Applied-jobs store used for filtering |
| `--json PATH` | none | Dual: combined `{marketing, history, generated_at}`. Single: list |
| `--json-marketing PATH`, `--json-history PATH` | none | Dual only: per-cohort lists |
| `--md PATH`, `--html PATH` | none | Markdown / self-contained HTML shortlist |
| `--open` | off | Open the HTML (or the MD, if there is no HTML) in the default app |
| `--search TEXT`, `--location TEXT` | empty | Informational only, printed in the shortlist header |

**LLM backend flags.** These are added to `match` and `draft` by `ai_agent_core`. Agent mode
needs none of them. See [AI.md](AI.md) before using them, and never use them on the 8 GB machine.

| Flag | Meaning |
|---|---|
| `--ollama-model NAME` | Local mode |
| `--ollama-url URL`, `--ollama-timeout-s S` | Local endpoint and timeout. Defaults come from `backend.yaml` |
| `--llm-provider NAME` **and** `--llm-model NAME` | Cloud mode (both required) |
| `--llm-base-url`, `--llm-timeout-s`, `--llm-temperature`, `--llm-max-tokens` | Cloud tuning |
| `--llm-api-key-file PATH`, `--llm-api-key-dir PATH` | Where the cloud key is read from. Prefer these to `--llm-api-key`, which puts the key in shell history |

## applied

```bash
uv run ai-job-seeker applied add \
  --from-shortlist-json implementation/job_seeker/config/output/_pipeline/latest_shortlist.json \
  --cohort marketing --position 3 --position 7
uv run ai-job-seeker applied add --title "Role title" --company "Company"
uv run ai-job-seeker applied list [--as-json]
uv run ai-job-seeker applied remove --title "Role title" --company "Company"
uv run ai-job-seeker applied remove --all          # irreversible: empties the store
uv run ai-job-seeker applied sync-from-sheet       # prints instructions only
```

| `add` flag | Meaning |
|---|---|
| `--from-shortlist-json PATH` + `--cohort marketing\|history` + `--position N` (repeatable) | Copy title, company, link and source from shortlist entries |
| `--title`, `--company`, `--url`, `--source` | Manual entry. Only `--title` is required |
| `--applied-on YYYY-MM-DD` | Defaults to today |
| `--status` | Defaults to `applied` (others: interviewed, rejected, offer, closed) |
| `--notes` | Free text |
| `--applied-json PATH` | Store path. Also accepted by `list`, `remove` and `sync-from-sheet` |

## draft (placeholder)

```bash
uv run ai-job-seeker draft     # prints backend mode + CV location; "Stage 4 (draft) not implemented yet."
```

## Tests

```bash
uv run python3 -m pytest -q                                                    # all (32 collected)
uv run python3 -m pytest -q implementation/job_seeker/tests/test_match.py      # one file
```

## Governance validators

These need the sibling `../ai_agent_pco` checkout.

```bash
uv run python3 ../ai_agent_pco/scripts/distill_harness.py governed-repo-validate --repo .
uv run python3 ../ai_agent_pco/scripts/distill_harness.py governance-audit --repo . --fail
```

## Diagnostics

```bash
git check-ignore implementation/job_seeker/config/profile/kiera.yaml   # must print the path
git check-ignore implementation/job_seeker/config/output/              # must print the path
```

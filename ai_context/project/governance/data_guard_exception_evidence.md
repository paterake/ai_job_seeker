# Data guard exception: whole repo

Evidence for the `data-guard-*` entries in `exception_registry.yaml`.

## Operator decision

Operator, 2026-10-29, first-hand to the PCO director session: "anything that ai_invest and ai_job_seeker does is
exempt - in effect the exceptions are for both repos".

## What the entries cover

One entry per top-level path of this repo, because the rule accepts no `path:*`: `.claude/*`, `.gitignore`,
`CLAUDE.md`, `README.md`, `ai_context/*`, `docs/*`, `implementation/*`, `pyproject.toml`, `uv.lock`.
Rule: `ai_context/pco/governance/data_guard.yaml`. Owner Rakesh Patel; granted by Rakesh Patel (operator).

## Expiry

Granted 2026-10-29, expires 2027-01-27 (the 90-day cap). The entries lapse then and the files are scanned again.
They need renewal, or removal, before that date.

## Office files stay denied

The gate never excepts Office types (xlsx, xlsm, xls, docx, docm, doc, pptx, ppt). These entries do not change that.

## Named gaps

- A top-level path added later is not covered until an entry is added for it.
- One malformed entry stops the gate for the whole repo.
- An agent can commit its own entry; only the reviewer verdict stands between.

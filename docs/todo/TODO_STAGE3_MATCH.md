# ai_job_seeker — Backlog Item: Stage 3 Match Scoring (two-phase scorer)

Project-level anchor doc. Baseline repo is `../ai_job_seeker`.

Stage 3 sits between Ingest (Stage 2) and Draft (Stage 4). It consumes
normalised `JobListing`s from the ingest pipeline and returns a ranked
shortlist of `ScoredListing` records with a per-listing rationale.

The LLM-authoring step (phase 2) reuses `ai_agent_core.execution`'s
`generate_json`, `execution_config_from_namespace`,
`resolve_execution_mode`, `AgentHandoffRequired`, and
`format_agent_handoff` surfaces exactly as wired by the wire-up anchor.

Per backlog-continuity contract, a fresh session should be able to
execute Still-Todo from this file alone.

---

## Resume (start here)

- **Status:** Stage 3 COMPLETE. Two-phase scorer is in place, CLI wired,
  16 match tests pass green, workspace-wide 32/32 tests (no regressions
  from Stage 0-2), all three CLIs green on default zero-key dry-run,
  PII + outputs gitignore confirmed, zero lint/type diagnostics.
- **Next:** Stage 4 — Draft (tailored cover letter + CV per shortlist).
  Scaffold `docs/todo/TODO_STAGE4_DRAFT.md` mirroring this file's
  structure (Completion criteria, Done, Still-todo, Constraints,
  Verification), then resume from its anchor.
- **Session start prompt for Stage 4 once anchored:**

  ```
  from docs/todo/TODO_STAGE4_DRAFT.md continue
  ```

- **Before touching Stage-4 code, read (in order):**
  1. `ai_context/project/ASSISTANTS.md` then platform
     `ai_context/pco/ASSISTANTS.md`.
  2. `ai_context/project/governance/REPO_CONTRACT.md` — confirms
     `ai_job_seeker` consumes `ai_agent_core` as a dependency (never
     vendor); confirms lethal-trifecta isolation posture.
  3. `../ai_agent_core/implementation/ai_agent_core/src/ai_agent_core/execution/__init__.py`
     — the shared public surface any LLM-authoring step calls.
  4. Stage-3 surfaces Stage 4 builds on:
     - `implementation/job_seeker/src/ai_job_seeker/match/__init__.py`
       (`ScoredListing`, `rank_listings`). The `ScoredListing` record is
       the unit Stage-4 drafts from.
     - The LLM-authoring pattern proved by
       `implementation/job_seeker/src/ai_job_seeker/match/llm_judge.py`:
       trifecta-safe section ordering (INSTRUCTIONS first, then fenced
       PROFILE, then fenced LISTINGS untrusted data), single
       `generate_json(cfg, prompt_text, require_dict=True)`, local
       `_validate_schema` after parse, `AgentHandoffRequired` prints
       `format_agent_handoff` with temp-file paths then re-raises (never
       swallow).
  5. `## Accumulated Active Constraints` below — every one of these is
     binding on every remaining stage, including Draft.

---

## Backlog Item: Stage 3 — Match scoring

### Context

The ingest pipeline already returns a deduplicated, age-filtered list of
`JobListing` records (dry-run or live). The profile loader already
returns a validated dict (`identity`, `target`, `summary`, `skills`,
`experience`). The LLM backend switch is wired into the `match`
subparser and verified for 3 modes.

Stage 3 fills in the middle: take the two inputs and produce a ranked
shortlist. It is split into two phases on purpose:

- **Phase 1 (deterministic pre-pass):** cheap Python rules — no LLM, no
  mixing of profile secrets with untrusted posting text in a prompt
  context. Produces a baseline score, obvious dropouts, and structured
  keyword-overlap evidence. Trifecta-safe.
- **Phase 2 (LLM judge):** calls `generate_json(...)` from
  `ai_agent_core.execution` against a strict JSON schema. Defaults to
  AGENT handoff (in-session coding agent authors a score) so this works
  with zero API keys; Ollama and OpenRouter are one CLI flag away. This
  is the single LLM-authoring step per match run.

### Completion criteria

At the end of this item all of the following hold (all VERIFIED GREEN):

1. `implementation/job_seeker/src/ai_job_seeker/match/` package
   exists:
   - `schema.py` — `ScoredListing` dataclass
     (`listing: JobListing`, `phase1_score`, `phase1_evidence: list[str]`,
     `phase2_score | None`, `phase2_rationale | None`,
     `fabricated_claim_flags: list[str]`, `final_score`,
     `ranked_position`).
   - `deterministic.py` — `score_deterministic(profile, listing) ->
     (float, list[str])` covering role keywords, location, remote,
     salary, posted-age bonus; normalised 0–100; never crashes.
   - `llm_judge.py` — `score_with_llm(cfg, profile, listings) ->
     dict[str, dict]` keyed by `source + source_id`; single prompt with
     INSTRUCTIONS then fenced PROFILE + fenced LISTINGS (trifecta-safe);
     `_validate_schema` on output; `AgentHandoffRequired` prints
     `format_agent_handoff` with temp-file paths and re-raises.
   - `__init__.py` re-exports public surface: `ScoredListing`,
     `rank_listings`, `score_with_llm`, `score_deterministic`.
2. `rank_listings(profile, listings, cfg, mode, top_n, w1, w2) -> list[ScoredListing]`
   composes phase-1 then (optional) phase-2, sorts descending by
   final_score with stable tie-breaker, assigns dense `ranked_position`,
   and caps to top-N. Default w1=0.4, w2=0.6 (phase-2 weighted).
3. The existing `ai-job-seeker match` subparser placeholder is
   replaced with a real implementation that:
   - Loads the profile (existing `--candidate` behaviour; ProfileError → rc 1).
   - Accepts `--ingest-json PATH` OR calls `run_ingest_dry()` when
     neither that nor live ingest flags are set (default behaviour:
     dry-run, zero API keys needed).
   - Calls `add_execution_args` → `_build_mode(args)` → if mode is
     anything except agent, also invokes the LLM judge; otherwise,
     stops after phase 1 and prints a "phase 2 skipped — AGENT mode" note.
   - Accepts `--top N` (default 10) and `--json PATH` (writes ranked
     ScoredListing dicts via `to_dict()`, omitting `listing.raw`).
   - Prints a ranked table (rank | final | phase1 | phase2 | source |
     title[:50]) to stdout.
   - `AgentHandoffRequired` propagates to exit-code 2.
4. 16 smoke tests in
   `implementation/job_seeker/tests/test_match.py` covering:
   - Deterministic score moves when profile-role keyword matches vs not.
   - Deterministic score moves on location/remote match vs mismatch.
   - Salary clamp: salary below profile minimum lowers phase-1 score.
   - No-salary-preference neutral component + missing-fields no crash.
   - Freshness bonus (age within half max_age_days).
   - Normalised 0–100 bounds (never <0 or >100 regardless of inputs).
   - LLM-judge mock (monkeypatch `generate_json`) returns a valid
     payload → phase-2 scores merge, fabricated flags surface, trifecta
     ordering holds.
   - LLM-judge `AgentHandoffRequired` path → handoff message in stdout,
     exception re-raised.
   - Full `rank_listings` with dry-run listings → length ≤ top-N,
     `ranked_position` dense 1..N, unique listing keys.
   - Agent-mode rank_listings → phase-2 scores are None, final collapses to phase-1.
   - Stable tie-sort on equal final_scores.
   - `ScoredListing.to_dict()` JSON-serialises without `listing.raw`.
   - CLI `match` default → stdout ranked table, exit 0.
   - CLI `match --ollama-model …` with monkeypatched AgentHandoffRequired → exit 2.
5. No regressions: all 16 prior Stage 0-2 + wire-up tests still pass
   at workspace root (`uv run python -m pytest -q` → 32/32 total). Profile and
   ingest dry-run CLIs still work; PII stays gitignored.

### Done

All 8 still-todo steps completed in session 6a7b739a3ec31b8744b042c0 continuation:

1. ✅ Scaffolded `implementation/job_seeker/src/ai_job_seeker/match/` package:
   `schema.py`, `deterministic.py`, `llm_judge.py`, `__init__.py`.
   Public surface via `__init__.py`: `ScoredListing`, `rank_listings`,
   `score_deterministic`, `score_with_llm`.
2. ✅ Deterministic pre-pass `score_deterministic(profile, listing, *, max_age_days=21)`
   → (float 0-100, list[str]): keyword overlap +5/token cap+25; location +15;
   remote policy (+10/−5/neutral); salary clamp ±15; freshness +5 within
   half max_age. Baseline +40; clamped to 0-100. Never crashes on absent fields.
3. ✅ LLM judge `score_with_llm(cfg, profile, listings, *, module, call_site)`
   → dict keyed by `source::source_id`. Single `generate_json` call with
   trifecta-safe prompt ordering (INSTRUCTIONS → fenced PROFILE DATA →
   fenced LISTINGS; `description` truncated to 800 chars with
   `_description_truncated` flag). Per-row `_validate_schema` after parse.
   On `AgentHandoffRequired`: writes prompt + empty-result JSON to `$TMPDIR`,
   prints `format_agent_handoff()` with paths, re-raises (never swallow).
   Uses shared-lib API shape `generate_json(cfg, prompt_text, require_dict=True)` exactly.
4. ✅ `rank_listings(profile, listings, cfg=None, mode=None, top_n=10,
   w1=0.4, w2=0.6, max_age_days=21)` composed in `__init__.py`. Phase-2 runs
   iff cfg AND mode AND `mode.value != "agent"`. Final = phase1*0.4 +
   (phase2 or phase1)*0.6. Stable sort `(-final_score, listing_key asc)`;
   dense 1..N rank; cap top_n.
5. ✅ Replaced `_cmd_match` placeholder in `cli.py`: added `--candidate
   --search-config --ingest-json --top --json` flags; ProfileError → rc 1;
   listings from JSON via `_load_listings_from_json` (loose loader, coerces
   unknown keys, warns and skips bad rows) or `run_ingest_dry(search_cfg)`
   default; mode via `_build_mode(args)`; AGENT mode skips phase-2 and
   prints note; prints ranked table `(# | Final | P1 | P2 | Src | Title[:50])`;
   `--json` writes `ScoredListing.to_dict()` array. AgentHandoffRequired
   from phase-2 bubbles through → CLI returns rc 2 (never silently
   downgrades to phase-1 only).
6. ✅ Smoke tests in `test_match.py`: 16 tests covering all cases listed
   under Completion criteria (4) plus robustness guards. LLM judge mocked
   via monkeypatch; no network calls. All pass offline.
7. ✅ Full verification pass recorded under `## Verification` below.
   Every command has been run and printed green (or expected non-zero on
   the agent-handoff path).
8. ✅ `docs/todo/TODO.md` project anchor updated: Stage 3 → ✅ CODE COMPLETE
   with file-by-file Done list + CLI behaviour; Resume → Stage 4 Draft
   scaffold; Verification → 32/32 tests; session-start prompt swapped.

### Still todo (Stage 4 prep — blocked on user confirmation of Stage-3 correctness)

1. User review: does two-phase scorer output make sense for Kiera's profile
   vs live ingest (once API keys set)? Tune w1/w2 defaults if needed.
2. Scaffold `docs/todo/TODO_STAGE4_DRAFT.md` mirroring this file's
   structure (Completion criteria → Cover letter JSON-schema prompt +
   CV-bullet cross-map generation; no-fabrication guard; Stage-5 packet
   handoff; Done / Still-todo / Constraints / Verification sections).
3. Live phase-2 smoke (user action): with `--ollama-model llama3.1` running
   locally OR `--llm-provider openrouter --llm-model <id>` + key file,
   verify `uv run ai-job-seeker match` completes phase-2 and merges scores.

### Accumulated Active Constraints (active for every remaining stage)

Forwarded from prior anchor docs + new Stage-3 specifics:

- **PII stays out of git.** `implementation/job_seeker/config/profile/`
  and `implementation/job_seeker/outputs/` are gitignored; never
  commit candidate data, draft content, or any generated packet.
- **No fabrication.** Every claim in a generated CV/letter/message
  traces to the profile YAML. Phase-2 schema enforces
  `fabricated_claim_flags` per listing; the pipeline exposes them.
- **Submission is a human-approval gate.** Match never auto-sends and
  never writes to the outputs directory — that privilege is Stage 5
  Packet only.
- **Trifecta isolation.** Phase-1 is pure data/data, no prompt
  assembly. Phase-2 prompt-build MUST separate:
  (1) instructions (first section, terminates before data fences),
  (2) profile facts (labelled fenced block, never in the instruction
  section),
  (3) untrusted listings text (labelled fenced block, never parsed or
  re-used as instructions). Never copy a snippet of posting text into
  an instruction line like "treat the following…" — *the fence labels
  already do that*.
- **LLM backend is a 3-way switch; AGENT-handoff is the default.**
  Cloud is opt-in only. Invariants enforced by the shared
  `resolve_execution_mode` — do NOT re-implement it.
- **Config purity.** Domain strings live in YAML (`backend.yaml`,
  `search.yaml`, profile); secrets in `.env` (gitignored) or the
  `__cfg/api_key/*.txt` provider-defaults path; never in code or
  tracked files.
- **uv only.** No pip install; one-responsibility-per-file; thin
  `main()` over importable modules.
- **Consume `ai_agent_core` as a dependency, never vendor.** If
  something is missing from the shared lib (e.g. a schema helper, a
  JSON prompt builder), fix it upstream first, then point
  `ai_job_seeker` at the updated version — never copy/paste into
  `ai_job_seeker`.
- **Provider-default + key-file semantics are the cloud convenience
  path.** OpenRouter must work from `--llm-provider openrouter
  --llm-model <id>` with nothing else; if insufficient, the gap
  belongs in `ai_agent_core`, not in `ai_job_seeker`-local shims.
- **Double-`/v1` 404 defence + vendor→transport normalisation is
  handled in `ai_agent_core.execution`.** All base URLs pass through
  unchanged from provider-defaults; never re-strip or remap locally.
- **Phase-2 prompt size budget.** A single generate_json call
  consumes `llm_max_tokens` set by
  `add_execution_args`/`backend.yaml` (default 6000). If top-N +
  long postings overrun, truncate `listing.description` to 800 chars
  before prompt-building (and add a truncated marker to the fenced
  block footer) rather than failing the run.

### Verification

All commands run and recorded green at session close:

1. ✅ Dependency + shared-lib imports:
   `uv run --project implementation/job_seeker python -c "…"` → **prints `imports-ok`**.
2. ✅ Profile still works:
   `uv run ai-job-seeker profile` → prints candidate Kiera Patel, 8 roles / 8 skills / 8 experience, rc=0.
3. ✅ Ingest dry-run still works (feeds Stage 3):
   `uv run ai-job-seeker ingest --dry-run` → 4 listings (adzuna×2, reed, themuse), max_age=21 days, rc=0.
4. ✅ Match command in phase-1-only default (no LLM flags == AGENT mode):
   `uv run ai-job-seeker match` → ranked table (N=4 ≤ 10), note "phase-2 LLM judge skipped — AGENT mode", rc=0.
5. ✅ Match agent-handoff path (pytest monkeypatch):
   `test_cli_match_agent_handoff_exits_2` → CLI returns rc=2 AND stdout/stderr contains "handoff"/"coding agent".
   `test_llm_judge_agent_handoff_prints_and_reraises` → prints handoff block then re-raises.
6. ✅ Smoke tests pass facet-level:
   `uv run --project implementation/job_seeker python -m pytest implementation/job_seeker/tests/test_match.py -q` → **16 passed**.
7. ✅ Workspace-wide pytest (no regressions):
   `uv run python -m pytest -q` → **32 passed** (16 Stage 0-2 + 16 Stage 3 match).
8. ✅ PII not tracked:
   `git check-ignore implementation/job_seeker/config/profile/kiera.yaml` → `.gitignore:31:implementation/job_seeker/config/profile/` matches.
   `git check-ignore implementation/job_seeker/outputs/.gitkeep` → `.gitignore:32:implementation/job_seeker/outputs/` matches.
9. ✅ No lint/type diagnostics via IDE `GetDiagnostics` → empty result.

### Gotchas

- **`--ingest-json` schema contract:** when writing and reading the
  listings JSON, fields are the `JobListing.to_dict()` output. If a
  hand-rolled JSON is used instead, Stage 3 still accepts a "loose"
  loader (`_load_listings_from_json` in cli.py) that coerces unknown
  source_ids gracefully — never crashes on extra keys.
- **Ollama phase-2 with no model running:** in phase-2 `mode ==
  OLLAMA`, `generate_json` raises an HTTP-level error. That is the
  correct behaviour. Stage 3 does not catch it, nor fall back to
  phase-1 silently — a clear stderr trace is correct UX, matching the
  wire-up item's "fail loud" pattern for cloud too.
- **Deterministic scorer never crashes on absent fields.** e.g.
  profile has no `target.expected_salary_min` → salary component
  contributes 0 and an evidence bullet says "no salary preference
  in profile". Listing has `salary_min = None` → no penalty.
- **`ranked_position` after ties.** Use `(final_score desc,
  source_id asc)` as secondary sort so two listings with identical
  scores still get a stable, reproducible rank across runs.
- **Phase-2 LLM judge returns partial data?** The `_validate_schema`
  local step enforces per-row required keys, types, and ranges; any
  deviation raises `GenerationError` loudly before merge. Do NOT
  implement a "best-effort merge" of partial phase-2 data onto phase-1.
- **Profile PII must not be echoed to stdout.** The match table
  prints job-listing fields and scores, never the candidate's name,
  contact, or specific experience details. Rationale bullets from
  phase-2 can appear but Stage-3 system prompt explicitly instructs
  against verbatim phone/email PII.
- **Test file path vs fixture path:** tests resolving config YAMLs
  use `Path(__file__).resolve().parents[1] / "config" / ...yaml`
  (Stage-2 pattern) — pytest cwd and import-mode can make relative
  paths point to `implementation/` otherwise.
- **Shared-lib `format_agent_handoff` signature.** It REQUIRES
  `prompt_file: Path` + `output_file: Path` (not None) and does not
  accept a `schema=` kwarg. Stage-3 implementation writes prompt +
  seed JSON to `$TMPDIR` and passes those real paths; callers then
  hand the temp files to their coding agent as described by the
  handoff block.

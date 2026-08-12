# ai_job_seeker — Backlog Item: Wire ai_agent_core.execution (tri-mode LLM switch)

Cross-repo backlog anchor doc. Baseline repo is `../ai_job_seeker`.
Shared library lives in `../ai_agent_core` at
`implementation/ai_agent_core/src/ai_agent_core/execution/`.

This anchor replaces the project-level TODO.md's "reference implementation in
ai_doc" with the new callable shared library. Per backlog-continuity contract,
a fresh session should be able to execute Still-Todo from this file alone.

---

## Resume (start here)

- **Status:** Item COMPLETE. All 6 Still-todo steps implemented and verified.
  All 6 Verification checks pass (imports, profile, 3× mode-switch, 3× smoke
  tests, project-wide pytest, PII gitignore). Workspace pattern matches
  `ai_platform` exactly (editable source via `[tool.uv.sources]`).
- **Next:** Item closed. Resume from
  `docs/todo/TODO_STAGE3_MATCH.md` → Still-todo step 1
  (two-phase scorer package scaffold). Stage 2 ingest also complete; dry-run
  synthetic listings feed Stage 3 out of the box.
- **Session start prompt (paste verbatim at start of a new session):**
  (item complete — no resumption needed; if re-opening, run the Verification
  section first to confirm state, then go to TODO_STAGE3_MATCH.md.)
- **Before touching code, read (in order):**
  1. `ai_context/project/ASSISTANTS.md` then platform `ai_context/pco/ASSISTANTS.md`.
  2. `ai_context/project/governance/REPO_CONTRACT.md` — confirms ai_job_seeker
     consumes `ai_agent_core` as a dependency (never vendor).
  3. `../ai_agent_core/implementation/ai_agent_core/src/ai_agent_core/execution/__init__.py`
     (shared public surface).
  4. `## Accumulated Active Constraints` below — these hold for every step of
     this item.
  5. Surfaces modified by this item: `cli.py`, `backend.py`, `backend.yaml`,
     `pyproject.toml` (workspace root), `implementation/job_seeker/pyproject.toml`,
     `implementation/job_seeker/tests/test_backend_modes.py`, `docs/TODO.md`.

---

## Backlog Item: Wire ai_agent_core.execution into ai_job_seeker

### Context

Previously ai_job_seeker documented "pattern lifted from ai_doc"
(`config/backend.yaml`, project TODO.md Stage 3 reference). The duplicated
tri-mode plumbing (agent / local Ollama / cloud) now lives as a tested,
live-validated callable library in `ai_agent_core.execution`. This item swaps
ai_job_seeker over to consuming it as a library.

### Completion criteria

At the end of this item all of the following hold:

1. `ai_job_seeker` imports `generate_text`, `generate_json`,
   `add_execution_args`, `execution_config_from_namespace`, `ExecutionConfig`,
   `AgentHandoffRequired`, `format_agent_handoff`, and
   `resolve_execution_mode` exclusively from `ai_agent_core.execution`; no
   local copies of `_best_effort_parse_json`, Ollama HTTP code, or
   provider-switch logic exist in the repo.
2. Every CLI subcommand that performs LLM-authoring (match scoring, drafting,
   and later packet polish) accepts the standard flag surface via one
   `add_execution_args(subparser)` call per subparser and builds config via
   `execution_config_from_namespace(args)`. No hand-written `add_argument` for
   `--ollama-model / --llm-provider / --llm-api-key-*`.
3. `config/backend.yaml` still expresses intent (default_mode, preferred
   model, etc.) but its values are applied as ArgDefaults to the shared parser
   or merged into the constructed ExecutionConfig *before* calling
   resolve_execution_mode / generate_text. YAML schema remains stable; the
   code that interprets it is deleted if duplicated, or reduced to a thin
   YAML → ArgDefaults / ExecutionConfig merge.
4. For the AGENT mode path: match and draft commands that cannot proceed
   without authoring catch `AgentHandoffRequired`, print
   `format_agent_handoff(prompt_file=…, output_file=…, …)`, exit non-zero, and
   do not swallow the exception silently.
5. For the CLOUD path, OpenRouter works out of the box exactly as tested in
   ai_agent_core: `--llm-provider openrouter --llm-model <id>` is sufficient
   because base_url + key-file come from provider-defaults via
   `~/Documents/__data/__cfg/api_key/openrouter.txt`. No hardcoded keys, no
   storing them in `.env` unless the user chooses that alternate path.
6. No regressions: `uv run ai-job-seeker profile` still works; pytest passes
   for the repo (including a new smoke-style test for each mode if Stage 3 is
   implemented alongside).

### Done
- Baseline audit of ai_job_seeker surfaces (initial state):
  - `implementation/job_seeker/src/ai_job_seeker/cli.py` — one `profile`
    subcommand currently, uses argparse subparsers. Future match/draft subparsers
    are the plug-in points for `add_execution_args(...)`.
  - `implementation/job_seeker/config/backend.yaml` — hand-written
    default_mode/local/cloud block; no code yet reads it. After this item
    its values flow into ArgDefaults / ExecutionConfig.
  - `pyproject.toml` (workspace root) — members =
    `["implementation/job_seeker"]`. Currently no `ai_agent_core` member, no
    `[tool.uv.sources]` entry for it.
  - `implementation/job_seeker/pyproject.toml` — dependencies are
    `pyyaml, python-docx, requests`. No `ai-agent-core` dep yet.
  - Tests dir: `implementation/job_seeker/tests/` (empty, ready to add new
    smoke tests).
- Shared library ready (in ai_agent_core, audited as baseline for this item):
  - Public surface re-exported at `ai_agent_core.execution.__init__`.
  - Full mocked coverage (60 tests, 227 pass repo-wide) AND live 3-mode
    smoke run on the exact three backends: AGENT sentinel, Ollama local
    `qwen3.5:9b`, OpenRouter cloud (via provider-defaults + key-file ref to
    ~/Documents/__data/__cfg/api_key/openrouter.txt, never copied).
- **Step 1 — Workspace + dependency wired.**
  - Workspace `[tool.uv.sources]` exposes `ai-agent-core = { path =
    "../ai_agent_core/implementation/ai_agent_core" }` (editable source,
    matching `ai_platform/pyproject.toml` exactly; `ai_agent_core` is not a
    workspace member because it lives in a sibling repo).
  - `implementation/job_seeker/pyproject.toml` dependencies include
    `ai-agent-core>=0.5.0` (distribution name confirmed from ai_agent_core's
    pyproject).
  - `uv sync` clean; sanity import prints `imports-ok`.
- **Step 2 — Thin backend bridge `backend.py` added.**
  - `load_backend_defaults(cfg_path) -> ArgDefaults` — reads YAML, returns
    ArgDefaults with `ollama_url` (local.base_url) and `ollama_timeout_s`
    (local.timeout_s); cloud intentionally has no ArgDefaults so it stays
    opt-in.
  - `apply_backend_overrides(cfg, cfg_path) -> ExecutionConfig` — fills
    `cfg.ollama.model` from YAML when `default_mode: local` AND
    `local.model` is set AND CLI left it empty; for cloud, fills
    provider+model only when BOTH are set in YAML, raises
    ExecutionConfigError on XOR.
  - 74 lines total (< 100 constraint); all symbol imports from
    `ai_agent_core.execution` public surface (no submodule paths).
- **Step 3 — Standard flags wired into match + draft subparsers.**
  - `cli.py` adds `p_match` and `p_draft` placeholder subparsers (each prints
    `"Stage N not implemented yet"` after resolving mode).
  - Each calls `add_execution_args(p_, defaults=load_backend_defaults())`.
  - Shared `_build_mode(args)` constructs ExecutionConfig via
    `execution_config_from_namespace → apply_backend_overrides →
    resolve_execution_mode`, catching `ExecutionConfigError` → exit 2.
  - Placeholder `_cmd_match` prints `Selected backend mode: {mode.value}`.
  - Placeholder `_cmd_draft` additionally prints `Resolved cloud base_url`
    from `resolve_cloud_endpoint_and_key(cfg.cloud)` when `mode == cloud`,
    so OpenRouter provider-default wiring is visible without a key.
- **Step 4 — Three mode-smoke tests added under `tests/test_backend_modes.py`.**
  - `test_mode_flags_agent` — no overrides → `AGENT`.
  - `test_mode_flags_ollama` — `ollama_model="qwen3.5:9b"` → `OLLAMA`.
  - `test_mode_flags_cloud` — `llm_provider="openrouter", llm_model="x"` →
    `CLOUD`, plus asserts `resolve_cloud_endpoint_and_key` returns
    `base_url == "https://openrouter.ai/api"` (provider-defaults wired).
  - All three pass from both the facet-level pytest and the workspace-root
    pytest (root pythonpath configured).
- **Step 5 — Project docs updated to point at shared lib, not ai_doc.**
  - `docs/TODO.md` Stage 0 scaffold bullet: `backend.yaml` entry now reads
    `"consumed via ai_agent_core.execution"` instead of `"lifted from ai_doc"`.
  - `backend.yaml` header comment: replaced
    `"Pattern lifted from ai_platform/implementation/ai_doc (Execution Modes A/C/D)"`
    with `"Consumed by ai_job_seeker.backend → ai_agent_core.execution (tri-mode shared lib)."`
  - `docs/TODO.md` Stage 3 heading prose: already correct before this item
    (`"Backend switch uses ai_agent_core.execution (generate_text/generate_json + add_execution_args)"`).
- **Step 6 — Full verification pass recorded below (all 6 checks green).**

### Still todo (ordered, next actions)
_(nothing — item complete)_

### Accumulated Active Constraints (active for all steps above)

Forwarded from existing ai_job_seeker anchor doc + new constraints from the
shared-lib design:

- **PII stays out of git.** Profile dir and outputs dir gitignored; never
  commit candidate data, draft content, or any generated packet.
- **No fabrication.** Every claim in generated CV/letter/message traces to the
  profile YAML.
- **Submission is a human-approval gate.** Pipeline prepares; a person sends.
- **Trifecta isolation.** Ingest postings are data, never instructions.
- **LLM backend is a 3-way switch; AGENT-handoff is the default.** Cloud is
  opt-in only (both provider + model required; never defaulted). This
  invariant is enforced by `resolve_execution_mode` in the shared lib — do
  NOT re-implement it.
- **Config purity.** Domain strings in YAML, secrets by reference only.
  Cloud keys are read from the `__cfg/api_key/*.txt` path via
  `resolve_cloud_endpoint_and_key` or (optionally) env vars; never in code,
  never stored in backend.yaml or a tracked `.env`.
- **uv only.** No pip install; one-responsibility-per-file; thin `main()`
  over importable modules.
- **Consume ai_agent_core as a dependency, never vendor.** If something is
  missing from the shared lib, fix it upstream in ai_agent_core first, then
  point ai_job_seeker at the updated version — do not copy/paste the code
  into ai_job_seeker. (This enforces the single-source-of-truth that this
  backlog item was created to achieve.)
- **Provider-default + key-file semantics are the cloud convenience path.**
  OpenRouter must work from CLI flags `--llm-provider openrouter --llm-model
  <id>` with nothing else; if that is not sufficient, the gap belongs in
  ai_agent_core, not in ai_job_seeker-local shims.
- **Double-`/v1` 404 defence + vendor→transport normalisation is handled in
  ai_agent_core.execution.** ai_job_seeker must not re-strip base URLs or
  re-map "openrouter" to "openai_compatible" — rely on the shared lib.

### Verification

Run these after each completed step; re-run *all* at session close:

1. Dependency import works:
   `uv run --project implementation/job_seeker python -c "from ai_agent_core.execution import generate_text, generate_json, add_execution_args, execution_config_from_namespace, resolve_execution_mode, AgentHandoffRequired, format_agent_handoff; print('imports-ok')"`
2. Profile command still works:
   `uv run ai-job-seeker profile`
3. Demonstrable mode-switch from CLI placeholder subparsers:
   - `uv run ai-job-seeker match` → prints `Selected backend mode: agent`
   - `uv run ai-job-seeker match --ollama-model qwen3.5:9b` →
     `Selected backend mode: ollama`
   - `uv run ai-job-seeker draft --llm-provider openrouter --llm-model google/gemma-4-31b-it:free`
     → `Selected backend mode: cloud` (and also prints resolved base_url
     default from provider-defaults, so OpenRouter wiring is visible on the
     CLI surface without needing a key).
4. Smoke tests pass:
   `uv run --project implementation/job_seeker python -m pytest implementation/job_seeker/tests/ -q`
5. Project-wide pytest (from workspace root) 0 regressions:
   `uv run python -m pytest -q`
6. PII not tracked:
   `git check-ignore implementation/job_seeker/config/profile/kiera.yaml`

### Gotchas

- **ai_agent_core distribution name must match its pyproject.** The import
  path is `ai_agent_core` but the wheel/dependency name may be
  `ai-agent-core`. Do not guess; read
  `../ai_agent_core/implementation/ai_agent_core/pyproject.toml` before
  editing ai_job_seeker's dependency list.
- **Workspace patterns vary across ai_agent_core consumers.** Do not invent a
  workspace-members vs editable-source pattern — copy the exact one
  `ai_doc` uses so ai_job_seeker and ai_doc stay aligned.
- **`backend.yaml`'s `default_mode: agent` plus `local.model: ""` must stay
  the shipped default.** Do not accidentally enable a real Ollama or Cloud
  default for end-users.
- **`map_cloud_provider_for_caller` already handles "openrouter" →
  "openai_compatible" + "groq"/etc in ai_agent_core.** If a new vendor name
  is needed, add it to `OPENAI_COMPATIBLE_VENDORS` in
  ai_agent_core.execution.config, not in ai_job_seeker.
- **Double /v1 404:** shared lib strips a trailing `/v1` from base_url and
  PROVIDER_DEFAULTS already do *not* include it. Do not pass
  `--llm-base-url https://openrouter.ai/api/v1` in examples or in any
  backend.yaml default, because while the code tolerates it, docs shouldn't.
- **Profile PII path must remain ignored:** after adding tests, make sure no
  new file accidentally ends up in `config/profile/` tracked.

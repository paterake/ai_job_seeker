# Agent Hooks

The PCO ships three agent-neutral gates. Each checks one tool call, given as arguments, and answers with its exit
code: 0 passes (no output), 2 denies, with the structured reason on stderr. An agent adapter, which lives in the
agent's own configuration outside `ai_context/`, runs the gate from the harness's pre-tool-use hook: it passes the
call's details as arguments and turns exit 2 into the harness's deny decision. On a pass the call goes through the
harness's normal permission flow; a gate never grants permission. Sync delivers a gate's script and config to a
consumer repo, not its settings wiring: a consumer runs a gate once its own settings call the adapter.

| Gate | Arguments | Needs | Fails closed (exit 2, one-line `GOVERNANCE STOP`) when |
|---|---|---|---|
| `check_execution_limits.sh` | `--state-dir <dir>` (required), `--session <id>` | ruby | no `--state-dir`, no ruby, or no positive `max_tool_calls` in the limits file: a session it cannot count is unbounded. |
| `check_guard.sh` | `--command <shell command>`, `--path <file path>` (either may be empty) | — | given neither flag: a gate given nothing checks nothing. |
| `check_data_guard.sh` | `--path <file path>` (may be empty) | ruby, `file` | for an existing file that is not denied by type: ruby or `file` missing, config missing or unreadable, type or pattern list empty. An empty, directory or missing path passes without these checks. |

The adapter also fails closed, for every gate, when `HOME` is not set (gate state lives under it), when it cannot read the call, when the gate is missing, or when the gate exits with
anything other than 0 or 2. When the adapter itself is missing or crashes: integration spoke → Not enforced.

- `check_guard.sh`: denies `git push --force` / `-f` / `--force-with-lease` / a `+refspec` (`force_push_refused`), because it rewrites shared history; it matches command text (a subshell or `git --<option> push` included), so a quoted form (`bash -c "git push -f"`) or a git alias is not caught. It also denies a file edit under `ai_context/pco/` in any repo other than the PCO (`synced_pco_edit_refused`), matched on the real path, so an edit through a symlinked rules or skills folder is caught too: that tree is PCO-owned and sync overwrites a local edit, so the change belongs in the PCO. The PCO is recognised by its consumer manifest, `ai_context/project/governance/consumers.yaml`, which exists only in the PCO repo. A shell command that writes into `ai_context/pco/` is not checked.

- `check_execution_limits.sh`: counts shell calls per session in `<state-dir>/tool_calls/<id>` (the single
  `<state-dir>/tool_call_count` when there is no session id) and denies (`execution_limit_hit`) once the count
  reaches `max_tool_calls`, writing `<state-dir>/execution_limit_hit`. Every session starts at 0.

- `check_data_guard.sh`: denies (`data_guard_refused`) a file whose extension is an Office type, without opening it
  (case-insensitive, on the given and the symlink-resolved name, even if the file does not exist), and an existing
  text file with a line matching a named pattern. Types, patterns, allowlist (path globs, exact strings) and the
  scan size cap are in `governance/data_guard.yaml`. A binary non-Office file (a PDF, say) and a file over the cap
  pass unscanned; an empty, directory or missing path passes. The deny line names the reason code, path, pattern
  or type and line number, never matched text, because the adapter forwards it to the model.
  Repo exceptions: after the Office deny and the allowlist path check, an active entry in the repo's committed
  `ai_context/project/governance/exception_registry.yaml` passes the files its `scope` covers unscanned. The
  gate reads `HEAD` (`git show`), so a working-tree edit does nothing until committed. An entry applies when its `rule`
  equals `exception_rule` in `data_guard.yaml`; `scope` is `path:<glob>` relative to the repo root, and the text before
  its first `/` must be a plain name of letters, digits, dot, dash and underscore, with no pattern characters, and not
  `.` or `..`, and no segment may be `..` (so `path:docs/fixtures/*` is accepted, `path:*.md`, `path:!(x)/*` and
  `path:docs/../x` are not); after that name `*` crosses `/`. Office
  types are never excepted. Entries that are expired, revoked or past `expires` are skipped and the file is scanned.
  A missing field, a `granted` or `expires` that is not a quoted ISO date string, or a `status` other than active,
  expired or revoked in any data-guard entry stops the gate (`GOVERNANCE STOP: ... cannot read exception registry`)
  for every scanned text file in that repo until fixed; for an active, unexpired entry, so does `expires` more than
  `exception_max_days` after `granted`, an `evidence` path not in `HEAD`, or a scope that fails the rule. A path
  outside the repo never matches.

Not hooks:
- **Capability decisions** are guidance (`code-architecture.md` → Driver Selection), reviewed at code review
  (`harness-tool-contract.md` → Capability Decisions Are Reviewed, Not Gated).
- **Exception expiry:** a validator, not a hook ([master-data spoke](../../master-data/README.md)); an expired
  exception can be renewed or removed, so it is not a must-never-fail gate.

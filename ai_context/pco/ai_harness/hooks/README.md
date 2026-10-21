# Agent Hooks

The PCO ships two agent-neutral gates. Each checks one tool call, given as arguments, and answers with its exit
code: 0 passes (no output), 2 denies, with the structured reason on stderr. An agent adapter, which lives in the
agent's own configuration outside `ai_context/`, runs the gate from the harness's pre-tool-use hook: it passes the
call's details as arguments and turns exit 2 into the harness's deny decision. On a pass the call goes through the
harness's normal permission flow; a gate never grants permission. Consumer repos pick up a gate on their next sync.

| Gate | Arguments | Needs | Fails closed (exit 2, one-line `GOVERNANCE STOP`) when |
|---|---|---|---|
| `check_execution_limits.sh` | `--state-dir <dir>` (required), `--session <id>` | ruby | no `--state-dir`, no ruby, or no positive `max_tool_calls` in the limits file: a session it cannot count is unbounded. |
| `check_guard.sh` | `--command <shell command>`, `--path <file path>` (either may be empty) | — | given neither flag: a gate given nothing checks nothing. |

The adapter also fails closed when it cannot read the call, when the gate is missing, or when the gate exits with
anything other than 0 or 2. When the adapter itself is missing or crashes: integration spoke → Not enforced.

- `check_guard.sh`: denies `git push --force` / `-f` / `--force-with-lease` / a `+refspec` (`force_push_refused`), because it rewrites shared history; it matches command text (a subshell or `git --<option> push` included), so a quoted form (`bash -c "git push -f"`) or a git alias is not caught. It also denies a file edit under `ai_context/pco/` in any repo other than the PCO (`synced_pco_edit_refused`), matched on the real path, so an edit through a symlinked rules or skills folder is caught too: that tree is PCO-owned and sync overwrites a local edit, so the change belongs in the PCO. The PCO is recognised by its consumer manifest, `ai_context/project/governance/consumers.yaml`, which exists only in the PCO repo. A shell command that writes into `ai_context/pco/` is not checked.

- `check_execution_limits.sh`: counts shell calls per session in `<state-dir>/tool_calls/<id>` (the single
  `<state-dir>/tool_call_count` when there is no session id) and denies (`execution_limit_hit`) once the count
  reaches `max_tool_calls`, writing `<state-dir>/execution_limit_hit`. Every session starts at 0.

Not hooks:
- **Capability decisions** are guidance (`code-architecture.md` → Driver Selection), reviewed at code review
  (`harness-tool-contract.md` → Capability Decisions Are Reviewed, Not Gated).
- **Exception expiry:** a validator, not a hook ([master-data spoke](../../master-data/README.md)); an expired
  exception can be renewed or removed, so it is not a must-never-fail gate.

# Agent Hooks

The PCO ships two Claude Code gate hooks. Each returns a PreToolUse decision inside `hookSpecificOutput`. When the
gate trips, the hook prints `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
"permissionDecisionReason": <structured reason>}}` and Claude Code blocks the tool call, in interactive
and non-interactive sessions alike. When it does not trip, the hook exits 0 with no output, so the
call goes through the normal permission flow; it never returns `allow`, because an explicit
`allow` would skip the permission prompt. Consumer repos pick up the script on their next sync.

A gate that cannot run fails closed: it exits 2 with a one-line `GOVERNANCE STOP` reason on stderr, which
Claude Code shows and which blocks the call. Exit 2 needs no `jq`.

| Hook | Event | Needs | When a tool or its config is missing |
|---|---|---|---|
| `check_execution_limits.sh` | PreToolUse(Bash) | jq, ruby | No jq, no ruby, or no positive `max_tool_calls` in the limits file: blocks every shell call, because a session it cannot count is unbounded. |
| `check_guard.sh` | PreToolUse(Bash, Edit, Write, MultiEdit, NotebookEdit) | jq | No jq: blocks every call it sees. |

- `check_guard.sh`: denies `git push --force` / `-f` / `--force-with-lease` / a `+refspec` (`force_push_refused`), because it rewrites shared history. It also denies a file edit under `ai_context/pco/` in any repo other than the PCO (`synced_pco_edit_refused`): that tree is PCO-owned and sync overwrites a local edit, so the change belongs in the PCO. The PCO is recognised by `ai_context/project/governance/consumers.yaml`. A shell command that writes into `ai_context/pco/` is not checked.

- `check_execution_limits.sh`: counts Bash calls per session in `.claude/tool_calls/<session_id>` (falls back to `.claude/tool_call_count` when the payload has no `session_id`) and denies (`execution_limit_hit`) once the count reaches `max_tool_calls`, writing `.claude/execution_limit_hit`. Every session starts at 0.

Not hooks:
- **Capability decisions** are guidance (`governance.md` → Driver Selection), reviewed at code review
  (`harness-tool-contract.md` → Capability Decisions Are Reviewed, Not Gated).
- **Exception expiry:** `exception-registry-validate` (run by `governed-repo-validate`) fails on an
  expired exception. An expired exception can be renewed or removed, so it is not a must-never-fail gate.

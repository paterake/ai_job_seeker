# Agent Hooks

The gate hooks below return a PreToolUse decision inside `hookSpecificOutput`. When a gate trips,
the hook prints `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
"permissionDecisionReason": <structured reason>}}` and Claude Code blocks the tool call, in interactive
and non-interactive sessions alike. When a gate does not trip, the hook exits 0 with no output, so the
call goes through the normal permission flow; the hooks never return `allow`, because an explicit
`allow` would skip the permission prompt. Consumer repos pick up these scripts on their next sync.

A gate that cannot run fails closed: it exits 2 with a one-line `GOVERNANCE STOP` reason on stderr, which
Claude Code shows and which blocks the call. Exit 2 needs no `jq`.

| Hook | Event | Needs | When a tool or its config is missing |
|---|---|---|---|
| `check_capability_decision.sh` | PreToolUse(Bash) | jq, git | No jq: blocks commit / PR-creation commands, and passes other calls. No git: passes, because there is nothing to commit. |
| `check_execution_limits.sh` | PreToolUse(Bash) | jq, ruby | No jq, no ruby, or no positive `max_tool_calls` in the limits file: blocks every shell call, because a session it cannot count is unbounded. |
| `setup_cloud_session.sh` | SessionStart | apt-get | Runs only when `CLAUDE_CODE_REMOTE=true`. Installs whichever of jq, ruby and git is missing. If that fails it prints one line to stdout, which Claude Code adds to the session context, and lets the session start; the gates then block as above. |

- `check_capability_decision.sh`: denies commit / PR-creation commands (`capability_decision_required` / `capability_decision_invalid`) for parser-/extractor-shaped content-interpretation changes unless a valid capability-decision record is present. Detection is a path/keyword heuristic over every file the command could commit: staged, unstaged and untracked. The hook runs before the command, so checking only staged files let `git add … && git commit` and `git commit -a` through (observed 2026-10-20). Two consequences of that over-approximation:
  - a stray untracked parser-shaped file blocks commits until it has a record or is gitignored;
  - an untracked record satisfies the gate even when the command won't commit it.
- `check_execution_limits.sh`: counts Bash calls per session in `.claude/tool_calls/<session_id>` (falls back to `.claude/tool_call_count` when the payload has no `session_id`) and denies (`execution_limit_hit`) once the count reaches `max_tool_calls`, writing `.claude/execution_limit_hit`. Every session starts at 0.

Exception expiry is not a hook: `exception-registry-validate` (run by `governed-repo-validate`) fails on an
expired exception. An expired exception can be renewed or removed, so it is not a must-never-fail gate.

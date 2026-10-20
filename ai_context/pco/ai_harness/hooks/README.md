# Agent Hooks

`pre-commit` is a git hook, not a Claude Code hook: git runs it for every commit made in a clone whose
`core.hooksPath` is `ai_context/pco/ai_harness/hooks`, whichever tool commits. `sync`, `wire` and
`init-consumer` set that, and so does `setup_cloud_session.sh` in any Claude Code session, when it is unset.
It checks only what is staged, which is what the commit records, so a command that creates, stages and commits a
file in one call cannot pass it. A PreToolUse hook runs before the command and could not see such a file
(observed 2026-10-20). It denies by printing the deny shape on stderr and exiting 1, and it needs only git.

The Claude Code gate hook below returns a PreToolUse decision inside `hookSpecificOutput`. When a gate trips,
the hook prints `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
"permissionDecisionReason": <structured reason>}}` and Claude Code blocks the tool call, in interactive
and non-interactive sessions alike. When a gate does not trip, the hook exits 0 with no output, so the
call goes through the normal permission flow; the hooks never return `allow`, because an explicit
`allow` would skip the permission prompt. Consumer repos pick up these scripts on their next sync.

A gate that cannot run fails closed: it exits 2 with a one-line `GOVERNANCE STOP` reason on stderr, which
Claude Code shows and which blocks the call. Exit 2 needs no `jq`.

| Hook | Event | Needs | When a tool or its config is missing |
|---|---|---|---|
| `pre-commit` | git pre-commit | git | Without git nothing is committed. Not in `core.hooksPath`: it does not run (`validate_harness_wiring.py` fails). |
| `check_execution_limits.sh` | PreToolUse(Bash) | jq, ruby | No jq, no ruby, or no positive `max_tool_calls` in the limits file: blocks every shell call, because a session it cannot count is unbounded. |
| `setup_cloud_session.sh` | SessionStart | git; apt-get (cloud) | Sets `core.hooksPath` when it is unset (no git: skipped). When `CLAUDE_CODE_REMOTE=true` it also installs whichever of jq, ruby and git is missing. If either step fails it prints one line to stdout, which Claude Code adds to the session context, and lets the session start; the gates then behave as above. |

- `pre-commit`: refuses the commit (`capability_decision_required` / `capability_decision_invalid`) for staged parser-/extractor-shaped content-interpretation changes unless a valid capability-decision record is staged with them. Detection is a path/keyword heuristic over the staged files. `git commit --no-verify` skips it; a PreToolUse check against that is added only on evidence that agents do it (operator, 2026-10-20).
- `check_execution_limits.sh`: counts Bash calls per session in `.claude/tool_calls/<session_id>` (falls back to `.claude/tool_call_count` when the payload has no `session_id`) and denies (`execution_limit_hit`) once the count reaches `max_tool_calls`, writing `.claude/execution_limit_hit`. Every session starts at 0.

Exception expiry is not a hook: `exception-registry-validate` (run by `governed-repo-validate`) fails on an
expired exception. An expired exception can be renewed or removed, so it is not a must-never-fail gate.

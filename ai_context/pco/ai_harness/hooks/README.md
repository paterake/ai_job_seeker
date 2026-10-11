# Agent Hooks

The gate hooks below return a PreToolUse decision inside `hookSpecificOutput`. When a gate trips,
the hook prints `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
"permissionDecisionReason": <structured reason>}}` and Claude Code blocks the tool call, in interactive
and non-interactive sessions alike. When a gate does not trip, the hook exits 0 with no output, so the
call goes through the normal permission flow; the hooks never return `allow`, because an explicit
`allow` would skip the permission prompt. Consumer repos pick up these scripts on their next sync.

- `check_exception_expiry.sh`: denies Bash calls (`expired_exceptions`) while a repo-local governance exception has expired. Fails open (silent) when `scripts/distill_harness.py` is absent, which is the case in consumer repos, so it enforces in the PCO repo only. It fails closed on any validator failure (malformed registry, missing expiry, `uv` unavailable), denying every shell command until the registry validates.
- `check_capability_decision.sh`: denies commit / PR-creation commands (`capability_decision_required` / `capability_decision_invalid`) for parser-/extractor-shaped content-interpretation changes unless a valid capability-decision record is staged. Detection is a path/keyword heuristic over staged files.
- `check_execution_limits.sh`: counts Bash calls per session in `.claude/tool_calls/<session_id>` (falls back to `.claude/tool_call_count` when the payload has no `session_id`) and denies (`execution_limit_hit`) once the count reaches `max_tool_calls`, writing `.claude/execution_limit_hit`. Every session starts at 0. Fails open (silent) if the limits file cannot be read.
- `gate_git_push.sh`: retired 2026-10-11 by operator decision; a silent no-op. Pushes to the operator's own repositories are pre-approved and review is enforced by the user-level commit gate. The file stays because consumer `settings.json` files still reference it.
- `init_run_id.sh`: Seeds a stable `run_id` at session start.
- `remind_evidence_package.sh`: Stop-hook reminder to close the run with evidence.

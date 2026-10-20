#!/usr/bin/env bash
# check_execution_limits.sh — PreToolUse hook: count Bash tool calls per session and deny at the limit.
# Governance: operations rule — every workflow must be bounded by explicit limits.
# Counter is keyed by the hook payload's session_id: $REPO_ROOT/.claude/tool_calls/<session_id>,
# so every session starts at 0. Without a session_id it falls back to $REPO_ROOT/.claude/tool_call_count.
# Under the limit: increments the counter and exits 0 with no output (normal permission flow applies).
# At the limit: writes the hit file and emits a PreToolUse "deny" in hookSpecificOutput.
# Fails closed: without jq or ruby, or without a readable positive max_tool_calls, it blocks the call (exit 2;
# Claude Code shows the one-line reason), because a session it cannot count is unbounded.
# Env overrides for testing: TOOL_CALL_COUNT_FILE, EXECUTION_LIMITS_FILE, EXECUTION_LIMIT_HIT_FILE
set -euo pipefail

fail_closed() {
    printf 'GOVERNANCE STOP: check_execution_limits.sh cannot enforce max_tool_calls: %s\n' "$1" >&2
    exit 2
}
for tool in jq ruby; do
    command -v "$tool" >/dev/null 2>&1 \
        || fail_closed "$tool not found on PATH (install it; cloud sessions: setup_cloud_session.sh)"
done

payload="$(cat)"
session_id="$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null || true)"
session_id="$(printf '%s' "$session_id" | tr -cd 'A-Za-z0-9_-')"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if [[ -n "$session_id" ]]; then
    DEFAULT_COUNT_FILE="$REPO_ROOT/.claude/tool_calls/$session_id"
else
    DEFAULT_COUNT_FILE="$REPO_ROOT/.claude/tool_call_count"
fi
COUNT_FILE="${TOOL_CALL_COUNT_FILE:-$DEFAULT_COUNT_FILE}"
LIMITS_FILE="${EXECUTION_LIMITS_FILE:-$REPO_ROOT/ai_context/pco/governance/execution_limits.yaml}"
HIT_FILE="${EXECUTION_LIMIT_HIT_FILE:-$REPO_ROOT/.claude/execution_limit_hit}"

# Read max_tool_calls from config via ruby (matches distill_harness.py's YAML loader).
MAX_TOOL_CALLS="$(ruby -ryaml -e "
data = YAML.load_file(ARGV[0])
v = data.dig('limits', 'max_tool_calls', 'value')
abort 'not a positive int' unless v.is_a?(Integer) && v > 0
puts v
" "$LIMITS_FILE" 2>/dev/null)" \
    || fail_closed "no positive limits.max_tool_calls.value in $LIMITS_FILE (fix it with the file-edit tool)"

# Read current count (0 if file absent or contains non-integer)
COUNT=0
if [[ -f "$COUNT_FILE" ]]; then
    raw="$(tr -d '[:space:]' < "$COUNT_FILE")"
    [[ "$raw" =~ ^[0-9]+$ ]] && COUNT="$raw"
fi

if [[ "$COUNT" -ge "$MAX_TOOL_CALLS" ]]; then
    printf 'limit: max_tool_calls\nvalue_at_stop: %d\nmax_allowed: %d\n' "$COUNT" "$MAX_TOOL_CALLS" > "$HIT_FILE"
    reason="$(printf 'GOVERNANCE STOP\nrisk_tier: high\ndenial_reason: execution_limit_hit\nlimit: max_tool_calls\nvalue_at_stop: %d\nmax_allowed: %d\nnext_action: shell commands are denied for the rest of this session; start a new session (its count starts at 0) and continue from the anchor doc' \
        "$COUNT" "$MAX_TOOL_CALLS")"
    jq -nc --arg reason "$reason" \
        '{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": $reason}}'
else
    mkdir -p "$(dirname "$COUNT_FILE")"
    printf '%d\n' "$(( COUNT + 1 ))" > "$COUNT_FILE"
fi
exit 0

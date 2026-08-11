#!/usr/bin/env bash
# check_execution_limits.sh — PreToolUse hook: count Bash tool calls and block on limit.
# Governance: operations rule — every workflow must be bounded by explicit limits.
# Counter increments on each allowed call; limit comes from execution_limits.yaml.
# Env overrides for testing: TOOL_CALL_COUNT_FILE, EXECUTION_LIMITS_FILE, EXECUTION_LIMIT_HIT_FILE
set -euo pipefail

cat > /dev/null  # consume stdin (hook contract; payload not needed)

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
COUNT_FILE="${TOOL_CALL_COUNT_FILE:-$REPO_ROOT/.claude/tool_call_count}"
LIMITS_FILE="${EXECUTION_LIMITS_FILE:-$REPO_ROOT/ai_context/pco/governance/execution_limits.yaml}"
HIT_FILE="${EXECUTION_LIMIT_HIT_FILE:-$REPO_ROOT/.claude/execution_limit_hit}"

# Read max_tool_calls from config via ruby (matches distill_harness.py's YAML loader).
# On any config error: fail-open (allow) to avoid blocking on a misconfigured limits file.
MAX_TOOL_CALLS="$(ruby -ryaml -e "
data = YAML.load_file(ARGV[0])
v = data.dig('limits', 'max_tool_calls', 'value')
abort 'not a positive int' unless v.is_a?(Integer) && v > 0
puts v
" "$LIMITS_FILE" 2>/dev/null)" || {
    jq -nc '{"permissionDecision": "allow"}'
    exit 0
}

# Read current count (0 if file absent or contains non-integer)
COUNT=0
if [[ -f "$COUNT_FILE" ]]; then
    raw="$(tr -d '[:space:]' < "$COUNT_FILE")"
    [[ "$raw" =~ ^[0-9]+$ ]] && COUNT="$raw"
fi

if [[ "$COUNT" -ge "$MAX_TOOL_CALLS" ]]; then
    printf 'limit: max_tool_calls\nvalue_at_stop: %d\nmax_allowed: %d\n' "$COUNT" "$MAX_TOOL_CALLS" > "$HIT_FILE"
    reason="$(printf 'GOVERNANCE STOP\nrisk_tier: high\ndenial_reason: execution_limit_hit\nlimit: max_tool_calls\nvalue_at_stop: %d\nmax_allowed: %d\nnext_action: write a partial evidence record (stop_condition.type: limit_hit), then invoke /evidence-package to close the run' \
        "$COUNT" "$MAX_TOOL_CALLS")"
    jq -nc --arg reason "$reason" '{"permissionDecision": "defer", "reason": $reason}'
else
    printf '%d\n' "$(( COUNT + 1 ))" > "$COUNT_FILE"
    jq -nc '{"permissionDecision": "allow"}'
fi

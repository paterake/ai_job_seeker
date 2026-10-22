#!/usr/bin/env bash
# check_execution_limits.sh — gate for one shell call; agent-neutral. Counts shell calls per session and denies at
# the limit. Governance: operations rule — every workflow must be bounded by explicit limits.
# Usage: check_execution_limits.sh --state-dir <dir> [--session <id>]
#   The agent's adapter names a state directory it owns. The counter is <dir>/tool_calls/<id>, so every session
#   starts at 0; with no session id it is the single <dir>/tool_call_count.
# Under the limit: increments the counter, exit 0, no output.
# At the limit: writes <dir>/execution_limit_hit, exit 2, structured reason on stderr.
# Fails closed (exit 2, one-line GOVERNANCE STOP): no --state-dir, no ruby, or no readable positive
# max_tool_calls, because a session it cannot count is unbounded.
set -euo pipefail

fail_closed() {
    printf 'GOVERNANCE STOP: check_execution_limits.sh cannot enforce max_tool_calls: %s\n' "$1" >&2
    exit 2
}

state_dir=""
session_id=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --state-dir | --session)
            [[ $# -ge 2 ]] || fail_closed "$1 needs a value"
            [[ "$1" == --state-dir ]] && state_dir="$2" || session_id="$2"
            shift 2
            ;;
        *) fail_closed "unknown argument: $1" ;;
    esac
done
[[ -n "$state_dir" ]] || fail_closed "no --state-dir (wire the agent adapter)"
command -v ruby >/dev/null 2>&1 || fail_closed "ruby not found on PATH (install it)"
session_id="$(printf '%s' "$session_id" | tr -cd 'A-Za-z0-9_-')"

# The repo root is four levels above this script: <repo>/ai_context/pco/ai_harness/hooks/.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
if [[ -n "$session_id" ]]; then
    COUNT_FILE="$state_dir/tool_calls/$session_id"
else
    COUNT_FILE="$state_dir/tool_call_count"
fi
LIMITS_FILE="$REPO_ROOT/ai_context/pco/governance/execution_limits.yaml"
HIT_FILE="$state_dir/execution_limit_hit"

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
    mkdir -p "$(dirname "$HIT_FILE")"
    printf 'limit: max_tool_calls\nvalue_at_stop: %d\nmax_allowed: %d\n' "$COUNT" "$MAX_TOOL_CALLS" > "$HIT_FILE"
    printf 'GOVERNANCE STOP\nrisk_tier: high\ndenial_reason: execution_limit_hit\nlimit: max_tool_calls\nvalue_at_stop: %d\nmax_allowed: %d\nnext_action: shell commands are denied for the rest of this session; start a new session (its count starts at 0) and continue from the anchor doc\n' \
        "$COUNT" "$MAX_TOOL_CALLS" >&2
    exit 2
fi
mkdir -p "$(dirname "$COUNT_FILE")"
printf '%d\n' "$(( COUNT + 1 ))" > "$COUNT_FILE"
exit 0

#!/usr/bin/env bash
set -euo pipefail

payload="$(cat)"
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')"

case "$cmd" in
  *"git push"*"origin main"*|*"git push"*" main"*)
    reason="$(cat <<'DENY'
GOVERNANCE DENY
risk_tier: high
denial_reason: approval_required
policy_set: pco-core/v1
approval_record: missing
next_action: request approval from governance board, or scope down to a non-main branch push
DENY
)"
    jq -nc --arg reason "$reason" '{"permissionDecision": "defer", "reason": $reason}'
    ;;
  *)
    jq -nc '{"permissionDecision": "allow"}'
    ;;
esac

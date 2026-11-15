#!/usr/bin/env bash
# PostToolUse and PostToolUseFailure (async): append one tool_call event in a shape compatible with ai_agent_core's tool_call.
# Stores sizes (code points) and sha256 hashes of tool_input / tool_response only, never their text.
# On failure the payload's .error is free tool text: it is hashed and counted, never copied;
# error and error_type are the fixed codes 'interrupted' or 'tool_error'.
# No set -e, no trap; always exits 0 and prints nothing. No session_id: nothing is emitted.
# PCO_TELEMETRY=0 turns it off; PCO_TELEMETRY_DIR is the base (default ~/Documents/__ai).
[ "${PCO_TELEMETRY:-1}" = "0" ] && exit 0
payload="$(cat)" || exit 0
sid="$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null)" || exit 0
[ -n "$sid" ] || exit 0
case "$sid" in */*|.*) exit 0 ;; esac
base="${PCO_TELEMETRY_DIR:-$HOME/Documents/__ai}"
mkdir -p "$base" 2>/dev/null || exit 0
if env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_COMMON_DIR git -C "$base" rev-parse --is-inside-work-tree >/dev/null 2>&1; then exit 0; fi
dir="$base/ai_ops/agent_harness/$sid/telemetry"
mkdir -p "$dir" 2>/dev/null || exit 0
f="$dir/events.jsonl"

failed="$(printf '%s' "$payload" | jq -r 'if (.hook_event_name // "") == "PostToolUseFailure" then "1" else "" end' 2>/dev/null)"
inp="$(printf '%s' "$payload" | jq -c '.tool_input' 2>/dev/null)" || exit 0
if [ -n "$failed" ]; then
  out="$(printf '%s' "$payload" | jq -j '.error // "" | tostring' 2>/dev/null)" || exit 0
else
  out="$(printf '%s' "$payload" | jq -c '.tool_response' 2>/dev/null)" || exit 0
fi
ih="$(printf '%s' "$inp" | shasum -a 256 | cut -d' ' -f1)"
oh="$(printf '%s' "$out" | shasum -a 256 | cut -d' ' -f1)"
ic="$(printf '%s' "$inp" | jq -Rs 'length' 2>/dev/null)" || exit 0
oc="$(printf '%s' "$out" | jq -Rs 'length' 2>/dev/null)" || exit 0
idre='^[A-Za-z0-9._-]{1,64}$'
trace="${PCO_TRACE_ID:-$sid}"; parent="${PCO_PARENT_SESSION:-}"
[[ "$trace" =~ $idre ]] || trace=""
[[ "$parent" =~ $idre ]] || parent=""
ts="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"
line="$(printf '%s' "$payload" | jq -c --arg ts "$ts" --arg sid "$sid" --arg ih "$ih" --arg oh "$oh" \
  --argjson ic "$ic" --argjson oc "$oc" --arg failed "$failed" \
  --arg trace "$trace" --arg parent "$parent" --arg idre "$idre" \
  '(if $failed != "" then (if .is_interrupt == true then "interrupted" else "tool_error" end) else null end) as $e
   | {schema_version: 1, event: "tool_call", timestamp: $ts, module: "agent_harness", run_id: $sid,
      tool: (.tool_name // "unknown"), input_chars: $ic, input_hash: $ih, output_chars: $oc, output_hash: $oh,
      latency_ms: ((.duration_ms // 0) | floor), error: $e, error_type: $e, degrade_mode: null,
      hook_event: (.hook_event_name // ""), tool_use_id: (.tool_use_id // ""), latency_measured: has("duration_ms"),
      trace_id: $trace, parent_session_id: $parent,
      agent_id: ((.agent_id // "") | if type == "string" and test($idre) then . else "" end), message_hash: ""}' 2>/dev/null)" \
  && [ -n "$line" ] && printf '%s\n' "$line" >> "$f" 2>/dev/null
exit 0

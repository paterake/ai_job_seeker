#!/usr/bin/env bash
# tel_emit.sh — the PCO's tool-call telemetry emitter. distill_harness.py wire installs it into a wired agent's
# <config_dir>/hooks/, and that agent's post-tool-use hook runs it for each finished tool call. It reads one hook
# payload on stdin and appends one `tool_call` record to the run's telemetry file, in the same shape and location
# ai_agent_harness/claude/agent-harness/scripts/tel_emit.sh writes, so records from any wired agent share one file
# and one schema (ai_agent_core's tool_call shape). It names no agent: the fields it reads (tool_name, tool_input,
# tool_response, session_id) are the Claude-compatible payload both agents send.
# Only hashes and sizes are stored, never tool text. It never fails and never prints: a hook that prints is read as
# an agent decision, and a telemetry fault must not change the agent's flow. No set -e, no trap: every path ends 0.
# PCO_TELEMETRY=0 turns it off; PCO_TELEMETRY_DIR is the base (default ~/Documents/__ai).
[ "${PCO_TELEMETRY:-1}" = "0" ] && exit 0
payload="$(cat)"
base="${PCO_TELEMETRY_DIR:-$HOME/Documents/__ai}"
mkdir -p "$base" 2>/dev/null || exit 0
# The base must be outside any git work tree: never write telemetry inside a checkout.
if env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_COMMON_DIR git -C "$base" rev-parse --is-inside-work-tree >/dev/null 2>&1; then exit 0; fi
command -v jq >/dev/null 2>&1 || exit 0
printf '%s' "$payload" | jq -e 'type == "object"' >/dev/null 2>&1 || exit 0

tool="$(printf '%s' "$payload" | jq -r '.tool_name // empty' 2>/dev/null)"
sid="$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null)"
inp="$(printf '%s' "$payload" | jq -c '.tool_input // {}' 2>/dev/null)"
[ -n "$inp" ] || inp='{}'
out="$(printf '%s' "$payload" | jq -c 'select(.tool_response != null) | .tool_response' 2>/dev/null)"

if [ -z "$sid" ]; then run_id="git-hook-$(date -u +%Y%m%d)"; src="git_hook"; else run_id="$sid"; src="plugin_hook"; fi
case "$run_id" in */*|.*) exit 0 ;; esac
idre='^[A-Za-z0-9._-]{1,64}$'
trace="${PCO_TRACE_ID:-$run_id}"; parent="${PCO_PARENT_SESSION:-}"
[[ "$trace" =~ $idre ]] || trace=""
[[ "$parent" =~ $idre ]] || parent=""
dir="$base/ai_ops/agent_harness/$run_id/telemetry"
mkdir -p "$dir" 2>/dev/null || exit 0
f="$dir/events.jsonl"
ih="$(printf '%s' "$inp" | shasum -a 256 | cut -d' ' -f1)"
ochars=0; oh="$(printf '' | shasum -a 256 | cut -d' ' -f1)"
if [ -n "$out" ]; then ochars="${#out}"; oh="$(printf '%s' "$out" | shasum -a 256 | cut -d' ' -f1)"; fi
ts="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"
line="$(jq -cn --arg ts "$ts" --arg run "$run_id" --arg tool "$tool" --arg inp "$inp" --arg ih "$ih" --arg oh "$oh" \
  --argjson oc "$ochars" --arg src "$src" --arg trace "$trace" --arg parent "$parent" \
  '{schema_version: 1, event: "tool_call", timestamp: $ts, module: "agent_harness", run_id: $run, tool: $tool,
    input_chars: ($inp | length), input_hash: $ih, output_chars: $oc, output_hash: $oh, latency_ms: 0,
    error: null, error_type: null, degrade_mode: null,
    decision: "", tree: "", reason_code: "", source: $src,
    trace_id: $trace, parent_session_id: $parent, agent_id: "", message_hash: "", matched_token: ""}')" && printf '%s\n' "$line" >> "$f" 2>/dev/null
exit 0

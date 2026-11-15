#!/usr/bin/env bash
# Append one gate event to the session telemetry file, in a tool_call shape compatible with ai_agent_core's.
#   tel_emit.sh <tool> <decision> <tree> <reason_code> <session_id> [agent_id] [message_hash] [matched_token]   (empty strings allowed)
# matched_token is stored only if it is one of: cd pushd dash_C git_dir work_tree git_env multiple; else empty.
# Trace keys on every event: trace_id (PCO_TRACE_ID, default run_id), parent_session_id (PCO_PARENT_SESSION),
# agent_id, message_hash; each is stored empty unless it matches its fixed pattern.
# Run as a separate process, never sourced. It never fails and never prints: the git pre-commit
# wrapper treats any hook stdout as a refusal, and a telemetry fault must not change a gate result.
# PCO_TELEMETRY=0 turns it off; PCO_TELEMETRY_DIR is the base (default ~/Documents/__ai).
# Only hashes and sizes are stored, never text. No set -e, no trap: every path ends in exit 0.
[ "${PCO_TELEMETRY:-1}" = "0" ] && exit 0
tool="${1:-}"; decision="${2:-}"; tree="${3:-}"; code="${4:-}"; sid="${5:-}"
agent="${6:-}"; mh="${7:-}"; mt="${8:-}"
case "$mt" in cd|pushd|dash_C|git_dir|work_tree|git_env|multiple) ;; *) mt="" ;; esac
base="${PCO_TELEMETRY_DIR:-$HOME/Documents/__ai}"
mkdir -p "$base" 2>/dev/null || exit 0
# The base must be outside any git work tree.
if env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_COMMON_DIR git -C "$base" rev-parse --is-inside-work-tree >/dev/null 2>&1; then exit 0; fi
if [ -z "$sid" ]; then run_id="git-hook-$(date -u +%Y%m%d)"; source="git_hook"; else run_id="$sid"; source="plugin_hook"; fi
case "$run_id" in */*|.*) exit 0 ;; esac
idre='^[A-Za-z0-9._-]{1,64}$'
trace="${PCO_TRACE_ID:-$run_id}"; parent="${PCO_PARENT_SESSION:-}"
[[ "$trace" =~ $idre ]] || trace=""
[[ "$parent" =~ $idre ]] || parent=""
[[ "$agent" =~ $idre ]] || agent=""
[[ "$mh" =~ ^[0-9a-f]{64}$ ]] || mh=""
dir="$base/ai_ops/agent_harness/$run_id/telemetry"
mkdir -p "$dir" 2>/dev/null || exit 0
f="$dir/events.jsonl"
inp="$(jq -cn --arg t "$tool" --arg d "$decision" --arg r "$tree" --arg c "$code" '{tool: $t, decision: $d, tree: $r, reason_code: $c}')" || exit 0
[ -n "$inp" ] || exit 0
ih="$(printf '%s' "$inp" | shasum -a 256 | cut -d' ' -f1)"
oh="$(printf '' | shasum -a 256 | cut -d' ' -f1)"
ts="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"
line="$(jq -cn --arg ts "$ts" --arg run "$run_id" --arg tool "$tool" --arg inp "$inp" --arg ih "$ih" --arg oh "$oh" \
  --arg d "$decision" --arg tree "$tree" --arg code "$code" --arg src "$source" \
  --arg trace "$trace" --arg parent "$parent" --arg agent "$agent" --arg mh "$mh" --arg mt "$mt" \
  '{schema_version: 1, event: "tool_call", timestamp: $ts, module: "agent_harness", run_id: $run, tool: $tool,
    input_chars: ($inp | length), input_hash: $ih, output_chars: 0, output_hash: $oh, latency_ms: 0,
    error: null, error_type: null, degrade_mode: null,
    decision: $d, tree: $tree, reason_code: $code, source: $src,
    trace_id: $trace, parent_session_id: $parent, agent_id: $agent, message_hash: $mh, matched_token: $mt}')" && printf '%s\n' "$line" >> "$f" 2>/dev/null
exit 0

#!/usr/bin/env bash
# Sourced by the PreToolUse gates (gate_commit.sh, check_work_ids.sh, gate_dispatch.sh); not run on its own.
# Needs GATE_TOOL set by the caller (the tool name in telemetry) and may read the caller's $sid and $tree.
# A fault here affects every gate, so each caller refuses (exit 2) when it cannot source this file.
# Reason codes added for the director gate (director_lock.sh): director_held, director_unknown, generation_cap.
# tel: telemetry is a separate process with all output discarded: hook stdout must stay exactly the deny JSON.
tel() {   # $1 = decision, $2 = fixed reason code, $3 = optional fixed matched token
  "$(dirname "$0")/tel_emit.sh" "${GATE_TOOL:-gate}" "$1" "${tree:-}" "$2" "${sid:-}" "" "" "${3:-}" </dev/null >/dev/null 2>&1 || true
}
deny() {   # $1 = reason text (never stored), $2 = fixed reason code, $3 = optional fixed matched token
  tel deny "${2:-script_error}" "${3:-}"
  jq -nc --arg r "$1" '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $r}}' \
    || { printf '%s\n' "$1" >&2; exit 2; }   # jq broken: exit 2 still blocks
  exit 0
}

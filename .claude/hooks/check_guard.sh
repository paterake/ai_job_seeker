#!/usr/bin/env bash
# gate_adapter.sh — adapter between the wired agent's pre-tool-use hook and the agent-neutral PCO gates in
# ai_context/pco/ai_harness/hooks/. It is the only code that speaks the agent's hook protocol; which agent is wired
# is set in config/agent_wiring.json. distill_harness.py wire installs this file into <agent config folder>/hooks/
# once per gate, under the gate's own name (check_guard.sh, check_execution_limits.sh); the installed name picks
# the gate. Do not edit the installed copies.
# Reads the hook payload on stdin and passes the call's command, file path and session id to the gate.
# Gate exit 0: exit 0, no output, so the agent's normal permission flow applies (never "allow").
# Gate exit 2: a pre-tool-use "deny" decision whose reason is the gate's stderr.
# Fails closed (exit 2, one-line reason): no jq, a payload that is not a JSON object, a guard payload with neither
# a command nor a file path, the gate is missing, or the gate exits with any other code.
set -uo pipefail

gate="$(basename "$0")"
fail_closed() {
    printf 'GOVERNANCE STOP: %s adapter: %s\n' "$gate" "$1" >&2
    exit 2
}

# Installed at <repo>/<agent config folder>/hooks/<gate>; the config folder also holds the gate's state.
state_dir="$(cd "$(dirname "$0")/.." && pwd)"
root="$(dirname "$state_dir")"
gate_path="$root/ai_context/pco/ai_harness/hooks/$gate"
command -v jq >/dev/null 2>&1 || fail_closed "jq not found on PATH (install it)"
[[ -f "$gate_path" ]] || fail_closed "gate not found: $gate_path (re-sync the PCO)"

payload="$(cat)"
printf '%s' "$payload" | jq -e 'type == "object"' >/dev/null 2>&1 \
    || fail_closed "cannot read the hook payload (not a JSON object)"
field() { printf '%s' "$payload" | jq -r "($1) // empty"; }
case "$gate" in
    check_guard.sh)
        cmd="$(field .tool_input.command)"
        path="$(field '.tool_input.file_path // .tool_input.notebook_path')"
        # Every tool this gate is wired to carries a command or a file path; neither means the call was not read.
        [[ -n "$cmd" || -n "$path" ]] || fail_closed "the hook payload has no command or file path"
        args=(--command "$cmd" --path "$path")
        ;;
    check_execution_limits.sh)
        args=(--state-dir "$state_dir" --session "$(field .session_id)")
        ;;
    *) fail_closed "no PCO gate is named $gate" ;;
esac

reason="$(bash "$gate_path" "${args[@]}" 2>&1 >/dev/null </dev/null)"
rc=$?
case "$rc" in
    0) exit 0 ;;
    2) jq -nc --arg r "$reason" \
        '{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": $r}}' ;;
    *) fail_closed "$gate exited $rc: $reason" ;;
esac
exit 0

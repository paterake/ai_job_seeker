#!/usr/bin/env bash
# check_guard.sh — PreToolUse hook (Bash, Edit, Write, MultiEdit, NotebookEdit). Refuses:
#   - a file edit under ai_context/pco/ in any repo other than the PCO: that tree is PCO-owned, and sync
#     overwrites a local edit, so the fix never reaches the other repos;
#   - git push --force (or -f / --force-with-lease): it rewrites shared history.
# The PCO is recognised by its consumer manifest (ai_context/project/governance/consumers.yaml).
# Pass: exit 0 with no output. Block: PreToolUse "deny" in hookSpecificOutput. No jq: exit 2 (fails closed).
set -uo pipefail

payload="$(cat)"
if ! command -v jq >/dev/null 2>&1; then
    printf 'GOVERNANCE STOP: check_guard.sh cannot check this call: jq not found on PATH (install it)\n' >&2
    exit 2
fi

deny() {
    jq -nc --arg r "$1" \
        '{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": $r}}'
    exit 0
}

cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')"
if [[ -n "$cmd" ]] \
    && printf '%s' "$cmd" | grep -Eq '(^|[;&|[:space:]])git([[:space:]]+-[cC][[:space:]]+[^[:space:]]+)*[[:space:]]+push([[:space:]].*)?[[:space:]](--force(-with-lease)?(=[^[:space:]]*)?|-[a-zA-Z]*f[a-zA-Z]*)([[:space:]]|$)'; then
    deny "GOVERNANCE DENY
denial_reason: force_push_refused
next_action: push without --force; if history really must be rewritten, the operator does it"
fi

path="$(printf '%s' "$payload" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')"
if [[ "$path" == */ai_context/pco/* || "$path" == ai_context/pco/* ]]; then
    root="${path%%ai_context/pco/*}"
    [[ -z "$root" ]] && root="./"
    if [[ ! -f "${root}ai_context/project/governance/consumers.yaml" ]]; then
        deny "GOVERNANCE DENY
denial_reason: synced_pco_edit_refused
next_action: ai_context/pco/ is PCO-owned and sync overwrites local edits; make the change in the PCO repo (ai_agent_pco) and re-sync, or put repo-specific content in ai_context/project/"
    fi
fi
exit 0

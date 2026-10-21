#!/usr/bin/env bash
# check_guard.sh — gate for one tool call; agent-neutral. The agent's adapter passes the call's shell command and
# file path as arguments (either may be empty). Refuses:
#   - a file edit under ai_context/pco/ (after resolving symlinks) in any repo other than the PCO: that tree is PCO-owned, and sync
#     overwrites a local edit, so the fix never reaches the other repos;
#   - git push --force (or -f / --force-with-lease / a +refspec): it rewrites shared history.
# The PCO is recognised by its consumer manifest (ai_context/project/governance/consumers.yaml).
# Usage: check_guard.sh --command <shell command> --path <file path>
# Pass: exit 0, no output. Deny: exit 2, structured reason on stderr. Called with neither flag: exit 2 (fails
# closed), because a gate that is given nothing checks nothing.
set -uo pipefail

stop() {
    printf 'GOVERNANCE STOP: check_guard.sh %s\n' "$1" >&2
    exit 2
}
deny() {
    printf '%s\n' "$1" >&2
    exit 2
}

cmd=""
path=""
given=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --command | --path)
            [[ $# -ge 2 ]] || stop "$1 needs a value"
            [[ "$1" == --command ]] && cmd="$2" || path="$2"
            given=1
            shift 2
            ;;
        *) stop "unknown argument: $1" ;;
    esac
done
[[ $given -eq 1 ]] || stop "was given no --command or --path (wire the agent adapter)"

if [[ -n "$cmd" ]] \
    && printf '%s' "$cmd" | grep -Eq '(^|[;&|([:space:]`])git([[:space:]]+(-[cC][[:space:]]+[^[:space:]]+|--[a-z][^[:space:]]*))*[[:space:]]+push([[:space:]][^;&|)`]*)?[[:space:]](--force(-with-lease)?(=[^[:space:];&|)`]*)?|-[a-zA-Z]*f[a-zA-Z]*|\+[^[:space:];&|)`]+)([[:space:];&|)`]|$)'; then
    deny "GOVERNANCE DENY
denial_reason: force_push_refused
next_action: push without --force; if history really must be rewritten, the operator does it"
fi

# The real path: the agent edits a synced rule or skill where it loaded it (a symlinked folder in its
# configuration), so the literal path need not contain ai_context/pco/.
real_path() {
    local p="$1" tail="" d n=0 t
    [[ "$p" == /* ]] || p="$PWD/$p"
    while [[ -L "$p" && $n -lt 40 ]]; do
        t="$(readlink "$p")"
        [[ "$t" == /* ]] && p="$t" || p="$(dirname "$p")/$t"
        n=$((n + 1))
    done
    d="$(dirname "$p")"
    while [[ ! -d "$d" ]]; do
        tail="$(basename "$d")/$tail"
        d="$(dirname "$d")"
    done
    d="$(cd -P "$d" && pwd -P)" || return 1
    printf '%s/%s%s' "${d%/}" "$tail" "$(basename "$p")"
}
if [[ -n "$path" ]]; then
    path="$(real_path "$path")" || stop "cannot resolve path: $path"
fi

if [[ "$path" == */ai_context/pco/* ]]; then
    root="${path%%ai_context/pco/*}"
    if [[ ! -f "${root}ai_context/project/governance/consumers.yaml" ]]; then
        deny "GOVERNANCE DENY
denial_reason: synced_pco_edit_refused
next_action: ai_context/pco/ is PCO-owned and sync overwrites local edits; make the change in the PCO repo (ai_agent_pco) and re-sync, or put repo-specific content in ai_context/project/"
    fi
fi
exit 0

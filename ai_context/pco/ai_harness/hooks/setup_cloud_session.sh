#!/usr/bin/env bash
# setup_cloud_session.sh — SessionStart hook: install the tools the gate hooks need in a Claude Code cloud session.
# Runs only when CLAUDE_CODE_REMOTE=true; local sessions exit 0 at once (there a missing tool makes the gates
# fail closed, and the operator installs it). The gates need jq (both), ruby (check_execution_limits.sh) and
# git (check_capability_decision.sh). Never blocks the session: on failure it prints one line naming the
# consequence to stdout, which Claude Code adds to the session context (stderr on exit 0 is not shown).
set -uo pipefail

[[ "${CLAUDE_CODE_REMOTE:-}" == "true" ]] || exit 0

missing=()
for tool in jq ruby git; do
    command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
done
[[ "${#missing[@]}" -eq 0 ]] && exit 0

sudo=""
[[ "$(id -u)" -ne 0 ]] && sudo="sudo"
if $sudo apt-get update -qq >/dev/null 2>&1 && $sudo apt-get install -y -qq "${missing[@]}" >/dev/null 2>&1; then
    echo "setup_cloud_session: installed ${missing[*]} for the governance gate hooks"
else
    echo "setup_cloud_session: could not install ${missing[*]}; without jq or ruby the governance gate hooks deny shell commands, and without git nothing can be committed, until they are on PATH"
fi
exit 0

#!/usr/bin/env bash
# setup_cloud_session.sh — SessionStart hook: make the governance gates runnable in this clone.
# Every session: point git at the PCO hooks dir (core.hooksPath, clone-local, so a fresh clone lacks it) unless
# the clone already sets one, so the pre-commit capability-decision gate runs; a local value overrides a global one. Cloud sessions (CLAUDE_CODE_REMOTE=true)
# also install the tools the gates need: jq and ruby (check_execution_limits.sh) and git (pre-commit). Locally
# a missing tool makes the gates fail closed, and the operator installs it. Never blocks the session: on
# failure it prints one line naming the consequence to stdout, which Claude Code adds to the session context
# (stderr on exit 0 is not shown).
set -uo pipefail

if [[ "${CLAUDE_CODE_REMOTE:-}" == "true" ]]; then
    missing=()
    for tool in jq ruby git; do
        command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
    done
    if [[ "${#missing[@]}" -gt 0 ]]; then
        sudo=""
        [[ "$(id -u)" -ne 0 ]] && sudo="sudo"
        if $sudo apt-get update -qq >/dev/null 2>&1 && $sudo apt-get install -y -qq "${missing[@]}" >/dev/null 2>&1; then
            echo "setup_cloud_session: installed ${missing[*]} for the governance gate hooks"
        else
            echo "setup_cloud_session: could not install ${missing[*]}; without jq or ruby the governance gate hooks deny shell commands, and without git nothing can be committed, until they are on PATH"
        fi
    fi
fi

if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1 \
    && ! git config --local core.hooksPath >/dev/null 2>&1; then
    git config --local core.hooksPath ai_context/pco/ai_harness/hooks \
        || echo "setup_cloud_session: could not set core.hooksPath; the pre-commit capability-decision gate does not run in this clone"
fi
exit 0

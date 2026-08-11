#!/usr/bin/env bash
# init_run_id.sh — generate a stable run_id for this session.
# Fires on UserPromptSubmit. Creates .claude/current_run_id on first call only.
# Governance: operations rule — run_id must be generated at session entry, never mid-run.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RUN_ID_FILE="$REPO_ROOT/.claude/current_run_id"

if [[ -f "$RUN_ID_FILE" ]]; then
    exit 0
fi

if command -v uuidgen &>/dev/null; then
    UUID="$(uuidgen | tr '[:upper:]' '[:lower:]')"
else
    UUID="$(python3 -c 'import uuid; print(uuid.uuid4())')"
fi

TS="$(date +%Y%m%d-%H%M%S)"
echo "run-${TS}-${UUID:0:8}" > "$RUN_ID_FILE"
exit 0

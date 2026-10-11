#!/usr/bin/env bash
# gate_git_push.sh — RETIRED 2026-10-11 by operator decision. Silent no-op.
# Pushes to the operator's own repositories are pre-approved, and review before commit is
# enforced by the user-level pco-harness commit gate, so this push gate no longer blocks anything.
# The file is kept because consumer settings.json files still reference it; a missing file would error.
set -euo pipefail

cat > /dev/null  # consume stdin (hook contract); no decision is emitted
exit 0

#!/usr/bin/env bash
# Runs one harness hook script, named by the first argument, only in a cloud session (CLAUDE_CODE_REMOTE=true,
# documented in the hooks doc). On a laptop the user-level agent-harness plugin runs the same scripts, so this
# exits 0 with no output there. The name must be a plain file name in this pack.
here="$(dirname "$0")"
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || { cat >/dev/null; exit 0; }
case "${1:-}" in ''|*/*|.*) printf 'cloud_only: bad script name\n' >&2; exit 2 ;; esac
s="$1"; shift
[ -x "$here/scripts/$s" ] && exec "$here/scripts/$s" "$@"
[ -x "$here/$s" ] && exec "$here/$s" "$@"
printf 'cloud_only: %s missing\n' "$s" >&2; exit 2

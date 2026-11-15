#!/usr/bin/env bash
# Preflight, read-only: report whether each path's repo is trusted for `claude --bg` workers.
# Usage: trust_check.sh <path>...   Prints "<repo> true|false|missing" per path, then for each
# untrusted one the operator step "(cd <repo> && claude), accept, exit". Exit 0 all trusted, 1 any
# not, 2 a path that is not in a git repo. Reads only hasTrustDialogAccepted from ~/.claude.json;
# never writes it. A worktree is checked as its main repo (--git-common-dir).
set -uo pipefail
[ "$#" -ge 1 ] || { echo "usage: trust_check.sh <path>..." >&2; exit 2; }
rc=0
for p in "$@"; do
  common="$(git -C "$p" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" \
    || { echo "trust_check: not a git path: $p" >&2; exit 2; }
  repo="$(dirname "$common")"
  st="$(python3 -I - "$repo" <<'PY'
import json, os, sys
try:
    d = json.load(open(os.path.expanduser('~/.claude.json'))).get('projects', {})
except Exception:
    d = {}
v = d.get(sys.argv[1], {}).get('hasTrustDialogAccepted')
print('true' if v is True else 'false' if v is False else 'missing')
PY
)"
  echo "$repo $st"
  if [ "$st" != true ]; then printf '(cd %q && claude), accept, exit\n' "$repo"; rc=1; fi
done
exit "$rc"

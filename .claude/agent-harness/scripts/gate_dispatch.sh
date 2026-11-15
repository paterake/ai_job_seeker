#!/usr/bin/env bash
# PreToolUse: a dispatch must carry a Retained-code check line in its brief. A dispatch is a Bash `claude ... --bg`
# command (brief: its last positional argument) or a cloud `mcp__claude-code-remote__create_session` call (brief:
# tool_input.prompt; an empty prompt is denied). Proves a record exists in the brief at dispatch, not that
# decision-check ran or was right. Anything else exits 0 silently, with no telemetry.
set -uo pipefail

payload="$(cat)" || { printf 'gate: cannot read the hook payload, refused (fail closed)\n' >&2; exit 2; }
tool="$(printf '%s' "$payload" | jq -r '.tool_name // empty')" \
  || { printf 'gate: jq failed, refused (fail closed)\n' >&2; exit 2; }
if [ "$tool" = mcp__claude-code-remote__create_session ]; then
  via=session; cmd=""   # the loop guard reads $cmd
else
  via=bg
  cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')" \
    || { printf 'gate: jq failed, refused (fail closed)\n' >&2; exit 2; }
  grep -Eq '(^|[;&|(`[:space:]])claude[[:space:]]([^;&|]*[[:space:]])?--bg([[:space:]]|$)' <<<"${cmd//$'\n'/ }" || exit 0   # newlines folded: grep matches per line
fi

sid=""; tree=""
GATE_TOOL=gate_dispatch
. "$(dirname "$0")/gate_deny.sh" || { printf 'gate: gate_deny.sh missing, refused (fail closed)\n' >&2; exit 2; }
trap 'deny "DISPATCH GATE: gate script error, dispatch refused (fail closed)." script_error' ERR
sid="$(printf '%s' "$payload" | jq -r '.session_id // empty')"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty')"
. "$(dirname "$0")/director_lock.sh" 2>/dev/null || true   # missing or unreadable: the director checks stay undefined and are skipped

forms='Retained-code check: not a metric-driven backlog   OR   Retained-code check: decision-check CONSISTENT, excluded: <the excluded groups, or none>'
if [ "$via" = session ]; then
  how="Add one line to the create_session prompt, in one of these forms: $forms."
  brief="$(printf '%s' "$payload" | jq -r '.tool_input.prompt // empty')"
else
how="Add one line to the brief, in one of these forms: $forms. Send the brief inline in single quotes (write each ' as '\\'')."

brief="$(printf '%s' "$cmd" | perl "$(dirname "$0")/dispatch_brief.pl")" \
  || deny "DISPATCH GATE: cannot read the brief of this claude --bg command (${brief:-no detail}). Use one claude --bg command with an inline brief in single quotes: no heredoc, \$(...), backticks outside single quotes, or @file. $how" brief_unreadable
fi

re='^[[:space:]]*Retained-code check:[[:space:]]*(not a metric-driven backlog|decision-check CONSISTENT, excluded: (.+))[[:space:]]*$'
found=0
while IFS= read -r line || [ -n "$line" ]; do
  [[ $line =~ $re ]] || continue
  v="${BASH_REMATCH[2]}"
  if [ -z "${BASH_REMATCH[2]}" ]; then found=1; break; fi   # the "not a metric-driven backlog" form
  v="${v%"${v##*[![:space:]]}"}"
  [ -n "$v" ] && [[ $v != *'<'* && $v != *'>'* ]] && { found=1; break; }
done <<<"$brief" || true

if [ "$found" = 1 ]; then
  # One active director and the successor loop guard (director_lock.sh). Each runs in a command substitution with the
  # ERR trap suspended: only return code 10 refuses; any other outcome is a skip (fail open).
  trap - ERR; dmsg="$(director_check dispatch 2>/dev/null)"; drc=$?; trap 'deny "DISPATCH GATE: gate script error, dispatch refused (fail closed)." script_error' ERR; [ "$drc" -eq 10 ] && deny "$dmsg" director_held
  trap - ERR; dmsg="$(director_loopguard 2>/dev/null)"; drc=$?; trap 'deny "DISPATCH GATE: gate script error, dispatch refused (fail closed)." script_error' ERR; [ "$drc" -eq 10 ] && deny "$dmsg" generation_cap
  tel allowed check_found; exit 0
fi
deny "DISPATCH GATE: the brief has no valid Retained-code check: line (missing, empty excluded value, or a value left as a <placeholder>). $how" no_retained_check

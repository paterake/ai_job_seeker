#!/usr/bin/env bash
# PreToolUse (Bash, if `*pco-director-*`): write or move the director marker <git-common-dir>/pco-director. The
# only writer of that file. Acts only on the exact trimmed command `true pco-director-claim` or
# `true pco-director-release`. A command in which a piece (split on && ; || |) starts with either word but the whole
# is not exactly it is a near-miss and is denied, naming the command to run alone, because nothing was claimed.
# Every other command, including one that only names the word as data, exits 0 silently. The near-miss path fails
# open (gate_deny.sh or jq missing: exit 0); the exact path keeps its fail-closed exit 2.
set -uo pipefail
GATE_TOOL=director_marker; sid=""; tree=""
payload="$(cat)" || { printf 'director: cannot read the hook payload\n' >&2; exit 2; }
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')" || { case "$payload" in *'"true pco-director-claim"'*|*'"true pco-director-release"'*) exit 2 ;; *) exit 0 ;; esac; }
cmd="${cmd#"${cmd%%[![:space:]]*}"}"; cmd="${cmd%"${cmd##*[![:space:]]}"}"
case "$cmd" in
  "true pco-director-claim") act=claim ;;
  "true pco-director-release") act=release ;;
  *)
    case "$cmd" in *pco-director-*) ;; *) exit 0 ;; esac
    hit=""; nl=$'\n'; split="${cmd//&&/$nl}"; split="${split//||/$nl}"; split="${split//;/$nl}"; split="${split//|/$nl}"
    while IFS= read -r piece || [ -n "$piece" ]; do
      piece="${piece#"${piece%%[![:space:]]*}"}"
      while [[ $piece =~ ^[A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+(.*)$ ]]; do piece="${BASH_REMATCH[1]}"; done
      for w in claim release; do
        if [[ $piece == "true pco-director-$w" || $piece == "true pco-director-$w"[[:space:]]* ]]; then hit="true pco-director-$w"; fi
      done
    done <<<"$split"
    [ -n "$hit" ] || exit 0
    command -v jq >/dev/null 2>&1 || exit 0
    . "$(dirname "$0")/gate_deny.sh" 2>/dev/null || exit 0
    deny "DIRECTOR GATE: not run; this is not exactly the claim/release command, so nothing was claimed or released (matched: $hit). Run exactly \`true pco-director-claim\` (or \`true pco-director-release\`) on its own, with nothing before or after it." director_unknown "$hit"
    exit 0 ;;
esac
. "$(dirname "$0")/gate_deny.sh" || { printf 'director: gate_deny.sh missing, refused\n' >&2; exit 2; }
. "$(dirname "$0")/director_lock.sh" || { printf 'director: director_lock.sh missing, refused\n' >&2; exit 2; }
sid="$(printf '%s' "$payload" | jq -r '.session_id // empty')"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty')"
note() { jq -nc --arg r "$1" '{hookSpecificOutput: {hookEventName: "PreToolUse", additionalContext: $r}}'; exit 0; }
[ -n "$sid" ] || deny "DIRECTOR GATE: the hook payload has no session_id; cannot $act." director_unknown
_dl_gitinfo "${cwd:-$PWD}" || deny "DIRECTOR GATE: not a git repository at ${cwd:-$PWD}; cannot $act." not_a_repo
m="$DL_COMMON/pco-director"; rel="$DL_COMMON/pco-director.released"

if [ "$act" = release ]; then
  [ -f "$m" ] || note "No director marker to release."
  hs="$(jq -r '.session // empty' "$m" 2>/dev/null)"
  [ "$hs" = "$sid" ] || deny "DIRECTOR GATE: release refused: the marker is held by ${hs:-an unreadable holder}, not this session ($sid)." director_held
  mv -f "$m" "$rel" || deny "DIRECTOR GATE: cannot move the marker to pco-director.released." script_error
  note "Director marker released (kept as pco-director.released). Do not act until the successor has claimed."
fi

_dl_agents || deny "DIRECTOR GATE: claim refused: cannot read 'claude agents --json' to find this session's pid." director_unknown
row="$(jq -c --arg s "$sid" 'first(.[] | select(.sessionId == $s)) // empty' <<<"$DL_AGENTS")"
[ -n "$row" ] || deny "DIRECTOR GATE: claim refused: session $sid is not in 'claude agents --json', so its pid is unknown." director_unknown
pid="$(jq -r '.pid' <<<"$row")"; name="$(jq -r '.name // "unnamed"' <<<"$row")"
if [ -f "$m" ]; then
  hs="$(jq -r '.session // empty' "$m" 2>/dev/null)"
  if [ -n "$hs" ] && [ "$hs" != "$sid" ]; then
    _dl_state "$m"; st=$?
    if [ "$st" -ne 1 ]; then
      deny "DIRECTOR GATE: claim refused: session $(jq -r '.name // "unnamed"' "$m") ($hs) holds director authority for this repo (state: $([ "$st" -eq 0 ] && echo live || echo unknown)). If it is gone, the operator runs: rm $m" director_held
    fi
  fi
fi
def="$(_dl_default "${cwd:-$PWD}")" || def=""
main_sha=""
[ -n "$def" ] && main_sha="$(git -C "${cwd:-$PWD}" rev-parse -q --verify "refs/remotes/origin/$def" 2>/dev/null)"
tmp="$m.tmp.$$"
jq -nc --arg s "$sid" --arg n "$name" --argjson p "$pid" --argjson t "$(date +%s)" --arg ma "$main_sha" \
  '{session: $s, name: $n, pid: $p, claimedAt: $t, mainAtClaim: $ma}' > "$tmp" \
  && mv -f "$tmp" "$m" || { rm -f "$tmp"; deny "DIRECTOR GATE: cannot write the marker." script_error; }
rm -f "$rel"
note "Director marker claimed by $name ($sid)."

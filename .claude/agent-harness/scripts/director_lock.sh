#!/usr/bin/env bash
# Sourced by gate_commit.sh, gate_dispatch.sh and director_marker.sh; never run on its own.
# One active director per repo: the marker <git-common-dir>/pco-director names the holder session.
# director_check and director_loopguard NEVER call deny and NEVER call exit. Contract with the caller,
# which runs them in a command substitution: return 10 = a live different holder (or a refused launch)
# is established and the reason text is on stdout; any other outcome (0, an error, 127 for a missing
# function, an unbound variable, empty output) means "skip", so the existing gates decide unchanged.
# Reads the caller's $cmd (the command text), $cwd and $sid (the hook payload fields).

_dl_gitinfo() {   # $1 = directory; sets DL_GITDIR, DL_COMMON
  DL_GITDIR="$(git -C "$1" rev-parse --absolute-git-dir 2>/dev/null)" || return 1
  DL_COMMON="$(git -C "$1" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || return 1
  [ -n "$DL_GITDIR" ] && [ -n "$DL_COMMON" ]
}

_dl_default() {   # $1 = directory; prints the default branch name
  local d b
  d="$(git -C "$1" symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null)" && [ -n "$d" ] && { printf '%s\n' "${d#origin/}"; return 0; }
  for b in main master; do
    git -C "$1" show-ref -q --verify "refs/heads/$b" 2>/dev/null && { printf '%s\n' "$b"; return 0; }
  done
  return 1
}

_dl_agents() {   # fills DL_AGENTS with the claude agents JSON array; fails when it cannot
  command -v claude >/dev/null 2>&1 && command -v jq >/dev/null 2>&1 || return 1
  DL_AGENTS="$(claude agents --json 2>/dev/null)" || return 1
  jq -e 'type == "array"' <<<"$DL_AGENTS" >/dev/null 2>&1
}

# $1 = marker file. Returns 0 = holder is live, 1 = stale, 2 = cannot tell.
# STALE only if the holder session is absent from `claude agents --json`, or `kill -0 <pid>` fails,
# or claimedAt (epoch seconds) is older than PCO_DIRECTOR_MAX_AGE_HOURS (default 12, a recommendation).
# State "done" is not used: a waiting live successor can look the same.
_dl_state() {
  local m="$1" hs hp ca max now
  jq -e '(.session | type == "string") and (.pid | type == "number") and (.claimedAt | type == "number")' "$m" >/dev/null 2>&1 || return 2
  hs="$(jq -r '.session' "$m")"; hp="$(jq -r '.pid' "$m")"; ca="$(jq -r '.claimedAt' "$m")"
  _dl_agents || return 2
  jq -e --arg s "$hs" 'any(.[]; .sessionId == $s)' <<<"$DL_AGENTS" >/dev/null 2>&1 || return 1
  kill -0 "$hp" 2>/dev/null || return 1
  max="${PCO_DIRECTOR_MAX_AGE_HOURS:-12}"
  [[ $max =~ ^[0-9]+$ && $ca =~ ^[0-9]+$ ]] || return 2
  now="$(date +%s)"
  [ $((now - ca)) -gt $((max * 3600)) ] && return 1
  return 0
}

# Does the push command in $cmd push the default branch? $1 = default branch, $2 = current branch ("" if none).
_dl_push_hits_default() {
  local def="$1" cur="$2" rest t r pos=0 hit=1
  set -f
  rest="${cmd#*[[:space:]]push}"; rest="${rest%%[;&|]*}"
  for t in $rest; do
    case "$t" in
      --all|--mirror) hit=0 ;;
      -*) ;;
      *)
        pos=$((pos + 1))
        [ "$pos" -ge 2 ] || continue
        r="${t//[\'\"]/}"; r="${r#+}"
        [ "$r" = HEAD ] && [ "$cur" = "$def" ] && hit=0
        r="${r##*:}"; r="${r#refs/heads/}"
        [ "$r" = "$def" ] && hit=0
        ;;
    esac
  done
  [ "$pos" -le 1 ] && [ "$cur" = "$def" ] && hit=0   # bare push, or remote only, while on the default branch
  return "$hit"
}

director_check() {   # $1 = commit | push | dispatch
  local kind="${1:-}" dir="${cwd:-$PWD}" c def cur m hs hn st
  if [ "$kind" = push ]; then
    c="$(sed -nE 's/.*[[:space:]]([^[:space:]]*\/)?git[[:space:]]+-C[[:space:]]+([^[:space:]]+).*/\2/p' <<<" $cmd")"
    c="${c//[\'\"]/}"
    if [ -n "$c" ]; then case "$c" in /*) dir="$c" ;; *) dir="$dir/$c" ;; esac; fi
  fi
  _dl_gitinfo "$dir" || return 0
  m="$DL_COMMON/pco-director"
  [ -f "$m" ] || return 0
  if [ "$kind" != dispatch ]; then
    def="$(_dl_default "$dir")" || return 0
    cur="$(git -C "$dir" symbolic-ref -q --short HEAD 2>/dev/null)" || cur=""
    case "$kind" in
      commit) [ "$DL_GITDIR" = "$DL_COMMON" ] && [ "$cur" = "$def" ] || return 0 ;;
      push) _dl_push_hits_default "$def" "$cur" || return 0 ;;
      *) return 0 ;;
    esac
  fi
  hs="$(jq -r '.session // empty' "$m" 2>/dev/null)" || return 0
  [ -n "$hs" ] || return 0
  [ "${sid:-}" = "$hs" ] && return 0
  [ "${PCO_DIRECTOR_OVERRIDE:-}" = 1 ] && return 0
  _dl_state "$m"; st=$?
  if [ "$st" -eq 2 ]; then type tel >/dev/null 2>&1 && tel allowed director_unknown; return 0; fi
  [ "$st" -eq 1 ] && return 0
  hn="$(jq -r '.name // "unnamed"' "$m" 2>/dev/null)"
  printf 'DIRECTOR GATE: session %s (%s) holds director authority for this repo. This session forwards peer replies to it and answers questions only. Operator way through: start claude with PCO_DIRECTOR_OVERRIDE=1 in its environment, or run: rm %s\n' "$hn" "$hs" "$m"
  return 10
}

# Successor-launch loop guard for a background launch. A successor launch carries PCO_DIRECTOR_GEN in its
# --settings env (worker dispatches carry no PCO_DIRECTOR_GEN and are never touched). The hook env's
# PCO_DIRECTOR_GEN is the caller's own generation (absent = 0). Unverified residual: a successor launched
# without GEN, or a session that strips its own env, is not caught.
director_loopguard() {
  local launched n max dir="${cwd:-$PWD}" f s ma now
  grep -q 'PCO_DIRECTOR_GEN' <<<"$cmd" || return 0
  launched="$(grep -Eo 'PCO_DIRECTOR_GEN"?[[:space:]]*:[[:space:]]*"?[0-9]+' <<<"$cmd" | grep -Eo '[0-9]+$' | head -1)"
  n="${PCO_DIRECTOR_GEN:-0}"; [[ $n =~ ^[0-9]+$ ]] || n=0
  max="${PCO_DIRECTOR_MAX_GEN:-20}"; [[ $max =~ ^[0-9]+$ ]] || max=20
  if [ -z "$launched" ]; then
    printf 'DISPATCH GATE: PCO_DIRECTOR_GEN in this launch has no number. A successor launch sets it to your own generation plus one (yours is %s).\n' "$n"; return 10
  fi
  if [ "$launched" -ne $((n + 1)) ]; then
    printf 'DISPATCH GATE: successor launch sets PCO_DIRECTOR_GEN=%s; this session is generation %s, so it must set %s.\n' "$launched" "$n" $((n + 1)); return 10
  fi
  if [ "$launched" -gt "$max" ]; then
    printf 'DISPATCH GATE: generation cap reached: PCO_DIRECTOR_GEN=%s exceeds PCO_DIRECTOR_MAX_GEN=%s. Stop and report to the operator.\n' "$launched" "$max"; return 10
  fi
  _dl_gitinfo "$dir" || return 0
  now="$(git -C "$dir" rev-parse -q --verify "refs/remotes/origin/$(_dl_default "$dir")" 2>/dev/null)" || return 0
  for f in "$DL_COMMON/pco-director.released" "$DL_COMMON/pco-director"; do
    [ -f "$f" ] || continue
    s="$(jq -r '.session // empty' "$f" 2>/dev/null)" || continue
    [ -n "$s" ] && [ "$s" = "${sid:-}" ] || continue
    ma="$(jq -r '.mainAtClaim // empty' "$f" 2>/dev/null)"
    if [ -n "$ma" ] && [ "$ma" = "$now" ]; then
      printf 'DISPATCH GATE: no progress since this director claimed: origin default branch is still %s. Land work before handing off, or stop and report to the operator.\n' "$ma"; return 10
    fi
    break
  done
  return 0
}

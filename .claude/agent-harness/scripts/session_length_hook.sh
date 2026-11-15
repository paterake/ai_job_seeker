#!/usr/bin/env bash
# PostToolUse hook: nudge the agent to checkpoint, and a fleet director to hand off to a successor, when the main
# session's context or turn count crosses a threshold. Fires after every tool call, so it also
# works in autonomous/background runs where UserPromptSubmit does not fire.
# Fails open: any error -> exit 0, no output. Needs jq; without it the control is off.
# Thresholds (override in settings.json env, or export in the shell that launches claude):
PCO_SESSION_CTX_TOKENS="${PCO_SESSION_CTX_TOKENS:-250000}"   # context tokens per band
PCO_SESSION_TURNS="${PCO_SESSION_TURNS:-150}"                # assistant turns per band
PCO_SESSION_SHELL_CALLS="${PCO_SESSION_SHELL_CALLS:-120}"    # Bash calls per band, subagent calls included
PCO_SESSION_CACHE_DIR="${PCO_SESSION_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/pco-session-length}"
PCO_SESSION_TAIL_BYTES="${PCO_SESSION_TAIL_BYTES:-262144}"   # bounded transcript tail read
trap 'exit 0' EXIT
exec 2>/dev/null
command -v jq >/dev/null || exit 0

in="$(cat)"
sid="$(printf '%s' "$in" | jq -r '.session_id // empty' | tr -cd 'A-Za-z0-9-')"
tp="$(printf '%s' "$in" | jq -r '.transcript_path // empty')"
agent="$(printf '%s' "$in" | jq -r '.agent_id // empty')"
tool="$(printf '%s' "$in" | jq -r '.tool_name // empty')"
case "$PCO_SESSION_CTX_TOKENS$PCO_SESSION_TURNS$PCO_SESSION_SHELL_CALLS$PCO_SESSION_TAIL_BYTES" in *[!0-9]*) exit 0 ;; esac
[ "$PCO_SESSION_CTX_TOKENS" -gt 0 ] && [ "$PCO_SESSION_TURNS" -gt 0 ] && [ "$PCO_SESSION_SHELL_CALLS" -gt 0 ] || exit 0
[ -n "$sid" ] || exit 0

rd() { local v; v="$(cat "$1" 2>/dev/null)"; case "$v" in ''|*[!0-9]*) echo 0 ;; *) echo "$v" ;; esac; }
mkdir -p "$PCO_SESSION_CACHE_DIR" || exit 0
# Shell (Bash) calls per session id: subagents share the parent's id, so their calls count too.
shf="$PCO_SESSION_CACHE_DIR/$sid.shells"
if [ "$tool" = "Bash" ]; then
  [ -f "$shf" ] || find "$PCO_SESSION_CACHE_DIR" -type f -mtime +14 -delete
  echo $(( $(rd "$shf") + 1 )) > "$shf"
fi
# Everything below is main-session only.
[ -z "$agent" ] || exit 0
case "$tp" in */subagents/*) exit 0 ;; esac

why=""; shellhit=0
shells="$(rd "$shf")"; sb=$((shells / PCO_SESSION_SHELL_CALLS)); ss="$(rd "$PCO_SESSION_CACHE_DIR/$sid.shellband")"
if [ "$sb" -ge 1 ] && [ "$sb" -gt "$ss" ]; then why="${shells} shell calls (threshold ${PCO_SESSION_SHELL_CALLS})"; shellhit=1; echo "$sb" > "$PCO_SESSION_CACHE_DIR/$sid.shellband"; fi

# Context and turn bands need the transcript; a failure here leaves the shell band intact.
ctxturn() {
  [ -n "$tp" ] && [ -f "$tp" ] || return 0
  # Last main-session assistant line in the tail (first line dropped only when the tail is cut: probably partial).
  local size skip last ctx mid tf pid turns cb tb cs ts
  size="$(wc -c < "$tp")"; skip=1; [ "$size" -gt "$PCO_SESSION_TAIL_BYTES" ] && skip=2
  last="$(tail -c "$PCO_SESSION_TAIL_BYTES" "$tp" | tail -n +"$skip" \
    | jq -Rc 'fromjson? | select(.type=="assistant" and .isSidechain!=true)' | tail -n 1)"
  [ -n "$last" ] || return 0
  ctx="$(printf '%s' "$last" | jq -r '.message.usage | (.input_tokens // 0) + (.cache_read_input_tokens // 0) + (.cache_creation_input_tokens // 0)')"
  mid="$(printf '%s' "$last" | jq -r '.message.id // empty')"
  case "$ctx" in ''|*[!0-9]*) return 0 ;; esac

  tf="$PCO_SESSION_CACHE_DIR/$sid.turns"
  if [ ! -f "$tf" ]; then
    find "$PCO_SESSION_CACHE_DIR" -type f -mtime +14 -delete
    printf '%s %s\n' "$mid" 1 > "$tf"
  fi
  read -r pid turns < "$tf"
  case "$turns" in ''|*[!0-9]*) turns=1 ;; esac
  if [ -n "$mid" ] && [ "$mid" != "$pid" ]; then
    turns=$((turns + 1)); printf '%s %s\n' "$mid" "$turns" > "$tf"
  fi

  cb=$((ctx / PCO_SESSION_CTX_TOKENS)); tb=$((turns / PCO_SESSION_TURNS))
  cs="$(rd "$PCO_SESSION_CACHE_DIR/$sid.ctxband")"; ts="$(rd "$PCO_SESSION_CACHE_DIR/$sid.turnband")"
  if [ "$cb" -ge 1 ] && [ "$cb" -gt "$cs" ]; then why="${why:+$why; }context is ${ctx} tokens (threshold ${PCO_SESSION_CTX_TOKENS})"; echo "$cb" > "$PCO_SESSION_CACHE_DIR/$sid.ctxband"; fi
  if [ "$tb" -ge 1 ] && [ "$tb" -gt "$ts" ]; then why="${why:+$why; }at least ${turns} assistant turns (threshold ${PCO_SESSION_TURNS})"; echo "$tb" > "$PCO_SESSION_CACHE_DIR/$sid.turnband"; fi
  return 0
}
ctxturn || true
[ -n "$why" ] || exit 0
find "$PCO_SESSION_CACHE_DIR" -type f -mtime +14 -delete

extra=""
[ "$shellhit" = 1 ] && extra=" ${shells} shell calls used; the repo's shell-call limit denies ALL further shell calls, so a director must hand off now while shell calls remain."
jq -nc --arg w "$why" --arg x "$extra" '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:("SESSION LENGTH: this session is long (" + $w + "). Every further turn re-reads that context at full cost. Finish the current step, then run /backlog-continuity to write an anchor checkpoint. If you are a fleet director, hand off to a successor director per the fleet skill (successor director section) instead of waiting for the operator (release the director marker, launch the successor, which claims it). If you are not a director, tell the operator a fresh session suits the next task. One session per task." + $x)}}'
exit 0

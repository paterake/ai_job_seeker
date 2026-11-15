#!/usr/bin/env bash
# PostToolUse on SubagentHandback and SubagentStop (agent-harness:reviewer): record a PASS for the staged tree the reviewer judged.
# Records only when the verdict names the current staged tree and every staged path is unchanged in
# the working tree (so the files the reviewer read are the staged content). Other files may differ.
set -uo pipefail

payload="$(cat)"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty')"

# The reviewer's final answer:
# - PostToolUse on SubagentHandback (background and interactive sessions): the report is the call's
#   tool_input.message, delivered in the hook input itself. The transcript is written asynchronously
#   and may lag when SubagentStop fires, so this hook input is the primary source.
# - SubagentStop with a final text answer: last_assistant_message. A hand-back reaches SubagentStop
#   only through the transcript, read as a last resort (an interim PASS followed by another tool call
#   records nothing).
event="$(printf '%s' "$payload" | jq -r '.hook_event_name // empty')"
agent_type="$(printf '%s' "$payload" | jq -r '.agent_type // empty')"
final=""
case "$event" in
  PostToolUse)
    [ "$(printf '%s' "$payload" | jq -r '.tool_name // empty')" = "SubagentHandback" ] || exit 0
    # In a cloud session the reviewer comes from the repo's .claude/agents/ (cloud pack) and is named plain "reviewer".
    [ "$agent_type" = "agent-harness:reviewer" ] || { [ "${CLAUDE_CODE_REMOTE:-}" = "true" ] && [ "$agent_type" = "reviewer" ]; } || exit 0
    final="$(printf '%s' "$payload" | jq -r '.tool_input.message // empty')"
    ;;
  SubagentStop)
    transcript="$(printf '%s' "$payload" | jq -r '.agent_transcript_path // empty')"
    case "$transcript" in "~/"*) transcript="$HOME/${transcript#\~/}" ;; esac
    final="$(printf '%s' "$payload" | jq -r '.last_assistant_message // empty')"
    if printf '%s' "$final" | head -n 1 | grep -Eq '^VERDICT: '; then
      :
    elif [ -n "$transcript" ] && [ -f "$transcript" ]; then
      final="$(jq -rs '[.[] | select(.type == "assistant") | .message.content[]?
          | select(.type != "thinking" and .type != "redacted_thinking")] | last
          | if .type == "tool_use" and .name == "SubagentHandback" then (.input.message // "")
            elif .type == "text" then .text else "" end' "$transcript" 2>/dev/null)"
    fi
    ;;
  *) exit 0 ;;
esac
first_line="$(printf '%s' "$final" | head -n 1)"

# One verdict event per matched verdict line (PASS, REVISE or ESCALATE), before any early exit below.
# Fixed codes and a sha256 of the message only, never verdict text. SubagentStop and the hand-back
# hook can both fire for one verdict: with a non-empty agent_id, an event with the same agent_id,
# reason_code and message_hash already in this session's events.jsonl suppresses the second.
# With an empty agent_id nothing is deduped. Any failure here is ignored.
verdict="$(printf '%s' "$first_line" | sed -nE 's/^VERDICT: (PASS|REVISE|ESCALATE).*/\1/p')"
if [ -n "$verdict" ] && [ "${PCO_TELEMETRY:-1}" != "0" ]; then
  vsid="$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null)"
  vagent="$(printf '%s' "$payload" | jq -r '.agent_id // empty' 2>/dev/null)"
  vtree="$(printf '%s' "$first_line" | sed -nE 's/^VERDICT: [A-Z]+ tree=([0-9a-f]{40,64})[[:space:]]*$/\1/p')"
  vcode="verdict_$(printf '%s' "$verdict" | tr 'A-Z' 'a-z')"
  vhash="$(printf '%s' "$final" | shasum -a 256 | cut -d' ' -f1)"
  vf="${PCO_TELEMETRY_DIR:-$HOME/Documents/__ai}/ai_ops/agent_harness/$vsid/telemetry/events.jsonl"
  case "$vsid" in ""|*/*|.*) vsid="" ;; esac
  dup=""
  if [ -n "$vsid" ] && [ -n "$vagent" ] && [ -f "$vf" ] && grep -qF "$vhash" "$vf" 2>/dev/null; then
    jq -en --arg a "$vagent" --arg c "$vcode" --arg h "$vhash" \
      'any(inputs; .agent_id == $a and .reason_code == $c and .message_hash == $h)' "$vf" >/dev/null 2>&1 && dup=1
  fi
  [ -n "$vsid" ] && [ -z "$dup" ] \
    && "$(dirname "$0")/tel_emit.sh" record_pass verdict "$vtree" "$vcode" "$vsid" "$vagent" "$vhash" </dev/null >/dev/null 2>&1
fi

hash="$(printf '%s' "$first_line" | sed -nE 's/^VERDICT: PASS tree=([0-9a-f]{40,64})[[:space:]]*$/\1/p')"
[ -n "$hash" ] || exit 0
[ -n "$cwd" ] || exit 0

git_dir="$(git -C "$cwd" rev-parse --absolute-git-dir 2>/dev/null)" || exit 0
current="$(git -C "$cwd" write-tree 2>/dev/null)" || exit 0
if [ "$hash" != "$current" ]; then
  # Not recorded: the verdict names a tree this cwd does not hold (staged elsewhere, e.g. another
  # worktree). Never record a tree that cannot be verified here. Tell the user why; do not block.
  cwd_top="$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)" || cwd_top="$cwd"
  "$(dirname "$0")/tel_emit.sh" record_pass not_recorded "$hash" cwd_tree_mismatch \
    "$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null)" </dev/null >/dev/null 2>&1
  jq -n --arg top "$cwd_top" --arg cur "$current" --arg h "$hash" \
    '{systemMessage: ("agent-harness: reviewer PASS not recorded. The verdict names tree " + $h + ", but the session cwd " + $top + " has tree " + $cur + ". The staged tree is probably in another worktree or repo. Make the commit from a session whose cwd is that worktree, so the reviewer runs there.")}'
  exit 0
fi
top="$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)" || exit 0   # staged paths are root-relative
git -C "$top" diff --cached --name-only -z | xargs -0 git -C "$top" diff --quiet -- 2>/dev/null || exit 0

mkdir -p "$git_dir/pco-review" && printf '%s\n' "$first_line" > "$git_dir/pco-review/$hash" \
  && "$(dirname "$0")/tel_emit.sh" record_pass pass_recorded "$hash" recorded \
       "$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null)" </dev/null >/dev/null 2>&1
exit 0

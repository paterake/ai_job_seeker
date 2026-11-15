#!/usr/bin/env bash
# SessionStart (cloud only, through cloud_only.sh): adds part N of the working-method rule to the session's context.
# The rule is longer than the 10,000-character cap on a hook's additionalContext (hooks doc), so pack.sh writes one
# SessionStart entry per part. Parts are split at "## " headings by split_rule. Part 1 also carries the cloud note.
# Fails open: any error prints nothing.
here="$(dirname "$0")"
cat >/dev/null
n="${1:-1}"
case "$n" in *[!0-9]*|'') exit 0 ;; esac
. "$here/split_rule.sh" 2>/dev/null || exit 0
text="$(split_rule "$here/rules/pco-working-method.md" "$n")" || exit 0
[ -n "$text" ] || exit 0
if [ "$n" = 1 ]; then
  note="Cloud session: the agent-harness working method is carried by this repository's .claude/ (the user-level plugin and rule are not installed in a cloud container). The harness agents here are named reviewer and decision-check, without the agent-harness: prefix; /agent-harness:change-loop is not available, so run the reviewer agent directly on the git write-tree hash before each commit. The commit gate and the session-length hook are active. /backlog-continuity and retire-backlog load only where this repository's .claude/skills holds them (a governed repo does; unverified in cloud); otherwise follow ai_context/pco/governance/AI_ASSISTANT_BACKLOG_CONTINUITY.md, and when the session-length text appears, update the Director handoff record in the run's anchor doc. The working-method rule follows (part $n)."
  text="$note"$'\n\n'"$text"
fi
jq -nc --arg c "$text" '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $c}}'

#!/usr/bin/env bash
# PreToolUse (Bash, if "*git*commit*" or "*git*push*"): allow a commit only when a reviewer PASS is recorded for
# the staged tree. Emits hookSpecificOutput deny — top-level/defer decisions are ignored interactively.
set -uo pipefail

sid=""; tree=""   # set before the ERR trap: deny() reads them and runs before they are filled
GATE_TOOL=gate_commit
fail='gate: cannot read the hook payload, refused (fail closed)'
payload="$(cat)" || { printf '%s\n' "$fail" >&2; exit 2; }
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty')" || { printf '%s\n' "$fail" >&2; exit 2; }
sid="$(printf '%s' "$payload" | jq -r '.session_id // empty')" || { printf '%s\n' "$fail" >&2; exit 2; }
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')" || { printf '%s\n' "$fail" >&2; exit 2; }
# One active director (director_lock.sh): a push of the default branch by a session that is not the holder is
# refused. This branch only denies or falls through, never exits 0, so a combined `git commit ... && git push`
# still gets the reviewer-PASS check below. It sources its helpers with a plain skip: a missing file means the
# director check is not run (fail open, deliberate), never a new refusal. The check runs in a command
# substitution and cannot deny: only its return code 10 becomes a refusal; any other outcome is a skip.
if grep -Eq '(^|[;&|(`[:space:]])([^[:space:];&|(`]*/)?git([[:space:]]+(-[cC]|--(namespace|config-env|shallow-file|attr-source|git-dir|work-tree))[[:space:]]+[^[:space:]]+|[[:space:]]+-[^[:space:]]+)*[[:space:]]+push([[:space:]]|$)' <<<"$cmd"; then
  if . "$(dirname "$0")/gate_deny.sh" 2>/dev/null && . "$(dirname "$0")/director_lock.sh" 2>/dev/null; then
    dmsg="$(director_check push 2>/dev/null)"; drc=$?
    [ "$drc" -eq 10 ] && deny "$dmsg" director_held
  fi
fi
# No "commit" in the text: neither refusal below can apply, so exit before the shared deny helpers are needed.
grep -Eq -e 'commit' <<<"$cmd" || exit 0
. "$(dirname "$0")/gate_deny.sh" || { printf 'gate: gate_deny.sh missing, refused (fail closed)\n' >&2; exit 2; }
. "$(dirname "$0")/director_lock.sh" 2>/dev/null || true   # missing or unreadable: director_check stays undefined and is skipped
trap 'deny "COMMIT GATE: gate script error, commit refused (fail closed)." script_error' ERR
# The gate inspects only the session cwd, so a commit that moves to another directory or repo
# would be judged against the wrong tree. The tokens are looked for in the command's skeleton
# (shell_skeleton.pl: single-quoted text and heredoc bodies removed; double-quoted text removed unless a
# substitution makes it live; the raw text if it cannot read the command, so it fails closed). It refuses
# when the raw text or the skeleton holds a git commit and the skeleton holds a token. Here-strings, not
# pipes: under pipefail grep -q can SIGPIPE printf and skip the deny.
cw='(^|[;&|(`[:space:]])([^[:space:];&|(`]*/)?git([[:space:]]+(-[cC]|--(namespace|config-env|shallow-file|attr-source|git-dir|work-tree))[[:space:]]+[^[:space:]]+|[[:space:]]+-[^[:space:]]+)*[[:space:]]+commit([[:space:]]|$)'
skel="$(printf '%s' "$cmd" | perl "$(dirname "$0")/shell_skeleton.pl")" || skel=$cmd
[ -n "$skel" ] || skel=$cmd
if { grep -Eq -e "$cw" <<<"$cmd" || grep -Eq -e "$cw" <<<"$skel"; } \
   && grep -Eq -e '(^|[^[:alnum:]_])cd([^[:alnum:]_]|$)|pushd|-C|--git-dir|--work-tree|GIT_' <<<"$skel"; then
  # Telemetry only, after the decision: name the matched token. Keep these fragments in step with the regex above.
  mt=""; n=0
  for pair in 'cd:(^|[^[:alnum:]_])cd([^[:alnum:]_]|$)' 'pushd:pushd' 'dash_C:-C' 'git_dir:--git-dir' 'work_tree:--work-tree' 'git_env:GIT_'; do
    if grep -Eq -e "${pair#*:}" <<<"$skel"; then mt="${pair%%:*}"; n=$((n + 1)); fi || true
  done
  [ "$n" -gt 1 ] && mt="multiple"
  deny "COMMIT GATE: refused a commit command that changes directory or repo (cd, pushd, -C, --git-dir, --work-tree, GIT_*): the gate only inspects the session cwd. Run cd <repo> in a separate Bash call, then commit alone from that cwd." cd_or_repo_change "$mt"
fi
# The if filters also fire on any command whose text holds git and commit or push, $(), backticks or $VAR; act only on a git commit.
grep -Eq -e "$cw" <<<"$cmd" || exit 0
how="Stage the change, run agent-harness:reviewer with the git write-tree hash, get 'VERDICT: PASS tree=<hash>', then git commit (no -a, no paths)."

git_dir="$(git -C "$cwd" rev-parse --absolute-git-dir 2>/dev/null)" || deny "COMMIT GATE: not a git repository at $cwd." not_a_repo
# Refuse forms that commit something other than the staged tree; unrelated unstaged files are fine.
why="$(printf '%s' "$cmd" | perl "$(dirname "$0")/commit_args_ok.pl")" || deny "COMMIT GATE: refused '$why'. $how" bad_commit_args
# One active director: a commit on the default branch of the main checkout by a non-holder is refused. The ERR trap is
# suspended and restored (same text as above), and the check runs in a command substitution, so any error inside it
# is a skip and the reviewer-PASS lookup below runs unchanged: fail open, no new fail-closed path.
trap - ERR; dmsg="$(director_check commit 2>/dev/null)"; drc=$?; trap 'deny "COMMIT GATE: gate script error, commit refused (fail closed)." script_error' ERR; [ "$drc" -eq 10 ] && deny "$dmsg" director_held
tree="$(git -C "$cwd" write-tree 2>/dev/null)" || deny "COMMIT GATE: cannot compute the staged tree (unmerged paths?)." write_tree_failed

[ -f "$git_dir/pco-review/$tree" ] && { tel allowed pass_found; exit 0; }
deny "COMMIT GATE: no reviewer PASS recorded for staged tree $tree. $how" no_pass

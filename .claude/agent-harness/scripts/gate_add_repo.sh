#!/usr/bin/env bash
# PreToolUse on mcp__claude-code-remote__add_repo: a cloud session may attach a second repository only for reading,
# and only one its own repository lists. It denies unless tool_input.access is "read" or unset, owner and repo are
# plain names, and owner/repo is a line of <project>/.claude/allowed-repos.txt (one owner/repo per line, # comments,
# case-insensitive). A missing or unreadable list denies. Any script error denies (fail closed).
# The list sits under .claude/, so changing it is an operator-approved edit. The pack's add_repo allow entry exists
# only because this hook narrows it: the two land and leave together.
set -uo pipefail

payload="$(cat)" || { printf 'gate: cannot read the hook payload, refused (fail closed)\n' >&2; exit 2; }
tool="$(printf '%s' "$payload" | jq -r '.tool_name // empty')" \
  || { printf 'gate: jq failed, refused (fail closed)\n' >&2; exit 2; }
[ "$tool" = mcp__claude-code-remote__add_repo ] || exit 0

sid=""; tree=""
GATE_TOOL=gate_add_repo
. "$(dirname "$0")/gate_deny.sh" || { printf 'gate: gate_deny.sh missing, refused (fail closed)\n' >&2; exit 2; }
trap 'deny "ADD_REPO GATE: gate script error, add_repo refused (fail closed)." script_error' ERR
sid="$(printf '%s' "$payload" | jq -r '.session_id // empty')"
owner="$(printf '%s' "$payload" | jq -r '.tool_input.owner // empty')"
repo="$(printf '%s' "$payload" | jq -r '.tool_input.repo // empty')"
access="$(printf '%s' "$payload" | jq -r '.tool_input.access // "read"')"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty')"

[ "$access" = read ] || deny "ADD_REPO GATE: only read access may be attached (asked: $access). Pushing to another repository is that repository's own session's work." access_not_read
name='^[A-Za-z0-9][A-Za-z0-9._-]*$'
[[ $owner =~ $name && $repo =~ $name && $repo != *..* ]] || deny "ADD_REPO GATE: owner and repo must be plain names." bad_name

root="${CLAUDE_PROJECT_DIR:-}"
[ -n "$root" ] || root="$(git -C "${cwd:-.}" rev-parse --show-toplevel 2>/dev/null)" || root=""
list="$root/.claude/allowed-repos.txt"
[ -n "$root" ] && [ -r "$list" ] || deny "ADD_REPO GATE: this repository has no .claude/allowed-repos.txt, so no repository may be attached. Adding one is an operator-approved change." no_list

want="$(printf '%s/%s' "$owner" "$repo" | tr '[:upper:]' '[:lower:]')"
found=0
while IFS= read -r line || [ -n "$line" ]; do
  line="${line%%#*}"; line="${line//[[:space:]]/}"
  [ -n "$line" ] || continue
  [ "$(printf '%s' "$line" | tr '[:upper:]' '[:lower:]')" = "$want" ] && { found=1; break; }
done <"$list"
[ "$found" = 1 ] || deny "ADD_REPO GATE: $owner/$repo is not in .claude/allowed-repos.txt. Adding it is an operator-approved change." not_listed
tel allowed listed
exit 0

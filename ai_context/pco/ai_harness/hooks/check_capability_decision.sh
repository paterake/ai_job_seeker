#!/usr/bin/env bash
# check_capability_decision.sh — PreToolUse hook: require a capability-decision record
# before commit / PR creation when changes the command can commit (staged, unstaged or untracked) look like a
# new content-interpretation surface.
# Pass: exit 0 with no output (normal permission flow applies). Block: PreToolUse "deny" in hookSpecificOutput.
set -euo pipefail

payload="$(cat)"
if ! command -v jq >/dev/null 2>&1; then
    # Fails closed without jq, but only for commit / PR-creation commands (exit 2; Claude Code shows the reason):
    # it can neither parse the command nor emit a deny, and other shell calls are not this gate's concern.
    case "$payload" in
        *"git commit"*|*"gh pr create"*)
            printf 'GOVERNANCE STOP: check_capability_decision.sh cannot check this commit / PR: jq not found on PATH (install it; cloud sessions: setup_cloud_session.sh)\n' >&2
            exit 2
            ;;
    esac
    exit 0
fi
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')"

case "$cmd" in
  *"git commit"*|*"gh pr create"*)
    ;;
  *)
    exit 0
    ;;
esac

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# core.quotePath=false: list non-ASCII paths as-is, not C-quoted, so they match the patterns and can be read.
GIT=(git -c core.quotePath=false)

# Paths the command can commit: staged, unstaged and untracked. The hook runs before the command, so
# `git add … && git commit` and `git commit -a` stage their files only after this check.
UNTRACKED=()
while IFS= read -r line; do
    [[ -n "$line" ]] && UNTRACKED+=("$line")
done < <("${GIT[@]}" ls-files --others --exclude-standard 2>/dev/null || true)
CHANGED_PATHS=()
while IFS= read -r line; do
    [[ -n "$line" ]] && CHANGED_PATHS+=("$line")
done < <(
    { "${GIT[@]}" diff --cached --name-only --diff-filter=ACMR
      "${GIT[@]}" diff --name-only --diff-filter=ACMR
      printf '%s\n' "${UNTRACKED[@]}"; } 2>/dev/null | sort -u
)
if [[ "${#CHANGED_PATHS[@]}" -eq 0 ]]; then
    exit 0
fi

SOURCE_RE='\.(py|ts|tsx|js|jsx)$'
SHAPE_RE='(parser|extract|extraction|distill|classifier|classification|semantic|grounding|normalis|normaliz|inference|entity|relation|facet)'
CODE_DIR_RE='(^|/)(src|implementation|app|lib|packages|modules)/'

require_record=0
risky_paths=()

for path in "${CHANGED_PATHS[@]}"; do
    if [[ "$path" =~ $SOURCE_RE ]] && [[ "$path" =~ $SHAPE_RE ]]; then
        risky_paths+=("$path")
        require_record=1
    fi
done

if [[ "$require_record" -eq 0 ]]; then
    new_source_count="$(
        { "${GIT[@]}" diff --cached --name-only --diff-filter=A; printf '%s\n' "${UNTRACKED[@]}"; } 2>/dev/null \
        | sort -u \
        | awk -v code_re="$CODE_DIR_RE" '
            $0 ~ /\.(py|ts|tsx|js|jsx)$/ && $0 ~ code_re { c++ }
            END { print c + 0 }
        '
    )"
    # Untracked files feed the keyword scan only if they are readable source files: the heuristic counts source
    # files, and an unreadable path (broken symlink, nested repo) must not abort the hook. Only the first 1 MB of each
# is read, so a huge file cannot stall the commit. Word boundaries are
    # spelled out because mawk has no \b.
    keyword_hits="$(
        { "${GIT[@]}" diff HEAD --unified=0 -- . ':(exclude)audit/capability_decisions/*' 2>/dev/null \
            || "${GIT[@]}" diff --cached --unified=0 -- . ':(exclude)audit/capability_decisions/*' 2>/dev/null
          for f in "${UNTRACKED[@]}"; do
              if [[ "$f" =~ $SOURCE_RE && -f "$f" && -r "$f" ]]; then head -c 1000000 "$f" 2>/dev/null | sed 's/^/+/'; fi
          done
          true; } \
        | awk '
            /^\+/ && $0 !~ /^\+\+\+/ && $0 ~ /(^|[^[:alnum:]_])(parse|parser|extract|distill|classif|semantic|infer|ground|facet|entity|relation)([^[:alnum:]_]|$)/ { c++ }
            END { print c + 0 }
        '
    )"
    if [[ "${new_source_count:-0}" =~ ^[0-9]+$ ]] && [[ "${keyword_hits:-0}" =~ ^[0-9]+$ ]] \
        && [[ "$new_source_count" -ge 4 ]] && [[ "$keyword_hits" -ge 1 ]]; then
        require_record=1
    fi
fi

if [[ "$require_record" -eq 0 ]]; then
    exit 0
fi

RECORDS=()
while IFS= read -r line; do
    [[ -n "$line" ]] && RECORDS+=("$line")
done < <(
    printf '%s\n' "${CHANGED_PATHS[@]}" \
    | grep -E '^audit/capability_decisions/.*\.md$' \
    | grep -Ev '^audit/capability_decisions/README\.md$' || true
)

if [[ "${#RECORDS[@]}" -eq 0 ]]; then
    reason="$(cat <<'DENY'
GOVERNANCE DENY
risk_tier: high
denial_reason: capability_decision_required
policy_set: pco-core/v1
next_action: add a capability-decision record under audit/capability_decisions/ using audit/templates/capability_decision_record.md, then retry the commit / PR command
DENY
)"
    jq -nc --arg reason "$reason" \
        '{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": $reason}}'
    exit 0
fi

missing_fields=()
for record in "${RECORDS[@]}"; do
    # The working-tree copy is what `git add` will commit; fall back to the index if it was deleted.
    staged_record="$(cat "$record" 2>/dev/null || git show ":$record" 2>/dev/null || true)"
    for heading in \
        '**Task Type:**' \
        '**Chosen Driver:**' \
        '## Why This Driver Fits' \
        '## Why The Other Driver Was Not Chosen' \
        '## Prompt / Config Consideration'
    do
        if ! printf '%s' "$staged_record" | grep -Fq "$heading"; then
            missing_fields+=("$record :: missing $heading")
        fi
    done
done

if [[ "${#missing_fields[@]}" -gt 0 ]]; then
    detail="$(printf '%s\n' "${missing_fields[@]}" | paste -sd '; ' -)"
    reason="$(printf 'GOVERNANCE DENY\nrisk_tier: high\ndenial_reason: capability_decision_invalid\npolicy_set: pco-core/v1\ndetail: %s\nnext_action: fill the required sections in the capability-decision record, then retry the commit / PR command' "$detail")"
    jq -nc --arg reason "$reason" \
        '{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": $reason}}'
    exit 0
fi

exit 0

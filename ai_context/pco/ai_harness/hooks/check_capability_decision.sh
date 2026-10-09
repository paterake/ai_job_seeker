#!/usr/bin/env bash
# check_capability_decision.sh — PreToolUse hook: require a capability-decision record
# before commit / PR creation when staged changes look like a new content-interpretation surface.
set -euo pipefail

payload="$(cat)"
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')"

case "$cmd" in
  *"git commit"*|*"gh pr create"*)
    ;;
  *)
    jq -nc '{"permissionDecision": "allow"}'
    exit 0
    ;;
esac

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

STAGED_PATHS=()
while IFS= read -r line; do
    [[ -n "$line" ]] && STAGED_PATHS+=("$line")
done < <(git diff --cached --name-only --diff-filter=ACMR)
if [[ "${#STAGED_PATHS[@]}" -eq 0 ]]; then
    jq -nc '{"permissionDecision": "allow"}'
    exit 0
fi

SOURCE_RE='\.(py|ts|tsx|js|jsx)$'
SHAPE_RE='(parser|extract|extraction|distill|classifier|classification|semantic|grounding|normalis|normaliz|inference|entity|relation|facet)'
CODE_DIR_RE='(^|/)(src|implementation|app|lib|packages|modules)/'

require_record=0
risky_paths=()

for path in "${STAGED_PATHS[@]}"; do
    if [[ "$path" =~ $SOURCE_RE ]] && [[ "$path" =~ $SHAPE_RE ]]; then
        risky_paths+=("$path")
        require_record=1
    fi
done

if [[ "$require_record" -eq 0 ]]; then
    new_source_count="$(
        git diff --cached --name-status --diff-filter=A \
        | awk -v code_re="$CODE_DIR_RE" '
            $2 ~ /\.(py|ts|tsx|js|jsx)$/ && $2 ~ code_re { c++ }
            END { print c + 0 }
        '
    )"
    keyword_hits="$(
        git diff --cached --unified=0 -- . ':(exclude)audit/capability_decisions/*' \
        | awk '
            /^\+/ && $0 !~ /^\+\+\+/ && $0 ~ /\b(parse|parser|extract|distill|classif|semantic|infer|ground|facet|entity|relation)\b/ { c++ }
            END { print c + 0 }
        '
    )"
    if [[ "${new_source_count:-0}" =~ ^[0-9]+$ ]] && [[ "${keyword_hits:-0}" =~ ^[0-9]+$ ]] \
        && [[ "$new_source_count" -ge 4 ]] && [[ "$keyword_hits" -ge 1 ]]; then
        require_record=1
    fi
fi

if [[ "$require_record" -eq 0 ]]; then
    jq -nc '{"permissionDecision": "allow"}'
    exit 0
fi

RECORDS=()
while IFS= read -r line; do
    [[ -n "$line" ]] && RECORDS+=("$line")
done < <(
    printf '%s\n' "${STAGED_PATHS[@]}" \
    | grep -E '^audit/capability_decisions/.*\.md$' \
    | grep -Ev '^audit/capability_decisions/README\.md$' || true
)

if [[ "${#RECORDS[@]}" -eq 0 ]]; then
    reason="$(cat <<'DENY'
GOVERNANCE DENY
risk_tier: high
denial_reason: capability_decision_required
policy_set: pco-core/v1
next_action: add a capability-decision record under audit/capability_decisions/ using audit/templates/capability_decision_record.md, stage it, then retry the commit / PR command
DENY
)"
    jq -nc --arg reason "$reason" '{"permissionDecision": "defer", "reason": $reason}'
    exit 0
fi

missing_fields=()
for record in "${RECORDS[@]}"; do
    staged_record="$(git show ":$record" 2>/dev/null || true)"
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
    reason="$(printf 'GOVERNANCE DENY\nrisk_tier: high\ndenial_reason: capability_decision_invalid\npolicy_set: pco-core/v1\ndetail: %s\nnext_action: fill the required sections in the staged capability-decision record, then retry the commit / PR command' "$detail")"
    jq -nc --arg reason "$reason" '{"permissionDecision": "defer", "reason": $reason}'
    exit 0
fi

jq -nc '{"permissionDecision": "allow"}'

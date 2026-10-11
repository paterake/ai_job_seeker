#!/usr/bin/env bash
# check_exception_expiry.sh — PreToolUse hook: deny while any governance exception has expired.
# Pass: exit 0 with no output (normal permission flow applies). Block: PreToolUse "deny" in hookSpecificOutput.
# Fail-open: when scripts/distill_harness.py is absent (consumer repos), the hook exits 0 silently.
set -uo pipefail

# Consume stdin (required by hook contract; payload not needed for this check)
cat > /dev/null

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
validator="$repo_root/scripts/distill_harness.py"

if [ ! -f "$validator" ]; then
    # No validator in this repo root (e.g. a consumer repo, or cwd drifted outside the PCO) — nothing to check.
    exit 0
fi

output="$(cd "$repo_root" && uv run python3 "$validator" exception-registry-validate --repo "$repo_root" 2>&1)"
exit_code=$?

if [ "$exit_code" -ne 0 ]; then
    reason="$(printf 'GOVERNANCE DENY\nrisk_tier: high\ndenial_reason: expired_exceptions\ndetail: one or more governance exceptions have expired and must be renewed or removed\npolicy_set: pco-core/v1\nnext_action: renew or remove the expired entry in exception_registry.yaml with the file-edit tool (shell commands are denied until then); validator_output below names it\nvalidator_output: %s' "$output")"
    jq -nc --arg reason "$reason" \
        '{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": $reason}}'
fi
exit 0

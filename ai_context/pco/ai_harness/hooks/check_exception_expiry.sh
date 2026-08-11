#!/usr/bin/env bash
set -uo pipefail

# Consume stdin (required by hook contract; payload not needed for this check)
cat > /dev/null

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
validator="$repo_root/scripts/distill_harness.py"

if [ ! -f "$validator" ]; then
    # No validator in this repo root (e.g. cwd drifted outside the PCO) — nothing to check.
    jq -nc '{"permissionDecision": "allow"}'
    exit 0
fi

output="$(python3 "$validator" exception-registry-validate --repo "$repo_root" 2>&1)"
exit_code=$?

if [ "$exit_code" -ne 0 ]; then
    reason="$(printf 'GOVERNANCE DENY\nrisk_tier: high\ndenial_reason: expired_exceptions\ndetail: one or more governance exceptions have expired and must be renewed or removed\npolicy_set: pco-core/v1\nnext_action: run "python3 scripts/distill_harness.py exception-registry-validate --repo ." then update or remove expired entries in exception_registry.yaml\nvalidator_output: %s' "$output")"
    jq -nc --arg reason "$reason" '{"permissionDecision": "defer", "reason": $reason}'
else
    jq -nc '{"permissionDecision": "allow"}'
fi

#!/usr/bin/env bash
# remind_evidence_package.sh — Stop hook: warns if no evidence record was written for this run.
# Governance: operations rule — every governed run must produce a written evidence record.
# This hook is advisory: it always exits 0 (cannot block after the session has stopped).
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RUN_ID_FILE="$REPO_ROOT/.claude/current_run_id"

if [[ ! -f "$RUN_ID_FILE" ]]; then
    exit 0
fi

RUN_ID="$(cat "$RUN_ID_FILE")"
RECORD="$REPO_ROOT/audit/runs/${RUN_ID}.yaml"

if [[ -f "$RECORD" ]]; then
    exit 0
fi

cat >&2 <<EOF
⚠️  GOVERNANCE REMINDER: no evidence record written for this run.
   run_id : $RUN_ID
   missing: audit/runs/${RUN_ID}.yaml

   To close this run, invoke /evidence-package or copy the template:
     cp audit/templates/evidence_record.yaml audit/runs/${RUN_ID}.yaml
   Then populate all fields and validate:
     python3 scripts/distill_harness.py evidence-validate --record audit/runs/${RUN_ID}.yaml
EOF

exit 0

# Agent Hooks

- `gate_git_push.sh`: Defers `git push` to main branch for human approval.
- `check_exception_expiry.sh`: Defers Bash execution when repo-local governance exceptions have expired.
- `check_capability_decision.sh`: Defers commit / PR creation for parser-/extractor-shaped content-interpretation changes unless a capability-decision record is staged.
- `check_execution_limits.sh`: Stops Bash tool use when the configured execution budget is exhausted.
- `init_run_id.sh`: Seeds a stable `run_id` at session start.
- `remind_evidence_package.sh`: Stop-hook reminder to close the run with evidence.

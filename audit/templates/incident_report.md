# Incident — <short description>

**Date:** YYYY-MM-DD
**Incident ID:** INC-YYYYMMDD-<slug>
**Repo/module:**
**Severity:** low | medium | high | critical
**Detected by:** (human review | sensor | production alert | user report)

## What happened

## Root cause class
(overeagerness | assumption filling | brute-force fix | false success signal | genie risk | code quality drift | sensor silence | other)

## Governance action
- [ ] New eval case added to `eval/` in affected repo
- [ ] Exception registry updated (if exception was involved)
- [ ] Rule updated: <link>
- [ ] Sensor added/updated: <link>
- [ ] Capability stage changed: <link to capability_registry.yaml>

## Cross-references (required if a governance surface changed)
- Rules changed: (e.g. `ai_context/pco/ai_harness/rules/operations.md#...`)
- Registry entries changed: (e.g. `exception_registry.yaml: EXC-001`, `capability_registry.yaml: CAP-...`)
- Evidence: (PR link, run_id(s), governance-audit output excerpt)

## Verification
How was the fix confirmed? (test name, eval result, governance-audit output)

---
# Per-Tier Deny Interface

> Canonical deny response schema for governed agent runs. All hooks and control-plane denials must produce a response conforming to this shape. This is the observable interface — enforcement wiring (hook scripts, detection logic, allowlists) is not disclosed here.

## Deny Response Shape

The target shape for a denial event is these six fields. The current PCO hooks emit a subset:
none emits `run_id` or `approval_record` (the retired push gate was the only one that emitted
`approval_record`), and `check_execution_limits.sh` also omits `policy_set` (see Current Enforcement Points):

```
run_id:           <stable run identifier propagated from entry point; "local" if outside a governed run>
policy_set:       <policy pack id + version — e.g. pco-core/v1>
risk_tier:        <low | medium | high | critical>
denial_reason:    <reason code — see table below>
approval_record:  <approval record id, or "missing">
next_action:      <what the operator must do to unblock>
```

## Denial Reason Codes

| Reason code | Trigger condition | Applicable tiers |
|---|---|---|
| `approval_required` | Tier 3/4 change (High/Critical) attempted without a traceable approval record | High, Critical |
| `entitlement_exceeded` | Tool not in the role's entitlement set for the current risk tier | Medium, High, Critical |
| `exception_expired` | Exception invoked after its expiry date | Any |
| `capability_experimental` | Capability in Experimental lifecycle stage invoked without a recorded adoption escalation | Any |
| `supervision_required` | Action requires a fully supervised workflow; autonomous execution not permitted at this tier | Critical |
| `expired_exceptions` | Emitted by the exception-expiry hook when a repo-local governance exception has expired (the hook's name for `exception_expired`) | Any |
| `execution_limit_hit` | Emitted by the execution-limits hook when the tool-call budget is exhausted | Any |
| `capability_decision_required` | Emitted by the capability-decision hook: parser-/extractor-shaped change staged without a capability-decision record | Any |
| `capability_decision_invalid` | Emitted by the capability-decision hook: staged capability-decision record is missing required sections | Any |

## Per-Tier Denial Shapes

| Risk tier | Denial trigger | Reason code | Approval state | next_action |
|---|---|---|---|---|
| Low | Most Low-tier actions proceed without pre-approval | — | Not required | Proceed |
| Medium | Tool not in role entitlements | `entitlement_exceeded` | Not required | Scope down to entitled tools, or request entitlement grant via the exception process |
| High | Protected change attempted without approval record | `approval_required` | Required — missing | Request approval from governance board; record the approval before re-attempting |
| Critical | Fully supervised workflow required; autonomous execution blocked | `supervision_required` | Required — missing | Initiate fully supervised workflow with explicit human approval at each step |

## Current Enforcement Points

The PCO hooks `check_exception_expiry.sh`, `check_capability_decision.sh` and `check_execution_limits.sh` return the deny shape as a PreToolUse `"deny"` inside `hookSpecificOutput`, with the structured reason in `permissionDecisionReason`. Claude Code blocks the tool call on a `deny`. When a hook does not trip it exits 0 with no output and the call goes through the normal permission flow. Where each hook fails open:

- Exception expiry: silent when the repo has no `scripts/distill_harness.py`, so it enforces in the PCO repo only, not in consumer repos. It fails closed on any validator failure (malformed registry, missing expiry, `uv` unavailable), denying every shell command until the registry validates.
- Execution limits: silent when the limits file cannot be read. The count is per session, so the limit bounds one session, not a run spanning several sessions.
- Capability decision: detection is a path/keyword heuristic over staged files; a content-interpretation change that matches neither passes silently.

The `approval_required` reason code and the High-tier row above remain the shape for any future protected-change gate; no PCO hook emits it today.

## Registration Surface

`master-data/tool_registry.yaml` is the complementary artefact: it enumerates governed tools with their risk tiers and entitlements, so the control plane knows which tools can trigger which denial conditions.

## References

- Capability tiers and supervision model: [HUB.md](HUB.md)
- Tool entitlement policy: [master-data/README.md](../master-data/README.md)
- Hooks vs guidance enforcement semantics: [ai_harness/rules/harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)
- Tool registry: [master-data/tool_registry.yaml](../master-data/tool_registry.yaml)
- Enforcement feedback loop (Tool denial event): [HUB.md — Enforcement feedback loop](HUB.md)

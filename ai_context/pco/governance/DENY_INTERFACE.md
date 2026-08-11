---
# Per-Tier Deny Interface

> Canonical deny response schema for governed agent runs. All hooks and control-plane denials must produce a response conforming to this shape. This is the observable interface — enforcement wiring (hook scripts, detection logic, allowlists) is not disclosed here.

## Deny Response Shape

Every denial event must carry these six fields:

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

## Per-Tier Denial Shapes

| Risk tier | Denial trigger | Reason code | Approval state | next_action |
|---|---|---|---|---|
| Low | Most Low-tier actions proceed without pre-approval | — | Not required | Proceed |
| Medium | Tool not in role entitlements | `entitlement_exceeded` | Not required | Scope down to entitled tools, or request entitlement grant via the exception process |
| High | Protected change attempted without approval record | `approval_required` | Required — missing | Request approval from governance board; record the approval before re-attempting |
| Critical | Fully supervised workflow required; autonomous execution blocked | `supervision_required` | Required — missing | Initiate fully supervised workflow with explicit human approval at each step |

## Current Enforcement Point

`.claude/hooks/gate_git_push.sh` intercepts `git push origin main` — a High-tier action (protected change, broad impact, irreversible without remediation). On denial it emits the following instantiation of the deny shape:

```
risk_tier: high
denial_reason: approval_required
policy_set: pco-core/v1
approval_record: missing
next_action: request approval from governance board, or scope down to a non-main branch push
```

## Registration Surface

`master-data/tool_registry.yaml` is the complementary artefact: it enumerates governed tools with their risk tiers and entitlements, so the control plane knows which tools can trigger which denial conditions.

## References

- Capability tiers and supervision model: [HUB.md](HUB.md)
- Tool entitlement policy: [master-data/README.md](../master-data/README.md)
- Hooks vs guidance enforcement semantics: [ai_harness/rules/harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)
- Tool registry: [master-data/tool_registry.yaml](../master-data/tool_registry.yaml)
- Enforcement feedback loop (Tool denial event): [HUB.md — Enforcement feedback loop](HUB.md)

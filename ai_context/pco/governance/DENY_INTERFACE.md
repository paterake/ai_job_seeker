# Per-Tier Deny Interface

> Canonical deny response schema for governed agent runs. All hook denials, and denials by a future control plane ([HUB.md](HUB.md) → Not enforced), must produce a response conforming to this shape. This is the observable interface — detection logic is not described here.

## Deny Response Shape

The target shape for a denial event is these six fields. The current PCO hooks emit a subset:
none emits `run_id`, `approval_record` or `policy_set`, and `check_guard.sh` also omits `risk_tier` (see Current Enforcement Points):

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
| `approval_required` | A Tier 3/4 capability change attempted without a traceable approval record | High, Critical |
| `entitlement_exceeded` | Tool not in the role's entitlement set for the current risk tier | Medium, High, Critical |
| `exception_expired` | Exception invoked after its expiry date | Any |
| `capability_experimental` | A Tier 3/4 capability in the experimental stage adopted without a recorded escalation ([CONTRACT.md](CONTRACT.md) → Capability Lifecycle) | Any |
| `supervision_required` | Action requires a fully supervised workflow; autonomous execution not permitted at this tier | Critical |
| `execution_limit_hit` | Emitted by the execution-limits gate when the session's shell-call budget is exhausted | Any |
| `force_push_refused` | Emitted by the guard gate on a force push (what it matches: [hooks/README.md](../ai_harness/hooks/README.md)) | Any |
| `synced_pco_edit_refused` | Emitted by the guard gate on a file edit to the synced layer outside the PCO ([hooks/README.md](../ai_harness/hooks/README.md)) | Any |

"Applicable tiers" are a solution's risk tiers (low to critical). They are distinct from capability tiers (1–4,
[HUB.md](HUB.md) → Capability-tiered governance) and from a tool's own `risk_tier` (`lineage.md`).

## Per-Tier Denial Shapes

| Risk tier | Denial trigger | Reason code | Approval state | next_action |
|---|---|---|---|---|
| Low | Most Low-tier actions proceed without pre-approval | — | Not required | Proceed |
| Medium | Tool not in role entitlements | `entitlement_exceeded` | Not required | Scope down to entitled tools, or request entitlement grant via the exception process |
| High | Protected change attempted without approval record | `approval_required` | Required — missing | Request approval from the operator; record the approval before re-attempting |
| Critical | Fully supervised workflow required; autonomous execution blocked | `supervision_required` | Required — missing | Initiate fully supervised workflow with explicit human approval at each step |

## Current Enforcement Points

The PCO gates `check_execution_limits.sh` and `check_guard.sh` emit the structured reason; the agent adapter carries it into the harness's pre-tool-use deny decision. How they deny, pass and fail closed: [hooks/README.md](../ai_harness/hooks/README.md).

The `approval_required` reason code and the High-tier row above remain the shape for any future protected-change gate; no PCO hook emits it today.

## Registration Surface

`master-data/tool_registry.yaml` is the complementary artefact: it enumerates governed tools with their risk tiers and entitlements, so a control plane ([HUB.md](HUB.md) → Not enforced) could know which tools can trigger which denial conditions.

## References

- Capability tiers and supervision model: [HUB.md](HUB.md)
- Tool entitlement policy: [master-data/README.md](../master-data/README.md)
- Hooks vs guidance enforcement semantics: [ai_harness/rules/harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)
- Tool registry: [master-data/tool_registry.yaml](../master-data/tool_registry.yaml)
- Enforcement feedback loop (Tool denial event): [HUB.md — Enforcement feedback loop](HUB.md#enforcement-feedback-loop)

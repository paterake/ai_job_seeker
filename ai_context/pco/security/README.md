# Security & Safety (Spoke)
> Area: Agent Security & Safety

## Governs

- Untrusted content: the lethal trifecta and content source trust
- Per-task least privilege and secret handling
- Outbound destinations and exfiltration channels
- Tool and MCP server adoption
- Non-impersonation and epistemic honesty
- Trust boundaries between agents

## Enforced

- Tool registry shape: [master-data spoke](../master-data/README.md) → Enforced.
- Trifecta separation (§1), per-task privilege decomposition and secret brokering (§2), tool/MCP trust assessment
  (§4), non-impersonation (§5), epistemic honesty (§6), External Research (Bounded) and Multi-Agent Trust: human
  review against
  [security-threat-model.md](../ai_harness/rules/security-threat-model.md).
- Office files (types in `governance/data_guard.yaml`) and files matching a named PII pattern are denied to the file
  Read and Grep tools in `ai_agent_pco`: hook `check_data_guard.sh` (`data_guard_refused`;
  [hooks/README.md](../ai_harness/hooks/README.md)). Consumers are not guarded until their repo wires it.

## Not enforced

- Use of an unregistered tool or MCP server: [lineage spoke](../lineage/README.md) → Not enforced.
- Outbound allowlisting for runtime agents: required by security-threat-model.md → §3; no PCO check. The control
  plane meant to hold the allowlists: [governance/HUB.md](../governance/HUB.md) → Not enforced.
- Outbound allowlisting for coding sessions: no sandbox and no deny list in the agent's harness settings. Target, not
  implemented (outside §3's scope).
- Content source registration for High/Critical solutions and blocking of Prohibited sources: required by
  security-threat-model.md → §1; no PCO check.
- Secrets kept out of logs, telemetry, traces, run evidence and commits: required by security-threat-model.md → §2 and
  AGENTS.md → Security; no PCO check (no secret scanning).
- Data residency and access recertification: required by
  [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md) → Data Residency / Sovereignty /
  Cross-Border Transfer and Procurement & Access Lifecycle; no PCO check.
- Personal data and Office documents reaching the model by any other route (shell, MCP connectors, notebook read,
  prompt submit, pathless or directory Grep, non-Office binaries, files over the scan cap), or in a consumer whose
  settings do not wire the data guard: [integration spoke](../integration/README.md) → Not enforced.

## Rules

- [security-threat-model.md](../ai_harness/rules/security-threat-model.md)
- [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md) → Data Residency / Sovereignty /
  Cross-Border Transfer; Procurement & Access Lifecycle

## Canonical

### AgentFlayer

Malicious text in a Jira ticket or GitHub issue asks the agent for credential tokens and tells it to post them as a
public comment. It needs no code execution: the attack is carried entirely by crafted text, which is why §1 treats
every untrusted source as data.

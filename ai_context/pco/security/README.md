# Security & Safety (Spoke)
> DAMA mapping: Data Security → Agent Security & Safety

## Governs

- Untrusted content: the lethal trifecta and content source trust
- Per-task least privilege and secret handling
- Outbound destinations and exfiltration channels
- Tool and MCP server adoption
- Non-impersonation and epistemic honesty
- Trust boundaries between agents

## Enforced

- Tool registry checks and the PCO hooks: see the [integration spoke](../integration/README.md) → Enforced. The
  registry validator checks the file, not tool use.
- Trifecta separation (§1), per-task privilege decomposition and secret brokering (§2), tool/MCP trust assessment
  (§4), non-impersonation (§5), epistemic honesty (§6), External Research (Bounded) and Multi-Agent Trust: human
  review against
  [security-threat-model.md](../ai_harness/rules/security-threat-model.md).

## Not enforced

- Use of an unregistered tool or MCP server: required by [lineage.md](../ai_harness/rules/lineage.md) →
  Registries and Versioning; no PCO check (see the integration spoke → Not enforced).
- Outbound allowlisting for runtime agents: required by security-threat-model.md → §3; no PCO check. The control
  plane that maintains the allowlists: target, not implemented.
- Outbound allowlisting for coding sessions: no sandbox and no `permissions.deny` in `settings.json`. Target, not
  implemented (outside §3's scope).
- Content source registration for High/Critical solutions and blocking of Prohibited sources: required by
  security-threat-model.md → §1; no PCO check.
- Secrets kept out of logs, telemetry, traces, run evidence and commits: required by security-threat-model.md → §2 and
  AGENTS.md → Security; no PCO check (no secret scanning).
- Data residency and access recertification: required by
  [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md) → Data Residency / Sovereignty /
  Cross-Border Transfer and Procurement & Access Lifecycle; no PCO check.

## Rules

- [security-threat-model.md](../ai_harness/rules/security-threat-model.md)
- [ENTERPRISE_OBLIGATIONS.md](../governance/ENTERPRISE_OBLIGATIONS.md) → Data Residency / Sovereignty /
  Cross-Border Transfer; Procurement & Access Lifecycle

## Canonical

### AgentFlayer

Malicious text in a Jira ticket or GitHub issue asks the agent for credential tokens and tells it to post them as a
public comment. It needs no code execution: the attack is carried entirely by crafted text, which is why §1 treats
every untrusted source as data.

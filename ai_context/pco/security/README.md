# Security & Safety (Spoke)
> DAMA mapping: Data Security → Agent Security & Safety

## Purpose

Prevent the agent harness from becoming an exfiltration channel, a privilege escalation path, or an uncontrolled actor, while still enabling useful work under explicit constraints.

## PCO Emphasis

- Policy: defines data classes, risk tiers, approvals, and disallowed actions
- Control plane: enforces entitlements, brokering, sandboxing, and output controls
- Observability: records security evidence, detects misuse, and supports forensics

## Scope (what this spoke governs)

### Confidentiality and access control

- Least-privilege tool access per role and per risk tier
- Secrets management and brokering (no secrets in prompts/logs)
- Project and environment boundaries

### Integrity and safe execution

- Sandbox policies for tools that can mutate state
- Prevention of unauthorised or unreviewed changes
- Supply-chain hygiene for dependencies and tool plugins

### Safety and misuse resistance

- Prompt injection and tool abuse prevention
- Data exfiltration controls (network egress, content filters)
- Human-in-the-loop approvals for high-risk actions

## Governance Controls (hub decisions)

### Data classification for agent-accessible inputs

Governance defines:
- Data classes (public/internal/confidential/restricted)
- Which classes may be exposed to which workflows and roles
- Redaction and minimisation requirements

### Entitlement model

Governance defines:
- Role × tool × environment entitlements
- Conditions for elevation (approvals, time-bounded access)
- Audit requirements for sensitive actions

### High-risk action policy

Governance defines what is disallowed vs allowed with approvals, including:
- Network egress and external calls
- Accessing credential stores
- Writing to production systems or privileged repositories

## Artefacts and Surfaces (examples)

- Data classification policy and handling rules
- Tool entitlement matrix (role × tool × environment × risk tier)
- Secret handling standard (brokering, rotation, logging restrictions)
- Prompt injection test suite and adversarial scenarios
- Approval and escalation playbooks (who approves what, with what evidence)

## Enforcement Points (where the control plane enforces)

### Pre-run

- Tool entitlements validated for the role and risk tier
- Sensitive tools require approval tokens or explicit approvals
- Environment sandbox selection based on risk

### In-run

- Secret brokering at execution time (no secrets in prompts)
- Network egress control (allowlist/denylist) where applicable
- Output controls and redaction for logs and evidence
- Tool call validation and policy checks (blocking)

### Post-run

- Security event logging and anomaly detection
- Evidence retention and access control enforcement
- Review triggers for suspected policy violations

## Evidence and Metrics (what observability measures)

- Tool denial events and attempted policy violations
- Prompt injection detection rate and failure cases
- Secrets exposure incidents (target: zero) and near misses
- Unauthorised egress attempts and blocked calls
- Approval volume, latency, and exception expiry compliance

## Enforcement Rules

Canonical enforcement: [security-threat-model.md](../ai_harness/rules/security-threat-model.md)

Covers: the **Lethal Trifecta** (sensitive data + untrusted content + external communication),
named attack patterns (AgentFlayer, image exfiltration, MCP supply chain), six required controls
(content source trust classification, per-task least-privilege decomposition, external destination
allowlisting, tool/MCP trust assessment, non-impersonation, epistemic honesty), the agent
behaviour failure taxonomy, and multi-agent trust boundaries.

## Common Failure Modes

- Convenience shortcuts: secrets passed through prompts or stored in logs
- Over-broad tool access granted "temporarily" and not revoked
- Unbounded network egress enabling accidental disclosure
- Treating injection defence as a one-time hardening exercise
- Processing untrusted external content in the same session as credential access
- Adopting MCP servers without trust assessment

## Maturity Model (pragmatic)

### Level 1: Least privilege by default

- Tool entitlements exist and are enforced
- Secret brokering enforced; raw secrets blocked from prompts and logs
- High-risk tools are blocked or require approval

### Level 2: Measured and tested

- Injection/misuse tests run as part of regression protection
- Security telemetry supports forensics and accountability
- Exceptions are time-bounded with evidence and expiry

### Level 3: Adaptive and resilient

- Risk-based routing automatically strengthens controls when needed
- Misuse detection drives policy updates and tool hardening
- Security posture improves over time without reducing useful throughput

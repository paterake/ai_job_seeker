# Tooling & Integration (Spoke)
> DAMA mapping: Data Integration & Interoperability → Tooling & Integration

## Purpose

Make tool integrations safe, consistent, and swappable without weakening governance, so the harness can evolve without per-project reinvention.

## PCO Emphasis

- Policy: defines which tools exist, how they may be used, and risk rules
- Control plane: brokers tool invocation through registries, schemas, and entitlements
- Observability: records tool usage, failure patterns, and risk signals

## Scope (what this spoke governs)

### Tool registry and standardisation

- Tool identity, ownership, and lifecycle
- Tool schemas (inputs/outputs) and validation
- Tool risk rating and allowed contexts

### Interoperability

- Standard connector patterns (auth, retries, timeouts)
- Protocol boundaries (tool interface remains stable while implementations change)
- Cross-agent consistency (tools behave the same regardless of which agent calls them)

### Dependency governance

- What third-party dependencies are permitted
- How new tools are introduced and reviewed
- How breaking changes are rolled out safely

### Model–harness co-evolution (governed risk)

Models learn harness-specific behaviour through post-training and usage feedback loops. Tool and harness interfaces can become implicit dependencies.

- Changing a tool interface or behaviour can degrade model performance even if the model is "capable" in theory
- A harness that is optimised for one model may not transfer cleanly to another without regression evidence
- Governance treats tool/harness changes as model-impact events, not only engineering changes

### Edit-tool contract (capability floor)

The edit-tool format is a capability floor, not a configuration detail. Models are post-trained and RL'd against a specific harness's edit dialect (e.g. unified diff vs. search-and-replace block). This calibration is implicit.

**The portability distinction**: governance transfers across harnesses; the edit-tool contract does not transfer automatically. A governance layer that is clean and portable does not guarantee that the tool format layer will work correctly on a different harness.

A mismatched edit dialect collapses success rate and creates retry loops regardless of governance quality. Recovery is complete when the expected format is restored — with no model change.

Practical implications:
- When switching harnesses, identify and validate the edit-tool format before declaring the migration complete
- When upgrading models, re-validate the edit-tool contract — forward compatibility is not guaranteed
- Unexplained success rate drops after a harness or model change should be diagnosed as a potential format mismatch before concluding model regression

## Governance Controls (hub decisions)

### Tool onboarding policy

Governance defines:
- Minimum requirements for a tool to be registered (schema, owner, risk rating)
- Review process for new tools (security, safety, operational impact)
- Deprecation and migration rules

Tool selection discipline — avoid near-duplicate tools; name the failure mode a tool prevents; treat MCP as supply-chain risk: [governance.md](../ai_harness/rules/governance.md).

### Entitlements and risk tiers

Governance defines:
- Which roles can invoke which tools
- Which tools are restricted to sandbox environments
- Which tools require explicit approvals and evidence

### Interoperability standards

Governance defines standard behaviour for:
- Authentication patterns (token, brokering, delegation)
- Error semantics and retry rules
- Observability requirements (telemetry fields anchor: [operations.md](../ai_harness/rules/operations.md))

### Tool/harness change control (model-impact events)

Governance defines:

- Which tool changes are treated as model-impacting (schema changes, argument semantics, output format, default behaviours)
- Regression protection coverage for such changes (contract tests + eval suites tied to representative workflows)
- Rollout approach (compatibility windows, dual-write/dual-read where applicable, canarying, rollback readiness)

## Artefacts and Surfaces (examples)

- Tool registry (tool ID, owner, schema version, risk rating)
- Connector standards (timeouts, retries, idempotency, error taxonomy)
- Entitlement matrix (role × tool × environment × risk tier)
- Deprecation policy (compatibility windows, migration guidance)
- Test harness for tools (contract tests, safety tests)

## Enforcement Rules

Canonical enforcement:
- Edit-tool contract, approval gates (effective oversight — competent overseer, no rubber-stamp — and segregation of duties at go-live, author ≠ approver), hooks vs guidance: [harness-tool-contract.md](../ai_harness/rules/harness-tool-contract.md)
- Tool selection discipline, MCP supply-chain risk, OSS preference: [governance.md](../ai_harness/rules/governance.md)
- Vendor procurement / TPRM (completed third-party risk assessment before adoption) and access recertification: [governance.md](../ai_harness/rules/governance.md)
- Telemetry contract for tool calls, tool registry requirements: [operations.md](../ai_harness/rules/operations.md)

## Enforcement Points (where the control plane enforces)

- Tool schemas are validated at invocation; unregistered tools are blocked
- Risk-tier entitlements checked before tool execution
- Model-impacting tool changes are flagged and require regression evidence before merge

## Evidence and Metrics (what observability measures)

- Tool usage distribution by risk tier and role
- Contract test pass rate and schema violation rate
- Tool failure rate, latency, timeout frequency
- Shadow-tool attempts
- Deprecation compliance (% calls to deprecated versions)

## Common Failure Modes

- Shadow tools: ad-hoc scripts bypassing governance and audit
- Schema drift: tools change without versioning, breaking reproducibility
- Vendor coupling: tool interfaces encode a specific agent/provider assumption
- Unbounded capabilities: "utility" tools that accidentally become exfil paths

## Maturity Model (pragmatic)

### Level 1: Registered and validated

- Tool registry exists with schemas
- Schema validation is enforced for high-impact tools
- Basic entitlement rules exist

### Level 2: Governed interoperability

- Standard connector patterns exist and are used consistently
- Deprecation and migration policy is real (compat windows, enforced rollout)
- Tool changes are regression-protected by contract tests

### Level 3: Swappable ecosystem

- Tools can be substituted without weakening policy or breaking workflows
- Risk-aware routing selects safer tools by default for high-risk tasks
- Telemetry-driven improvement reduces failures and cost over time

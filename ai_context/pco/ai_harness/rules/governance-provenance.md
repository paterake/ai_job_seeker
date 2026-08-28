---
description: Governance provenance and scope of validation — the PCO declares the use-case scope its governance is validated for, and every rule file records its evidence basis. Loaded when authoring or changing governance surfaces.
globs:
  - "ai_context/**/*.md"
  - "docs/**/*.md"
basis: operational-experience
---

# Governance Provenance and Scope of Validation

## Scope of Validation (Required)

- The PCO must declare the use-case scope its governance has been **validated** for. Extending
  governance to a use case outside that scope is an open workstream, not an inherited guarantee,
  and is unproven until re-validated against the new scope.
- **Current validated scope:** the runtime-governance axis — source trust, lineage, bounded
  execution, eval gates, kill switches, multi-agent trust — is validated through production use.
  The legal / procurement / organisational axis is a declared workstream, not yet independently
  validated.
- **Consequence:** without a stated validated scope, governance proven for one use case is
  silently assumed general — the mechanism that let one axis's governance be treated as
  enterprise-complete. A named scope converts a hidden overclaim into a credible boundary.

## Rule Provenance (Required)

- Every rule file records its evidence basis in frontmatter as `basis:`, one of:
  `primary-standard` · `incident` · `research-derived` · `operational-experience`.
- A `research-derived` rule is advisory until independently validated (see `agent-behavior.md`,
  External Research → Independent Validation); it must not be treated as authoritative on the
  strength of its own synthesis path alone.
- **Consequence:** a research-derived rule and a hard-won incident rule look identical without a
  basis tag; a reviewer cannot tell which to re-validate against primary sources. Provenance makes
  targeted re-validation possible instead of re-auditing the whole corpus.

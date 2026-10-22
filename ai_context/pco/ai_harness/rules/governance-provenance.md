---
description: Governance provenance and scope of validation — the PCO declares the use-case scope its governance is validated for, and every rule file records its evidence basis. Loaded when authoring or changing governance surfaces.
basis: operational-experience
spoke: assurance
paths:
  - "ai_context/**/*.md"
  - "docs/**/*.md"
---

> Governance narrative: [assurance spoke](../../assurance/README.md)

# Governance Provenance and Scope of Validation

## Scope of Validation (Required)

- The PCO must declare the use-case scope its governance has been **validated** for. Extending
  governance to a use case outside that scope is an open workstream, not an inherited guarantee,
  and is unproven until re-validated against the new scope.
- The declaration is dated, names each axis as validated or as a workstream, and states the evidence for each; it
  never implies coverage by omission (`publication.md` → Claim Scoping). The current declaration:
  [assurance spoke](../../assurance/README.md) → Declared Scope of Validation.
- **Consequence:** without a stated validated scope, governance proven for one use case is
  silently assumed general — the mechanism by which one axis's governance is treated as
  enterprise-complete. A named scope converts a hidden overclaim into a credible boundary.

## Rule Provenance (Required)

- Every rule file records its evidence basis in frontmatter as `basis:`, one of:
  `primary-standard` · `incident` · `research-derived` · `operational-experience`.
  The tag is the author's first-pass judgement; a reviewer may reclassify it.
- A `research-derived` rule is advisory until independently validated (see Independent Validation below); it must not be treated as authoritative on the
  strength of its own synthesis path alone.
- **Consequence:** a research-derived rule and a hard-won incident rule look identical without a
  basis tag; a reviewer cannot tell which to re-validate against primary sources. Provenance makes
  targeted re-validation possible instead of re-auditing the whole corpus.

## Independent Validation (of assistant-derived governance)

Governance content derived from LLM/assistant research is **advisory until validated by a source
that does not share the assistant's synthesis path** ([HUB.md](../../governance/HUB.md) → Independent review
pattern) — a human domain expert or a primary standard —
before it is treated as authoritative. Tag such content `basis: research-derived` (see
Rule Provenance above) and record the validation when it lands.

**Consequence:** an assistant stress-testing its own prior output shares that output's blind spots;
treating the result as an independent audit re-imports the same bias through every future
assistant-assisted governance change.

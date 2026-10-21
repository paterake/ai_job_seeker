# PRD — [Module Name]

> A PRD is a contract, not documentation about code. See authoring contract: `ai_context/pco/governance/DOCS_CONTRACT.md`

## Authoring Disciplines

These apply to every PRD. Structure below is directional — omit sections that do not apply; add sections the problem genuinely needs.

1. **Code-blind** — no file paths, no function names, no test names. Implementation detail belongs in `ARCHITECTURE.md`.
2. **Error Envelope is required** — state what callers get on failure. Omitting it means callers silently assume "raises exception" or "returns empty."
3. **Acceptance Criteria must be falsifiable** — "works correctly" is not a criterion. Each checkbox must name an input, an output, and a verifiable constraint.
4. **Performance targets require dates** — a target without a date is an aspiration. Write `[value] by [date]` or omit it entirely.

---

## Problem

What pain exists and why it is hard. State the forcing function: why must this be solved now,
and what happens if it is not?

## Solution

What the module does at a high level — one paragraph. Avoid implementation detail.

## Scope and Boundaries

**Owns:**
- [What this module is solely responsible for]

**Delegates:**
- [What this module calls into other modules or platform primitives to get — name the boundary]

**Out of scope:**
- [What is explicitly not this module's problem]

## Contracts

### Inputs

- Format and schema of inputs accepted
- Required fields and validation rules
- What is rejected at the boundary (and how — error vs. silent drop)

### Outputs

- Artefact types produced (files, events, API responses)
- Output schema and stability promise (stable / provisional / internal-only)
- Where outputs are written (path pattern or destination contract — no hardcoded paths)

### Error Envelope *(required)*

What callers can rely on when something goes wrong:
- Structured error shape
- Degrade modes (what partial output is returned on partial failure)
- What is never returned (e.g. silent empty)

## Requirements

### Functional (SHALL statements)

- The module SHALL ...
- The module SHALL NOT ...

### Non-Functional

State only what applies. Common axes: throughput, latency, reliability, scale limits, security
boundaries, data handling constraints. Performance targets require dates (see discipline 4 above).

For LLM-calling modules, execution bounds (caps, retries, degrade modes) are governed by
`ai_context/pco/ai_harness/rules/operations.md` — state the values here, not the rules.

## Acceptance Criteria *(required — falsifiable only)*

- [ ] Given [input], the module produces [output] meeting [schema/constraint]
- [ ] Given [failure condition], the module returns a structured error (not silent empty)
- [ ] [Cap] is enforced: inputs exceeding [limit] are rejected with [error type]

## Known Limitations

Explicit, honest, and bounded. What this module does not handle well and why.
If a limitation is planned to be addressed, reference the TODO item — do not embed a roadmap here.

## Related Modules

| Module | Relationship |
|--------|-------------|
| [name] | [delegates to / depended on by / shares boundary with] — describe the contract at the boundary |

# Intent — [Module Name]

> Holds only what the code cannot show: what must be true, why, and what was ruled out. It is code-blind and
> states no fact an agent could read from the code, config or `--help`.

## Authoring Disciplines

Omit sections that do not apply; add sections the problem genuinely needs.

1. **Code-blind** — no source file paths, function names or test names.
2. **Error Envelope is required** — state what callers get on failure. Omitting it means callers silently assume "raises exception" or "returns empty."
3. **Guarantees must be falsifiable** — "works correctly" is not a guarantee. Each names an input, an output, and a verifiable constraint.
4. **Performance targets require dates** — a target without a date is an aspiration. Write `[value] by [date]` or omit it entirely.

---

## Purpose

What pain exists and why it is hard. State the forcing function: why must this be solved now,
and what happens if it is not?

## Scope and Boundaries

**Owns:**
- [What this module is solely responsible for]

**Delegates:**
- [What this module calls into other modules or platform primitives to get — name the boundary contract]

**Non-goals:**
- [What is explicitly not this module's problem]

## Guarantees

### Inputs and Outputs

- What is accepted, and what is rejected at the boundary (and how — error vs. silent drop)
- Output stability promise (stable / provisional / internal-only)

### Error Envelope *(required)*

What callers can rely on when something goes wrong:
- Structured error shape
- Degrade modes (what partial output is returned on partial failure)
- What is never returned (e.g. silent empty)

### Acceptance *(falsifiable only)*

- [ ] Given [input], the module produces [output] meeting [schema/constraint]
- [ ] Given [failure condition], the module returns a structured error (not silent empty)
- [ ] [Cap] is enforced: inputs exceeding [limit] are rejected with [error type]

## Decisions

| Decision | Rejected alternatives | Why |
|---|---|---|
| [what was chosen] | [what was considered and ruled out] | [the reason the code cannot show] |

For LLM-calling modules, record why each execution bound (cap, retry, degrade mode) sits where it does; the
values themselves are config.

## Outside Constraints

Operator decisions, obligations, external systems and environment the code depends on but cannot show.

## Known Limitations

Explicit, honest, and bounded. What this module does not handle well and why.
If a limitation is planned to be addressed, reference the backlog item — do not embed a roadmap here.

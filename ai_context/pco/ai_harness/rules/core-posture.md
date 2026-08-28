---
description: Core posture — non-negotiable architectural pillars, PCO read-only rule, human approval requirement for governance changes, and memory file discipline. Loaded for all tasks.
globs:
  - "**/*"
basis: operational-experience
---

# Core Posture

1. **No direct project configuration**: Agents must rely on the platform rules, not local overrides.
2. **Blocking pillars**: Architectural pillars in this directory are non-negotiable.
3. **Audit trails**: All major actions must be tracked or recorded in the designated logs.
4. **PCO is read-only for downstream agents**: Agents running in consumer repos (any repo that syncs from the PCO) must never edit PCO rule files directly — not even to apply a valid fix.
5. **Human approval is required for governance changes**: Any change to platform governance surfaces (PCO rules/hooks/skills and governance contracts) must receive explicit human approval; agents must not self-approve or bypass review.

## Policy Injection Semantics (Required)

- Core posture, security posture, and other blocking governance pillars must be injected as non-conversational policy by the harness at session start (not as user-editable or conversational guidance).
- If policy packs are used, the run must record the policy pack identifiers/versions in run evidence.

## PCO Update Protocol (non-negotiable)

When an agent in a downstream project identifies a gap or error in a PCO rule:

1. **Stop.** Do not edit the PCO file.
2. **Surface the finding.** Produce a structured gap report stating: which file, what is missing or wrong, the specific consequence, and the suggested fix text.
3. **Escalate upstream.** Flag the gap to the human operator for a dedicated PCO session in `ai_agent_pco`.
4. The PCO session applies the fix, commits, and runs `/sync-pco` to propagate back.

**Consequence of violation:** a direct edit in a downstream copy creates silent divergence — the change lives only in that repo, is overwritten on the next sync without notice, and the authoritative source never receives the improvement. The gap recurs in every other consumer repo and in every future sync. This is exactly the drift condition the PCO architecture is designed to prevent.

## Memory Files

Memory files must contain **pointers and non-obvious gotchas only** — never copies of content that has an authoritative source elsewhere.

**Permitted:**
- Pointers to authoritative files
- Non-obvious gotchas not captured in any project file (silent failure modes, operational warnings, known traps)
- Active blockers and in-flight work (ephemeral — remove when resolved)

**Prohibited — write a pointer instead:**
- Module status or maturity levels → point to the project's maturity snapshot file
- Package descriptions or roles → point to the project's package map file
- Config values (model names, thresholds, chunk sizes) → point to the config file
- Architectural summaries or pipeline diagrams → point to the module's ARCHITECTURE.md
- Roadmap or phase status → point to the project's design decisions file

**The test**: does an authoritative file already own this information? If yes, write a pointer — never a copy. A copy without CI enforcement will drift; drifted memory produces wrong decisions in future sessions without any visible signal.

**Line discipline**: every line in a context or governance file must earn its place.
- Can you name the specific past failure or hard constraint that motivated this line?
- If the line encodes a preference rather than a constraint with a named consequence, remove it.
- Files under ~60 active lines are more effective than comprehensive style guides — shorter files mean each rule carries more weight in the model's context window.

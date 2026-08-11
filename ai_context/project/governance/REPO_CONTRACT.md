# REPO_CONTRACT — ai_job_seeker

Declares how this repo extends the platform without contradicting it. An AI agent that applies
to jobs on `ai_agent_core`.

## Additive Content Map

| Spoke | Additions |
|---|---|
| harness | Repo-specific application/submission skills and rules under `ai_context/project/ai_harness/` (none yet) |
| governance | Submission approval gate + PII/credential handling contract under `ai_context/project/governance/` (to author) |
| security | Trust-tier policy for job-posting sources, applied per `security-threat-model.md` (to author) |
| operations | Application workflow, budgets, and phase decomposition under `ai_context/project/operations/` (to author) |
| knowledge | System description (profile → match → draft → submit) under `ai_context/project/knowledge/` (to author) |

## Additive-Only Acknowledgment

This repo is additive-only relative to `ai_agent_pco`:

- No platform rule under `ai_context/pco/ai_harness/rules/` is overridden, negated, or contradicted by local guidance.
- Repo-specific content may strengthen constraints, but may not weaken or contradict the platform pillars.
- Repo-specific additions must live under `ai_context/project/` and map to a named platform spoke.

## Sensor Layer Declaration

- **LLMOps substrate: depends on `ai_agent_core`.** LLM calls, retrieval, telemetry, budgets,
  tracing, and circuit-breaking are brokered through the shared substrate — not reimplemented here.
  The dependency must be pinned explicitly (no floating latest), per `operations.md`.
- Computational sensors: inherited from `ai_agent_core` (telemetry events, budget guardrails,
  run manifests). Repo-specific behavioural sensors (non-impersonation check, no-fabrication
  check on generated CVs) are to be authored and wired as hooks.

## Guide/Sensor Coherence Map

| Platform pillar | Primary guide | Primary sensor |
|---|---|---|
| Safety / injection posture (trifecta) | `ai_context/pco/ai_harness/rules/security-threat-model.md` | Source trust-tier gate on posting ingestion (to author) |
| Non-impersonation | `security-threat-model.md` §5 + project `ASSISTANTS.md` | Recruiter-message impersonation check (to author) |
| No fabricated experience | Project `ASSISTANTS.md` non-negotiables | No-fabrication check on generated CVs (to author) |
| Outbound submission control | Submission approval gate (to author) | Approval-record hook before send (to wire) |
| Bounded LLM execution | `ai_context/pco/ai_harness/rules/operations.md` | `ai_agent_core` budget + circuit breaker |

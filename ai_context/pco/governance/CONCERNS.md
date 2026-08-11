# Concern Profiles (Why the Agent Context Differs by Repo)

## Why This Exists

The harness wiring is the same everywhere (the same `ai_harness` paths and the same `.claude/.qwen/.trae` symlink pattern), but the **dominant risk surface** differs by repo.

If the context layer does not reflect those differences, assistants will behave like generic tools:
- they will over-focus on irrelevant constraints
- they will miss the real failure modes for the repo
- they will drift the repo away from its intended operating model

This file explains the “why” and defines the concern profiles that shape what belongs in each repo’s `ai_context/`.

## The Three Primary Concern Profiles

### 1) LLM Systems (ai_platform)

**Primary risk:** silent quality regressions and uncontrolled execution.

**Typical failure modes:**
- unbounded loops (cost blow-ups)
- missing eval discipline (no proof of correctness)
- retrieval correctness issues (hallucinations caused by poor provenance or weak gates)
- missing tracing / inability to debug runs after the fact

**Context emphasis:**
- operational discipline (timeouts, budgets, degrade modes)
- retrieval correctness (hybrid search, provenance, quality gates)
- evaluation and regression protection

**Concrete implementation reference:** `ai_platform/ai_context`

### 2) Publishing Systems (ai_publish)

**Primary risk:** information leakage and narrative drift from the real engineering record.

**Typical failure modes:**
- accidental disclosure (internal paths, client identifiers, programme names)
- “evidence theatre” (publishing claims not supported by real run artefacts)
- duplication and drift across packs (multiple sources of truth)

**Context emphasis:**
- publication safety gates
- evidence discipline (real run IDs, dated proof points)
- workflow governance (what is human-owned vs assistant-owned)

**Concrete implementation reference:** `ai_publish/ai_context`

### 3) Data and Document Engineering (elt_lake)

**Primary risk:** incorrect transformation and irreproducible results across mixed workloads.

**Typical failure modes:**
- inconsistent formatting/standards across generated artefacts
- transform logic that is not deterministic or not repeatable
- schema drift and silent changes in outputs

**Context emphasis:**
- deterministic transformations and validation
- structured outputs and formatting rules
- safe automation patterns (idempotency, replay, audit)

**Concrete implementation reference:** `elt_lake/ai_context`

### 4) Platform Governance (ai_agent_pco)

**Primary risk:** governance drift — rules, structure, or contracts diverge across the PCO and its consumer repos without anyone noticing.

**Typical failure modes:**
- a fix applied directly to a consumer repo's `pco/` content instead of the PCO (overwritten on next sync, never propagates to other repos)
- PCO-specific skills or docs accidentally synced into consumer repos (consumers see irrelevant or misleading tooling)
- `ai_context/pco/` and `ai_context/project/` boundaries blurred (platform artifact contaminated with repo-specific content)
- CONTRACT.md or governance docs describing the old structure after a restructure (agents navigate from stale descriptions)
- Skills wiring (`distill_harness.py wire`) not re-run after adding or moving a skill (`.claude/skills/` has stale symlinks)

**Context emphasis:**
- sync boundary discipline (what belongs in `pco/` vs `project/`)
- PCO update protocol (surface gaps upstream; do not edit consumer `pco/` files directly)
- distill_harness.py correctness (the sync and wire commands are the enforcement mechanism)
- governance doc currency (CONTRACT.md, CONCERNS.md, ANTI_DRIFT.md must reflect the current structure)

**Concrete implementation reference:** `ai_agent_pco/ai_context/project/`

---

## What ai_agent_pco Provides (the Superset)

`ai_agent_pco/ai_context/pco/` provides:
- a shared harness substrate (`pco/ai_harness/`)
- a minimal cross-cutting ruleset (governance, operations discipline, context sync)
- syncing tooling (`distill_harness.py`) that can *plan*, *validate*, and *wire* changes against a target repo before writing

It is not intended to erase repo differences. It exists to centralise the reusable substrate and make variation intentional rather than accidental.


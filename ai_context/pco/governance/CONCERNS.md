# Concern Profiles (Why the Agent Context Differs by Repo)

## Why This Exists

The harness wiring is the same everywhere (the same `ai_harness` paths and the same agent wiring pattern), but the **dominant risk surface** differs by repo.

If the context layer does not reflect those differences, assistants will behave like generic tools:
- they will over-focus on irrelevant constraints
- they will miss the real failure modes for the repo
- they will drift the repo away from its intended operating model

This file explains the “why” and defines the concern profiles that shape what a repo puts in its `ai_context/project/`.
A repo names its profile, and the failure modes specific to it, in its own project layer.

## Primary Concern Profiles

### 1) LLM Systems

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

### 2) Publishing Systems

**Primary risk:** information leakage and narrative drift from the real engineering record.

**Typical failure modes:**
- accidental disclosure (internal paths, client identifiers, programme names)
- “evidence theatre” (publishing claims not supported by real run artefacts)
- duplication and drift across packs (multiple sources of truth)

**Context emphasis:**
- publication safety gates
- evidence discipline (real run IDs, dated proof points)
- workflow governance (what is human-owned vs assistant-owned)

### 3) Data and Document Engineering

**Primary risk:** incorrect transformation and irreproducible results across mixed workloads.

**Typical failure modes:**
- inconsistent formatting/standards across generated artefacts
- transform logic that is not deterministic or not repeatable
- schema drift and silent changes in outputs

**Context emphasis:**
- deterministic transformations and validation
- structured outputs and formatting rules
- safe automation patterns (idempotency, replay, audit)

### 4) Platform Governance

**Primary risk:** governance drift — rules, structure or contracts diverge across the governing repo and the
repos it governs without anyone noticing.

**Context emphasis:**
- sync boundary discipline (what is platform-owned vs repo-owned)
- gaps surfaced upstream, never patched locally
- governance doc currency after a restructure

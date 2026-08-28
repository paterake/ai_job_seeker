---
description: Compliance lifecycle — data residency, data-subject rights and automated-decision safeguards, IP/output ownership, and records retention/legal hold. Loaded when declaring data sources, model endpoints, or AI-solution specs.
globs:
  - "**/*.yaml"
  - "**/*.yml"
  - "**/*.md"
  - "**/*.py"
basis: research-derived
---

# Compliance Lifecycle Rules

**Status:** authored from an internal adversarial coverage test (2026-08-27). Wording is advisory
until Legal/DPO sign-off (see `agent-behavior.md` → Independent Validation). These rules require
solutions to **declare and control** an obligation; they do not state the legal answer.

## Data Residency / Sovereignty / Cross-Border Transfer

- Every data source and every model endpoint must declare its processing region and permitted
  transfer scope (including sub-processors). A source or model whose region is undeclared or
  outside policy is non-conformant and must not be used in a governed run.
- **Consequence:** undeclared residency is an unbounded sovereignty/transfer exposure that every
  runtime control is blind to — trust class and lawful basis do not encode where processing happens.

## Data-Subject Rights & Automated-Decision Safeguards

- A solution whose risk tier is High/Critical and whose decisions affect individuals must declare:
  how a decision is explained, how it is contested, how a human reviews it, and how data-subject
  access requests over prompt/output logs are served.
- **Consequence:** an unappealable automated decision over personal data is a direct regulatory
  breach; no eval gate detects the absence of an explanation or contest path.

## IP / Output Ownership & License Contamination

- Every solution declares ownership of its generated output and the license posture of the sources
  feeding generation; a source whose license forbids the intended use is non-conformant.
- **Consequence:** license bleed and contested output ownership are legal liabilities the runtime
  layer cannot see — provenance without license posture proves origin but not the right to use it.

## Records Retention & Legal Hold

- Run evidence and logs must carry a retention schedule and a legal-hold override that suspends
  deletion when invoked. Append-only is a durability property, not a retention policy.
- **Consequence:** over-retention and under-retention are both compliance failures; "keep everything
  forever" breaches minimisation, and unscheduled deletion destroys records under legal hold.

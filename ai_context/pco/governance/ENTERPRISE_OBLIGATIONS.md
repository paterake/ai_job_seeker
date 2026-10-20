# Enterprise Obligations

> Read on demand — not an auto-loaded rule. These obligations apply when a solution is taken to
> enterprise production (High/Critical risk tier, personal data, external vendors, go-live), not to
> routine coding-agent work.

## Compliance Lifecycle

**Status:** wording is advisory until Legal/DPO sign-off (see `governance-provenance.md` → Independent Validation). These rules require
solutions to **declare and control** an obligation; they do not state the legal answer.

### Data Residency / Sovereignty / Cross-Border Transfer

- Every data source and every model endpoint must declare its processing region and permitted
  transfer scope (including sub-processors). A source or model whose region is undeclared or
  outside policy is non-conformant and must not be used in a governed run.
- **Consequence:** undeclared residency is an unbounded sovereignty/transfer exposure that every
  runtime control is blind to — trust class and lawful basis do not encode where processing happens.

### Data-Subject Rights & Automated-Decision Safeguards

- A solution whose risk tier is High/Critical and whose decisions affect individuals must declare:
  how a decision is explained, how it is contested, how a human reviews it, and how data-subject
  access requests over prompt/output logs are served.
- **Consequence:** an unappealable automated decision over personal data is a direct regulatory
  breach; no eval gate detects the absence of an explanation or contest path.

### IP / Output Ownership & License Contamination

- Every solution declares ownership of its generated output and the license posture of the sources
  feeding generation; a source whose license forbids the intended use is non-conformant.
- **Consequence:** license bleed and contested output ownership are legal liabilities the runtime
  layer cannot see — provenance without license posture proves origin but not the right to use it.

### Records Retention & Legal Hold

- Run evidence and logs must carry a retention schedule and a legal-hold override that suspends
  deletion when invoked. Append-only is a durability property, not a retention policy.
- **Consequence:** over-retention and under-retention are both compliance failures; "keep everything
  forever" breaches minimisation, and unscheduled deletion destroys records under legal hold.

## Procurement & Access Lifecycle

- **Vendor procurement / TPRM.** A model or tool vendor must carry a completed third-party risk
  assessment covering data handling, contractual liability, and exit terms before adoption —
  `vendor_assessment_ref` is a pointer to that completed process, not a substitute for it.
  **Consequence:** a vendor field with no assessment behind it is due-diligence theatre; the
  liability and exit exposure it was meant to control is unmanaged.
- **Access recertification.** Human and agent access to a solution is provisioned by named identity
  and recertified on a schedule; joiner/mover/leaver changes are applied. **Consequence:** access
  granted once and never reviewed is how orphaned privilege accumulates across hundreds of
  solutions — the standing exposure no runtime control detects.

## Regulatory Notification & FinOps

- **Regulatory notification.** The Incident Capture rule (`assurance.md`) is extended: an incident
  that crosses an external-notification threshold must record who notifies which authority, by when
  (the applicable statutory clock), and the notification sent — as run evidence. **Consequence:**
  internal incident capture with no notification trigger silently misses a statutory clock; the
  breach is contained technically but unreported legally.
- **FinOps chargeback & budget authority.** Beyond per-run cost, each solution/pod declares budget
  ownership, chargeback attribution, and a cost-dispute path. **Consequence:** cost with no named
  owner is cost nobody controls; federated spend fragments and no one is accountable for the total.

## Go-Live Approval Gates

These extend the Approval Gates in `harness-tool-contract.md`.

- **Effective oversight (not nominal).** For a gate on a High/Critical solution, the named overseer
  must be competent for that risk tier and the gate must be designed to resist automation bias — the
  approval record captures a substantive decision, not a rubber-stamp. **Consequence:** a signature
  box is not oversight; nominal sign-off fails the AI Act's effectiveness bar while appearing compliant.
- **Segregation of duties at go-live.** At the go-live gate, the approver must not be the author of
  the change; author ≠ approver is enforced, not advisory. **Consequence:** self-approval at go-live
  defeats the conformance gate — the one control the gate exists to provide is bypassed by one person.

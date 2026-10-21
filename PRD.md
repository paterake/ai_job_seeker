# PRD: ai_job_seeker

> A contract, not a description of code. How it is built: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Problem

A graduate candidate is searching across several UK job boards. Each board returns hundreds of
postings, many duplicated across boards, many impossible for this candidate (foreign-language,
engineering, senior or overseas roles), and many already applied for. Sorting them by hand every
day takes hours and misses roles that fit the candidate's actual strengths. Postings are untrusted
web content and the candidate's CV is personal data. Anything that leaves the machine on the
candidate's behalf does real and lasting reputational harm if it is wrong.

## Solution

A local pipeline turns a CV into a reviewable structured profile and pulls live postings into
normalised, deduplicated pools. It removes hard-blocked and already-applied roles, then ranks what
is left into two independent cohorts in a single human-readable shortlist. Every score carries
evidence. The default scoring is deterministic and needs no model. An optional LLM judge adds a
second score, and planned later stages draft tailored applications. Nothing is ever sent without
explicit human approval.

## Scope and Boundaries

**Owns:**
- Profile extraction from a CV document, and validation of the profile.
- Job-board acquisition, normalisation to one listing schema, cross-source dedupe and the age filter.
- The hard-block exclusion policy, the deterministic scorer, cohort ranking and shortlist rendering (HTML, Markdown, JSON).
- The local applied-jobs store and the filter that removes applied roles from later runs.
- The prompt, output schema and result validation of the phase-2 LLM judge.
- The output folder convention (stable aliases, timestamped archive, 7-day retention).

**Delegates:**
- To the shared LLM substrate (`ai_agent_core`): choosing the backend mode (agent, local or cloud),
  provider wiring, JSON generation, cloud credential resolution, request timeouts and retries,
  and the agent-handoff signal. This repo does not reimplement any of these.
- To the job boards: search semantics and data quality.
- To the human operator: reviewing the profile, deciding where to apply, and every outbound action.
- To the applied-jobs skill (browser layer): syncing the external tracker spreadsheet.

**Out of scope:**
- Submitting applications, emailing recruiters, or any automated outbound communication.
- Logging in to job sites, or storing credentials for them.
- Serving more than one candidate at a time. The pipeline runs against one profile per run.

## Contracts

### Inputs

- **CV document** (word-processor format) for profile extraction. Extraction is deterministic
  and keeps only text present in the document. Target preferences (roles, locations, salary,
  contract types) are left empty and marked for human review.
- **Profile** (structured YAML). Required sections: identity, target, summary, skills, experience.
  A profile that is missing, unreadable, not a mapping, or missing any required section is
  rejected with an error. A partial profile is never used.
- **Search configuration**: the enabled sources, their endpoints, limits, the maximum posting age
  and the dedupe fields. A missing source endpoint, a non-positive maximum age, or malformed YAML
  is rejected with an error.
- **Exclusion policy**: phrase and token lists plus a geographic allow/deny list. A missing or
  unreadable policy file means no exclusions are applied (see Known Limitations).
- **Listing pools**: JSON lists in the normalised listing schema. Rows that are not objects, or
  that carry an unknown source, are skipped with a warning. Unknown keys are ignored.
- **Search terms and location** for live ingest.

### Outputs

- **Profile YAML** (PII, gitignored). It is never overwritten unless the operator explicitly asks.
- **Listing pool JSON**: normalised listings without the raw source payload. *Provisional* schema.
- **Ranked shortlist** in JSON, Markdown and self-contained HTML. Each entry carries the phase-1
  score, phase-1 evidence lines, an optional phase-2 score and rationale, fabricated-claim flags,
  a final score and a rank position (1..N, no gaps; ties broken by source identifier). The dual-cohort JSON is an object with one list per cohort plus
  a generation timestamp. *Provisional* schema.
- **Applied-jobs store**: a list of records, each with at least a title and an applied-on date.
- Every written artefact goes to a timestamped archive copy and is also copied to a stable
  "latest" alias. Archive copies older than 7 days are pruned whenever an artefact is written to
  the same folder.

### Error Envelope

- Each command returns a process exit code: 0 means success; 1 means invalid input, config, or
  source failure; 2 means the operator must act (agent handoff required, LLM substrate missing,
  backend configuration invalid, a profile overwrite refused, or a missing applied-jobs sub-action).
  Errors go to stderr as one-line messages with a remediation hint.
- **Source credentials missing**: that source is skipped and the skip is reported. The other
  sources still run.
- **Source HTTP failure** (any non-success status): the whole ingest command fails. There is no
  partial output and no retry.
- **Phase-2 judge returns malformed output**: it is rejected as a generation error and the ranking
  command fails. Partial phase-2 data is never merged onto phase-1 scores.
- **Phase-2 needs the coding agent to author the answer**: the prompt and an empty result file are
  written to the system temp directory, handoff instructions are printed, and the command exits 2.
- **Known silent-empty gap**: if every listing is hard-blocked or already applied, the ranking
  command still exits 0 with an empty shortlist (see Known Limitations).

## Requirements

### Functional

- The system SHALL normalise every source into one listing schema before any other stage reads it.
  Posting text SHALL be carried as data and never interpreted as instructions.
- The system SHALL dedupe listings across sources on normalised (title, company). The first
  listing seen wins.
- The system SHALL drop listings with an empty title or company, and listings older than the
  configured maximum age.
- Before scoring, the system SHALL remove listings that match the hard-block policy (non-English
  language requirement, engineering title, senior or executive title, construction sector,
  specialist-subject teaching mismatch, or a location outside the allow-list that matches a
  foreign city or country). Each removal SHALL be reported by reason.
- Before scoring, the system SHALL remove listings that match the applied-jobs store, either on
  exact (title, company) or on title alone for records that have no company.
- In dual-cohort mode the system SHALL rank two cohorts independently, each with its own cap and
  its own listing pool:
  - **Cohort A (marketing and communications)** SHALL be ranked only against its own pool. When
    the operator supplies a dedicated pool for it, it SHALL use the base scorer with no cohort
    bonus, so its ordering reproduces a single-cohort run on the same pool.
  - **Cohort B (history, research and academic)** SHALL add a three-band keyword bonus (at most
    +22) and widen role matching with the cohort's keywords. It SHALL exclude any role already
    present in Cohort A and promote the next-best candidates, so the two sections never repeat a role.
- Every score SHALL come with evidence lines that explain each component that contributed.
- The system SHALL NOT fabricate: profile values come from the CV or from explicit operator edits.
  Generated drafts (when built) SHALL trace every claim to the profile.
- The system SHALL NOT send, submit or email anything on the candidate's behalf. Any future
  outbound packet SHALL require an explicit human approval record.
- The system SHALL NOT present itself as the candidate or as a human in any recruiter-facing text.
- Code that reads untrusted postings SHALL NOT share an LLM instruction context with credentials
  or with any submission channel. In LLM prompts, profile data and listing data SHALL sit in
  separately labelled data blocks after the instructions.
- The system SHALL keep PII (profile, outputs, applied store) and secrets out of version control.
  Secrets SHALL be read from an external per-service file location first and from environment
  variables second, and SHALL never appear in error messages.
- The default backend SHALL be agent mode (no model call). Cloud mode SHALL be opt-in only, and
  SHALL require both a provider and a model.

### Non-Functional

- **Determinism.** Phase-1 ranking is deterministic when all of the following are the same: the
  listing pools, their order, the profile, the exclusion policy, the maximum-age setting, the
  cohort options, and the calendar date the run is scored on (posting freshness is measured
  against the current clock). Ties break on the listing's source identifier. Live ingest is not
  deterministic, because board results change. Phase-2 scores are not deterministic.
- **Execution bounds, as implemented:**
  - Each board request has a 30-second timeout.
  - Board pagination is capped (configured page counts, and a fixed three pages for one board).
  - Phase-2 is a single model call per ranking pass. Each listing description in the prompt is
    cut to 800 characters.
  - Model timeouts and output-token caps come from the LLM substrate's defaults.
- **Execution bounds not implemented (known gaps):**
  - No retry or backoff on board requests.
  - No cap on how many listings go into one phase-2 prompt.
  - No run identifier, telemetry event, lineage manifest or cost budget is emitted by this repo.
  - No input-size caps on listing pools.
  - Whether the substrate retries on the local backend is unverified. On the cloud backend its
    default is a single attempt.
- **Hardware.** The reference machine has 8 GB of RAM and runs agent mode only. This is operator
  guidance. Nothing in the code enforces it.

## Acceptance Criteria

**Profile**
- [ ] Given a CV document, extraction writes a profile with identity, summary, skills, experience
  and education taken from the document text, leaves target roles, locations, salary and contract
  types empty, and lists them as required-review fields.
- [ ] Given an existing profile and no explicit overwrite request, extraction refuses and exits non-zero.
- [ ] Given a profile missing any required section, every command that loads it exits 1 and names
  the missing sections.

**Ingest**
- [ ] Given offline (dry-run) mode, ingest returns synthetic listings for each enabled source, with
  case/whitespace duplicates collapsed, and needs no credentials.
- [ ] Given a source whose credentials are missing, ingest reports that source as skipped and
  still returns the other sources' listings.
- [ ] Given two listings that differ only in case or whitespace of title and company, exactly one survives.
- [ ] Given a listing older than the configured maximum age, it does not appear in the output.
- [ ] Written pool JSON never contains the raw source payload.

**Match (dual cohort)**
- [ ] Given a listing whose title contains "engineer", it never appears in any shortlist.
- [ ] Given an applied-jobs record with an empty company, every listing with that title is removed from both cohorts.
- [ ] Given a role that appears in Cohort A's top N, it does not appear in Cohort B.
- [ ] Given the same pool, profile, policy and date, two runs produce the same Cohort A order.
- [ ] Each cohort contains at most its configured cap, ranked 1..N with no gaps.
- [ ] In agent mode no model is called and every phase-2 field is empty.
- [ ] When phase-2 needs the coding agent, the command exits 2 after printing handoff instructions.

**Draft**: not built. The placeholder reports the backend mode and the CV location, then exits 0.
Acceptance criteria are to be written when the stage is designed.

**Packet**: not built. Acceptance requires an approval record before anything leaves the machine.

**Applied-jobs tracking**
- [ ] Adding a record whose (title, company) already exists leaves the store unchanged and reports it as existing.
- [ ] Adding records by cohort and rank position from a shortlist JSON copies title, company, link and source from that entry.
- [ ] The next ranking run removes every stored role and reports how many were removed per cohort.

## Known Limitations

- **Silent empty shortlist.** If every listing is filtered out, ranking exits 0 with empty
  sections. This breaks the platform's "no silent empty" degrade rule.
- **Synthetic fallback.** In dual-cohort mode, if one cohort is given no pool, synthetic sample
  listings are used for it. The fallback is printed but does not fail the run.
- **Exclusion policy fails open.** A missing or malformed policy file applies no exclusions and
  gives no error.
- **Salary component never fires on extracted profiles.** The scorer reads an expected-minimum
  salary key that extraction does not write (extraction writes a differently named key).
- **Search terms.** One board ignores search terms entirely and returns location-filtered results
  only. Comma-separated terms are joined into a single all-words query, so multi-concept searches
  narrow rather than widen.
- **Inconsistent key normalisation.** The applied-jobs filter and the pool merge lowercase and
  trim, but do not collapse internal whitespace (ingest dedupe does). The Cohort B exclusion of
  Cohort A roles is case-sensitive.
- **The phase-2 prompt includes the whole profile, contact section included.** In cloud mode
  this PII leaves the machine. The prompt asks the model not to echo contact details, but nothing
  enforces it.
- **No eval harness for phase-2**, and no behavioural sensors for non-impersonation or
  no-fabrication (both are planned in the repo contract).
- **Every command needs the LLM substrate installed.** The command-line entry point imports it at
  load time, so stages that make no model call (profile, ingest) still depend on it.

## Related Modules

| Module | Relationship |
|---|---|
| `ai_agent_core` (pinned git dependency) | This repo delegates to it for backend-mode resolution, JSON generation, cloud endpoints and keys, and the agent-handoff signal. It is consumed as a git dependency pinned to release tag `v0.11.0` (`==0.11.0`). |
| Job boards (three public APIs) | Upstream data sources. Their content is untrusted. |
| Applied-jobs skill and the external tracker sheet | Downstream. The skill writes the local store through the CLI and mirrors rows to the sheet through the browser. |

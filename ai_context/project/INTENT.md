# Intent — ai_job_seeker

> Holds only what the code cannot show: what must be true, why, and what was ruled out. Shape:
> [INTENT_TEMPLATE.md](../pco/templates/INTENT_TEMPLATE.md).

## Purpose

A graduate candidate is searching across several UK job boards. Each board returns hundreds of postings, many
duplicated across boards, many impossible for this candidate (foreign-language, engineering, senior or overseas
roles), and many already applied for. Sorting them by hand every day takes hours and misses roles that fit the
candidate's actual strengths. Postings are untrusted web content and the candidate's CV is personal data.
Anything that leaves the machine on the candidate's behalf does real and lasting reputational harm if it is wrong.

A local pipeline turns a CV into a reviewable structured profile and pulls live postings into normalised,
deduplicated pools. It removes hard-blocked and already-applied roles, then ranks what is left into two
independent cohorts in a single human-readable shortlist. Every score carries evidence. The default scoring is
deterministic and needs no model. An optional LLM judge adds a second score, and planned later stages (Draft,
Packet) draft tailored applications. Nothing is ever sent without explicit human approval.

A second, separate component serves a different candidate: a senior contractor looking for contract roles in data and AI,
ideally outside IR35, remote or London. It reuses the same ingest and shares none of the graduate pipeline's
scoring, exclusions or profile, so changing one candidate's search cannot change the other's results.

## Scope and Boundaries

**Owns:**
- Profile extraction from a CV document, and validation of the profile.
- Job-board acquisition, normalisation to one listing schema, cross-source dedupe and the age filter.
- The hard-block exclusion policy, the deterministic scorer, cohort ranking and shortlist rendering (HTML,
  Markdown, JSON).
- The local applied-jobs store and the filter that removes applied roles from later runs.
- The prompt, output schema and result validation of the phase-2 LLM judge.
- The output folder convention (stable aliases, timestamped archive, 7-day retention).
- The contract-search component (`implementation/contract_search`): its own config-driven scorer (contract, IR35,
  remote and location signals read from advert text), profile, search config, opt-in Apify sources (CWJobs,
  JobServe) and shortlist. It imports the
  ingest layer unchanged and nothing from the graduate pipeline's match package.

**Delegates:**
- To the shared LLM substrate (`ai_agent_core`): choosing the backend mode (agent, local or cloud), provider
  wiring, JSON generation, cloud credential resolution, request timeouts and retries, and the agent-handoff
  signal. This repo does not reimplement any of these.
- To the job boards (three public APIs, untrusted upstream sources): search semantics and data quality.
- To the human operator: reviewing the profile, deciding where to apply, and every outbound action.
- To the applied-jobs skill (browser layer): syncing the external tracker spreadsheet.

**Non-goals:**
- Submitting applications, emailing recruiters, or any automated outbound communication.
- Logging in to job sites, or storing credentials for them.
- Serving more than one candidate in one run. Each component runs against one profile per run; the graduate
  pipeline and the contract search are separate components with separate profiles and outputs.
- Inferring IR35 status. The contract search reports it only when the advert states it.

## Guarantees

### Inputs and Outputs

Inputs:
- **CV document** (word-processor format) for profile extraction. Extraction is deterministic and keeps only text
  present in the document. Target preferences (roles, locations, salary, contract types) are left empty and
  marked for human review.
- **Profile** (structured YAML). Required sections: identity, target, summary, skills, experience. A profile that
  is missing, unreadable, not a mapping, or missing any required section is rejected with an error. A partial
  profile is never used.
- **Search configuration**: the enabled sources, their endpoints, limits, the maximum posting age and the dedupe
  fields. A missing source endpoint, a non-positive maximum age, or malformed YAML is rejected with an error.
- **Exclusion policy**: phrase and token lists plus a geographic allow/deny list. A missing or unreadable policy
  file means no exclusions are applied (see Known Limitations).
- **Listing pools**: JSON lists in the normalised listing schema. Rows that are not objects, or that carry an
  unknown source, are skipped with a warning. Unknown keys are ignored.
- **Search terms and location** for live ingest.

Outputs:
- **Profile YAML** (PII, gitignored, owner-only file permissions). It is never overwritten unless the operator
  explicitly asks.
- **Listing pool JSON**: normalised listings without the raw source payload. *Provisional* schema.
- **Ranked shortlist** in JSON, Markdown and self-contained HTML. Each entry carries the phase-1 score, phase-1
  evidence lines, an optional phase-2 score and rationale, fabricated-claim flags, a final score and a rank
  position (1..N, no gaps; ties broken by source identifier). The dual-cohort JSON is an object with one list per
  cohort plus a generation timestamp. *Provisional* schema. All listing text in the HTML is escaped, and its
  links open with no opener and no follow.
- **Applied-jobs store**: a list of records, each with at least a title and an applied-on date. It is written in
  place, with no archive copy.
- Every other written artefact goes to a timestamped archive copy beside its target and is also copied to a
  stable "latest" alias. Archive copies older than 7 days are pruned whenever an artefact is written to the same
  folder. All artefacts from one match run share one timestamp.

Behaviour:
- Every source is normalised into one listing schema before any other stage reads it. Posting text is carried as
  data and never interpreted as instructions.
- Ingest and match are separate processes connected only by JSON files. Match never calls the boards.
- Listings are deduped across sources on normalised (title, company); the first listing seen wins. Listings with
  an empty title or company, or older than the configured maximum age, are dropped.
- Before scoring, listings that match the applied-jobs store are removed, on exact (title, company) or on title
  alone for records that have no company. Each run reports how many were removed per cohort.
- Before scoring, listings that match the hard-block policy are removed (non-English language requirement,
  engineering title, senior or executive title, construction sector, specialist-subject teaching mismatch, or a
  location outside the allow-list that matches a foreign city or country). Each removal is reported by reason.
- In dual-cohort mode the two cohorts are ranked independently, each with its own cap and its own listing pool:
  - **Cohort A (marketing and communications)** is ranked only against its own pool. When the operator supplies
    a dedicated pool for it, it uses the base scorer with no cohort bonus, so its ordering reproduces a
    single-cohort run on the same pool.
  - **Cohort B (history, research and academic)** adds a three-band keyword bonus (at most +22) and widens role
    matching with the cohort's keywords. It excludes any role already present in Cohort A and promotes the
    next-best candidates, so the two sections never repeat a role.
- Every score comes with evidence lines that explain each component that contributed.
- With no phase-2 result for a listing, its final score is its phase-1 score. Fabricated-claim flags are shown
  but never change the ranking. Phase-2 output is advisory and gates nothing until a versioned eval set and
  threshold exist.
- No fabrication: profile values come from the CV or from explicit operator edits. Generated drafts (when built)
  trace every claim to the profile.
- Nothing is sent, submitted or emailed on the candidate's behalf. Any future outbound packet requires an
  explicit human approval record.
- No recruiter-facing text presents the system as the candidate or as a human.
- Code that reads untrusted postings does not share an LLM instruction context with credentials or with any
  submission channel. In the phase-2 prompt the instructions come first and are the only place instructions
  appear; profile data and listing data follow in separately labelled data blocks, never interleaved.
- PII (profile, outputs, applied store) and secrets stay out of version control. Secrets are read from an
  external per-service file location first and from environment variables second, and never appear in error
  messages.
- The default backend is agent mode (no model call). Cloud mode is opt-in only and requires both a provider and
  a model.
- **Determinism.** Phase-1 ranking is deterministic when all of the following are the same: the listing pools,
  their order, the profile, the exclusion policy, the maximum-age setting, the cohort options, and the calendar
  date the run is scored on (posting freshness is measured against the current clock). Live ingest is not
  deterministic, because board results change. Phase-2 scores are not deterministic.

### Error Envelope

- Each command returns a process exit code: 0 means success; 1 means invalid input, config, or source failure;
  2 means the operator must act (agent handoff required, LLM substrate missing, backend configuration invalid, a
  profile overwrite refused, or a missing applied-jobs sub-action). Errors go to stderr as one-line messages with
  a remediation hint.
- **Source credentials missing**: that source is skipped and the skip is reported. The other sources still run.
- **Source HTTP failure** (any non-success status): the whole ingest command fails. There is no partial output
  and no retry. A row that fails normalisation is dropped without a report.
- **Phase-2 judge returns malformed output** (missing keys, a score outside 0–100, other than exactly three
  rationale bullets, flags not a list): it is rejected as a generation error and the ranking command fails.
  Partial phase-2 data is never merged onto phase-1 scores.
- **Phase-2 needs the coding agent to author the answer**: the prompt and an empty result file are written to
  the system temp directory, handoff instructions are printed, and the command exits 2. Nothing is swallowed.
- **Known silent-empty gap**: if every listing is hard-blocked or already applied, the ranking command still
  exits 0 with an empty shortlist (see Known Limitations).

### Acceptance

**Profile**
- [ ] Given a CV document, extraction writes a profile with identity, summary, skills, experience and education
  taken from the document text, leaves target roles, locations, salary and contract types empty, and lists them
  as required-review fields.
- [ ] Given an existing profile and no explicit overwrite request, extraction refuses and exits non-zero.
- [ ] Given a profile missing any required section, every command that loads it exits 1 and names the missing
  sections.

**Ingest**
- [ ] Given offline (dry-run) mode, ingest returns synthetic listings for each enabled source, with
  case/whitespace duplicates collapsed, and needs no credentials.
- [ ] Given a source whose credentials are missing, ingest reports that source as skipped and still returns the
  other sources' listings.
- [ ] Given two listings that differ only in case or whitespace of title and company, exactly one survives.
- [ ] Given a listing older than the configured maximum age, it does not appear in the output.
- [ ] Written pool JSON never contains the raw source payload.

**Match (dual cohort)**
- [ ] Given a listing whose title contains "engineer", it never appears in any shortlist.
- [ ] Given an applied-jobs record with an empty company, every listing with that title is removed from both
  cohorts.
- [ ] Given a role that appears in Cohort A's top N, it does not appear in Cohort B.
- [ ] Given the same pool, profile, policy and date, two runs produce the same Cohort A order.
- [ ] Each cohort contains at most its configured cap, ranked 1..N with no gaps.
- [ ] In agent mode no model is called and every phase-2 field is empty.
- [ ] When phase-2 needs the coding agent, the command exits 2 after printing handoff instructions.

**Draft**: not built. The placeholder reports the backend mode and the CV location, then exits 0. Acceptance
criteria are to be written when the stage is designed.

**Packet**: not built. Acceptance requires an approval record before anything leaves the machine.

**Applied-jobs tracking**
- [ ] Adding a record whose (title, company) already exists leaves the store unchanged and reports it as existing.
- [ ] Adding records by cohort and rank position from a shortlist JSON copies title, company, link and source
  from that entry.
- [ ] The next ranking run removes every stored role and reports how many were removed per cohort.

## Decisions

| Decision | Why |
|---|---|
| Deterministic phase-1 scoring first; the model judge is an optional, additive phase 2 behind a backend switch | Phase 1 is cheap, explainable, runs on an 8 GB machine and needs no keys |
| Exclusions live in YAML | The candidate's "never show me X" feedback changes data, not code |
| Two independent cohorts in one HTML file | Cohort A is preserved exactly at the operator's request; Cohort B widens discovery without disturbing it |
| Cohort B widens role matching with its own keywords, for Cohort B only | The marketing-heavy target-role list scores genuine research, policy and archive roles at zero role overlap, and the bonus alone cannot lift them into the top 25; scoping it to Cohort B leaves Cohort A's order unchanged |
| A stable "latest" alias plus a 7-day timestamped archive | A re-run never destroys the previous deliverable, and the folder the candidate opens stays clean |
| Postings are data only: ingest never interprets them, and the phase-2 prompt puts them in a labelled untrusted block after the instructions | The repo combines PII, untrusted content and (planned) outbound channels; ingest reads board credentials in the same process that fetches postings, which is a mechanical HTTP call with no LLM context |
| A second candidate gets a separate component, not a mode of the graduate pipeline (operator 2026-10-26) | The graduate scorer hard-blocks engineer and architect titles and carries graduate keyword sets in code; sharing it would either break the contract search or change the graduate candidate's results |
| Contract search title weights favour data architecture and engineering, then AI roles in the same area and AI or data adoption roles; governance, strategy and generic solution-architect titles rank lower (operator 2026-10-26) | The operator's focus is architecture and engineering; governance-officer and non-data solution-architect adverts crowded the 2026-10-26 shortlist |
| The contract search drops listings with a yearly salary and no contract wording, does not read hybrid adverts as remote, and subtracts 20 for required clearance (2026-10-26) | Adzuna labels estimated-salary permanent adverts as contract; a hybrid advert outside London is not remote; no clearance is recorded in the profile, so a required one is a poor fit but not a drop |
| The contract search drops a listing whose stated top day rate is under 650, penalises inside-IR35 rates under 750 and rewards rates of 800 or more; an unstated rate is never dropped (operator 2026-10-26: ideally 800+, outside IR35 650+, inside IR35 750+, down to about 650 inside) | Most adverts state no rate, so requiring one would hide valid roles; the floor removes only roles the operator would not take |
| The contract search reads contract, IR35 and remote status from explicit advert phrases kept in config, and ranks rather than drops on IR35 | The phrases are fixed text that exact patterns recover (config-driven, no model); most adverts do not state IR35, so dropping unstated ones would hide valid roles |
| The CV extractor is a deterministic parser for one graduate-CV layout, recognised by section headers | No capability-decision record exists for it, so it is a candidate for capability-fit review |

## Outside Constraints

- **Hardware.** The reference machine has 8 GB of RAM and runs agent mode only; a local model can run it out of
  memory. This is operator guidance, stated in the backend config and the job-search skill's hard rules. Nothing
  in the code enforces it.
- **Operator rules for the default run** (Cohort A cap never below 25; Cohort B searched creatively across all
  history-cohort categories) are owned by the
  [kiera-job-search skill](ai_harness/skills/kiera-job-search/SKILL.md) Hard rules.
- **Job boards.** One board ignores search terms and filters by location only. The others treat a multi-word
  query as all-words, so comma-separated concepts narrow the search rather than widen it.
- **Secrets** live outside the repo, in a per-service folder shared across repos. Cloud-LLM keys are resolved by
  `ai_agent_core`.
- **The external tracker sheet** is reached only through the browser by the log-applied-jobs skill; the CLI has
  no sheet access.
- **The candidate's CV** sits outside the repo, at the location the backend config names.

## Known Limitations

- **Silent empty shortlist.** If every listing is filtered out, ranking exits 0 with empty sections. This breaks
  the platform's "no silent empty" degrade rule.
- **Synthetic fallback.** If a cohort is given no pool, synthetic sample listings are used for it. The fallback
  is printed but does not fail the run. Every synthetic listing is hard-blocked, so a bare ranking run is empty.
- **Exclusion policy fails open.** A missing or malformed policy file applies no exclusions and gives no error.
- **Exclusion and cohort vocabularies are partly fixed in code.** The catch-all engineering title tokens, both
  cohort keyword sets and the CV-strength synonyms are not in config, so changing them needs a code change.
- **Salary component never fires on extracted profiles.** The scorer reads an expected-minimum salary key that
  extraction does not write (extraction writes a differently named key).
- **Contract search signals are advert text only.** Listings that never say contract, IR35 or day rate are
  dropped or shown as `unstated`; the boards' truncated descriptions can hide a signal the full advert has.
- **Search terms.** Comma-separated terms are joined into a single all-words query, so multi-concept searches
  narrow rather than widen.
- **Inconsistent key normalisation.** The applied-jobs filter and the pool merge lowercase and trim, but do not
  collapse internal whitespace (ingest dedupe does). The Cohort B exclusion of Cohort A roles is case-sensitive.
- **The phase-2 prompt includes the whole profile, contact section included.** In cloud mode this PII leaves the
  machine. The prompt asks the model not to echo contact details, but nothing enforces it.
- **Agent handoff has no way back in.** No ranking option reads an agent-authored phase-2 result file, so the
  handoff path is incomplete.
- **Execution bounds not implemented:** no retry or backoff on board requests; no cap on how many listings go
  into one phase-2 prompt (one call per ranking pass, each description cut to 800 characters); no run
  identifier, telemetry event, lineage manifest or cost budget emitted by this repo; no input-size caps on
  listing pools. Model timeouts and output-token caps are the substrate's defaults; on the cloud backend its
  default is a single attempt, and whether it retries on the local backend is unverified.
- **No eval harness for phase 2** (no gold set, threshold or calibration of the score or the fabricated-claim
  flags), no ranking-quality metric for phase 1, and no behavioural sensors for non-impersonation or
  no-fabrication (planned in [REPO_CONTRACT.md](governance/REPO_CONTRACT.md)).
- **Every command needs the LLM substrate installed.** The command-line entry point imports it at load time, so
  stages that make no model call (profile, ingest) still depend on it.
- **The tracked backend config identifies the candidate.** It carries an absolute CV folder path and CV file
  stems.

These limitations are triaged under item 4 of [docs/todo/backlog.md](../../docs/todo/backlog.md).

---
name: "kiera-job-search"
description: "Runs Kiera Patel's full job search pipeline (CV→YAML extract, dual-pool live ingest, dual-cohort match+rank, two-section HTML shortlist). Invoke when user says 'perform job search for Kiera Patel' or wants live job board results written out for review."
---

# Kiera Job Search

Run the full 5-stage ai_job_seeker pipeline end-to-end for Kiera Patel and print the output paths so she can review the shortlist.
The pipeline now produces a **dual-cohort shortlist** in a single HTML file:
- **Section A (preserved):** Marketing & Communications top 25 — byte-for-byte the same ranking as the original single-cohort baseline, never reduced or re-ordered.
- **Section B (new):** Historian, Research & Academic top 25 — creative broader set that weights Kiera's History BA + Research & Analysis hard skill + 3+ years academic support / marking CV track. Includes research/insight/analyst, library/archive/records, heritage/museum/curatorial, policy/civil-service, bid/fundraising, editorial/writer, tutoring/education, legal-adjacent, and grad-scheme roles.

A single role may appear in *both* sections if it scores well under both criteria (e.g. a Content Executive uses writing skills that History graduates excel at).

**Hardware constraint**: MacBook Air M3 (8GB). Default backend mode = `agent` (phase-1 deterministic scoring only, no Ollama / local model). Stage-2 live ingest and Stage-3 match run without any LLM.

## Default run parameters

| Parameter | Default |
|---|---|
| Candidate profile path | `implementation/job_seeker/config/profile/kiera.yaml` (gitignored PII) |
| CV .docx source | `/Users/kierapatel/Documents/__personal/careers/cv/Kiera_Patel_CV.docx` (outside repo) |
| **API search terms — Pool 1 (Marketing)** | Single term `marketing`. Adzuna's "what" param uses AND logic, so multi-term comma-separated strings return zero results on Adzuna. This query broadly covers comms, content, PR, brand, digital, grad roles in marketing orgs. |
| **API search terms — Pool 2 (Research/Graduate)** | Single compound term `graduate research` (space-separated, all three boards handle this). Catches research, insight, analyst, policy, archive, library, heritage, grad-scheme, academic support, teaching-assistant roles that the marketing pool under-samples. |
| **Cohort 1 (Marketing) scorer** | Small bonus for marketing/content/comms/PR/brand/SEO/account/executive/coordinator keywords → preserves original Section A ordering from the single-cohort baseline. |
| **Cohort 2 (Historian) scorer** | Three-band bonus (max +22) for HISTORY_COHORT_KEYWORDS (~80 terms across 10 creative categories: research/insight/analyst, library/archive/records, heritage/museum/gallery/curatorial, policy/civil-service, bid/fundraising, editorial/journalism/writer, tutoring/education/academic support, legal-adjacent paralegal/compliance/casework, general grad schemes, plus explicit Research & Analysis / written-communication / numeracy CV-strength synonyms). Augments role-overlap token set with history keywords for the history cohort ONLY (so genuine research roles reach the top-25 of Section B). |
| Location | `London` |
| Section A cap (`--top`) | `25` — Marketing & Communications cohort. NEVER reduce this below 25 in default runs; the user explicitly said "dont reduce the top 25 currently shown". |
| Section B cap (`--research-top`) | `25` — Historian & Research-Academic cohort. Passing `--research-top N>0` triggers the DUAL-COHORT code path in `ai-job-seeker match`. |
| Profile extract mode | `--force` every run (re-extracts from the .docx so YAML never goes stale). The role-keyword patch in Step 2b is required after every extract to restore the 34-term list + London locations, since --extract writes fresh YAML from the .docx. |

## Trigger phrases

Invoke this skill whenever the user says ANYTHING close to "run Kiera's job search end-to-end and give me the output paths so I can review the shortlist". Explicit triggers include (Kiera may use first-person greetings like "Hi, I am Kiera"):

- "Hi, I am kiera, perform the job search" / "Hi, I am Kiera, do the job search" / first-person Kiera greeting + any job-search request
- "perform job search for kiera patel" / "perform job search for Kiera"
- "run a job search for Kiera (Patel)"
- "find jobs for Kiera Patel" / "find me jobs" (if the user has identified as Kiera)
- "search job boards for Kiera (Patel)"
- "do the job search" / "run the job search" (in context where the project/repo is ai_job_seeker)
- any similar request that means "pull live listings and rank them against Kiera's CV + History graduate strengths"

If the user explicitly specifies **search terms** or a **location** in the same prompt, override the defaults above; otherwise keep them.

## Pipeline steps (execute in order)

Work from the repo root: `/Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker`. Every command must use `uv run …` (never install Python globally).

**Step 1 — Ensure the sibling ai_agent_core repo exists on disk.**
- Path must be: `/Users/kierapatel/Documents/__code/git/emailrak/ai_agent_core` (git-cloned sibling).
- The workspace declares it as a path dependency. If it's missing, print the remediation hint: clone `git@github.com:paterake/ai_agent_core.git` into that folder. The profile/ingest/match-agent commands will work without it, but the `match` subparser still resolves the workspace at `uv run` time so the sibling checkout must exist.

**Step 2 — Re-extract profile YAML from Kiera's CV (always --force).**
```bash
cd /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker
uv run ai-job-seeker profile --extract --force
```
This overwrites `implementation/job_seeker/config/profile/kiera.yaml` with facts parsed from the `.docx`. It prints required-review fields (target locations, salary min, contract types, target roles confirmation). Do not skip this step even if the YAML exists.

**Step 2b — (if profile.target.roles is the short 'marketing, communications' hint) expand the target roles list.**
The user confirmed Kiera is a *History graduate* with *strong research skills* — interested in research-heavy roles "almost like a paralegal but not paralegal". Before running ingest/match, **update** `kiera.yaml` → `target.roles` to include all of:
```yaml
roles:
  - marketing
  - content
  - communications
  - PR
  - brand
  - social media
  - copywriting
  - research
  - insight
  - editorial
  - journalist
  - writer
  - bid writer
  - fundraiser
  - policy
  - analyst
  - administration
  - data entry
  - content strategy
  - content production
  - account coordinator
  - marketing executive
  - marketing assistant
  - communications officer
  - communications assistant
  - research assistant
  - research associate
  - information officer
  - heritage
  - museum
  - gallery
  - civil service fast stream
  - graduate scheme
  - graduate programme
```
Set `target.locations = ["London"]` and `target.remote = "any"` (London-based, accept hybrid or remote-tagged listings). Leave `salary_min_gbp` and `contract_types` as empty/None if still under review — the scorer correctly treats missing salary preference as neutral (doesn't penalise listings *for* salary).

**Step 3 — Live ingest, TWO pools (Adzuna + Reed + The Muse each time).**
Secrets live in `~/Documents/__cfg/apikey/…/` on disk (file-first loader, env var fallback). Credentials for all three services are pre-installed. Run **two separate ingest commands** so Pool 2 catches research/graduate roles that Pool 1 misses:

```bash
cd /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker

# Pool 1 — Marketing & Comms (broad original pool, covers comms/content/PR/brand)
uv run ai-job-seeker ingest \
  --search "marketing" \
  --location "<LOCATION_OVERRIDE_or_London>" \
  --json implementation/job_seeker/config/output/pool_marketing.json

# Pool 2 — Research, Insight, Graduate, Analyst, Policy (fills in historian-fit roles that Pool 1 under-samples)
uv run ai-job-seeker ingest \
  --search "graduate research" \
  --location "<LOCATION_OVERRIDE_or_London>" \
  --json implementation/job_seeker/config/output/pool_research.json
```

Rules for the `--search` param per board API:
- For a single concept: single term (e.g. `research`, `graduate`, `content`).
- For multiple concepts: space-join to form a compound query (e.g. `"marketing graduate"`, `"graduate research"`). All three boards handle space-separated phrases well.
- NEVER comma-separate terms (e.g. `"marketing, research"`) — Adzuna's "what" applies AND logic across commas → zero results.

If any source prints `SKIP` (because a secret is missing), surface that to the user — don't silently fail to ingest.

**Step 4 — Match + rank, DUAL COHORT + PER-COHORT POOLS (agent default, no LLM, works on 8GB M3).**

CRITICAL PRESERVATION RULE (from user, do not deviate): **`--top` for Section A is ALWAYS 25. Never reduce below 25.** Kiera explicitly asked to keep the original marketing top-25 shown at 15:00 today, because she had suitable roles in it. The only way to guarantee this (without research pool interlopers jumping into Section A) is to rank Section A **exclusively against the original marketing-ingest pool** (or the prior `latest_listings.json` single-pool from today's first run), and rank Section B **against the merged pool** so it can draw on creative research/historian roles.

Use the **per-cohort ingest flags** (`--marketing-ingest-json` for Section A only; `--history-ingest-json` repeated for Section B only):

```bash
cd /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker
uv run ai-job-seeker match \
  --marketing-ingest-json implementation/job_seeker/config/output/latest_listings.json \
  --history-ingest-json   implementation/job_seeker/config/output/pool_marketing.json \
  --history-ingest-json   implementation/job_seeker/config/output/pool_research.json \
  --top 25 \
  --research-top 25 \
  --search "marketing + graduate research" \
  --location "<LOCATION_OVERRIDE_or_London>" \
  --json-marketing implementation/job_seeker/config/output/latest_shortlist_marketing.json \
  --json-history   implementation/job_seeker/config/output/latest_shortlist_history.json \
  --json           implementation/job_seeker/config/output/latest_shortlist.json \
  --md             implementation/job_seeker/config/output/latest_shortlist.md \
  --html           implementation/job_seeker/config/output/latest_shortlist.html
```

What each flag does (internal behaviour):
- `--marketing-ingest-json latest_listings.json` → Section A ranks ONLY against the original single-pool (155 listings, the same pool Kiera saw at 15:00 today). The CLI also automatically drops the tiny marketing-cohort bonus and uses vanilla `cohort=None` scoring when this flag is set, so the scores and order match the original single-cohort run byte-for-byte as closely as possible.
- `--history-ingest-json pool_marketing.json --history-ingest-json pool_research.json` → Section B ranks against the dedup-merged pool (191 listings, marketing 153 + research 38 unique) with the full historian 3-band bonus (max +22) + role-overlap keyword augmentation, so research/insight/heritage/policy/editorial roles surface correctly.
- `--top 25` (never reduce) + `--research-top 25` enable the dual-cohort writer that renders both sections into ONE HTML/markdown file.

`--json` writes a combined `{marketing, history, generated_at}` dict. `--html` writes the single self-contained dual-section HTML with:
- A table-of-contents at the top (jump to either section)
- Section A table + score-breakdown accordion cards (marketing cohort — preserved original set)
- Section B table + score-breakdown accordion cards (historian cohort — creative CV-strength additions) with the 3-band bonus evidence visible per role
- Fully offline renderable, inline CSS, clickable apply links that open new tabs.

Phase-2 is skipped in agent mode per the hardware constraint.

**Step 5 — Auto-open Finder (output folder) + the shortlist HTML in the default browser.**

Kiera already has a Finder shortcut to the output folder pinned. Skip the `~/Downloads/` copy workaround (that was a sandbox hack). Instead, immediately after Step 4 completes, **run these two commands** — they work inside the Trae sandbox (they only call macOS `open`, no sandbox writes outside the repo):

```bash
# 1) Open a Finder window to the output folder (user can click "Date Modified" column header to sort newest-first)
open /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output

# 2) Open the latest dual-cohort shortlist HTML directly in Kiera's default browser (Safari / Chrome / whatever)
open /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output/latest_shortlist.html
```

Both return instantly (exit 0, non-blocking). If Kiera says she prefers `~/Downloads/` copy or a different destination, fall back to the old cp-then-open block (preserved above the skill's hard-rules section for reference), but the default is now direct-open via `open` because it's simpler and works from the sandbox.

**Step 6 — Report the output paths to the user, in NON-TECHNICAL language.**
After Steps 4+5 complete successfully (exit 0), print a clear, human-readable summary with absolute file-system links (clickable in the IDE):

```
✅ Kiera Patel job search complete (DUAL-COHORT output).

Inputs:
  · Pool 1 API search    : marketing (≈150 broad marketing/comms/content listings)
  · Pool 2 API search    : graduate research (≈50 research/grad/analyst roles)
  · Location             : <LOCATION>
  · Section A cap (Mktg) : 25 — PRESERVED, top 25 never reduced/re-ordered.
  · Section B cap (Hist) : 25 — historian/research/academic creative ranking.
  · Backend mode         : agent (phase-1 deterministic only — no Ollama/LLM, 8GB safe)
  · Merged pool (deduped): Pool 1 + Pool 2, de-duplicated on (title, company)

Ingest pulled <POOL1_COUNT> + <POOL2_COUNT> listings (merged deduped = <MERGED_COUNT>) from Adzuna + Reed + The Muse.
Dual-cohort ranked shortlist written:

  · Single HTML with TWO SECTIONS (copy this → ~/Downloads for Kiera):
    /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output/latest_shortlist.html
      — Section A: Marketing & Communications top 25 (original ranking preserved)
      — Section B: Historian, Research & Academic top 25 (creative History-BA fit)

  · Reviewable Markdown (two sections, clickable apply links):
    /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output/latest_shortlist.md

  · Combined machine-readable shortlist JSON {marketing, history}:
    /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output/latest_shortlist.json

  · Section A only (marketing) JSON:
    /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output/latest_shortlist_marketing.json

  · Section B only (historian/research) JSON:
    /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output/latest_shortlist_history.json

  · Pool 1 raw (marketing ingest JSON):
    /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output/pool_marketing.json
  · Pool 2 raw (research/grad ingest JSON):
    /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output/pool_research.json

💡 Tip: a role can appear in BOTH sections if it fits both criteria (e.g. Content Executive suits marketing AND uses the strong written-communication skills History graduates build via essays/dissertations). Both the Finder window and the shortlist in your browser should already be open on your Mac.
```

If any step fails (non-zero exit), stop and print the error + remediation to the user — don't press on with partial outputs.

## Hard rules enforced by the skill

- **Never reduce Section A below 25.** The user explicitly said: "dont reduce the top 25 currently shown as we would a role within that top 25 that was suitable." Section A = Marketing & Communications, preserved byte-for-byte.
- **Section B must be creative, not just libraries.** The HISTORY_COHORT_KEYWORDS span 10 categories (research/insight/analyst, library/archive, heritage/museum/curatorial, policy/civil-service, bid/fundraising, editorial/journalism/writer, tutoring/education, legal-adjacent paralegal/compliance, general grad schemes, plus explicit CV-strength synonyms). Never narrow Section B to just "library assistant" — the user told us library roles were mostly closed.
- **No fabrication.** Every value in the profile YAML traces directly to text extracted from the `.docx`. Target.roles extensions above are *explicit user-confirmed heuristics* and are marked as such in the CLI's required-review prompt.
- **No auto-send.** Stage 5 Packet is not built yet; even when it is, no application packet ever leaves the machine without a human-approval gate. The Markdown shortlist is for Kiera's review only.
- **No PII in git.** Everything under `config/profile/` and `config/output/` is gitignored; secrets live in `~/Documents/__cfg/apikey/` outside the repo entirely.
- **No OS Python pollution.** Run every command via `uv run …` from inside the repo root; never `pip install` to the system Python.
- **Hardware lock.** Match runs in `agent` mode by default (phase-1 deterministic scoring only). Never add `--ollama-model` or `--llm-provider` flags to the default skill flow for this 8GB M3 Air.

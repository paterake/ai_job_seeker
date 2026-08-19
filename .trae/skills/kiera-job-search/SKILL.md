---
name: "kiera-job-search"
description: "Runs Kiera Patel's full job search pipeline (CV→YAML extract, live ingest, match+rank, shortlist files). Invoke when user says 'perform job search for Kiera Patel' or wants live job board results written out for review."
---

# Kiera Job Search

Run the full 5-stage ai_job_seeker pipeline end-to-end for Kiera Patel and print the output paths so she can review the shortlist.

**Hardware constraint**: MacBook Air M3 (8GB). Default backend mode = `agent` (phase-1 deterministic scoring only, no Ollama / local model). Stage-2 live ingest and Stage-3 match run without any LLM.

## Default run parameters

| Parameter | Default |
|---|---|
| Candidate profile path | `implementation/job_seeker/config/profile/kiera.yaml` (gitignored PII) |
| CV .docx source | `/Users/kierapatel/Documents/__personal/careers/cv/Kiera_Patel_CV.docx` (outside repo) |
| **API search terms (sent to job boards)** | `marketing` — single term on purpose. Adzuna's "what" param uses AND logic, so multi-term strings return zero results on Adzuna. All three boards treat `marketing` as a broad query covering the adjacent role categories (comm, content, PR, brand, digital, research, grad roles in marketing orgs etc.). We get ~150 broad listings from Adzuna+Reed+Muse combined, then the 34-term scorer prioritises the research/graduate/analyst roles inside that pool. If the user explicitly asks for a narrower category, override with one term only (e.g. `research` or `graduate` or `content`). If they specify multiple terms, combine into a single space-separated compound query (e.g. "marketing graduate") — this works on all three boards. NEVER use more than one comma-separated term. |
| **Scorer role keywords** (used by match phase-1 to compute keyword overlap on fetched listings) | Full 34-term list: marketing, content, communications, PR, brand, social media, copywriting, research, insight, editorial, journalist, writer, bid writer, fundraiser, policy, analyst, administration, data entry, content strategy, content production, account coordinator, marketing executive, marketing assistant, communications officer, communications assistant, research assistant, research associate, information officer, heritage, museum, gallery, civil service fast stream, graduate scheme, graduate programme |
| Location | `London` |
| Shortlist cap (`--top`) | `25` |
| Profile extract mode | `--force` every run (re-extracts from the .docx so YAML never goes stale). The role-keyword patch in Step 2b is required after every extract to restore the 34-term list + London locations, since --extract writes fresh YAML from the .docx. |

## Trigger phrases

Invoke this skill whenever the user says anything close to:

- "perform job search for Kiera Patel"
- "run a job search for Kiera"
- "find jobs for Kiera Patel"
- "search job boards for Kiera"
- any similar request that means "pull live listings and rank them against Kiera's CV"

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

**Step 3 — Live ingest (Adzuna + Reed + The Muse).**
Secrets live in `~/Documents/__cfg/apikey/…/` on disk (file-first loader, env var fallback). Credentials for all three services are pre-installed by the installer script. Run with the **single-term default API string `marketing`** — Adzuna uses AND logic across comma-separated terms, so multi-term strings return zero results on Adzuna. The broader role-keyword list is for the match scorer, not the board APIs:
```bash
cd /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker
uv run ai-job-seeker ingest \
  --search "marketing" \
  --location "<LOCATION_OVERRIDE_or_London>" \
  --json implementation/job_seeker/config/output/latest_listings.json
```
If the user specified a custom search category:
- If it's a single concept, use the single term (e.g. "research", "graduate", "content")
- If it's multiple concepts, join with spaces to form a compound query (e.g. "marketing graduate") — all three boards handle space-separated phrases well.
- NEVER use comma-separated multi-term strings (Adzuna zero-results bug).

If any source prints `SKIP` (because a secret is missing), surface that to the user — don't silently fail to ingest.

**Step 4 — Match + rank (agent default, no LLM, works on 8GB M3).**
```bash
cd /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker
uv run ai-job-seeker match \
  --ingest-json implementation/job_seeker/config/output/latest_listings.json \
  --top <TOP N> \
  --search "<TERMS>" \
  --location "<LOCATION>" \
  --json implementation/job_seeker/config/output/latest_shortlist.json \
  --md   implementation/job_seeker/config/output/latest_shortlist.md
```
`<TOP N>` defaults to 25. Match prints the ranked table; phase-2 is skipped in agent mode per the hardware constraint.

**Step 5 — Report the output paths to the user.**
After Step 4 completes successfully (exit 0), print a clear, human-readable summary with absolute file-system links (clickable in the IDE):

```
✅ Kiera Patel job search complete.

Inputs:
  · API search terms : <TERMS sent to boards — default marketing,content,communications,research>
  · Location         : <LOCATION>
  · Shortlist cap    : <TOP N>
  · Backend mode     : agent (phase-1 deterministic only — no Ollama/LLM, 8GB safe)
  · Scorer role list : 34 keywords (the full marketing/content/comm/PR/research/insight/graduate set)

Ingest pulled <COUNT> live listings from Adzuna + Reed + The Muse.
Ranked shortlist (top <COUNT>) written to:

  · Reviewable Markdown (clickable apply links, for Kiera to read):
    /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output/latest_shortlist.md

  · Machine-readable shortlist JSON (for Stage 4 Draft later):
    /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output/latest_shortlist.json

  · Full unranked listings JSON (all sources, filtered + deduped):
    /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output/latest_listings.json
```

If any step fails (non-zero exit), stop and print the error + remediation to the user — don't press on with partial outputs.

## Hard rules enforced by the skill

- **No fabrication.** Every value in the profile YAML traces directly to text extracted from the `.docx`. Target.roles extensions above are *explicit user-confirmed heuristics* and are marked as such in the CLI's required-review prompt.
- **No auto-send.** Stage 5 Packet is not built yet; even when it is, no application packet ever leaves the machine without a human-approval gate. The Markdown shortlist is for Kiera's review only.
- **No PII in git.** Everything under `config/profile/` and `config/output/` is gitignored; secrets live in `~/Documents/__cfg/apikey/` outside the repo entirely.
- **No OS Python pollution.** Run every command via `uv run …` from inside the repo root; never `pip install` to the system Python.
- **Hardware lock.** Match runs in `agent` mode by default (phase-1 deterministic scoring only). Never add `--ollama-model` or `--llm-provider` flags to the default skill flow for this 8GB M3 Air.

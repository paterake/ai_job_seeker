---
name: "log-applied-jobs"
description: "Log which roles Kiera has applied to, by section/position ID from the shortlist. Resolves roles from latest_shortlist.json, writes them to the local applied_jobs.json (so the match filter removes them next run), and appends rows to Kiera's 'actions' Google Sheet 'jobs' tab via the interactive browser. Invoke when Kiera says things like 'I applied to Section A #3, Section B #5 and #7' or mentions logging applied roles / updating the tracker sheet."
---

# Log Applied Jobs

When Kiera tells us which roles she's applied to, we do three things in order:

1. **Parse her IDs** — pull out Section A + Section B (or "Marketing" / "Historian" / "Research") numbered positions from her message (supports comma-separated, range `3-7`, single, any mix).
2. **Write to local applied_jobs.json** via `ai-job-seeker applied add --from-shortlist-json … --cohort … --position N` so the next `match` run filters them out of the shortlist.
3. **Append rows to Kiera's Google Sheet "jobs" tab** via the interactive browser. Sheet URL is fixed: `https://docs.google.com/spreadsheets/d/1vVxOnjUM7T9PRvd7tpNw0Q8mzvajSKQ75euH6pHSFjA/edit?gid=499941486#gid=499941486`.

**Trigger phrases** (anything close to):
- "I've applied to Section A #3, #7, #12 and Section B #5"
- "Log that I applied to A1, A2, B4, B6"
- "I sent applications for Marketing positions 3 and 15 today"
- "Add applied to: Historian section positions 2, 5, 8"
- "Update my tracker sheet with the roles I applied to"
- any similar message that means "I've applied to specific shortlisted roles; record them and filter them out of the next shortlist"

## Defaults

| Parameter | Value |
|---|---|
| Shortlist JSON (combined dual-cohort) | `/Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output/_pipeline/latest_shortlist.json` |
| Per-cohort JSON fallbacks | `latest_shortlist_marketing.json`, `latest_shortlist_history.json` in `output/_pipeline/` (same directory as shortlist JSON) |
| Local applied store (pipeline cache) | `/Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker/implementation/job_seeker/config/output/_pipeline/applied_jobs.json` |
| **Canonical tracker (primary):** Google Drive `.gsheet` local path | `/Users/kierapatel/Library/CloudStorage/GoogleDrive-patelkiera@gmail.com/My Drive/personal/job_seeker/actions.gsheet` |
| Google Drive `.gsheet` doc_id (read from the stub file) | `1vVxOnjUM7T9PRvd7tpNw0Q8mzvajSKQ75euH6pHSFjA` |
| Google Sheet URL (derived from doc_id) | `https://docs.google.com/spreadsheets/d/1vVxOnjUM7T9PRvd7tpNw0Q8mzvajSKQ75euH6pHSFjA/edit?gid=499941486#gid=499941486` |
| Google Sheet tab | `jobs` (bottom tab bar — click first if not already on it) |
| Default applied status | `applied` |
| Applied date | today's ISO date (2026-09-13 format) — override if user says "applied last Friday" etc. |

## Output columns (Google Sheet "jobs" tab)

Kiera already has a **custom pre-existing header row** (row 1) in her "jobs" tab. ALWAYS auto-detect it first, NEVER overwrite row 1. The two known formats are:

### Format A — Kiera's current format (as of 2026-09-13 — use this if A1 = "Interested"):
| Column letter | Row 1 header | What we write into this column for each new applied row |
|---|---|---|
| A | Interested | **Role title** (from shortlist JSON listing.title, exact text) |
| B | Applied | `Yes` |
| C | Interview Stage | Leave blank for now (Kiera fills this in manually) |
| D | Result | Leave blank for now (Kiera fills this manually) |
| E → | Any extra columns Kiera adds later | If we recognise the header (Location / Company / Source / Apply Link / Applied On / Status / Notes), fill them in; otherwise leave blank |

If Format A is detected, you SHOULD also try to slip the most useful extra fields into any empty columns to the RIGHT of D (if those columns already exist or if Kiera has added headers). For example, if columns E..I exist and are empty in row 20, you can write: Applied On → E, Company → F, Location → G, Source → H, Apply Link → I.

### Format B — Preferred fallback (if A1 is blank, write these headers first then data):
| Column | Content |
|---|---|
| A · Applied On | ISO date, e.g. `2026-09-02` |
| B · Section | `Section A (Marketing)` or `Section B (Historian/Research)` |
| C · Rank in Section | The # number Kiera cited, e.g. `3` |
| D · Role Title | Job listing title (exact from shortlist JSON listing.title) |
| E · Company | Company from listing.company |
| F · Location | listing.location (if present) |
| G · Source | `adzuna` / `reed` / `themuse` (listing.source) |
| H · Apply Link | Full listing.url (clickable — if Sheets lets you set HYPERLINK formula use `=HYPERLINK(url, "Apply")` otherwise just paste the URL) |
| I · Final Score | ScoredListing.final_score from the JSON, e.g. `68.0` |
| J · Status | `applied` (or `interviewed`, `rejected`, `offer` if Kiera says) |
| K · Notes | Free text if Kiera added any comments with her prompt |

## Step-by-step execution

Work from repo root: `/Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker`. All commands use `uv run …`.

**Step 1 — Parse the cohort IDs from Kiera's message.**
- Recognise Section A / Marketing / Mkt / M = `cohort=marketing`
- Recognise Section B / Historian / Research / Academic / History / H / R / B = `cohort=history`
- Number patterns: accept `3`, `#3`, `no.3`, `position 3`, ranges `3-7` inclusive, comma lists `2,5,7-9`, mixed `A3 B5 A7`
- Example mapping: "Section A #3, #7, #12 and Section B #5" → `(marketing, [3,7,12]), (history, [5])`
- Print what you parsed so Kiera can correct:
  ```
  Parsed IDs:
    · Section A (Marketing) positions 3, 7, 12
    · Section B (Historian & Research) position 5
  Confirming correct — if I got any wrong, tell me which ones.
  ```
  If ambiguous (e.g. no section prefix, just "positions 3 5 7"), ask Kiera which section(s) she means before proceeding — don't guess.

**Step 2 — Write to local applied_jobs.json via `ai-job-seeker applied add`.**
For each (cohort, positions[]) group, run:
```bash
cd /Users/kierapatel/Documents/__code/git/emailrak/ai_job_seeker
# For each cohort group; --position can be passed multiple times or comma separated via shell expansion
uv run ai-job-seeker applied add \
  --from-shortlist-json implementation/job_seeker/config/output/_pipeline/latest_shortlist.json \
  --cohort marketing \
  --position 3 --position 7 --position 12
```
Run `applied list` after to confirm the new records are in.

**Step 3 — Load and browse to the Google Sheet via integrated_browser tools.**

Canonical source of truth is the Google Drive file at:
`/Users/kierapatel/Library/CloudStorage/GoogleDrive-patelkiera@gmail.com/My Drive/personal/job_seeker/actions.gsheet`
Read the `.gsheet` JSON stub (it's a tiny plain JSON file with keys `doc_id` and `resource_key`) to confirm the doc_id before opening. Use the doc_id to build the URL if the file ever moves:
`https://docs.google.com/spreadsheets/d/<DOC_ID>/edit?gid=499941486#gid=499941486`

Open the sheet (reuse the tab if it's already open per `browser_tabs list`):
```
URL: https://docs.google.com/spreadsheets/d/1vVxOnjUM7T9PRvd7tpNw0Q8mzvajSKQ75euH6pHSFjA/edit?gid=499941486#gid=499941486
```
Wait for it to load (2–3s, `browser_wait_for` then snapshot).
If not already on the "jobs" tab, click it (bottom tab bar; ref from snapshot).

**Step 4 — Detect existing header format and find the first empty row.**

Google Sheets renders the grid in DOM with the sheet toolbar first. To extract row-1 headers and find the first empty row:
1. Navigate (Name Box → `A1` → Enter) and read the formula bar value to get A1's text. That tells you the header format.
2. Then navigate across `B1`, `C1`, `D1` etc reading the formula bar until you hit blanks — that gives you the full header row.
3. If A1 is blank, write Format B headers first, then append data starting at row 2.
4. If A1 == "Interested", we're in Kiera's **Format A** (Interested / Applied / Interview Stage / Result). Match that format: new rows start with the Role Title in A, "Yes" in B. Leave C and D blank for Kiera to fill manually.
5. **Finding first empty row:** Navigate Name Box → `A2` → Enter, then read formula bar. Keep incrementing row number until formula bar is empty. That N is the start row.

Kiera's sheet currently (Sept 2026) has 19 applied rows in Format A — data in rows 2..20, row 21 is the first empty row. Use a screenshot to confirm row numbers visually if the DOM-based read is ambiguous.

**Step 5 — Write the new rows.**


For each new applied record (in the order Kiera listed them):
1. Click on the starting cell in Column A of row N (use browser_click on the grid, or `browser_evaluate` to select and set the cell's formula/value programmatically — programmatic is more reliable because the grid cells aren't always individual input elements).
2. To write a cell value reliably in Sheets: select it (set the active range), then use the currently-editing formula bar or `browser_evaluate` that dispatches input events. Sheets keyboard shortcut pattern (reliably works in all Google accounts): type cell address like `A12` into the Name Box (top-left address field) and press Enter → that row scrolls into view and cell is selected, then paste/write the text.
3. Write each column value, Tab-ing between cells, and when the row is complete press Enter to commit row N and move to row N+1 first cell.

If the DOM click/type approach flaks out, fall back to a single `browser_evaluate` script that:
- Finds the Name Box input (`.docs-name-input`, `.waffle-name-box-input`, or element with role=textbox whose accessible name is "A1")
- Writes `<letter><rowNum>` into it and simulates Enter
- Finds the active cell editor (`.cell-input`, `formula-input`, or document.activeElement)
- Sets `.value` and dispatches `new Event('input', {bubbles:true})` + `new KeyboardEvent('keydown', {key:'Tab'})` to move to next column
- Loops across columns for the row

If Sheets is being difficult with the DOM editor, use the Google Sheets built-in CSV paste approach:
- Build the rows as a multi-line TSV string in the skill agent's memory
- Click any empty cell below row 1, then `browser_type` the TSV (tabs between cells, newlines between rows) — Sheets auto-parses pasted TSV.

**Step 6 — Verify and confirm.**

Snapshot the sheet after writing. Read back column A of the new rows to confirm the applied-on date values are visible. Then print for Kiera (non-technical language, no shell blocks):
```
✅ Done — logged N applied role(s).

  1. Local JSON store updated → these roles are auto-filtered out of the NEXT job-search run you run.
  2. Google Sheet "jobs" tab appended → N new row(s) starting at row N.

Roles logged:
  · [Section A #3]  Social Media Marketing manager and copy writer — Rebound Recovery Ltd  (applied 2026-09-02)
  · ...

Quick access:
  · Tracked roles list: <click applied_jobs.json path>
  · Google Sheet (jobs tab): <click sheet URL>
```

## Hard rules

- **Never guess a position's cohort.** If the user says "positions 3,5,7" with no section prefix, ask which section before doing anything.
- **Sheet edits are always additive-only.** Never delete or overwrite existing rows in the "jobs" tab. Always append at the first empty row.
- **Local JSON and sheet must stay consistent.** Only declare success when BOTH (a) `ai-job-seeker applied list` shows the new records, AND (b) the browser snapshot confirms the new rows are visible in the sheet.
- **Sheet login requirement:** if Google redirects to `accounts.google.com/v3/signin`, tell Kiera: "I hit the Google login wall again. Could you quickly log in inside this browser tab, then say 'continue' and I'll finish writing the rows." Don't try to re-auth on her behalf.
- **No PII in git:** applied_jobs.json lives under `output/_pipeline/` which is under the gitignored `output/` directory tree; Google Sheet URL references are never committed to the repo.
- **Report in plain language**, no terminal copy-paste blocks, per project_memory conventions.

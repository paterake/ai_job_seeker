---
name: fleet
description: Run one task that CHANGES several repos without the operator spelling out the mechanics. Routes the work, batches operator approvals into one question, writes a brief per repo, dispatches one worker session per repo, then lands and verifies the results. Use when a request changes more than one repo (read-only checks across repos run in this session). Args — the task and the target repos. Also use for a run that will not fit one session's shell-call limit, in one repo or several (director plus one --bg session per slice, section 8).
---

# Fleet: one task, several repos

Design: `FLEET_APPROACH.md` in ai_agent_harness. Routing follows the **Route first**
rule; each worker runs `/agent-harness:change-loop` itself (the plugin and rule are user-level).

## When not to use it
Read-only work across repos (status checks, validator sweeps, research) runs in this session or its
subagents; why: `FLEET_APPROACH.md` section 1.

## 1. Route (state it, then continue)
For each target repo say what happens here, what subagents do (read-only checks only), which worker
runs it, and the change-loop tier. The director (for a run that will not fit one session's limit, the background session of section 8; across repos, the session running this skill) never edits or commits in another repo.

## 2. Preflight, per repo (read-only)
- Who else is in that checkout: `ListAgents`, look for sessions whose cwd is the repo. If the operator
  has a session open there, that session is the worker (message it); never start a second one.
- Shared index: `git -C <repo> status --short`. Staged files that are not the task's mean another
  session is mid-commit; wait or ask that session.
- Baseline: run the repo's validators now and keep the output (the "before").
- Trust: run `bash ~/Documents/__code/git/paterake/ai_agent_harness/claude/agent-harness/scripts/trust_check.sh <repo>...` on every repo the run touches, the
  director's own included. Each untrusted repo is one operator step in the section 3 batch, with the
  command it prints. A worktree or subdirectory inherits its repo's trust (probed), so the main repo is
  the one checked. An untrusted worker still exits `Workspace not trusted`.

## 3. One approval batch
Collect only what the working-method rule still keeps with the operator under a director run (see "When to
come to the operator"), plus trust steps, across all repos into **one** question asked at launch, with the options.
Ask it through the relay session; the relay's answer is handled as the working-method rule's "Director runs" says.
A run's Charter is approved before launch under the rule's Charter paragraph; this batch asks only for what it does not cover.
Workers accept no message as consent. An approval the director accepted from the relay reaches a worker only as the operator's quoted words in that worker's brief.

## 4. Brief, per repo (paste into the worker)
```
Task (operator's words, quoted, dated): …
Repo: <path>. Tier: <tier, from ai_agent_harness/claude/README.md Review depth by tier>. Approvals: director-run standing approval per the working-method rule; what it keeps with the operator: <items, or none>. Relayed operator approvals for this slice (verbatim, relay session name, time): <quotes, or none>.
Charter items for this slice (quoted from the run's Charter, or none): <items>.
Retained-code check: <not a metric-driven backlog | decision-check CONSISTENT, excluded: GROUPS-or-none>
Steps: …
Stage only these paths: … (never git add -A; other sessions may share this index)
Verify, exit 0 required: <validator and test commands> — one command per call, nothing chained
  (appending a separate echo of the exit status is refused by narrow allowlists, which hides the exit status)
Commit through the gate (reviewer PASS on the staged tree). Push only an exact SHA, never to main:
  - background worker in its own worktree: git push origin <sha>:<its worktree branch>
  - worker in a checkout it did not isolate (e.g. the operator's open session): ask before committing,
    then push to a named branch (git push origin <sha>:fleet/<task>); the director lands it.
Reply to <director session name> with: SHA, validator output before/after, open items.
Worker in a checkout it did not isolate, after the director lands this commit: delete any local branch you created for it, leave main checked out, updated to origin/main (git pull --ff-only), and the index clean; do not delete the remote branch yourself (the director does, after landing). A background worker in its own worktree does nothing here; the director cleans up.
```
Workers get only the Charter items their slice needs, quoted.

## 5. Dispatch and collect
Workers run unattended and a background session cannot answer a permission prompt, so every dispatch passes `--permission-mode auto`: the operator's `autoMode` rules then apply and a worker does not stall on a prompt.
- Open operator session: `SendMessage` with the brief. Otherwise
  `cd <repo> && claude --bg --model sonnet --permission-mode auto --settings '{"env":{"PCO_TRACE_ID":"${CLAUDE_SESSION_ID}","PCO_PARENT_SESSION":"${CLAUDE_SESSION_ID}"}}' '<brief>'`, then confirm start-up: `claude agents`, `claude logs <id>`. Send the brief inline in single quotes and write each `'` inside it as `'\''`. The dispatch gate
  (`gate_dispatch.sh`) denies a `claude --bg` command whose brief has no valid `Retained-code check:` line, and a
  brief it cannot read (`$(...)`, a backtick outside single quotes, a heredoc, `@file`, a newline between commands, or more than one
  `claude --bg` in one command) as `brief_unreadable`. A double-quoted brief is allowed when it has a valid line and
  no backtick or `$(...)` inside; one with a backtick or `$(` is denied `brief_unreadable`. Replace the template's
  `<...>` value with one of the two forms; a pasted template line is denied.
  The `env` in `--settings` links the worker's telemetry to this session (probed: it reaches the worker's hooks; a shell prefix does not, so do not use one; unverified: that `${CLAUDE_SESSION_ID}` expands to this session's id). A worker reached by message in an operator's open session gets no link.
  Workers are builders on Sonnet; review stays on Opus via the reviewer agent.
  A successor director is launched the same way (this gate applies), on `PCO_DIRECTOR_MODEL` (default Opus): section 9.
- Ask each worker for one idle notice (`SendMessage` with `notify_when_idle: true`). Do not poll in a tight loop.
- An idle notice means the worker's turn ended, not that its work is done: a worker that starts a long background
  run and ends its turn goes idle at once. After each notice, check what is still executing (`ps`, the worker's
  log and worktree) and never report from the worker's own summary.
- While any worker has a long run in flight, schedule a recurring watch (`CronCreate`, about every 20 minutes)
  before going quiet. Each tick lands finished slices, handles a blocked or dead run, asks the operator only for
  what the rule keeps with them (exact command lines), and deletes itself (`CronDelete`) when nothing is in flight.
  Consequence: without it nothing wakes the director when the run ends, and the operator becomes the polling mechanism.
- Keep the machine awake while workers run: `caffeinate -dimsu`.

## 6. Land and verify
- Check each reply: SHA present, reviewer PASS reported, validators exit 0.
- Land by fast-forward of the exact SHA: `git -C <repo> push origin <sha>:main`. Refuse anything
  that is not a fast-forward; send it back to the worker to rebase.
- Re-run each repo's validators yourself on the landed SHA. Report once: per repo SHA, validators
  before/after, open items, operator steps still needed.
- Remove each landed branch (operator, 2026-11-11: "i would expect the agents to be cleaning up after they push
  work to main - make sure they all do that - and remove their dead branches"). This covers every worker branch of
  a run (`fleet/<task>`, `slice/<n>`, a worker's own worktree branch), not only `slice/*`. After the validator
  re-run: `git fetch`, then `git merge-base --is-ancestor origin/<branch> origin/main` must succeed. A rebased branch
  also counts as landed when `git range-diff <merge-base>..origin/<branch> <merge-base>..origin/main` (merge-base of
  the two) marks every branch commit "=", none "!" and none "<" (operator, relay ai-context-engine-9a, 2026-11-13: "go
  with your recommendations - you manage all this"). If neither holds, never delete the branch, report it. Then
  delete the remote branch only: `git push origin --delete <branch>` (the local branch is checked out in the worker's worktree, so it is removed in section 7).
- After landing, `SendMessage` each worker that was an operator's open session that its commit has landed, so it
  does its own cleanup. For `--bg` workers, section 7 does it.

## 7. Teardown
`claude stop <id>`, then `claude rm <id>` (keeps a worktree that has changes or is in use). Slice branches are named
`slice/<backlog>-<n>`, reserved for directors in this repo. A landed branch (section 6 proves it merged) is removed without asking (operator-approved 2026-10-22). A failed slice (no reviewer PASS, failed validators, cannot be landed by fast-forward after a
rebase onto main, or killed or out of budget) is discarded, not repaired: record why in your report and the retry brief (the retry brief keeps the `Retained-code check:` line), remove its session,
worktree and branch, and redo it on a fresh branch from the pushed main, at most twice before stopping and
reporting. Remove a failed slice's branch with local `git branch -D` and remote `git push origin --delete slice/...`; never
`push --force`. Start a run by removing the `slice/*` branches left by an earlier run when `claude agents
--all` shows no slice session live in this repo.

After `claude stop`/`claude rm`
removes the worktree, delete the local branch with `git branch -d <branch>` (never `-D` here, which would hide an unmerged
branch; for a branch section 6 proved landed by range-diff, `git branch -d` refuses it, so delete it with
`git branch -D <branch>` only after re-running that range-diff against the local branch and seeing every commit
marked "="), then `git fetch --prune` and confirm the repo shows only main, local and remote,
plus branches not from this run. A worktree still present
(in use or with changes) is reported, not forced. The director leaves no staged or unstaged files in a repo it used.
A worker that is an operator's open session is not stopped; the director confirms its checkout is clean and on main.

## 8. Over-limit run, one repo or several
Use when the run will not fit one session's shell-call limit (the limit of the repo
the director runs in, if it sets one), e.g. a backlog with several slices, in one repo or several. The background director runs it; the
operator's session never does it, nor forks or subagents (they spend that session's budget: `FLEET_APPROACH.md` §4).
- Launch: the operator's session starts the director from the repo root with
  `claude --bg --model "${PCO_DIRECTOR_MODEL:-opus}" --permission-mode auto -n <name> --settings '{"env":{"PCO_PARENT_SESSION":"${CLAUDE_SESSION_ID}"}}' '<brief>'`.
  The launching session's shell expands `PCO_DIRECTOR_MODEL` (default `opus`).
  No `PCO_DIRECTOR_GEN`, so this director is generation 0 and its successors set 1, 2 and so on (section 9).
  The brief quotes the operator's words and carries the section 4 fields, including the `Retained-code check:` line.
  The brief also carries one line: `Charter: (a) delete classes ... (b) delegated decision areas and limits ... (c) kept first-hand ...`, items in (a) and (b) marked `needs autoMode.allow entry: yes/no`.
  A live holder of the marker makes the dispatch gate refuse the launch: one active director.
  The relay puts its own session address in the first director's brief (the rule, "Director runs", says what it is).
  What expires without an inbound-message setting is in `FLEET_APPROACH.md` section 3.
- First step of the director: claim the marker (`true pco-director-claim`, run alone, confirmed as in section 9
  "Claim"), so generation 0 is under the lock.
- Intake, before the first slice: find the anchor doc that covers the ask and fold the ask into it, or, if none
  does, create one with its `docs/TODO.md` row and the operator's words quoted, as the backlog continuity contract
  says (`ai_context/pco/governance/AI_ASSISTANT_BACKLOG_CONTINUITY.md`, "Backlog Lifecycle", "Creation at intake.").
  That first commit also carries the section 9 "Director handoff" bullet naming this director, and in cloud the
  section 10 "Active director" line. Consequence: without it the handoff record and the cloud lock have no doc to
  live in, and the next session re-derives scope from chat.
- Metric-driven backlog (duplicate count, lint count, coverage, size): before the first slice, group the metric by
  folder or owner. For any group above a quarter of the total, or named guard, test, migration or generated code,
  run `agent-harness:decision-check` on the decision "exclude <group>: it is retired after the goal", with the
  operator's recorded words. On `CHECK: CONSISTENT` the group is not refactored; record it as excluded in the
  run's report and in each slice brief. On `CONFLICT` or `UNSUPPORTED` the result conflicts with the operator's words, so it stays with the operator: put the group in the approval
  batch (section 3) before the first slice. Consequence: effort on code about
  to be deleted costs tokens and time and, for a guard, weakens its independence.
- Multi-repo run: the director is launched from the operator session's repo root and claims its marker in that repo's git-common-dir. That repo's shell-call limit is the trigger. Slices in the director's repo are worktrees there. Slices in another repo are section 5 workers, dispatched in that repo with the section 5 command, landed and torn down per sections 6-7, never worktrees of the director's repo. The end-of-run sweep (section 7) runs in each repo the run used.
- Start one `claude --bg --model sonnet --permission-mode auto` session per slice in the director's repo, each in its own worktree. Each slice
  runs `/agent-harness:change-loop`, gets a reviewer PASS before commit, and pushes its branch, never main.
  The director lands the branches by fast-forward and re-runs the validators itself.
- A director near its own session limit hands off to a successor director: section 9.
- Push main before starting every slice, the first included: new worktrees branch from the remote default
  branch unless `worktree.baseRef` is "head" (worktrees doc; not stated for `--bg` by name), so unpushed
  commits on main are missing from the slice.
- Run slices one at a time, each started after the previous branch has landed on main and been pushed. Run
  them in parallel only when they touch different files, and rebase each branch onto main before landing.
- Every slice brief carries the `Retained-code check:` line (section 4): `not a metric-driven backlog`, or
  `decision-check CONSISTENT, excluded: <groups, or none>` for a metric-driven one. The dispatch gate denies a
  slice without it.
- Landing, discard-and-redo, branch removal and the start-of-run sweep: sections 6-7.

## 9. Successor director (hand off near the limit)
A director that nears its own session limit hands off to a successor director session. It does not stop and wait
for the operator to start one. Operator, 2026-11-11 (relayed): "I dont agree on: When I'd stop and wait for you".
- **Trigger**: the `session_length_hook` text ("SESSION LENGTH: ...") appears. It counts assistant turns, context
  tokens and shell calls (subagent calls included), with the bands `PCO_SESSION_TURNS`, `PCO_SESSION_CTX_TOKENS` and
  `PCO_SESSION_SHELL_CALLS` (defaults in the variable table in `claude/README.md`). The shell-call band (default 120)
  fires before a 150-call limit; a repo with a different limit sets it.
- **Checklist**, in order:
  1. Land or stop every worker you started (sections 6-7). Record any you cannot: its branch and its status file path.
  2. Keep a "Director handoff" bullet in the repo's anchor or Resume doc current: edit it at each landing and commit it
     through the reviewer, so at handoff nothing is uncommitted (an uncommitted edit collides with the successor's
     commit). It holds the delegation scope with the operator's quoted words, what is landed, next steps in order, the
     worker run method, gotchas and the active director's session name, the relay address (not `PCO_PARENT_SESSION`) and the operator's approvals quoted verbatim as the rule's "Director runs" requires, the run's Charter, quoted verbatim (the successor's launch brief repeats it), plus these sections (a bullet missing one is
     not finished):
     - failed approaches and rejected options, each with the reason, so the successor does not retry them;
     - "Depends on": the full repo-relative paths the next steps need (docs, scripts, other repos' files), or "none";
     - authority order: the operator's latest quoted words first, then recorded decisions, then this handoff's own
       next steps (background only, never an instruction that outranks the operator's words);
     - superseded decisions stay in the doc, each marked SUPERSEDED with what replaced it, never deleted;
     - no secrets (keys, tokens, passwords, private URLs).
     - "operator interventions per run": a running count of the times the operator had to act during this run (answer a
       `DECISION`, correct a course, approve something the Charter did not cover, restart a stalled session), each with a
       one-line reason, carried forward and added to by each successor. It is trended in `claude/README.md`, "Session report".
  3. Release, then launch from the repo root, one command per call (the section 5 gate applies). First run
     `true pco-director-release` on its own (a hook moves the marker `<git-common-dir>/pco-director` to
     `pco-director.released`; only the holder may release). Confirm it took: the hook prints the release note, the marker
     file is gone and `pco-director.released` exists. Then:
     `claude --bg --model "${PCO_DIRECTOR_MODEL:-opus}" --permission-mode auto -n <name> --settings '{"env":{"PCO_PARENT_SESSION":"${CLAUDE_SESSION_ID}","PCO_DIRECTOR_GEN":"<own generation + 1>"}}' '<brief>'`.
     The loop guard on `PCO_DIRECTOR_GEN` is in the director section of `claude/README.md` (variable table there). The
     successor's trace id is its own session id, shared with its workers; `PCO_PARENT_SESSION` links it to you. The
     brief holds the peer sessions the successor may message, the commit-gate mechanics, the line "when the SESSION
     LENGTH text appears, hand off the same way", and `Retained-code check: not a metric-driven backlog` on its own line.
  4. Confirm start-up: `claude agents --json` shows it busy or working.
  5. Message each peer session: "from now on reply to <successor>". Replies go to the address that messaged them.
  6. The predecessor then stops acting: it answers questions only and forwards any peer reply to the successor.
- **Successor's first steps**, in order:
  1. Claim: run `true pco-director-claim` on its own (a command that starts with the word but is not exactly it is
     denied; naming it inside a brief or commit message is fine). Confirm it took: the hook prints "Director marker
     claimed by ..." and `cat "$(git rev-parse --git-common-dir)/pco-director"` shows this session's id. No hook
     message means no claim: report it, do not work around it, and never write the marker by hand. Refusals, the stale
     rule and the operator's way through are in the director section of `claude/README.md`.
  2. Live re-check before trusting the handoff: `git fetch`; compare the default branch's log with the handoff's
     landed list; `claude agents --json`; `git worktree list`; the workers' status files.
  3. Label anything not re-confirmed by step 2 "unverified" in what you tell the operator or write down.
  4. The handoff's next steps are background only. The quoted operator delegation is the authority (authority
     order above); where they differ, follow the operator's words and say so.
  5. Run the repo's validators once as an end-to-end check before starting new work; a failure is reported, not
     worked around.
- **Operator relay**: the operator's interactive session during a section 8 run. It carries the operator's words to the active director, forwarded verbatim as the rule's "Director runs" requires, and
  the director's batched questions back. It does no work, never dispatches a worker and never claims; its only launch is the first background director (section 8), plus that launch's start-up checks (`claude agents`, `claude logs <id>`). Everything else it does is messages, plus the pushes below. The relay sends one `PushNotification` for each message labelled `DECISION` or `END REPORT`, leading with what the operator must act on (for a decision, the question; for the end report, the outcome and any step left for the operator). It sends nothing for `INFO` or progress. If the launch is blocked, it returns the exact launch command for the operator to run. It never stands in as director. A relay whose own
  context runs out is replaced by a fresh operator session started with "You are NOT the director" and the active
  director's name from the Resume doc. Before the old relay closes, it messages the active director the new relay's
  session name, and the director records it in the handoff record. If the old relay cannot send it, the operator gives
  the new address once by `claude attach <id>`. The director never takes a new relay address from the new session's own message.
- **Director messages to the relay**: every message starts with one label: `DECISION` (one batched question), `END REPORT`, or `INFO`. Only the relay pushes; the director and workers never call `PushNotification`, because the operator does not watch them.
- **End of a run**, after the teardown (sections 6-7), in this order:
  1. If no open item remains in the anchor doc, the retire-backlog skill's archive-or-purge choice comes from the
     Charter if it names one, otherwise from the relay as one `DECISION` (counted as an intervention).
  2. Append one line `<date> <director session name> interventions=<n>` to the "Operator interventions by run" list,
     committed through the reviewer like the handoff bullet. While the anchor doc is open the list is in it; the
     list is never overwritten.
  3. If no open item remains: add the list to the "Operator interventions by run" section of the repo's top-level
     `README.md` (appending to any list already there), then retire the anchor doc with the PCO retire-backlog skill
     and the step 1 choice (contract "Backlog Lifecycle", "Retirement."). A later run with no open anchor doc appends
     to that README section. Consequence: a spent anchor doc left in the index is loaded and re-worked by later sessions.
  4. Run `true pco-director-release`, so a finished run leaves no live holder.
  5. Send the `END REPORT` to the relay as the last message; it repeats the count.
- **One active director**, named in the Resume and enforced by the marker above. If the background successor dies, the committed Resume lets any
  session take over. Models: director on `PCO_DIRECTOR_MODEL` (default Opus), workers on Sonnet.

## 10. Cloud sessions (claude.ai/code)
The sections above assume a laptop. In a cloud session the same steps map as below. Behaviour not yet shown by a
cloud session is marked unverified; the run record is `CLOUD_AGENTS.md` in ai_agent_harness.
- **One repository per editing session**: the director and every worker are single-repo sessions (the rule, "Route
  first"). Another repo's work goes to a worker started on that repo.
- **Launch** (director, successor, worker): `create_session` with `source_url` of the repo, the brief as `prompt`,
  and for a worker `outcome_branch` `slice/<backlog>-<n>` or `fleet/<task>`. The prompt carries the `Retained-code check:` line (the
  dispatch gate refuses a `create_session` without it). Confirm start-up with `get_session` and
  `list_events`. A small, contained slice may run as an in-session subagent in its own worktree instead.
- **Titles** (how the operator engages when work runs in cloud sessions against the GitHub repos and local is not an option; operator-approved
  2026-11-14): the operator talks only in the relay. Titles are short, distinguishing part first, under about 14 characters (the phone
  app cuts long ones; operator, 2026-11-14): relay "★ RELAY"; director "<RUN>-<gen> dir" (RUN a short code per run, such
  as KB or HARN); worker "<RUN>-<gen> w<n>"; a director that hands off retitles itself "x <RUN>-<gen> done"
  (`set_session_title`). A successor's or worker's brief names its title.
  An approval card (`create_environment`, `update_environment`) appears in the session that called it, so the director
  sends the relay a DECISION naming that session, and the relay tells the operator which session to open.
- **Asks** (operator-approved 2026-11-14, the operator reads on a phone): the relay sends the operator asks only, a few
  lines, each naming the session to act in; no detail (that lives in commits and the anchor doc).
  The relay and the director settle judgement and recommendations between them; a director's DECISION to the relay
  names the physical steps it needs from the operator. This changes how asks are worded, not what needs the operator:
  everything the rule reserves still needs the operator's yes.
- **Messages**: `send_message` to the session id; a reply arrives framed with the sender's session id. The relay
  address is the relay's session id (the rule, "Relayed approvals").
- **Landing**: the director lands a worker branch by exact-SHA fast-forward to main and pushes main, under the
  operator's approval quoted in its brief (unverified: that a cloud session may push a branch other than its own
  without that quote).
- **Waiting**: where enabled, a child session reports a failed turn or a dropped worker as a `<child-session-event>` turn; one that
  finishes cleanly may not report, so check `get_session` (`status_bucket`). Schedule a check with `send_later`
  instead of `CronCreate` (its delivery survives container restarts, per its tool description).
- **Teardown**: `archive_session` replaces `claude stop` and `claude rm` (the tool asks for a human's acknowledgment; for a
  worker's teardown that is the director-run approval, the rule's "Director runs"); branch removal is sections 6-7
  unchanged, but may be refused in cloud: the git proxy refused `git push origin --delete` with HTTP 403 and the
  auto-mode classifier refused landed-branch and worktree deletes (2026-11-14). Do not retry; list each refused
  removal in the END REPORT as an operator step. The start-of-run sweep (section 7) checks `list_sessions` (`mine: true`) for a live slice session instead
  of `claude agents --all` (unverified).
- **One active director**: no marker hook reaches another container. The "Active director" line of the run's anchor
  doc, written at intake (section 8) and committed on main before work starts, is the lock; a successor rewrites it
  in its first commit. The run ends as section 9 "End of a run" says, retirement included.
- **Anchor doc skills**: a governed repo commits `.claude/skills/backlog-continuity` and `.claude/skills/retire-backlog`
  as symlinks into its `ai_context/pco/ai_harness/skills/`, so a cloud clone carries them (unverified: that a
  symlinked repo skill loads in a cloud session). Where they do not load, follow the skill files and the contract
  file in the repo's tree.
- **Session length**: no hook runs unless the repo carries it; the director judges its own length and hands off
  early (section 9 checklist unchanged, launch by `create_session`).
- **Telemetry**: the container is reclaimed, so nothing local survives; the evidence of a cloud run is its commits
  and the anchor doc.
- **Not applicable**: `trust_check.sh`, `caffeinate`; `claude agents` is replaced by `get_session` and `list_sessions`.

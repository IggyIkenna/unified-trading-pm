---
doc_type: issue
title: A quickmerge --isolated worktree from a DIFFERENT slot/session appears nested inside slot 16's own directory tree, repeatedly blocking /done's dirty-check for unrelated tasks
summary: >-
  Slot 16's worktree contains `.tabs/16/oms-wt.oc3YkB` — a live git worktree whose HEAD commits are authored
  `ikennaigboaka [slot-2·laptop]`, not slot 16. It is a genuinely LIVE, actively-committing session (confirmed via
  `pgrep -f oms-wt.oc3YkB` returning 2 processes, and commits landing every few minutes) working an execution-service
  DeFi transfer/bridge refactor — not orphaned WIP. Because it is a `git status`-dirty directory physically located
  under `.tabs/16/`, the orchestrator's `/api/slots/16/done` dirty-check (`worker.md` DONE-GATE) treats it as slot 16's
  own uncommitted WIP and hard-rejects `/done` with `required_action: "quickmerge-or-stash"` — even though slot 16's
  own actual work (unrelated plan-doc edits, already committed + pushed + verified on origin) has nothing to do with
  it. This blocked 3 separate `/done` calls in one session (2026-08-21, slot 16) across 2 different unrelated tasks.
  Per RULES.md's "don't touch dirty files in another agent's tree" + the LIVENESS-gated inherited-dirty-WIP rule, this
  worktree must NOT be stashed/touched while live — so the only available response each time was to wait and retry.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [multi-agent-safety, per-tab-worktrees, quickmerge-isolated, done-gate, worker-lifecycle]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-21
priority: P2
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Discovered live during 2 unrelated slot-16 worker tasks (sports_taxonomy_p4_backfill, then
  cross_cutting_satellite_ao_dispatch_batch21, then defi_satellite_ao_dispatch_batch2_finalize) on 2026-08-21 —
  every `/done` call rejected on the exact same foreign path.
drift_direction: advance-code
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
  ]
---

# Foreign `--isolated` quickmerge worktree nested in the wrong slot's directory

## What was found (measured, 2026-08-21, slot 16)

- `.tabs/16/oms-wt.oc3YkB` exists as a real git worktree (`.git` is a file, not a directory — the worktree-pointer
  shape) with `git status --porcelain` showing 24-29 staged changes across the session (file count grew over time:
  `execution_service/adapters/defi_instruction_routes.py`, several `execution_service/engine/transfers/*` files,
  `execution_service/engine/delta_proxy_repricer.py`, `execution_service/engine/quote_maintenance.py`, several
  deleted `defi_execution/*`/`transfers/live_bridge_adapter.py` files, and matching test files).
- `git -C oms-wt.oc3YkB log -1` shows HEAD authored `ikennaigboaka [slot-2·laptop]` — a DIFFERENT slot (2, not 16)
  and a DIFFERENT machine class (`laptop`, not this AO worker's `planning` VM).
- `pgrep -f "oms-wt.oc3YkB"` returned 2 live processes at every check across an ~815s window, confirming this is a
  currently-active session, not orphaned/dead WIP — per the liveness rule, this must be PROTECTED (never
  stashed/touched), which is what this session did each time (waited/retried `/done` rather than acting on it).
- Branch is `live-defi-rollout` — same integration branch every slot tracks, consistent with a `quickmerge --isolated`
  worktree per CLAUDE.md: _"Ship scripts COMMIT FROM AN ISOLATED WORKTREE so a peer sharing your checkout can't
  revert your edits... `--isolated` in quickmerge is opt-in, NOT default (laptop-only, auto-OFF on AO)"_ — the
  `slot-2·laptop` author identity is consistent with a laptop-interactive session using `--isolated`.

## Why it matters

The orchestrator's `/api/slots/<N>/done` dirty-check (per `worker.md`'s DONE-GATE) appears to scan the entire
`.tabs/<N>/` directory tree for uncommitted changes, including this nested foreign worktree — so ANY slot whose
directory happens to contain another session's `--isolated` worktree gets its own unrelated `/done` calls
hard-rejected until the foreign session's WIP clears. This is NOT the already-documented "two operators sharing one
slot's checkout" class (`per-tab-worktrees.md`) — that's about two sessions sharing the SAME slot's identity/index.
This is a DIFFERENT slot's isolated worktree apparently landing inside slot 16's path.

**Unconfirmed root cause** (flagging, not asserting): whether `quickmerge --isolated`'s worktree-creation path scopes
the new worktree under the INVOKING slot's own `.tabs/<N>/` directory correctly, or uses some other path resolution
(e.g. relative to `pwd` at invocation time, or a shared temp root) that can land it under a DIFFERENT slot's tree when
invoked from an unusual cwd. Not investigated further this session — the live worktree could not safely be inspected
beyond `git log`/`git status`/`pgrep` without risking interference with a live session's work.

**Impact observed this session**: 3 separate `/done` calls across 2 different completed, unrelated, already-verified-
on-origin tasks were rejected and had to be retried (one eventually succeeded when the task turned out to be
orphaned and the check short-circuited; the pattern is otherwise a real, recurring source of wasted `/done` retries
/ worker confusion for any slot unlucky enough to have a foreign isolated worktree land in its tree).

## Todos

- [ ] [SCRIPT] P2. **Confirm whether `oms-wt.oc3YkB` is genuinely a quickmerge `--isolated` worktree** — grep
      `deployment-service`/`agent-orchestrator`/PM `scripts/quickmerge.sh`'s isolated-worktree creation path (search
      for `--isolated`, `mktemp`, worktree-add invocations) to see how the worktree's parent directory is chosen, and
      whether it can resolve to a DIFFERENT slot's `.tabs/<N>/` than the invoking session's own. If confirmed, this is
      a path-resolution bug in the isolated-worktree feature, not a done-gate bug.
- [ ] [SCRIPT] P2. **If confirmed as a path-resolution bug**: fix the isolated-worktree creation to always nest under
      the INVOKING session's own slot directory (or a slot-independent shared location the done-gate dirty-check
      explicitly excludes), so it can never land inside a different slot's `.tabs/<N>/` tree.
- [ ] [SCRIPT] P2. **Alternatively/additionally**: harden `/api/slots/<N>/done`'s dirty-check to recognize and skip a
      nested `oms-wt.*`/other-slot-owned worktree (distinguishable via its own commit author identity not matching
      slot N's own configured identity) rather than treating it as slot N's own WIP — this closes the symptom even if
      the root-cause path-resolution bug above turns out to be by-design/unfixable.
- [ ] [REVIEW] P3. **Once the fix lands**: verify by re-checking `.tabs/16/` (or whichever slot next reproduces the
      symptom) no longer shows a foreign worktree's dirty state blocking its own `/done` calls.

## Progress Log

- **2026-08-21 (slot-16)** — Filed after the pattern recurred 3x in one session across 2 unrelated tasks. No code
  investigated/changed — pure observation + escalation, since directly probing `quickmerge --isolated`'s internals
  mid-session would have meant editing shared script files outside this task's scope while a live peer session was
  actively working nearby.
- **2026-08-21 (slot-16), post-compact re-check** — Re-confirmed still live: `oms-wt.oc3YkB`'s HEAD commit was 319s
  old at check time (author `github-actions[bot]`, not the earlier-seen `ikennaigboaka [slot-2·laptop]` — the
  authoring identity on this worktree is not stable across commits, consistent with a bot/CI process periodically
  committing into the same live session rather than a single human's commits). `/api/slots/16/done` retried against
  `http://localhost:8765` (unauthenticated — see the worker.md auth-gap fix landed same commit) and rejected again
  with the identical `oms-wt.oc3YkB` dirty-file list (30 files, same set as before). Per pre-compact Step 7.2, two
  identical consecutive failures = stable condition, not flapping — stopped retrying; the already-shipped todo-1 work
  (`unified-trading-pm@832b8de031`+`19d99de82a`) stays acked-pending, no data at risk since it's already on origin.
- **2026-08-21 (slot-16), post-/heartbeat resume** — Third check, new session tick: `/heartbeat` re-dispatched the
  identical task (`dispatch_reason: "resume"`), confirming the server itself still considers this task open pending
  `/done`. `oms-wt.oc3YkB` HEAD had advanced to a new commit (still `github-actions[bot]`) but the staged dirty-file
  set was byte-identical to the two prior checks (same 30 files, same M/D markers) — the live session is committing
  but never reaching a clean staged tree. `/done` retried once more (3rd attempt, spaced across a full compaction
  cycle, not blind-looped) and rejected with the identical dirty list. This is now a 3x-identical stable condition
  across ~1hr+ of wall-clock time, not a transient race — raises confidence this is a long-lived, possibly-stuck-open
  live session (or one that will simply never present a clean tree until it finishes its own multi-commit sequence),
  strengthening todo 3's case (harden the done-gate to skip foreign-owned worktrees) as the more tractable fix vs.
  waiting for `oms-wt.oc3YkB` to clear naturally. Stopped retrying again per Step 7.2; no further `/done` attempts
  planned until either this worktree disappears or todo 3 lands.
